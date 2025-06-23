from PyQt6 import QtWidgets, QtGui
from core.constants import TIEBREAK_NAMES, TB_MEDIAN, TB_SOLKOFF, TB_CUMULATIVE, TB_CUMULATIVE_OPP, TB_SONNENBORN_BERGER, TB_MOST_BLACKS, CSV_FILTER
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
import csv
import logging

class StandingsTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tournament = None
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.standings_group = QtWidgets.QGroupBox("Standings")
        standings_layout = QtWidgets.QVBoxLayout(self.standings_group)
        self.table_standings = QtWidgets.QTableWidget(0, 3)
        self.table_standings.setHorizontalHeaderLabels(["Rank", "Player", "Score"])
        self.table_standings.setToolTip("Player standings sorted by Score and configured Tiebreakers.")
        self.table_standings.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_standings.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_standings.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_standings.setAlternatingRowColors(True)
        standings_layout.addWidget(self.table_standings)
        self.btn_print_standings = QtWidgets.QPushButton("Print Standings")
        self.btn_print_standings.setToolTip("Print the current standings table")
        standings_layout.addWidget(self.btn_print_standings)
        self.main_layout.addWidget(self.standings_group)
        self.btn_print_standings.clicked.connect(self.print_standings)

    def set_tournament(self, tournament):
        self.tournament = tournament

    def update_standings_table_headers(self):
         if not self.tournament: return
         base_headers = ["Rank", "Player", "Score"]
         tb_headers = [TIEBREAK_NAMES.get(key, key.upper()) for key in self.tournament.tiebreak_order] # Use upper for unknown keys
         full_headers = base_headers + tb_headers
         self.table_standings.setColumnCount(len(full_headers))
         self.table_standings.setHorizontalHeaderLabels(full_headers)
         self.table_standings.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch) # Player name
         for i in range(len(full_headers)):
              if i != 1: self.table_standings.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
         header_tooltips = ["Rank", "Player Name (Rating)", "Total Score"] + \
                           [TIEBREAK_NAMES.get(key, f"Tiebreak: {key}") for key in self.tournament.tiebreak_order]
         for i, tip in enumerate(header_tooltips):
            if i < self.table_standings.columnCount(): # Check index is valid
                  header_item = self.table_standings.horizontalHeaderItem(i)
                  if header_item: # Ensure the QTableWidgetItem for header exists
                      header_item.setToolTip(tip)

    def update_standings_table(self) -> None:
        if not self.tournament: 
            self.table_standings.setRowCount(0)
            return

        try:
             # Ensure headers match current config first
             expected_col_count = 3 + len(self.tournament.tiebreak_order)
             if self.table_standings.columnCount() != expected_col_count:
                  self.update_standings_table_headers()

             standings = self.tournament.get_standings() # Gets sorted *active* players by default
             # If you want to show all players (active then inactive):
             # all_players_sorted = sorted(
             #    list(self.tournament.players.values()),
             #    key=functools.cmp_to_key(lambda p1, p2: (0 if p1.is_active else 1) - (0 if p2.is_active else 1) or self.tournament._compare_players(p1, p2)),
             #    reverse=False # custom sort, reverse for score happens in _compare_players
             # )
             # standings = all_players_sorted # Use this if showing all players.

             self.table_standings.setRowCount(len(standings))

             tb_formats = { 
                 TB_MEDIAN: '.2f', TB_SOLKOFF: '.2f', TB_CUMULATIVE: '.1f', # Using .2f for Median/Solkoff for finer detail
                 TB_CUMULATIVE_OPP: '.1f', TB_SONNENBORN_BERGER: '.2f', TB_MOST_BLACKS: '.0f' 
             }

             for rank, player in enumerate(standings):
                  row = rank
                  rank_str = str(rank + 1)
                  status_str = "" # Standings usually only show active players from get_standings()
                  # If inactive players were included in `standings`:
                  # status_str = "" if player.is_active else " (I)" 
                  
                  item_rank = QtWidgets.QTableWidgetItem(rank_str)
                  item_player = QtWidgets.QTableWidgetItem(f"{player.name} ({player.rating or 'NR'})" + status_str) # NR for No Rating
                  item_score = QtWidgets.QTableWidgetItem(f"{player.score:.1f}")
                  
                  item_rank.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                  item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                  row_color = self.table_standings.palette().color(QtGui.QPalette.ColorRole.Text)
                  # if not player.is_active: row_color = QtGui.QColor("gray") # If showing inactive
                  
                  item_rank.setForeground(row_color)
                  item_player.setForeground(row_color)
                  item_score.setForeground(row_color)

                  self.table_standings.setItem(row, 0, item_rank)
                  self.table_standings.setItem(row, 1, item_player)
                  self.table_standings.setItem(row, 2, item_score)

                  col_offset = 3
                  for i, tb_key in enumerate(self.tournament.tiebreak_order):
                       value = player.tiebreakers.get(tb_key, 0.0)
                       format_spec = tb_formats.get(tb_key, '.2f') # Default format .2f
                       item_tb = QtWidgets.QTableWidgetItem(f"{value:{format_spec}}")
                       item_tb.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                       item_tb.setForeground(row_color)
                       self.table_standings.setItem(row, col_offset + i, item_tb)

             self.table_standings.resizeColumnsToContents()
             self.table_standings.resizeRowsToContents()

        except Exception as e:
             logging.exception("Error updating standings table:")
             QtWidgets.QMessageBox.warning(self, "Standings Error", f"Could not update standings: {e}")

    def export_standings(self) -> None:
        if not self.tournament: QtWidgets.QMessageBox.information(self, "Export Error", "No tournament data."); return
        standings = self.tournament.get_standings() # Gets active sorted players
        if not standings: QtWidgets.QMessageBox.information(self, "Export Error", "No standings available to export."); return

        filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Export Standings", "", CSV_FILTER)
        if not filename: return

        try:
            with open(filename, "w", encoding="utf-8", newline='') as f:
                is_csv = selected_filter.startswith("CSV")
                delimiter = "," if is_csv else "\t"
                writer = csv.writer(f, delimiter=delimiter) if is_csv else None

                header = [self.table_standings.horizontalHeaderItem(i).text() 
                          for i in range(self.table_standings.columnCount())]
                if writer: writer.writerow(header)
                else: f.write(delimiter.join(header) + "\n")

                tb_formats = { 
                    TB_MEDIAN: '.2f', TB_SOLKOFF: '.2f', TB_CUMULATIVE: '.1f',
                    TB_CUMULATIVE_OPP: '.1f', TB_SONNENBORN_BERGER: '.2f', TB_MOST_BLACKS: '.0f' 
                }

                for rank, player in enumerate(standings):
                    rank_str = str(rank + 1)
                    player_str = f"{player.name} ({player.rating or 'NR'})" 
                    # If exporting all players, including inactive:
                    # player_str += (" (I)" if not player.is_active else "")
                    score_str = f"{player.score:.1f}"
                    data_row = [rank_str, player_str, score_str]
                    
                    for tb_key in self.tournament.tiebreak_order:
                         value = player.tiebreakers.get(tb_key, 0.0)
                         format_spec = tb_formats.get(tb_key, '.2f')
                         data_row.append(f"{value:{format_spec}}")

                    if writer: writer.writerow(data_row)
                    else: f.write(delimiter.join(data_row) + "\n")

            QtWidgets.QMessageBox.information(self, "Export Successful", f"Standings exported to {filename}")
            if self.parent() and hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage(f"Standings exported to {filename}")
        except Exception as e:
            logging.exception("Error exporting standings:")
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Could not save standings:\n{e}")
            if self.parent() and hasattr(self.parent(), 'statusBar'):
                self.parent().statusBar().showMessage("Error exporting standings.")

    def print_standings(self):
        """Print the current standings table in a clean, ink-friendly, professional format with a polished legend."""
        if self.table_standings.rowCount() == 0:
            QtWidgets.QMessageBox.information(self, "Print Standings", "No standings to print.")
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)  # <-- FIXED LINE
        preview.setWindowTitle("Print Preview - Standings")
        def render_preview(printer_obj):
            doc = QtGui.QTextDocument()
            tb_keys = []
            tb_legend = []
            for i, tb_key in enumerate(self.tournament.tiebreak_order):
                short = f"TB{i+1}"
                tb_keys.append(short)
                tb_legend.append((short, TIEBREAK_NAMES.get(tb_key, tb_key.title())))
            html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: #000;
                        background: #fff;
                        margin: 0;
                        padding: 0;
                    }}
                    h2 {{
                        text-align: center;
                        margin: 0 0 0.5em 0;
                        font-size: 1.35em;
                        font-weight: normal;
                        letter-spacing: 0.03em;
                    }}
                    .subtitle {{
                        text-align: center;
                        font-size: 1.05em;
                        margin-bottom: 1.2em;
                    }}
                    table.standings {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 0 auto 1.5em auto;
                    }}
                    table.standings th, table.standings td {{
                        border: 1px solid #222;
                        padding: 6px 10px;
                        text-align: center;
                        font-size: 11pt;
                        white-space: nowrap;
                    }}
                    table.standings th {{
                        font-weight: bold;
                        background: none;
                    }}
                    .legend {{
                        width: 100%;
                        margin: 0 auto 1.5em auto;
                        font-size: 10.5pt;
                        color: #222;
                        border: 1px solid #bbb;
                        background: none;
                        padding: 8px 12px;
                        text-align: left;
                    }}
                    .legend-title {{
                        font-weight: bold;
                        font-size: 11pt;
                        margin-bottom: 0.3em;
                        display: block;
                        letter-spacing: 0.02em;
                    }}
                    .legend-table {{
                        border-collapse: collapse;
                        margin-top: 0.2em;
                    }}
                    .legend-table td {{
                        border: none;
                        padding: 2px 10px 2px 0;
                        font-size: 10pt;
                        vertical-align: top;
                    }}
                    .footer {{
                        text-align: center;
                        font-size: 9pt;
                        margin-top: 2em;
                        color: #888;
                        letter-spacing: 0.04em;
                    }}
                </style>
            </head>
            <body>
                <h2>Standings</h2>
                <div class="subtitle">{self.round_group.title() if hasattr(self, "round_group") else ""}</div>
                <div class="legend">
                    <span class="legend-title">Tiebreaker Legend</span>
                    <table class="legend-table">
            """
            for short, name in tb_legend:
                html += f"<tr><td><b>{short}</b></td><td>{name}</td></tr>"
            html += """
                    </table>
                </div>
                <table class="standings">
                    <tr>
                        <th style="width:6%;">#</th>
                        <th style="width:32%;">Player</th>
                        <th style="width:10%;">Score</th>
            """
            for short in tb_keys:
                html += f'<th style="width:7%;">{short}</th>'
            html += "</tr>"
            # --- Table Rows ---
            for row in range(self.table_standings.rowCount()):
                html += "<tr>"
                for col in range(self.table_standings.columnCount()):
                    item = self.table_standings.item(row, col)
                    cell = item.text() if item else ""
                    # Rank and Score columns bold
                    if col == 0 or col == 2:
                        html += f'<td style="font-weight:bold;">{cell}</td>'
                    else:
                        html += f"<td>{cell}</td>"
                html += "</tr>"
            html += f"""
                </table>
                <div class="footer">
                    Printed by Gambit Pairing &mdash; {QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm")}
                </div>
            </body>
            </html>
            """
            doc.setHtml(html)
            doc.print(printer_obj)
        preview.paintRequested.connect(render_preview)
        preview.exec()

    def update_ui_state(self):
        # Disable print standings if there are no standings
        has_standings = self.tournament is not None and self.table_standings.rowCount() > 0
        self.btn_print_standings.setEnabled(has_standings)
