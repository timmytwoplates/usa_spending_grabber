import sys
import csv
import json
import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, 
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, 
    QTextEdit, QTabWidget, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor  # Add this import at the top of your file

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom item that sorts numerically instead of alphabetically."""
    def __lt__(self, other):
        try:
            # Clean strings for numeric comparison (remove $ and commas)
            val1 = float(self.text().replace('$', '').replace(',', ''))
            val2 = float(other.text().replace('$', '').replace(',', ''))
            return val1 < val2
        except ValueError:
            return super().__lt__(other)

class FetchWorker(QThread):
    """Handles API requests in a separate thread."""
    progress_msg = pyqtSignal(str)
    progress_val = pyqtSignal(int)
    data_received = pyqtSignal(list, str)
    finished = pyqtSignal()

    def __init__(self, contract_ids, sort_by, order, limit):
        super().__init__()
        self.contract_ids = contract_ids
        self.sort_by = sort_by
        self.order = order
        self.limit = limit

    def run(self):
        url = "https://api.usaspending.gov/api/v2/transactions/"
        headers = {"Content-Type": "application/json"}
        
        total = len(self.contract_ids)
        for i, cid in enumerate(self.contract_ids):
            self.progress_msg.emit(f"Fetching: {cid}...")
            
            # Payload configured per API documentation
            payload = {
                "award_id": cid,
                "page": 1,
                "sort": self.sort_by,
                "order": self.order,
                "limit": self.limit
            }

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json().get("results", [])
                self.data_received.emit(data, cid)
            except Exception as e:
                self.progress_msg.emit(f"Error fetching {cid}: {str(e)}")
            
            self.progress_val.emit(int(((i + 1) / total) * 100))
        self.finished.emit()

class USASpendingPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USAspending.gov Data Pro")
        self.setMinimumSize(1100, 800)
        self.all_data = [] 
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Configuration Group
        input_group = QGroupBox("Configuration")
        input_layout = QHBoxLayout()
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Contract ID...")
        self.btn_import = QPushButton("Import CSV")
        self.btn_import.clicked.connect(self.import_csv)
        self.btn_template = QPushButton("Gen Template")
        self.btn_template.clicked.connect(self.generate_template)
        input_layout.addWidget(QLabel("Award ID:"))
        input_layout.addWidget(self.id_input)
        input_layout.addWidget(self.btn_import)
        input_layout.addWidget(self.btn_template)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Control Group
        ctrl_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["action_date", "federal_action_obligation", "modification_number", "action_type_description"])
        self.limit_input = QLineEdit("10")
        self.limit_input.setFixedWidth(50)
        self.btn_fetch = QPushButton("FETCH DATA")
        self.btn_fetch.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_fetch.clicked.connect(self.start_fetch)
        ctrl_layout.addWidget(QLabel("Sort:"))
        ctrl_layout.addWidget(self.sort_combo)
        ctrl_layout.addWidget(QLabel("Limit:"))
        ctrl_layout.addWidget(self.limit_input)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_fetch)
        main_layout.addLayout(ctrl_layout)

        # Tabs
        self.tabs = QTabWidget()
        self.table_tab = QWidget()
        table_lyt = QVBoxLayout(self.table_tab)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Live Filter Table Results...")
        self.filter_input.textChanged.connect(self.filter_table)
        table_lyt.addWidget(self.filter_input)

        # UI Grid with 7 Columns to accommodate Action Type and Description
        self.result_table = QTableWidget(0, 7)
        self.result_table.setHorizontalHeaderLabels([
            "Award ID", "Date", "Mod #", "Obligation", "Action Code", "Action Description", "Description"
        ])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setSortingEnabled(True)
        table_lyt.addWidget(self.result_table)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: 'Courier New';")
        self.tabs.addTab(self.table_tab, "Data Grid")
        self.tabs.addTab(self.log_output, "Activity Log")
        main_layout.addWidget(self.tabs)

        # Footer
        bottom_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self.export_to_csv)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.btn_export)
        main_layout.addLayout(bottom_layout)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def generate_template(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Template", "template.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["contract_id"])
                writer.writerow(["47QTCA20D002A"])

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path: self.id_input.setText(f"FILE:{path}")

    def start_fetch(self):
        raw_input = self.id_input.text().strip()
        ids = []
        if raw_input.startswith("FILE:"):
            path = raw_input.replace("FILE:", "")
            try:
                with open(path, 'r') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    ids = [row[0].strip().upper() for row in reader if row]
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
                return
        elif raw_input:
            cid = raw_input.upper()
            ids = [f"CONT_IDV_{cid}_4732" if "_" not in cid else cid]
        
        self.all_data = []
        self.result_table.setRowCount(0)
        self.btn_fetch.setEnabled(False)
        self.worker = FetchWorker(ids, self.sort_combo.currentText(), "desc", int(self.limit_input.text()))
        self.worker.progress_msg.connect(self.log)
        self.worker.progress_val.connect(self.progress_bar.setValue)
        self.worker.data_received.connect(self.process_incoming_data)
        self.worker.finished.connect(lambda: self.btn_fetch.setEnabled(True))
        self.worker.start()

    def process_incoming_data(self, data, award_id):
        """Processes API TransactionResults into internal list."""
        for item in data:
            entry = {
                "award_id": award_id,
                "date": item.get("action_date", ""),
                "mod": item.get("modification_number", ""),
                "amount": item.get("federal_action_obligation", 0),
                "action_type": item.get("action_type", ""), # Field from docs
                "action_desc": item.get("action_type_description", ""), # Field from docs
                "desc": item.get("description", "")
            }
            self.all_data.append(entry)
        self.refresh_table(self.all_data)

    def refresh_table(self, data_list):
        """
        Refreshes the UI grid and highlights rows where 
        the Action Code is not 'M'.
        """
        self.result_table.setSortingEnabled(False)
        self.result_table.setRowCount(len(data_list))
        
        # Define the highlight color (Light Yellow/Amber)
        highlight_color = QColor(10, 10, 10) 

        for row, info in enumerate(data_list):
            # Determine if this row needs highlighting
            # We compare against 'M' based on the Action Code field
            is_not_m = str(info['action_type']).upper() != 'M'

            # Create the items for each column
            items = [
                QTableWidgetItem(str(info['award_id'])),
                QTableWidgetItem(str(info['date'])),
                QTableWidgetItem(str(info['mod'] if info['mod'] else "N/A")),
                NumericTableWidgetItem(f"${info['amount']:,.2f}"),
                QTableWidgetItem(str(info['action_type'])),
                QTableWidgetItem(str(info['action_desc'])),
                QTableWidgetItem(str(info['desc']))
            ]

            # Apply the items to the row and set background if needed
            for col, item in enumerate(items):
                if is_not_m:
                    item.setBackground(highlight_color)
                self.result_table.setItem(row, col, item)
                
        self.result_table.setSortingEnabled(True)

    def filter_table(self):
        search_text = self.filter_input.text().lower()
        filtered = [d for d in self.all_data if search_text in str(d.values()).lower()]
        self.refresh_table(filtered)

    def export_to_csv(self):
        if not self.all_data: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Data", "usaspending_export.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.all_data[0].keys())
                writer.writeheader()
                writer.writerows(self.all_data)
            self.log(f"Exported to {path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = USASpendingPro()
    window.show()
    sys.exit(app.exec())