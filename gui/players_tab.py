from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, pyqtSignal
from core.player import Player
from core.tournament import Tournament
from core.constants import DEFAULT_TIEBREAK_SORT_ORDER
from gui.dialogs import PlayerDetailDialog
from typing import Optional
import csv
import logging

class PlayersTab(QtWidgets.QWidget):
    status_message = pyqtSignal(str)
    history_message = pyqtSignal(str)
    dirty = pyqtSignal()
    request_reset_tournament = pyqtSignal()
    standings_update_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tournament = None  # This should be set by the main window
        self.main_layout = QtWidgets.QVBoxLayout(self)
        player_group = QtWidgets.QGroupBox("Players")
        player_group.setToolTip("Manage players. Right-click list items for actions.")
        player_group_layout = QtWidgets.QVBoxLayout(player_group)
        self.list_players = QtWidgets.QListWidget()
        self.list_players.setToolTip("Registered players. Right-click to Edit/Withdraw/Reactivate/Remove.")
        self.list_players.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_players.customContextMenuRequested.connect(self.on_player_context_menu)
        self.list_players.setAlternatingRowColors(True)
        player_group_layout.addWidget(self.list_players)
        self.btn_add_player_detail = QtWidgets.QPushButton(" Add New Player...")
        self.btn_add_player_detail.setToolTip("Open dialog to add a new player with full details.")
        self.btn_add_player_detail.clicked.connect(self.add_player_detailed)
        player_group_layout.addWidget(self.btn_add_player_detail)
        self.main_layout.addWidget(player_group)

    def on_player_context_menu(self, point: QtCore.QPoint) -> None:
        item = self.list_players.itemAt(point)
        if not item or not self.tournament: return
        player_id = item.data(Qt.ItemDataRole.UserRole)
        player = self.tournament.players.get(player_id)
        if not player: return

        # Tournament started if pairings for R1 (index 0) exist.
        tournament_started = len(self.tournament.rounds_pairings_ids) > 0

        menu = QtWidgets.QMenu(self)
        edit_action = menu.addAction("Edit Player Details...")
        # Withdraw/Reactivate action text depends on player's current state
        withdraw_action_text = "Withdraw Player" if player.is_active else "Reactivate Player"
        withdraw_action = menu.addAction(withdraw_action_text)
        remove_action = menu.addAction("Remove Player")

        edit_action.setEnabled(not tournament_started) 
        remove_action.setEnabled(not tournament_started) 
        # Withdraw/Reactivate should be possible anytime, affecting future pairings/bye eligibility.
        withdraw_action.setEnabled(True) 

        action = menu.exec(self.list_players.mapToGlobal(point))

        if action == edit_action:
            dialog = PlayerDetailDialog(self, player_data=player.to_dict())
            if dialog.exec():
                data = dialog.get_player_data()
                if not data['name']:
                    QtWidgets.QMessageBox.warning(self, "Edit Error", "Player name cannot be empty.")
                    return
                # Check for duplicate name (only if name changed and it's not the current player's ID)
                if data['name'] != player.name and any(p.name == data['name'] for p in self.tournament.players.values()):
                     QtWidgets.QMessageBox.warning(self, "Edit Error", f"Another player named '{data['name']}' already exists.")
                     return
                
                player.name = data['name']
                player.rating = data['rating']
                player.gender = data.get('gender')
                player.dob = data.get('dob')
                player.phone = data.get('phone')
                player.email = data.get('email')
                player.club = data.get('club')
                player.federation = data.get('federation')
                
                self.update_player_list_item(player) # Helper to update QListWidgetItem
                self.history_message.emit(f"Player '{player.name}' details updated.")
                self.dirty.emit()
        elif action == withdraw_action:
             player.is_active = not player.is_active
             status_log_msg = "Withdrawn" if not player.is_active else "Reactivated"
             self.update_player_list_item(player)
             self.history_message.emit(f"Player '{player.name}' {status_log_msg}.")
             self.dirty.emit()
             self.standings_update_requested.emit() # Reflects active status if standings show inactive
             self.update_ui_state() # UI might depend on active player count

        elif action == remove_action:
             reply = QtWidgets.QMessageBox.question(self, "Remove Player", f"Remove player '{player.name}' permanently?",
                                                 QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                                                 QtWidgets.QMessageBox.StandardButton.No)
             if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                  # Remove from tournament data
                  if player.id in self.tournament.players:
                       del self.tournament.players[player.id]
                       self.history_message.emit(f"Player '{player.name}' removed from tournament.")
                  # Remove from UI list
                  self.list_players.takeItem(self.list_players.row(item))
                  self.parent().statusBar().showMessage(f"Player '{player.name}' removed.")
             # No need to handle No, as dialog will be closed

        # Update the UI state after any context menu action
        self.update_ui_state()

    def add_player_detailed(self):
        tournament_started = self.tournament and len(self.tournament.rounds_pairings_ids) > 0
        if tournament_started:
            QtWidgets.QMessageBox.warning(self, "Tournament Active", "Cannot add players after the tournament has started.")
            return
        if not self.tournament:
            # If adding player before "New Tournament" is fully confirmed via settings
            reply = QtWidgets.QMessageBox.information(self, "New Tournament", 
                                                  "A new tournament will be created with default settings. You can change settings later via File > Settings.",
                                                  QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
            if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return
            self.request_reset_tournament.emit() # Clear any previous partial state
            return  # Wait for main window to reset and set tournament, then user can retry add

        dialog = PlayerDetailDialog(self)
        if dialog.exec():
            data = dialog.get_player_data()
            if not data['name']:
                QtWidgets.QMessageBox.warning(self, "Validation Error", "Player name cannot be empty.")
                return
            if any(p.name == data['name'] for p in self.tournament.players.values()):
                QtWidgets.QMessageBox.warning(self, "Duplicate Player", f"Player '{data['name']}' already exists.")
                return
            new_player = Player(
                name=data['name'],
                rating=data['rating'],
                phone=data['phone'],
                email=data['email'],
                club=data['club'],
                federation=data['federation'],
                gender=data.get('gender'),
                dob=data.get('dob')
            )
            self.tournament.players[new_player.id] = new_player
            self.add_player_to_list_widget(new_player)
            self.status_message.emit(f"Added player: {new_player.name}")
            self.history_message.emit(f"Player '{new_player.name}' ({new_player.rating}) added.")
            self.dirty.emit()
            self.update_ui_state()

    def update_player_list_item(self, player: Player):
        """Finds and updates the QListWidgetItem for a given player."""
        for i in range(self.list_players.count()):
            item = self.list_players.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == player.id:
                display_text = f"{player.name} ({player.rating})"
                tooltip_parts = [f"ID: {player.id}"]
                if not player.is_active:
                    display_text += " (Inactive)"
                    tooltip_parts.append("Status: Inactive")
                else:
                    tooltip_parts.append("Status: Active")

                if player.gender: tooltip_parts.append(f"Gender: {player.gender}")
                if player.dob: tooltip_parts.append(f"Date of Birth: {player.dob}")
                if player.phone: tooltip_parts.append(f"Phone: {player.phone}")
                if player.email: tooltip_parts.append(f"Email: {player.email}")
                if player.club: tooltip_parts.append(f"Club: {player.club}")
                if player.federation: tooltip_parts.append(f"Federation: {player.federation}")
                
                item.setText(display_text)
                item.setToolTip("\n".join(tooltip_parts))
                item.setForeground(QtGui.QColor("gray") if not player.is_active else self.list_players.palette().color(QtGui.QPalette.ColorRole.Text))
                break

    def add_player_to_list_widget(self, player: Player):
         display_text = f"{player.name} ({player.rating})"
         tooltip_parts = [f"ID: {player.id}"]
         if not player.is_active:
             display_text += " (Inactive)"
             tooltip_parts.append("Status: Inactive")
         else:
            tooltip_parts.append("Status: Active")

         if player.gender: tooltip_parts.append(f"Gender: {player.gender}")
         if player.dob: tooltip_parts.append(f"Date of Birth: {player.dob}")
         if player.phone: tooltip_parts.append(f"Phone: {player.phone}")
         if player.email: tooltip_parts.append(f"Email: {player.email}")
         if player.club: tooltip_parts.append(f"Club: {player.club}")
         if player.federation: tooltip_parts.append(f"Federation: {player.federation}")

         list_item = QtWidgets.QListWidgetItem(display_text)
         list_item.setData(Qt.ItemDataRole.UserRole, player.id)
         list_item.setToolTip("\n".join(tooltip_parts))
         if not player.is_active:
              list_item.setForeground(QtGui.QColor("gray"))
         self.list_players.addItem(list_item)

    def import_players_csv(self):
        if self.tournament and len(self.tournament.rounds_pairings_ids) > 0:
            QtWidgets.QMessageBox.warning(self, "Import Error", "Cannot import players after tournament has started.")
            return
        if not self.tournament:
            QtWidgets.QMessageBox.warning(self, "No Tournament", "Please create a tournament before importing players.")
            return
        self._pending_import = False  # Clear flag if tournament exists

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Players", "", "CSV Files (*.csv);;Text Files (*.txt)")
        if not filename:
            return
        import csv
        try:
            with open(filename, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                added = 0
                for row in reader:
                    name = row.get("Name")
                    if not name:
                        continue
                    rating = row.get("Rating")
                    try:
                        rating = int(rating) if rating else None
                    except Exception:
                        rating = None
                    player = Player(
                        name=name,
                        rating=rating,
                        gender=row.get("Gender"),
                        dob=row.get("Date of Birth"),
                        phone=row.get("Phone"),
                        email=row.get("Email"),
                        club=row.get("Club"),
                        federation=row.get("Federation")
                    )
                    self.tournament.players[player.id] = player
                    added += 1
            self.history_message.emit(f"Imported {added} players from {filename}.")
            self.dirty.emit()
            self.refresh_player_list()
            self.update_ui_state()
            QtWidgets.QMessageBox.information(self, "Import Successful", f"Imported {added} players from {filename}.")
        except Exception as e:
            import logging
            logging.exception("Error importing players:")
            QtWidgets.QMessageBox.critical(self, "Import Error", f"Could not import players:\n{e}")

    def export_players_csv(self):
        if not self.tournament or not self.tournament.players:
            QtWidgets.QMessageBox.information(self, "Export Error", "No players available to export.")
            return
        filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Export Players", "", "CSV Files (*.csv);;Text Files (*.txt)")
        if not filename: return
        try:
            is_csv = selected_filter.startswith("CSV")
            delimiter = "," if is_csv else "\t"
            with open(filename, "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(["Name", "Rating", "Gender", "Date of Birth", "Phone", "Email", "Club", "Federation", "Active", "ID"]) # Added ID
                for player in sorted(list(self.tournament.players.values()), key=lambda p: p.name): # Sort by name
                    writer.writerow([
                        player.name,
                        player.rating if player.rating is not None else "",
                        player.gender or "",
                        player.dob or "",
                        player.phone or "",
                        player.email or "",
                        player.club or "",
                        player.federation or "",
                        "Yes" if player.is_active else "No",
                        player.id
                    ])
            QtWidgets.QMessageBox.information(self, "Export Successful", f"Players exported to {filename}")
            self.parent().statusBar().showMessage(f"Players exported to {filename}")
        except Exception as e:
            logging.exception("Error exporting players:")
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Could not export players:\n{e}")
            self.statusBar().showMessage("Error exporting players.")
            
    def set_tournament(self, tournament):
        self.tournament = tournament
        # Optionally refresh the player list here

    def update_ui_state(self):
        # Disable Add New Player button if no tournament exists
        if not self.tournament:
            self.btn_add_player_detail.setEnabled(False)
        else:
            # Enable only if tournament has not started
            tournament_started = len(self.tournament.rounds_pairings_ids) > 0
            self.btn_add_player_detail.setEnabled(not tournament_started)

    def refresh_player_list(self):
        self.list_players.clear()
        if not self.tournament or not self.tournament.players:
            return
        for player in sorted(self.tournament.players.values(), key=lambda p: p.name):
            self.add_player_to_list_widget(player)
