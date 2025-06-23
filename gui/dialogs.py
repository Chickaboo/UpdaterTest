from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from typing import List, Optional, Tuple, Dict, Any
from core.player import Player
from core.constants import TIEBREAK_NAMES

# --- GUI Dialogs ---
# (No changes to PlayerEditDialog, PlayerDetailDialog, SettingsDialog, ManualPairDialog unless behaviorally impacted by core changes)
# PlayerDetailDialog: Default rating could be None, Player class handles default.
# SettingsDialog: Tiebreak order changes are reflected.

class PlayerEditDialog(QtWidgets.QDialog):
     def __init__(self, player_name: str, player_rating: int, player_active: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Player")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.name_edit = QtWidgets.QLineEdit(player_name)
        self.rating_spin = QtWidgets.QSpinBox()
        self.rating_spin.setRange(0, 4000)
        self.rating_spin.setValue(player_rating if player_rating is not None else 1000) # Handle None rating
        self.active_check = QtWidgets.QCheckBox("Active")
        self.active_check.setChecked(player_active)
        self.active_check.setToolTip("Uncheck to mark player as withdrawn.")
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Name:", self.name_edit)
        form_layout.addRow("Rating:", self.rating_spin)
        form_layout.addRow(self.active_check)
        self.layout.addLayout(form_layout)
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
     def get_data(self) -> Tuple[str, int, bool]:
        name = self.name_edit.text().strip()
        rating = self.rating_spin.value()
        is_active = self.active_check.isChecked()
        return name, rating, is_active

class PlayerDetailDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, player_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Player")
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.rating_spin = QtWidgets.QSpinBox()
        self.rating_spin.setRange(0, 4000) # Rating can be 0 (e.g. unrated)
        self.rating_spin.setValue(1000) # Default if new

        # --- Make QSpinBox arrows black ---
        self.rating_spin.setStyleSheet("""
            QAbstractSpinBox::up-button, QAbstractSpinBox::down-button,
            QAbstractSpinBox::up-arrow, QAbstractSpinBox::down-arrow {
                qproperty-iconColor: #111;
            }
        """)

        gender_dob_layout = QtWidgets.QHBoxLayout()
        self.gender_combo = QtWidgets.QComboBox()
        self.gender_combo.addItems(["", "Male", "Female"])
        self.gender_combo.setToolTip("Select gender (optional)")
        gender_dob_layout.addWidget(QtWidgets.QLabel("Gender:"))
        gender_dob_layout.addWidget(self.gender_combo)
        self.dob_edit = QtWidgets.QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDisplayFormat("yyyy-MM-dd")
        # Allow null/empty date by default
        self.dob_edit.setSpecialValueText(" ") # Show blank when date is not set
        self.dob_edit.setDate(QtCore.QDate()) # Start with an invalid/null date
        self.dob_edit.setToolTip("Select date of birth (optional)")

        # --- Make QDateEdit calendar button black ---
        self.dob_edit.setStyleSheet("""
            QDateEdit::drop-down, QDateEdit::down-arrow, QDateEdit::calendarButton {
                qproperty-iconColor: #111;
            }
        """)
        # self.calendar_popup = QtWidgets.QCalendarWidget() # QDateEdit has its own popup
        # self.calendar_popup.setGridVisible(True)
        # self.calendar_popup.setMaximumDate(QtCore.QDate.currentDate())
        # self.dob_edit.setCalendarWidget(self.calendar_popup)
        gender_dob_layout.addSpacing(10)
        gender_dob_layout.addWidget(QtWidgets.QLabel("Date of Birth:"))
        gender_dob_layout.addWidget(self.dob_edit)
        phone_layout = QtWidgets.QHBoxLayout()
        self.phone_edit = QtWidgets.QLineEdit()
        self.btn_copy_phone = QtWidgets.QPushButton("📋")
        self.btn_copy_phone.setFixedWidth(28)
        self.btn_copy_phone.setToolTip("Copy phone number")
        self.btn_copy_phone.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(self.phone_edit.text()))
        phone_layout.addWidget(self.phone_edit)
        phone_layout.addWidget(self.btn_copy_phone)
        email_layout = QtWidgets.QHBoxLayout()
        self.email_edit = QtWidgets.QLineEdit()
        self.btn_copy_email = QtWidgets.QPushButton("📋")
        self.btn_copy_email.setFixedWidth(28)
        self.btn_copy_email.setToolTip("Copy email address")
        self.btn_copy_email.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(self.email_edit.text()))
        email_layout.addWidget(self.email_edit)
        email_layout.addWidget(self.btn_copy_email)
        self.club_edit = QtWidgets.QLineEdit()
        self.federation_edit = QtWidgets.QLineEdit()
        form.addRow("Name:", self.name_edit)
        form.addRow("Rating:", self.rating_spin)
        form.addRow(gender_dob_layout)
        form.addRow("Phone:", phone_layout)
        form.addRow("Email:", email_layout)
        form.addRow("Club:", self.club_edit)
        form.addRow("Federation:", self.federation_edit)
        layout.addLayout(form)
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        if player_data:
            self.name_edit.setText(player_data.get('name', ''))
            self.rating_spin.setValue(player_data.get('rating', 1000) if player_data.get('rating') is not None else 1000)
            gender = player_data.get('gender', '')
            idx = self.gender_combo.findText(gender) if gender else 0
            self.gender_combo.setCurrentIndex(idx if idx >= 0 else 0)
            dob_str = player_data.get('dob')
            if dob_str:
                q_date = QtCore.QDate.fromString(dob_str, "yyyy-MM-dd")
                if q_date.isValid(): self.dob_edit.setDate(q_date)
                else: self.dob_edit.setDate(QtCore.QDate()) # Set to null if invalid
            else:
                self.dob_edit.setDate(QtCore.QDate()) # Set to null if not present

            self.phone_edit.setText(player_data.get('phone', '') or '')
            self.email_edit.setText(player_data.get('email', '') or '')
            self.club_edit.setText(player_data.get('club', '') or '')
            self.federation_edit.setText(player_data.get('federation', '') or '')
    def accept(self):
        if self.dob_edit.date().isValid() and self.dob_edit.date() > QtCore.QDate.currentDate():
            QtWidgets.QMessageBox.warning(self, "Validation Error", "Date of birth cannot be in the future.")
            return
        super().accept()
    def get_player_data(self) -> Dict[str, Any]:
        dob_qdate = self.dob_edit.date()
        return {
            'name': self.name_edit.text().strip(),
            'rating': self.rating_spin.value(),
            'gender': self.gender_combo.currentText() if self.gender_combo.currentText() else None,
            'dob': dob_qdate.toString("yyyy-MM-dd") if dob_qdate.isValid() else None,
            'phone': self.phone_edit.text().strip() or None,
            'email': self.email_edit.text().strip() or None,
            'club': self.club_edit.text().strip() or None,
            'federation': self.federation_edit.text().strip() or None
        }

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, num_rounds: int, tiebreak_order: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tournament Settings")
        self.setMinimumWidth(350)
        self.current_tiebreak_order = list(tiebreak_order) 
        layout = QtWidgets.QVBoxLayout(self)
        rounds_group = QtWidgets.QGroupBox("General")
        rounds_layout = QtWidgets.QFormLayout(rounds_group)
        self.spin_num_rounds = QtWidgets.QSpinBox()
        self.spin_num_rounds.setRange(1, 50)
        self.spin_num_rounds.setValue(num_rounds)
        self.spin_num_rounds.setToolTip("Set the total number of rounds.")
        rounds_layout.addRow("Number of Rounds:", self.spin_num_rounds)
        layout.addWidget(rounds_group)
        tiebreak_group = QtWidgets.QGroupBox("Tiebreak Order")
        tiebreak_layout = QtWidgets.QHBoxLayout(tiebreak_group)
        self.tiebreak_list = QtWidgets.QListWidget()
        self.tiebreak_list.setToolTip("Order in which tiebreaks are applied (higher is better). Drag to reorder.")
        self.tiebreak_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.populate_tiebreak_list()
        tiebreak_layout.addWidget(self.tiebreak_list)
        move_button_layout = QtWidgets.QVBoxLayout()
        btn_up = QtWidgets.QPushButton("Up")
        btn_down = QtWidgets.QPushButton("Down")
        btn_up.clicked.connect(self.move_tiebreak_up)
        btn_down.clicked.connect(self.move_tiebreak_down)
        move_button_layout.addStretch()
        move_button_layout.addWidget(btn_up)
        move_button_layout.addWidget(btn_down)
        move_button_layout.addStretch()
        tiebreak_layout.addLayout(move_button_layout)
        layout.addWidget(tiebreak_group)
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    def populate_tiebreak_list(self):
        self.tiebreak_list.clear()
        for tb_key in self.current_tiebreak_order:
            display_name = TIEBREAK_NAMES.get(tb_key, tb_key) 
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, tb_key) 
            self.tiebreak_list.addItem(item)
    def move_tiebreak_up(self):
        current_row = self.tiebreak_list.currentRow()
        if current_row > 0:
            item = self.tiebreak_list.takeItem(current_row)
            self.tiebreak_list.insertItem(current_row - 1, item)
            self.tiebreak_list.setCurrentRow(current_row - 1)
            self.update_order_from_list()
    def move_tiebreak_down(self):
        current_row = self.tiebreak_list.currentRow()
        if current_row < self.tiebreak_list.count() - 1:
            item = self.tiebreak_list.takeItem(current_row)
            self.tiebreak_list.insertItem(current_row + 1, item)
            self.tiebreak_list.setCurrentRow(current_row + 1)
            self.update_order_from_list()
    def update_order_from_list(self):
         self.current_tiebreak_order = [self.tiebreak_list.item(i).data(Qt.ItemDataRole.UserRole)
                                        for i in range(self.tiebreak_list.count())]
    def accept(self):
         self.update_order_from_list()
         super().accept()
    def get_settings(self) -> Tuple[int, List[str]]:
        return self.spin_num_rounds.value(), self.current_tiebreak_order

class ManualPairDialog(QtWidgets.QDialog):
     def __init__(self, player_name: str, current_opponent_name: str, available_opponents: List[Player], parent=None):
          super().__init__(parent)
          self.setWindowTitle(f"Adjust Pairing for {player_name}")
          self.setMinimumWidth(300)
          self.available_opponents = available_opponents
          self.selected_opponent_id = None
          layout = QtWidgets.QVBoxLayout(self)
          layout.addWidget(QtWidgets.QLabel(f"Current Opponent: {current_opponent_name}"))
          layout.addWidget(QtWidgets.QLabel("Select New Opponent:"))
          self.opponent_combo = QtWidgets.QComboBox()
          self.opponent_combo.addItem("", None) 
          for opp in sorted(available_opponents, key=lambda p: p.name):
               self.opponent_combo.addItem(f"{opp.name} ({opp.rating})", opp.id)
          layout.addWidget(self.opponent_combo)
          self.buttons = QtWidgets.QDialogButtonBox(
               QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
          )
          self.buttons.accepted.connect(self.accept)
          self.buttons.rejected.connect(self.reject)
          layout.addWidget(self.buttons)
     def accept(self):
          self.selected_opponent_id = self.opponent_combo.currentData()
          if not self.selected_opponent_id:
               QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a new opponent.")
               return 
          super().accept()
     def get_selected_opponent_id(self) -> Optional[str]:
          return self.selected_opponent_id