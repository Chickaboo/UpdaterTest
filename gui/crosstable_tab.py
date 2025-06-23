from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt
import functools
from core.constants import WIN_SCORE, DRAW_SCORE, LOSS_SCORE

class CrosstableTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tournament = None
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.crosstable_group = QtWidgets.QGroupBox("Cross-Table")
        crosstable_layout = QtWidgets.QVBoxLayout(self.crosstable_group)
        self.table_crosstable = QtWidgets.QTableWidget(0, 0)
        self.table_crosstable.setToolTip("Grid showing results between players.")
        self.table_crosstable.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_crosstable.setAlternatingRowColors(True)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self.table_crosstable.setFont(font)
        crosstable_layout.addWidget(self.table_crosstable)
        self.main_layout.addWidget(self.crosstable_group)

    def set_tournament(self, tournament):
        self.tournament = tournament
        self.update_ui_state()

    def update_crosstable(self):
        if not self.tournament or not self.tournament.players:
            self.table_crosstable.setRowCount(0)
            self.table_crosstable.setColumnCount(0)
            return

        sorted_players = self.tournament.get_standings(active_only=False)
        if not sorted_players:
            self.table_crosstable.setRowCount(0)
            self.table_crosstable.setColumnCount(0)
            return

        player_id_to_rank_map = {p.id: i for i, p in enumerate(sorted_players)}
        n = len(sorted_players)

        self.table_crosstable.setRowCount(n)
        self.table_crosstable.setColumnCount(n + 3)  # Num, Name, Score + Opponent Ranks

        headers = ["#", "Player", "Score"] + [str(i + 1) for i in range(n)]
        self.table_crosstable.setHorizontalHeaderLabels(headers)
        v_headers = [f"{i+1}. {p.name} ({p.rating or 'NR'})" for i, p in enumerate(sorted_players)]
        self.table_crosstable.setVerticalHeaderLabels(v_headers)

        for r_idx, p1 in enumerate(sorted_players):
            rank_item = QtWidgets.QTableWidgetItem(str(r_idx + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_crosstable.setItem(r_idx, 0, rank_item)
            name_item = QtWidgets.QTableWidgetItem(f"{p1.name} ({p1.rating or 'NR'})")
            self.table_crosstable.setItem(r_idx, 1, name_item)
            score_item = QtWidgets.QTableWidgetItem(f"{p1.score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_crosstable.setItem(r_idx, 2, score_item)

            for round_num, opp_id_for_p1 in enumerate(p1.opponent_ids):
                if round_num >= len(p1.results):
                    continue
                result_char = ""
                color = None
                tooltip = ""
                if opp_id_for_p1 is None:
                    continue  # Byes not shown in grid
                elif opp_id_for_p1 in player_id_to_rank_map:
                    opp_rank_in_list = player_id_to_rank_map[opp_id_for_p1]
                    col_idx_for_opp = opp_rank_in_list + 3
                    result_val = p1.results[round_num]
                    color_played = p1.color_history[round_num]
                    opp_display_rank = opp_rank_in_list + 1
                    if result_val == WIN_SCORE:
                        result_char = f"+{opp_display_rank}"
                        color = QtGui.QColor("green")
                        tooltip = "Win"
                    elif result_val == DRAW_SCORE:
                        result_char = f"={opp_display_rank}"
                        color = QtGui.QColor("#888888")
                        tooltip = "Draw"
                    elif result_val == LOSS_SCORE:
                        result_char = f"-{opp_display_rank}"
                        color = QtGui.QColor("red")
                        tooltip = "Loss"
                    else:
                        result_char = f"?{opp_display_rank}"
                        color = QtGui.QColor("black")
                        tooltip = "Unknown"
                    if color_played == "White":
                        result_char += "w"
                        tooltip += " as White"
                    elif color_played == "Black":
                        result_char += "b"
                        tooltip += " as Black"
                    item = QtWidgets.QTableWidgetItem(result_char)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if color:
                        item.setForeground(color)
                    if tooltip:
                        item.setToolTip(tooltip)
                    self.table_crosstable.setItem(r_idx, col_idx_for_opp, item)
            # Diagonal: player vs self
            diag_item = QtWidgets.QTableWidgetItem("X")
            diag_item.setBackground(QtGui.QColor(220, 220, 220))
            diag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = diag_item.font()
            font.setBold(True)
            diag_item.setFont(font)
            diag_item.setToolTip("Player's own cell")
            self.table_crosstable.setItem(r_idx, r_idx + 3, diag_item)

        self.table_crosstable.resizeColumnsToContents()
        self.table_crosstable.resizeRowsToContents()

    def update_ui_state(self):
        self.update_crosstable()
