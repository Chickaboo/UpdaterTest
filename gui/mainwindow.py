from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtCore import QDateTime, QFileInfo, Qt
from typing import List, Tuple, Optional
import logging
import json
from pathlib import Path
import sys
import webbrowser
from core.updater import Updater

from core.tournament import Tournament
from core.player import Player
from core.constants import *

from gui.dialogs import SettingsDialog
from gui.players_tab import PlayersTab
from gui.tournament_tab import TournamentTab
from gui.standings_tab import StandingsTab
from gui.crosstable_tab import CrosstableTab
from gui.history_tab import HistoryTab

# --- Main Application Window ---

class SwissTournamentApp(QtWidgets.QMainWindow):
    """Main application window for the Swiss Tournament."""
    def __init__(self) -> None:
        super().__init__()
        self.tournament: Optional[Tournament] = None
        # current_round_index tracks rounds with recorded results.
        # 0 = no results yet. 1 = R1 results are in.
        self.current_round_index: int = 0
        self.last_recorded_results_data: List[Tuple[str, str, float]] = []
        self._current_filepath: Optional[str] = None
        self._dirty: bool = False
        self.updater: Optional[Updater] = None

        self._load_version()
        self._setup_ui()
        self._update_ui_state()
        if self.updater:
            QtCore.QTimer.singleShot(1500, self.check_for_updates_auto)

    def _load_version(self):
        """Loads the application version from version.json."""
        try:
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent.parent
            
            version_file = base_path / "version.json"

            with open(version_file, "r") as f:
                data = json.load(f)
                self.current_version = data.get("version", "0.0.0")
                self.updater = Updater(self.current_version)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logging.error(f"Could not load version information: {e}")
            self.current_version = APP_VERSION # Fallback
            self.updater = None
            QtWidgets.QMessageBox.warning(self, "Version Error", "Could not determine application version. Update checking is disabled.")

    def _setup_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 1000, 800)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        self._setup_main_panel()
        self._setup_menu()
        self._setup_toolbar()
        self.statusBar().showMessage("Ready - Create New or Load Tournament.")
        logging.info(f"{APP_NAME} v{APP_VERSION} started.")
        QtCore.QTimer.singleShot(100, self.show_about_dialog)

    def _setup_main_panel(self):
        """Creates the tab widget and populates it with the modular tab classes."""
        self.tabs = QtWidgets.QTabWidget()
        self.main_layout.addWidget(self.tabs)

        self.players_tab = PlayersTab(self)
        self.tournament_tab = TournamentTab(self)
        self.standings_tab = StandingsTab(self)
        self.crosstable_tab = CrosstableTab(self)
        self.history_tab = HistoryTab(self)

        self.players_tab.status_message.connect(self.statusBar().showMessage)
        self.tournament_tab.status_message.connect(self.statusBar().showMessage)
        self.players_tab.history_message.connect(self.history_tab.update_history_log)
        self.tournament_tab.history_message.connect(self.history_tab.update_history_log)
        self.players_tab.dirty.connect(self.mark_dirty)
        self.tournament_tab.dirty.connect(self.mark_dirty)
        self.tournament_tab.dirty.connect(self._update_ui_state)
        self.tournament_tab.round_completed.connect(self._on_round_completed)
        self.tournament_tab.standings_update_requested.connect(self.standings_tab.update_standings_table)

        self.tabs.addTab(self.players_tab, "Players")
        self.tabs.addTab(self.tournament_tab, "Tournament")
        self.tabs.addTab(self.standings_tab, "Standings")
        self.tabs.addTab(self.crosstable_tab, "Cross-Table")
        self.tabs.addTab(self.history_tab, "History Log")

    def _setup_menu(self):
        """Sets up the main menu bar, connecting actions to methods in the main window or tabs."""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        self.new_action = self._create_action("&New Tournament...", self.prompt_new_tournament, "Ctrl+N")
        self.load_action = self._create_action("&Load Tournament...", self.load_tournament, "Ctrl+O")
        self.save_action = self._create_action("&Save Tournament", self.save_tournament, "Ctrl+S")
        self.save_as_action = self._create_action("Save Tournament &As...", lambda: self.save_tournament(save_as=True), "Ctrl+Shift+S")
        self.import_players_action = self._create_action("&Import Players from CSV...", self.players_tab.import_players_csv)
        self.export_players_action = self._create_action("&Export Players to CSV...", self.players_tab.export_players_csv)
        self.export_standings_action = self._create_action("&Export Standings...", self.standings_tab.export_standings)
        self.settings_action = self._create_action("S&ettings...", self.show_settings_dialog)
        self.exit_action = self._create_action("E&xit", self.close, "Ctrl+Q")

        file_menu.addActions([self.new_action, self.load_action, self.save_action, self.save_as_action])
        file_menu.addSeparator()
        file_menu.addActions([self.import_players_action, self.export_players_action, self.export_standings_action])
        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Tournament Menu
        tournament_menu = menu_bar.addMenu("&Tournament")
        self.start_action = self._create_action("&Start Tournament", self.tournament_tab.start_tournament)
        self.prepare_round_action = self._create_action("&Prepare Next Round", self.tournament_tab.prepare_next_round)
        self.record_results_action = self._create_action("&Record Results && Advance", self.tournament_tab.record_and_advance)
        self.undo_results_action = self._create_action("&Undo Last Results", self.tournament_tab.undo_last_results)
        tournament_menu.addActions([self.start_action, self.prepare_round_action, self.record_results_action, self.undo_results_action])

        # Player Menu
        player_menu = menu_bar.addMenu("&Players")
        self.add_player_action = self._create_action("&Add Player...", self.players_tab.add_player_detailed)
        player_menu.addAction(self.add_player_action)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction("Players", lambda: self.tabs.setCurrentWidget(self.players_tab))
        view_menu.addAction("Tournament Control", lambda: self.tabs.setCurrentWidget(self.tournament_tab))
        view_menu.addAction("Standings", lambda: self.tabs.setCurrentWidget(self.standings_tab))
        view_menu.addAction("Cross-Table", lambda: self.tabs.setCurrentWidget(self.crosstable_tab))
        view_menu.addAction("History Log", lambda: self.tabs.setCurrentWidget(self.history_tab))

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About...", self.show_about_dialog)
        self.update_action = self._create_action("Check for &Updates...", self.check_for_updates_manual)
        help_menu.addAction(self.update_action)

    def _create_action(self, text: str, slot: callable, shortcut: str = "", tooltip: str = "") -> QAction:
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut: action.setShortcut(QtGui.QKeySequence(shortcut))
        if tooltip: action.setToolTip(tooltip); action.setStatusTip(tooltip)
        action.setIconVisibleInMenu(False)  # Hide icon in menus
        return action

    def _setup_toolbar(self):
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setIconSize(QtCore.QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                background: #f9fafb;
                border-bottom: 1px solid #bbb;
            }
        """)
        QtGui.QIcon.setThemeName("Adwaita")  # Adwaita is often monochrome, fallback to system if not found
        self.new_action.setIcon(QtGui.QIcon.fromTheme("document-new"))
        self.load_action.setIcon(QtGui.QIcon.fromTheme("document-open"))
        self.save_action.setIcon(QtGui.QIcon.fromTheme("document-save"))
        self.start_action.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        self.prepare_round_action.setIcon(QtGui.QIcon.fromTheme("view-refresh"))
        self.record_results_action.setIcon(QtGui.QIcon.fromTheme("document-send"))
        self.undo_results_action.setIcon(QtGui.QIcon.fromTheme("edit-undo"))
        # Add toolbar actions
        toolbar.addActions([self.new_action, self.load_action, self.save_action])
        toolbar.addSeparator()
        toolbar.addActions([self.start_action, self.prepare_round_action, self.record_results_action, self.undo_results_action])

    def _update_ui_state(self):
        """Updates the state of UI elements based on the tournament's current state."""
        tournament_exists = self.tournament is not None
        pairings_generated = len(self.tournament.rounds_pairings_ids) if tournament_exists else 0
        results_recorded = self.current_round_index
        total_rounds = self.tournament.num_rounds if tournament_exists else 0
        tournament_started = tournament_exists and pairings_generated > 0
        tournament_finished = tournament_exists and results_recorded >= total_rounds and total_rounds > 0

        # can_start = tournament_exists and not tournament_started and len(self.tournament.players) >= 2
        can_start = tournament_exists and not tournament_started
        can_prepare = tournament_exists and tournament_started and pairings_generated == results_recorded and not tournament_finished
        can_record = tournament_exists and tournament_started and pairings_generated > results_recorded and not tournament_finished
        can_undo = tournament_exists and results_recorded > 0 and bool(self.last_recorded_results_data)

        # Update main actions (toolbar and menu)
        self.start_action.setEnabled(can_start)
        self.prepare_round_action.setEnabled(can_prepare)
        self.record_results_action.setEnabled(can_record)
        self.undo_results_action.setEnabled(can_undo)
        self.save_action.setEnabled(tournament_exists)
        self.save_as_action.setEnabled(tournament_exists)
        self.export_standings_action.setEnabled(tournament_exists and results_recorded > 0)
        self.import_players_action.setEnabled(tournament_exists and not tournament_started)
        self.export_players_action.setEnabled(tournament_exists and len(self.tournament.players) > 0)
        self.add_player_action.setEnabled(not tournament_started)
        self.settings_action.setEnabled(tournament_exists)

        # Do NOT disable the Players tab after tournament starts
        # self.tabs.setTabEnabled(self.tabs.indexOf(self.players_tab), not tournament_started)

        # Delegate UI state updates to the tabs themselves
        self.players_tab.update_ui_state()
        self.tournament_tab.update_ui_state()
        self.standings_tab.update_ui_state()
        self.crosstable_tab.update_ui_state()
        self.history_tab.update_ui_state()

        # Update window title
        title = APP_NAME
        if self._current_filepath:
            title += f" - {QFileInfo(self._current_filepath).fileName()}"
        if self._dirty:
            title += "*"
        self.setWindowTitle(title)
        
        # Update status bar
        status = "Ready"
        if tournament_exists:
            if not tournament_started:
                status = f"Add players, then Start. {len(self.tournament.players)} players registered."
            elif can_record:
                status = f"Round {results_recorded + 1} pairings ready. Please enter results."
            elif can_prepare:
                status = f"Round {results_recorded} results recorded. Prepare Round {results_recorded + 1}."
            elif results_recorded == total_rounds and total_rounds > 0:
                status = f"Tournament finished. Final standings are available."
            else:
                status = f"Tournament in progress. Completed rounds: {results_recorded}/{total_rounds}."
        self.statusBar().showMessage(status)

    def mark_dirty(self, dirty=True):
        if self._dirty != dirty:
            self._dirty = dirty
            self._update_ui_state()

    def mark_clean(self):
        self.mark_dirty(False)

    def _set_tournament_on_tabs(self):
        """Passes the current tournament object to all tabs so they can access its data."""
        for tab in [self.players_tab, self.tournament_tab, self.standings_tab, self.crosstable_tab, self.history_tab]:
            if hasattr(tab, 'set_tournament'):
                tab.set_tournament(self.tournament)
        # Also set current_round_index on tournament_tab if method exists
        if hasattr(self.tournament_tab, 'set_current_round_index'):
            self.tournament_tab.set_current_round_index(self.current_round_index)
        # Ensure UI state is updated after tournament propagation
        self._update_ui_state()

    def reset_tournament_state(self):
        """Resets the entire application to a clean state."""
        self.tournament = None
        self.current_round_index = 0
        self.last_recorded_results_data = []
        self._current_filepath = None
        self.mark_clean()
        
        self._set_tournament_on_tabs() # Pass None to clear tabs
        
        # Explicitly clear UI elements in tabs
        self.players_tab.list_players.clear()
        self.tournament_tab.table_pairings.setRowCount(0)
        self.tournament_tab.lbl_bye.setText("Bye: None")
        self.standings_tab.table_standings.setRowCount(0)
        self.crosstable_tab.table_crosstable.setRowCount(0)
        self.history_tab.history_view.clear()
        
        self._update_ui_state()

    def _on_round_completed(self, new_round_index: int) -> None:
        """
        Slot called when a round is successfully recorded and advanced in the TournamentTab.
        Updates the main window's round index and UI state.
        """
        self.current_round_index = new_round_index
        # Propagate the new round index to the tournament_tab
        if hasattr(self.tournament_tab, 'set_current_round_index'):
            self.tournament_tab.set_current_round_index(new_round_index)
        self._update_ui_state()

    def prompt_new_tournament(self):
        if not self.check_save_before_proceeding():
            return
        self.reset_tournament_state()
        
        self.tournament = Tournament([], num_rounds=3, tiebreak_order=list(DEFAULT_TIEBREAK_SORT_ORDER))
        
        if self.show_settings_dialog():
            self.update_history_log(f"--- New Tournament Created (Rounds: {self.tournament.num_rounds}) ---")
            self.mark_dirty()
            self._set_tournament_on_tabs()
            self.standings_tab.update_standings_table_headers()
        else:
            self.reset_tournament_state()
        
        self._update_ui_state()

    def show_settings_dialog(self) -> bool:
        if not self.tournament:
            return False
        
        dialog = SettingsDialog(self.tournament.num_rounds, self.tournament.tiebreak_order, self)
        tournament_started = len(self.tournament.rounds_pairings_ids) > 0
        dialog.spin_num_rounds.setEnabled(not tournament_started)

        if dialog.exec():
            new_rounds, new_tiebreaks = dialog.get_settings()
            if self.tournament.num_rounds != new_rounds and not tournament_started:
                self.tournament.num_rounds = new_rounds
                self.update_history_log(f"Number of rounds set to {new_rounds}.")
                self.mark_dirty()
            
            if self.tournament.tiebreak_order != new_tiebreaks:
                self.tournament.tiebreak_order = new_tiebreaks
                self.update_history_log(f"Tiebreak order updated.")
                self.mark_dirty()
                self.standings_tab.update_standings_table_headers()
                self.standings_tab.update_standings_table()

            self._update_ui_state()
            return True
        return False

    def update_history_log(self, message: str):
        """Appends a timestamped message to the history log tab."""
        self.history_tab.update_history_log(message)

    def save_tournament(self, save_as=False):
        if not self.tournament: return False
        if not self._current_filepath or save_as:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Tournament", "", "JSON Files (*.json)")
            if not filename: return False
            self._current_filepath = filename
        
        try:
            data = self.tournament.to_dict()
            data['gui_state'] = {
                'current_round_index': self.current_round_index,
                'last_recorded_results_data': self.last_recorded_results_data
            }
            with open(self._current_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.mark_clean()
            self.statusBar().showMessage(f"Tournament saved to {self._current_filepath}")
            self.update_history_log(f"--- Tournament saved to {QFileInfo(self._current_filepath).fileName()} ---")
            return True
        except Exception as e:
            logging.exception("Error saving tournament:")
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Could not save tournament:\n{e}")
            return False

    def load_tournament(self):
        if not self.check_save_before_proceeding(): return
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Tournament", "", "JSON Files (*.json)")
        if not filename: return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.reset_tournament_state()
            self.tournament = Tournament.from_dict(data)
            
            gui_state = data.get('gui_state', {})
            self.current_round_index = gui_state.get('current_round_index', 0)
            self.last_recorded_results_data = gui_state.get('last_recorded_results_data', [])
            self._current_filepath = filename
            
            self._set_tournament_on_tabs()
            
            # Refresh all views
            self.players_tab.refresh_player_list()
            self.standings_tab.update_standings_table_headers()
            self.standings_tab.update_standings_table()
            self.crosstable_tab.update_crosstable()
            self.tournament_tab.display_pairings_for_input() # Display current round
            
            self.mark_clean()
            self.update_history_log(f"--- Tournament loaded from {QFileInfo(filename).fileName()} ---")
            self.statusBar().showMessage(f"Loaded tournament: {self.tournament.name}")

        except Exception as e:
            logging.exception("Error loading tournament:")
            self.reset_tournament_state()
            QtWidgets.QMessageBox.critical(self, "Load Error", f"Could not load tournament file:\n{e}")
        
        self._update_ui_state()

    def check_save_before_proceeding(self) -> bool:
        """Checks for unsaved changes and prompts the user to save."""
        if not self._dirty:
            return True
        reply = QtWidgets.QMessageBox.question(self, "Unsaved Changes",
                                     "You have unsaved changes. Do you want to save them?",
                                     QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Discard | QtWidgets.QMessageBox.StandardButton.Cancel)
        if reply == QtWidgets.QMessageBox.StandardButton.Save:
            return self.save_tournament()
        return reply != QtWidgets.QMessageBox.StandardButton.Cancel

    def show_about_dialog(self):
        """Show the About dialog with app info and about.webp image."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtGui import QPixmap
        import os
        dialog = QDialog(self)
        dialog.setWindowTitle(f"About {APP_NAME}")
        layout = QVBoxLayout(dialog)
        # Add about.webp image
        image_path = os.path.join(os.path.dirname(__file__), "about.webp")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                img_label = QLabel()
                img_label.setPixmap(pixmap.scaledToWidth(220))
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(img_label)
        # Add app info text
        info_label = QLabel(f"<b>{APP_NAME} v{APP_VERSION}</b><br>\nSwiss Tournament Manager\n<br>Copyright \u00A9 2025\n<br>Developed by Chickaboo\n<br><br>For help, join the <a href=\"https://discord.gg/eEnnetMDfr\">Discord</a> or contact <a href=\"https://www.chickaboo.net/contact\">support</a>.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setOpenExternalLinks(True)  # <-- Add this line
        layout.addWidget(info_label)
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)
        dialog.setLayout(layout)
        dialog.exec()

    def closeEvent(self, event: QCloseEvent):
        if self.check_save_before_proceeding():
            logging.info(f"{APP_NAME} closing.")
            event.accept()
        else:
            event.ignore()

    def check_for_updates_manual(self):
        """Manually checks for updates and notifies the user of the result."""
        if not self.updater:
            QtWidgets.QMessageBox.information(self, "Update Check", "The update checker is not configured.")
            return

        self.statusBar().showMessage("Checking for updates...")
        has_update = self.updater.check_for_updates()
        if has_update:
            self.prompt_update()
        else:
            self.statusBar().showMessage("No new updates available.")
            QtWidgets.QMessageBox.information(self, "Update Check", f"You are using the latest version of {APP_NAME} ({self.current_version}).")

    def check_for_updates_auto(self):
        """Automatically checks for updates in the background."""
        if not self.updater:
            return
        
        if self.updater.check_for_updates():
            self.prompt_update()

    def prompt_update(self):
        """Shows a dialog prompting the user to download the new version."""
        if not self.updater or not self.updater.latest_version_info:
            return

        latest_version = self.updater.get_latest_version()
        release_notes = self.updater.get_release_notes()
        download_url = self.updater.get_download_url()

        if not all([latest_version, release_notes, download_url]):
            QtWidgets.QMessageBox.warning(self, "Update Error", "Could not retrieve complete update information.")
            return

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg_box.setText(f"A new version of {APP_NAME} is available!")
        msg_box.setInformativeText(
            f"<b>Version {latest_version}</b> (You have {self.current_version})\n\n"
            f"<b>Release Notes:</b>\n{release_notes}"
        )
        
        download_button = msg_box.addButton("Download", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg_box.addButton("Later", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(download_button)

        msg_box.exec()

        if msg_box.clickedButton() == download_button:
            webbrowser.open(download_url)

    def _on_round_completed(self, round_index: int):
        """Slot called when a round is recorded and the tournament is advanced."""
        self.current_round_index = round_index
        self.mark_dirty()
        self._update_ui_state()