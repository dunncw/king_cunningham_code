import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTabWidget, QFormLayout, 
    QScrollArea, QFileDialog, QMessageBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QCheckBox, QDateEdit,
    QSpinBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from simplifile.models import Party, HelperDocument, SimplifilePackage
from simplifile.utils import (
    validate_package_data, get_document_types, 
    get_helper_document_types, format_date,
    save_config, load_config
)

class SimplifileUI(QWidget):
    start_simplifile_upload = pyqtSignal(str, str, str, str, dict)
    
    def __init__(self):
        super().__init__()
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile_config.json")
        self.config = load_config(self.config_file)
        self.package = SimplifileUI.create_empty_package()
        self.grantors = []
        self.grantees = []
        self.helper_documents = []
        self.init_ui()
    
    @staticmethod
    def create_empty_package():
        """Create an empty package structure"""
        package = SimplifilePackage()
        return package
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Progress bar and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Status:"))
        progress_layout.addWidget(self.status_label, 1)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        
        # Tabs for different sections
        tabs = QTabWidget()
        
        # API Configuration tab
        api_tab = QWidget()
        api_layout = QFormLayout()
        
        self.api_token_input = QLineEdit(self.config.get("api_token", ""))
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token_input.setPlaceholderText("Enter your Simplifile API token")
        api_layout.addRow("API Token:", self.api_token_input)
        
        self.submitter_id_input = QLineEdit(self.config.get("submitter_id", ""))
        self.submitter_id_input.setPlaceholderText("Your Simplifile submitter ID (e.g., SCTP3G)")
        api_layout.addRow("Submitter ID:", self.submitter_id_input)
        
        self.recipient_id_input = QLineEdit(self.config.get("recipient_id", ""))
        self.recipient_id_input.setPlaceholderText("Recipient ID (e.g., GAC3TH)")
        api_layout.addRow("Recipient ID:", self.recipient_id_input)
        
        save_api_btn = QPushButton("Save API Configuration")
        save_api_btn.clicked.connect(self.save_api_config)
        api_layout.addRow("", save_api_btn)
        
        api_tab.setLayout(api_layout)
        
        # Document tab
        doc_tab = QWidget()
        doc_layout = QFormLayout()
        
        document_group = QGroupBox("Main Document")
        document_form = QFormLayout()
        
        self.doc_path_input = QLineEdit(self.config.get("last_document_path", ""))
        self.doc_path_input.setReadOnly(True)
        doc_browse_btn = QPushButton("Browse...")
        doc_browse_btn.clicked.connect(self.browse_document)
        
        doc_path_layout = QHBoxLayout()
        doc_path_layout.addWidget(self.doc_path_input)
        doc_path_layout.addWidget(doc_browse_btn)
        document_form.addRow("Document:", doc_path_layout)
        
        self.ref_number_input = QLineEdit(self.package.reference_number)
        self.ref_number_input.setPlaceholderText("Contract or reference number")
        document_form.addRow("Reference Number:", self.ref_number_input)
        
        self.package_name_input = QLineEdit(self.package.package_name)
        self.package_name_input.setPlaceholderText("Package name (e.g., SMITH 12345)")
        document_form.addRow("Package Name:", self.package_name_input)
        
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(get_document_types())
        if self.package.document_type in get_document_types():
            self.doc_type_combo.setCurrentText(self.package.document_type)
        document_form.addRow("Document Type:", self.doc_type_combo)
        
        self.consideration_input = QLineEdit(self.package.consideration)
        self.consideration_input.setPlaceholderText("Value of transaction (e.g., 250000.00)")
        document_form.addRow("Consideration:", self.consideration_input)
        
        self.execution_date = QDateEdit()
        self.execution_date.setDisplayFormat("MM/dd/yyyy")
        self.execution_date.setDate(QDate.currentDate())
        document_form.addRow("Execution Date:", self.execution_date)
        
        self.legal_desc_input = QTextEdit(self.package.legal_description)
        self.legal_desc_input.setPlaceholderText("Legal description of property")
        self.legal_desc_input.setMaximumHeight(100)
        document_form.addRow("Legal Description:", self.legal_desc_input)
        
        self.parcel_id_input = QLineEdit(self.package.parcel_id)
        self.parcel_id_input.setPlaceholderText("Parcel ID (e.g., 14-0078-0007-096-9)")
        document_form.addRow("Parcel ID:", self.parcel_id_input)
        
        self.book_input = QLineEdit(self.package.book)
        self.book_input.setPlaceholderText("Book number")
        self.page_input = QLineEdit(self.package.page)
        self.page_input.setPlaceholderText("Page number")
        
        book_page_layout = QHBoxLayout()
        book_page_layout.addWidget(QLabel("Book:"))
        book_page_layout.addWidget(self.book_input)
        book_page_layout.addWidget(QLabel("Page:"))
        book_page_layout.addWidget(self.page_input)
        
        document_form.addRow("Reference Info:", book_page_layout)
        
        document_group.setLayout(document_form)
        doc_layout.addRow(document_group)
        
        # Helper documents
        helper_group = QGroupBox("Helper Documents (Optional)")
        helper_layout = QVBoxLayout()
        
        self.helper_table = QTableWidget(0, 3)
        self.helper_table.setHorizontalHeaderLabels(["Path", "Type", "Actions"])
        self.helper_table.horizontalHeader().setStretchLastSection(True)
        self.helper_table.setMinimumHeight(100)
        
        add_helper_btn = QPushButton("Add Helper Document")
        add_helper_btn.clicked.connect(self.add_helper_document)
        
        helper_layout.addWidget(self.helper_table)
        helper_layout.addWidget(add_helper_btn)
        
        helper_group.setLayout(helper_layout)
        doc_layout.addRow(helper_group)
        
        doc_tab.setLayout(doc_layout)
        
        # Parties tab
        parties_tab = QWidget()
        parties_layout = QVBoxLayout()
        
        # Grantors
        grantor_group = QGroupBox("Grantors (Sellers/Transferors)")
        grantor_layout = QVBoxLayout()
        
        self.grantor_table = QTableWidget(0, 5)
        self.grantor_table.setHorizontalHeaderLabels(["Type", "Name/First Name", "Middle", "Last Name", "Actions"])
        self.grantor_table.horizontalHeader().setStretchLastSection(True)
        
        add_grantor_btn = QPushButton("Add Grantor")
        add_grantor_btn.clicked.connect(lambda: self.add_party("grantor"))
        
        grantor_layout.addWidget(self.grantor_table)
        grantor_layout.addWidget(add_grantor_btn)
        
        grantor_group.setLayout(grantor_layout)
        parties_layout.addWidget(grantor_group)
        
        # Grantees
        grantee_group = QGroupBox("Grantees (Buyers/Recipients)")
        grantee_layout = QVBoxLayout()
        
        self.grantee_table = QTableWidget(0, 5)
        self.grantee_table.setHorizontalHeaderLabels(["Type", "Name/First Name", "Middle", "Last Name", "Actions"])
        self.grantee_table.horizontalHeader().setStretchLastSection(True)
        
        add_grantee_btn = QPushButton("Add Grantee")
        add_grantee_btn.clicked.connect(lambda: self.add_party("grantee"))
        
        grantee_layout.addWidget(self.grantee_table)
        grantee_layout.addWidget(add_grantee_btn)
        
        grantee_group.setLayout(grantee_layout)
        parties_layout.addWidget(grantee_group)
        
        parties_tab.setLayout(parties_layout)
        
        # Add tabs to tab widget
        tabs.addTab(api_tab, "API Configuration")
        tabs.addTab(doc_tab, "Document")
        tabs.addTab(parties_tab, "Parties")
        
        main_layout.addWidget(tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(self.validate_package)
        
        upload_btn = QPushButton("Upload to Simplifile")
        upload_btn.clicked.connect(self.upload_to_simplifile)
        upload_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(validate_btn)
        button_layout.addWidget(upload_btn)
        
        main_layout.addLayout(button_layout)
        
        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(100)
        main_layout.addWidget(self.output_text)
        
        self.setLayout(main_layout)
        
        # Load config data if available
        self.load_last_package_data()
    
    def save_api_config(self):
        """Save the API configuration"""
        self.config["api_token"] = self.api_token_input.text()
        self.config["submitter_id"] = self.submitter_id_input.text()
        self.config["recipient_id"] = self.recipient_id_input.text()
        
        if save_config(self.config, self.config_file):
            self.update_output("API configuration saved successfully")
        else:
            self.update_output("Error saving API configuration")
    
    def browse_document(self):
        """Open file dialog to select main document"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            self.doc_path_input.setText(file_path)
            self.config["last_document_path"] = file_path
            save_config(self.config, self.config_file)
            
            # Extract file name as default package name if empty
            if not self.package_name_input.text():
                base_name = os.path.basename(file_path)
                name_without_ext = os.path.splitext(base_name)[0]
                self.package_name_input.setText(name_without_ext.upper())
    
    def add_helper_document(self):
        """Add a helper document to the package"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Helper Document", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Add to table
        row_position = self.helper_table.rowCount()
        self.helper_table.insertRow(row_position)
        
        # File path
        self.helper_table.setItem(row_position, 0, QTableWidgetItem(file_path))
        
        # Document type dropdown
        type_combo = QComboBox()
        type_combo.addItems(get_helper_document_types())
        self.helper_table.setCellWidget(row_position, 1, type_combo)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_helper_document(row_position))
        self.helper_table.setCellWidget(row_position, 2, remove_btn)
        
        # Add to helper_documents list
        helper_doc = HelperDocument(file_path)
        self.helper_documents.append(helper_doc)
        
        self.update_output(f"Added helper document: {os.path.basename(file_path)}")
    
    def remove_helper_document(self, row):
        """Remove a helper document from the package"""
        if 0 <= row < len(self.helper_documents):
            file_path = self.helper_table.item(row, 0).text()
            self.helper_documents.pop(row)
            self.helper_table.removeRow(row)
            self.update_output(f"Removed helper document: {os.path.basename(file_path)}")
            
            # Update row indices for remaining remove buttons
            for i in range(row, self.helper_table.rowCount()):
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, row=i: self.remove_helper_document(row))
                self.helper_table.setCellWidget(i, 2, remove_btn)
    
    def add_party(self, party_type):
        """Add a grantor or grantee to the package"""
        row_position = 0
        table_widget = None
        
        if party_type == "grantor":
            row_position = self.grantor_table.rowCount()
            table_widget = self.grantor_table
        else:  # grantee
            row_position = self.grantee_table.rowCount()
            table_widget = self.grantee_table
        
        table_widget.insertRow(row_position)
        
        # Party type dropdown
        type_combo = QComboBox()
        type_combo.addItems(["PERSON", "ORGANIZATION"])
        type_combo.currentTextChanged.connect(
            lambda text, row=row_position, table=table_widget: 
            self.update_party_type(text, row, table)
        )
        table_widget.setCellWidget(row_position, 0, type_combo)
        
        # Default to PERSON: First Name, Middle Name, Last Name
        for col in range(1, 4):
            table_widget.setItem(row_position, col, QTableWidgetItem(""))
        
        # Remove button
        remove_btn = QPushButton("Remove")
        if party_type == "grantor":
            remove_btn.clicked.connect(lambda: self.remove_party("grantor", row_position))
        else:
            remove_btn.clicked.connect(lambda: self.remove_party("grantee", row_position))
        table_widget.setCellWidget(row_position, 4, remove_btn)
        
        # Create and add party object
        party = Party()
        if party_type == "grantor":
            self.grantors.append(party)
        else:
            self.grantees.append(party)
        
        self.update_output(f"Added {party_type}")
    
    def update_party_type(self, party_type, row, table_widget):
        """Update the party type and relevant fields"""
        # Clear existing values
        for col in range(1, 4):
            if table_widget.item(row, col):
                table_widget.item(row, col).setText("")
        
        # Update headers based on party type
        if party_type == "ORGANIZATION":
            table_widget.setItem(row, 1, QTableWidgetItem(""))
            # Disable unused cells
            for col in range(2, 4):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                table_widget.setItem(row, col, item)
        else:
            # Enable all cells for PERSON
            for col in range(1, 4):
                if table_widget.item(row, col):
                    flags = table_widget.item(row, col).flags()
                    flags |= Qt.ItemFlag.ItemIsEnabled
                    table_widget.item(row, col).setFlags(flags)
                else:
                    table_widget.setItem(row, col, QTableWidgetItem(""))
    
    def remove_party(self, party_type, row):
        """Remove a party from the package"""
        if party_type == "grantor":
            if 0 <= row < len(self.grantors):
                self.grantors.pop(row)
                self.grantor_table.removeRow(row)
                for i in range(row, self.grantor_table.rowCount()):
                    remove_btn = QPushButton("Remove")
                    remove_btn.clicked.connect(lambda checked, row=i: self.remove_party("grantor", row))
                    self.grantor_table.setCellWidget(i, 4, remove_btn)
        else:  # grantee
            if 0 <= row < len(self.grantees):
                self.grantees.pop(row)
                self.grantee_table.removeRow(row)
                for i in range(row, self.grantee_table.rowCount()):
                    remove_btn = QPushButton("Remove")
                    remove_btn.clicked.connect(lambda checked, row=i: self.remove_party("grantee", row))
                    self.grantee_table.setCellWidget(i, 4, remove_btn)
        
        self.update_output(f"Removed {party_type}")
    
    def gather_package_data(self):
        """Collect all package data from the form"""
        package_data = {
            "reference_number": self.ref_number_input.text(),
            "package_name": self.package_name_input.text(),
            "document_type": self.doc_type_combo.currentText(),
            "consideration": self.consideration_input.text(),
            "execution_date": self.execution_date.date().toString("MM/dd/yyyy"),
            "legal_description": self.legal_desc_input.toPlainText(),
            "parcel_id": self.parcel_id_input.text(),
            "book": self.book_input.text(),
            "page": self.page_input.text(),
            "grantors": [],
            "grantees": [],
            "helper_documents": []
        }
        
        # Gather grantors
        for row in range(self.grantor_table.rowCount()):
            party_type = self.grantor_table.cellWidget(row, 0).currentText()
            
            if party_type == "ORGANIZATION":
                name = self.grantor_table.item(row, 1).text() if self.grantor_table.item(row, 1) else ""
                party = {
                    "type": party_type,
                    "name": name
                }
            else:  # PERSON
                first_name = self.grantor_table.item(row, 1).text() if self.grantor_table.item(row, 1) else ""
                middle_name = self.grantor_table.item(row, 2).text() if self.grantor_table.item(row, 2) else ""
                last_name = self.grantor_table.item(row, 3).text() if self.grantor_table.item(row, 3) else ""
                party = {
                    "type": party_type,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name
                }
            
            package_data["grantors"].append(party)
        
        # Gather grantees
        for row in range(self.grantee_table.rowCount()):
            party_type = self.grantee_table.cellWidget(row, 0).currentText()
            
            if party_type == "ORGANIZATION":
                name = self.grantee_table.item(row, 1).text() if self.grantee_table.item(row, 1) else ""
                party = {
                    "type": party_type,
                    "name": name
                }
            else:  # PERSON
                first_name = self.grantee_table.item(row, 1).text() if self.grantee_table.item(row, 1) else ""
                middle_name = self.grantee_table.item(row, 2).text() if self.grantee_table.item(row, 2) else ""
                last_name = self.grantee_table.item(row, 3).text() if self.grantee_table.item(row, 3) else ""
                party = {
                    "type": party_type,
                    "first_name": first_name,
                    "middle_name": middle_name,
                    "last_name": last_name
                }
            
            package_data["grantees"].append(party)
        
        # Gather helper documents
        for row in range(self.helper_table.rowCount()):
            file_path = self.helper_table.item(row, 0).text()
            doc_type = self.helper_table.cellWidget(row, 1).currentText()
            
            helper_doc = {
                "path": file_path,
                "type": doc_type,
                "is_electronic": False
            }
            
            package_data["helper_documents"].append(helper_doc)
        
        return package_data
    
    def validate_package(self):
        """Validate the package data"""
        # Gather data from form
        package_data = self.gather_package_data()
        
        # Validate document path
        if not self.doc_path_input.text() or not os.path.exists(self.doc_path_input.text()):
            self.update_output("Error: Please select a valid document file")
            return False
        
        # Validate required fields and party data
        valid, message = validate_package_data(package_data)
        if not valid:
            self.update_output(f"Validation error: {message}")
            return False
        
        self.update_output("Package validation successful! Ready to upload.")
        return True
    
    def upload_to_simplifile(self):
        """Upload the package to Simplifile"""
        if not self.validate_package():
            return
        
        # Get API configuration
        api_token = self.api_token_input.text()
        submitter_id = self.submitter_id_input.text()
        recipient_id = self.recipient_id_input.text()
        
        if not api_token or not submitter_id or not recipient_id:
            self.update_output("Error: Please provide API token, submitter ID, and recipient ID")
            return
        
        # Gather package data
        package_data = self.gather_package_data()
        
        # Save current package data for future reference
        self.config["last_package_data"] = package_data
        save_config(self.config, self.config_file)
        
        # Emit signal to trigger upload process
        self.start_simplifile_upload.emit(
            api_token,
            submitter_id,
            recipient_id,
            self.doc_path_input.text(),
            package_data
        )
        
        self.update_output("Starting upload to Simplifile...")
        self.progress_bar.setValue(5)
    
    def update_progress(self, value):
        """Update the progress bar"""
        self.progress_bar.setValue(value)
    
    def update_output(self, message):
        """Add a message to the output text area"""
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.output_text.append(f"{timestamp} {message}")
        # Scroll to bottom
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )
        self.status_label.setText(message)
    
    def update_status(self, status):
        """Update the status label and log the message"""
        self.status_label.setText(status)
        self.update_output(status)
    
    def clear_form(self):
        """Clear all form fields"""
        # Clear document inputs
        self.ref_number_input.clear()
        self.package_name_input.clear()
        self.doc_type_combo.setCurrentIndex(0)
        self.consideration_input.setText("0.00")
        self.execution_date.setDate(QDate.currentDate())
        self.legal_desc_input.clear()
        self.parcel_id_input.clear()
        self.book_input.clear()
        self.page_input.clear()
        
        # Clear helper documents
        for _ in range(self.helper_table.rowCount()):
            self.helper_table.removeRow(0)
        self.helper_documents.clear()
        
        # Clear grantors
        for _ in range(self.grantor_table.rowCount()):
            self.grantor_table.removeRow(0)
        self.grantors.clear()
        
        # Clear grantees
        for _ in range(self.grantee_table.rowCount()):
            self.grantee_table.removeRow(0)
        self.grantees.clear()
        
        self.update_output("Form cleared")
    
    def load_last_package_data(self):
        """Load the last saved package data if available"""
        last_package = self.config.get("last_package_data", {})
        if not last_package:
            return
        
        # Load basic fields
        self.ref_number_input.setText(last_package.get("reference_number", ""))
        self.package_name_input.setText(last_package.get("package_name", ""))
        
        doc_type = last_package.get("document_type", "")
        if doc_type in get_document_types():
            self.doc_type_combo.setCurrentText(doc_type)
        
        self.consideration_input.setText(last_package.get("consideration", "0.00"))
        
        # Try to parse execution date
        exec_date = last_package.get("execution_date", "")
        if exec_date:
            try:
                date = QDate.fromString(exec_date, "MM/dd/yyyy")
                if date.isValid():
                    self.execution_date.setDate(date)
            except:
                pass
        
        self.legal_desc_input.setPlainText(last_package.get("legal_description", ""))
        self.parcel_id_input.setText(last_package.get("parcel_id", ""))
        self.book_input.setText(last_package.get("book", ""))
        self.page_input.setText(last_package.get("page", ""))
        
        # Load grantors
        for grantor in last_package.get("grantors", []):
            self.add_party("grantor")
            row = self.grantor_table.rowCount() - 1
            
            # Set type
            type_combo = self.grantor_table.cellWidget(row, 0)
            type_combo.setCurrentText(grantor.get("type", "PERSON"))
            
            # Set other fields based on type
            if grantor.get("type") == "ORGANIZATION":
                self.grantor_table.item(row, 1).setText(grantor.get("name", ""))
            else:
                self.grantor_table.item(row, 1).setText(grantor.get("first_name", ""))
                self.grantor_table.item(row, 2).setText(grantor.get("middle_name", ""))
                self.grantor_table.item(row, 3).setText(grantor.get("last_name", ""))
        
        # Load grantees
        for grantee in last_package.get("grantees", []):
            self.add_party("grantee")
            row = self.grantee_table.rowCount() - 1
            
            # Set type
            type_combo = self.grantee_table.cellWidget(row, 0)
            type_combo.setCurrentText(grantee.get("type", "PERSON"))
            
            # Set other fields based on type
            if grantee.get("type") == "ORGANIZATION":
                self.grantee_table.item(row, 1).setText(grantee.get("name", ""))
            else:
                self.grantee_table.item(row, 1).setText(grantee.get("first_name", ""))
                self.grantee_table.item(row, 2).setText(grantee.get("middle_name", ""))
                self.grantee_table.item(row, 3).setText(grantee.get("last_name", ""))