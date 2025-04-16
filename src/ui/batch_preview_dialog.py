# batch_preview_dialog.py - Updated to use centralized models
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QWidget, QTextEdit, QGroupBox, QCheckBox,
    QComboBox, QFrame, QMessageBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
import json
import pandas as pd
import os

class BatchPreviewDialog(QDialog):
    """Enhanced dialog to preview batch processing before submission"""
    
    def __init__(self, preview_data, parent=None):
        super().__init__(parent)
        # Convert string to dictionary if needed
        if isinstance(preview_data, str):
            try:
                self.preview_data = json.loads(preview_data)
            except json.JSONDecodeError:
                self.preview_data = {"error": "Invalid JSON data"}
        else:
            self.preview_data = preview_data
            
        self.parent = parent
        self.setWindowTitle("Batch Upload Preview")
        self.setMinimumSize(1000, 700)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        main_layout = QVBoxLayout()
        
        # Summary section
        summary_group = QGroupBox("Batch Summary")
        summary_layout = QVBoxLayout()
        
        # Summary data
        summary_data = self.preview_data.get("summary", {})
        total_packages = summary_data.get("total_packages", 0)
        deed_documents = summary_data.get("deed_documents", 0)
        mortgage_documents = summary_data.get("mortgage_documents", 0)
        excel_rows = summary_data.get("excel_rows", 0)
        
        # Create summary text
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setMaximumHeight(100)
        
        summary_html = f"""
        <h3>Batch Processing Summary</h3>
        <table style='width:100%'>
            <tr>
                <td width='25%'><b>Total Packages:</b> {total_packages}</td>
                <td width='25%'><b>Deed Documents:</b> {deed_documents}</td>
                <td width='25%'><b>Mortgage Satisfactions:</b> {mortgage_documents}</td>
                <td width='25%'><b>Excel Rows:</b> {excel_rows}</td>
            </tr>
        </table>
        """
        
        # Add warnings for mismatches
        if deed_documents != mortgage_documents:
            summary_html += f"""
            <p style='color:orange'><b>Warning:</b> Mismatch between deed documents ({deed_documents}) 
            and Mortgage Satisfactions ({mortgage_documents}). Some packages may be incomplete.</p>
            """
        
        if excel_rows < max(deed_documents, mortgage_documents):
            summary_html += f"""
            <p style='color:orange'><b>Warning:</b> Excel has fewer rows ({excel_rows}) than 
            documents to process ({max(deed_documents, mortgage_documents)}). Some documents won't be processed.</p>
            """
        
        # Add warnings from the data
        for warning in summary_data.get("warnings", []):
            summary_html += f"""
            <p style='color:orange'><b>Warning:</b> {warning}</p>
            """
        
        summary_text.setHtml(summary_html)
        summary_layout.addWidget(summary_text)
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        # Package preview section with tabs
        self.tab_widget = QTabWidget()
        
        # Add Package List tab (main overview)
        package_list_widget = self.create_package_list_tab()
        self.tab_widget.addTab(package_list_widget, "Package Overview")
        
        # Add Package Details tab
        package_details_widget = self.create_package_details_tab()
        self.tab_widget.addTab(package_details_widget, "Package Details")
        
        # Add Data Validation tab
        validation_widget = self.create_validation_tab()
        self.tab_widget.addTab(validation_widget, "Data Validation")

        # Add API Preview tab
        api_preview_widget = self.create_api_preview_tab()
        self.tab_widget.addTab(api_preview_widget, "API Preview")
        
        main_layout.addWidget(self.tab_widget, 1)  # Give it stretch factor for resizing
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Export button
        export_btn = QPushButton("Export Preview")
        export_btn.clicked.connect(self.export_preview)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_api_preview_tab(self):
        """Create a tab to display the raw API call structure"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("This tab shows the raw API payload structure that would be sent to Simplifile.")
        layout.addWidget(instructions)
        
        # Package selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Package:"))
        
        self.api_package_selector = QComboBox()
        packages = self.preview_data.get("packages", [])
        
        for package in packages:
            self.api_package_selector.addItem(
                f"{package.get('package_id')}: {package.get('package_name')}", 
                package.get("package_id")
            )
        
        self.api_package_selector.currentIndexChanged.connect(self.update_api_preview)
        selector_layout.addWidget(self.api_package_selector, 1)
        layout.addLayout(selector_layout)
        
        # API preview text area
        self.api_preview_text = QTextEdit()
        self.api_preview_text.setReadOnly(True)
        self.api_preview_text.setFont(QFont("Courier New", 10))  # Use monospace font for JSON
        self.api_preview_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # No word wrapping for JSON
        
        layout.addWidget(self.api_preview_text, 1)
        
        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_api_preview)
        layout.addWidget(copy_btn)
        
        # Initialize with first package if available
        if packages:
            self.update_api_preview(0)
        
        widget.setLayout(layout)
        return widget

    def update_api_preview(self, index):
        """Update the API preview text area with the selected package"""
        if index < 0:
            return
            
        packages = self.preview_data.get("packages", [])
        if index >= len(packages):
            return
            
        package = packages[index]
        
        # Get API payload preview - the model would generate this in real usage
        # Here we'll create a simplified version for display
        api_payload = self.create_api_payload_preview(package)
        
        # Format as JSON with indentation
        formatted_json = json.dumps(api_payload, indent=2)
        
        # Set text
        self.api_preview_text.setText(formatted_json)

    def create_api_payload_preview(self, package):
        """Create a preview of what the API payload would look like"""
        # This would be handled by the model in real usage
        # Here we'll create a simplified version for preview
        payload = {
            "documents": [],
            "recipient": "RECIPIENT_ID_PLACEHOLDER",  # Would be actual recipient ID in real call
            "submitterPackageID": package.get("package_id", ""),
            "name": package.get("package_name", ""),
            "operations": {
                "draftOnErrors": package.get("draft_on_errors", True),
                "submitImmediately": package.get("submit_immediately", False),
                "verifyPageMargins": package.get("verify_page_margins", True)
            }
        }
        
        # Process each document
        for doc in package.get("documents", []):
            document = {
                "submitterDocumentID": doc.get("document_id", ""),
                "name": doc.get("name", ""),
                "kindOfInstrument": [doc.get("type", "")],
                "indexingData": {
                    "executionDate": doc.get("execution_date", ""),
                    "grantors": [],
                    "grantees": [],
                    "legalDescriptions": []
                },
                "fileBytes": ["<base64 encoded file would be here>"]
            }
            
            # Add consideration if provided
            if "consideration" in doc:
                document["indexingData"]["consideration"] = doc.get("consideration", 0.00)
            
            # Add grantors
            for grantor in doc.get("grantors", []):
                if grantor.get("type") == "Organization":
                    document["indexingData"]["grantors"].append({
                        "nameUnparsed": grantor.get("name", ""),
                        "type": "Organization"
                    })
                else:
                    document["indexingData"]["grantors"].append({
                        "firstName": grantor.get("first_name", ""),
                        "lastName": grantor.get("last_name", ""),
                        "type": "Individual"
                    })
            
            # Add grantees
            for grantee in doc.get("grantees", []):
                if grantee.get("type") == "Organization":
                    document["indexingData"]["grantees"].append({
                        "nameUnparsed": grantee.get("name", ""),
                        "type": "Organization"
                    })
                else:
                    document["indexingData"]["grantees"].append({
                        "firstName": grantee.get("first_name", ""),
                        "lastName": grantee.get("last_name", ""),
                        "type": "Individual"
                    })
            
            # Add legal descriptions
            for desc in doc.get("legal_descriptions", []):
                # Ensure we combine description and parcel_id as the model would
                description = desc.get("description", "")
                parcel_id = desc.get("parcel_id", "")
                
                combined_description = description
                if parcel_id and parcel_id not in description:
                    combined_description = f"{description} {parcel_id}"
                    
                document["indexingData"]["legalDescriptions"].append({
                    "description": combined_description,
                    "parcelId": ""  # Leave parcelId blank as requested
                })
            
            # Add reference information
            if "reference_information" in doc:
                ref_info = []
                for ref in doc.get("reference_information", []):
                    ref_info.append({
                        "documentType": ref.get("document_type", ""),
                        "book": ref.get("book", ""),
                        "page": ref.get("page", "")
                    })
                
                if ref_info:
                    document["indexingData"]["referenceInformation"] = ref_info
            
            payload["documents"].append(document)
        
        return payload

    def copy_api_preview(self):
        """Copy API preview to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.api_preview_text.toPlainText())
        
        # Show brief message
        QMessageBox.information(self, "Copied", "API payload copied to clipboard")

    def create_package_list_tab(self):
        """Create the package list tab with simplified columns and detail buttons"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create table for package list with simplified columns
        table = QTableWidget()
        table.setColumnCount(4)  # Excel Row, Package Name, Documents, Actions
        table.setHorizontalHeaderLabels([
            "Excel Row", "Package Name", "Documents", "Actions"
        ])
        
        # Configure table
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Make the table read-only
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add packages to table
        packages = self.preview_data.get("packages", [])
        table.setRowCount(len(packages))
        
        for i, package in enumerate(packages):
            # Excel Row
            table.setItem(i, 0, QTableWidgetItem(str(package.get("excel_row", ""))))
            
            # Package Name
            table.setItem(i, 1, QTableWidgetItem(package.get("package_name", "")))
            
            # Documents - format as comma-separated list with page counts
            docs = package.get("documents", [])
            doc_list = []
            for doc in docs:
                doc_type = doc.get("type", "")
                page_count = doc.get("page_count", 0)
                doc_list.append(f"{doc_type} {page_count}p")
            
            doc_info = ", ".join(doc_list)
            table.setItem(i, 2, QTableWidgetItem(doc_info))
            
            # Actions - Add "Open Details" button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 0, 4, 0)
            
            open_details_btn = QPushButton("Open Details")
            open_details_btn.clicked.connect(lambda checked, row=i: self.show_package_details(row))
            
            actions_layout.addWidget(open_details_btn)
            actions_widget.setLayout(actions_layout)
            
            table.setCellWidget(i, 3, actions_widget)
        
        # Add a label with instructions
        instructions_label = QLabel("Package Overview - Click 'Open Details' to view document information")
        instructions_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(instructions_label)
        
        # Add a note about the read-only nature
        note_label = QLabel("Note: This is a preview only. Modifications need to be made in the original files.")
        note_label.setStyleSheet("color: #666;")
        layout.addWidget(note_label)
        
        layout.addWidget(table)
        widget.setLayout(layout)
        return widget
    
    def create_package_details_tab(self):
        """Create the package details tab with document selection and preview"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Selector section
        selector_group = QGroupBox("Select Package and Document")
        selector_layout = QVBoxLayout()
        
        # Package selector
        package_layout = QHBoxLayout()
        package_layout.addWidget(QLabel("Package:"))
        
        self.package_selector = QComboBox()
        packages = self.preview_data.get("packages", [])
        
        for package in packages:
            self.package_selector.addItem(
                f"{package.get('package_name')} (Row {package.get('excel_row', '')})", 
                package.get("package_id")
            )
        
        self.package_selector.currentIndexChanged.connect(self.update_document_selector)
        package_layout.addWidget(self.package_selector, 1)
        selector_layout.addLayout(package_layout)
        
        # Document selector
        doc_layout = QHBoxLayout()
        doc_layout.addWidget(QLabel("Document:"))
        
        self.document_selector = QComboBox()
        self.document_selector.currentIndexChanged.connect(self.update_document_preview)
        doc_layout.addWidget(self.document_selector, 1)
        selector_layout.addLayout(doc_layout)
        
        selector_group.setLayout(selector_layout)
        layout.addWidget(selector_group)
        
        # Document preview section
        preview_group = QGroupBox("Document Preview")
        preview_layout = QVBoxLayout()
        
        self.doc_preview = QTextEdit()
        self.doc_preview.setReadOnly(True)
        self.doc_preview.setMinimumHeight(400)
        self.doc_preview.setPlaceholderText("Select a package and document to view details")
        
        preview_layout.addWidget(self.doc_preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group, 1)  # Give it stretch factor for resizing
        
        # Update with initial package if available
        if packages:
            self.update_document_selector(0)
        
        widget.setLayout(layout)
        return widget

    def update_document_selector(self, package_index):
        """Update the document selector based on the selected package"""
        if package_index < 0:
            return
                
        packages = self.preview_data.get("packages", [])
        if package_index >= len(packages):
            return
                
        package = packages[package_index]
        documents = package.get("documents", [])
        
        # Clear and update document selector
        self.document_selector.clear()
        
        for doc in documents:
            doc_name = doc.get("name", "")
            doc_type = doc.get("type", "")
            doc_pages = doc.get("page_count", 0)
            self.document_selector.addItem(
                f"{doc_type} ({doc_name}) - {doc_pages}p",
                doc.get("document_id", "")
            )
        
        # Update preview if documents available
        if documents:
            self.update_document_preview(0)
        else:
            self.doc_preview.setHtml("<p>No documents available for this package</p>")

    def update_document_preview(self, doc_index):
        """Show document preview for the selected document"""
        if doc_index < 0:
            return
                
        # Get current package
        package_index = self.package_selector.currentIndex()
        packages = self.preview_data.get("packages", [])
        
        if package_index < 0 or package_index >= len(packages):
            return
                
        package = packages[package_index]
        documents = package.get("documents", [])
        
        if doc_index >= len(documents):
            return
                
        doc = documents[doc_index]
        
        # Get parent document info based on document type
        parent_doc_info = ""
        if doc.get("type") == "Deed - Timeshare":
            parent_doc_info = f"Parent Document: Deeds PDF, Pages {doc.get('page_range', '')}"
        elif doc.get("type") == "Mortgage Satisfaction":
            parent_doc_info = f"Parent Document: Mortgage Satisfactions PDF, Page {doc.get('page_range', '')}"
        
        # Format grantor list from the document data
        grantor_list = ""
        for grantor in doc.get("grantors", []):
            if grantor.get("type") == "Organization":
                grantor_list += f"{grantor.get('name', '')} (Organization)<br>"
            else:
                name_parts = [
                    grantor.get("first_name", ""), 
                    grantor.get("middle_name", ""), 
                    grantor.get("last_name", "")
                ]
                name = " ".join([p for p in name_parts if p])
                grantor_list += f"{name} (Individual)<br>"
        
        # Format grantee list from the document data
        grantee_list = ""
        for grantee in doc.get("grantees", []):
            if grantee.get("type") == "Organization":
                grantee_list += f"{grantee.get('name', '')} (Organization)<br>"
            else:
                name_parts = [
                    grantee.get("first_name", ""), 
                    grantee.get("middle_name", ""), 
                    grantee.get("last_name", "")
                ]
                name = " ".join([p for p in name_parts if p])
                grantee_list += f"{name} (Individual)<br>"
        
        # Format reference information
        ref_info = "Not provided"
        if doc.get("reference_information"):
            ref_items = []
            for ref in doc.get("reference_information", []):
                ref_items.append(f"Book {ref.get('book', '')}, Page {ref.get('page', '')}")
            ref_info = "<br>".join(ref_items)
        
        # Format the legal descriptions
        legal_descriptions = "Not provided"
        if doc.get("legal_descriptions"):
            desc_items = []
            for desc in doc.get("legal_descriptions", []):
                desc_items.append(f"{desc.get('description', '')} {desc.get('parcel_id', '')}")
            legal_descriptions = "<br>".join(desc_items)
        
        # Create simplified preview content
        html_content = f"""
        <p><b>Document Name:</b> {doc.get('name', 'Document')}</p>
        <p><b>Document Type:</b> {doc.get('type', '')}</p>
        <p><b>Document Length:</b> {doc.get('page_count', '')} page(s)</p>
        <p><b>Source Information:</b> {parent_doc_info}</p>
        <p><b>Execution Date:</b> {doc.get('execution_date', 'Not provided')}</p>
        <p><b>Legal Description:</b> {legal_descriptions}</p>
        <p><b>Reference Information:</b> {ref_info}</p>
        <p><b>Consideration:</b> {doc.get('consideration', 'Not provided')}</p>
        
        <p><b>Grantors:</b></p>
        <p>{grantor_list}</p>
        
        <p><b>Grantees:</b></p>
        <p>{grantee_list}</p>
        """
        
        self.doc_preview.setHtml(html_content)


    def create_validation_tab(self):
        """Create the validation tab for data checks with enhanced display"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add validation summary at the top
        summary_group = QGroupBox("Validation Summary")
        summary_layout = QVBoxLayout()
        
        # Get validation summary data
        validation_summary = self.preview_data.get("validation_summary", {})
        total_packages = validation_summary.get("total_packages", 0)
        valid_packages = validation_summary.get("valid_packages", 0)
        invalid_packages = validation_summary.get("invalid_packages", 0)
        missing_data_issues = validation_summary.get("missing_data_issues", 0)
        format_issues = validation_summary.get("format_issues", 0)
        document_issues = validation_summary.get("document_issues", 0)
        
        # Create summary text
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setMaximumHeight(100)
        
        summary_html = f"""
        <h3>Validation Summary</h3>
        <table style='width:100%'>
            <tr>
                <td width='33%'><b>Total Packages:</b> {total_packages}</td>
                <td width='33%'><b>Valid Packages:</b> {valid_packages}</td>
                <td width='33%'><b>Invalid Packages:</b> {invalid_packages}</td>
            </tr>
            <tr>
                <td width='33%'><b>Missing Data Issues:</b> {missing_data_issues}</td>
                <td width='33%'><b>Format Issues:</b> {format_issues}</td>
                <td width='33%'><b>Document Issues:</b> {document_issues}</td>
            </tr>
        </table>
        """
        
        # Add warning if there are issues
        if missing_data_issues > 0 or format_issues > 0 or document_issues > 0:
            summary_html += """
            <p style='color:orange'><b>Warning:</b> Some validation issues were detected. 
            Review the issues below before proceeding with upload.</p>
            """
        else:
            summary_html += """
            <p style='color:green'><b>Success:</b> No validation issues detected.</p>
            """
        
        summary_text.setHtml(summary_html)
        summary_layout.addWidget(summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Validation options
        options_group = QGroupBox("Validation Options")
        options_layout = QHBoxLayout()
        
        self.validate_names = QCheckBox("Validate Names")
        self.validate_names.setChecked(True)
        
        self.validate_refs = QCheckBox("Validate References")
        self.validate_refs.setChecked(True)
        
        self.validate_docs = QCheckBox("Validate Documents")
        self.validate_docs.setChecked(True)
        
        self.validate_grantor = QCheckBox("Validate Grantors")
        self.validate_grantor.setChecked(True)
        
        validate_btn = QPushButton("Run Validation")
        validate_btn.clicked.connect(self.run_validation)
        
        options_layout.addWidget(self.validate_names)
        options_layout.addWidget(self.validate_refs)
        options_layout.addWidget(self.validate_docs)
        options_layout.addWidget(self.validate_grantor)
        options_layout.addStretch()
        options_layout.addWidget(validate_btn)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Display validation issues - immediate display of Excel issues
        issues_group = QGroupBox("Detected Issues")
        issues_layout = QVBoxLayout()
        
        self.validation_results = QTableWidget()
        self.validation_results.setColumnCount(4)
        self.validation_results.setHorizontalHeaderLabels([
            "Package", "Check Type", "Status", "Details"
        ])
        
        # Configure table
        self.validation_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.validation_results.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Populate with existing validation issues from excel processing
        validation_data = self.preview_data.get("validation", {})
        validation_results = []
        
        # Add missing data items from preview
        for issue in validation_data.get("missing_data", []):
            validation_results.append({
                "package": "Data Issue",
                "check_type": "Missing Data",
                "status": "Error",
                "details": issue
            })
        
        # Add format issues from preview - these come from Excel validation
        for issue in validation_data.get("format_issues", []):
            validation_results.append({
                "package": "Format Issue",
                "check_type": "Data Format",
                "status": "Warning",
                "details": issue
            })
        
        # Add document issues from preview
        for issue in validation_data.get("document_issues", []):
            validation_results.append({
                "package": "Document Issue",
                "check_type": "Document Validation",
                "status": "Error",
                "details": issue
            })
        
        # Display validation results
        self.validation_results.setRowCount(len(validation_results))
        
        for i, result in enumerate(validation_results):
            # Package
            self.validation_results.setItem(i, 0, QTableWidgetItem(result.get("package", "")))
            
            # Check Type
            self.validation_results.setItem(i, 1, QTableWidgetItem(result.get("check_type", "")))
            
            # Status
            status_item = QTableWidgetItem(result.get("status", ""))
            if result.get("status") == "Error":
                status_item.setBackground(QColor(255, 200, 200))
            elif result.get("status") == "Warning":
                status_item.setBackground(QColor(255, 255, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.validation_results.setItem(i, 2, status_item)
            
            # Details
            self.validation_results.setItem(i, 3, QTableWidgetItem(result.get("details", "")))
        
        issues_layout.addWidget(self.validation_results)
        issues_group.setLayout(issues_layout)
        layout.addWidget(issues_group, 1)
        
        widget.setLayout(layout)
        return widget


    def show_package_details(self, row):
        """Show package details when a package is double-clicked"""
        packages = self.preview_data.get("packages", [])
        
        if row < 0 or row >= len(packages):
            return
            
        # Switch to details tab and select the package
        self.tab_widget.setCurrentIndex(1)
        self.package_selector.setCurrentIndex(row)


    def run_validation(self):
        """Run validation checks on the batch"""
        # Initialize validation results from preview data
        validation_results = []
        validation_data = self.preview_data.get("validation", {})
        
        # Add missing data items from preview
        for issue in validation_data.get("missing_data", []):
            validation_results.append({
                "package": "Data Issue",
                "check_type": "Missing Data",
                "status": "Error",
                "details": issue
            })
        
        # Add format issues from preview
        for issue in validation_data.get("format_issues", []):
            validation_results.append({
                "package": "Format Issue",
                "check_type": "Data Format",
                "status": "Warning",
                "details": issue
            })
        
        # Add document issues from preview
        for issue in validation_data.get("document_issues", []):
            validation_results.append({
                "package": "Document Issue",
                "check_type": "Document Validation",
                "status": "Error",
                "details": issue
            })
        
        # Run additional checks based on selected options
        packages = self.preview_data.get("packages", [])
        
        # Only add checks that are enabled
        if self.validate_names.isChecked():
            for package in packages:
                # Check names for proper format
                for doc in package.get("documents", []):
                    for grantor in doc.get("grantors", []):
                        if grantor.get("type") == "Individual":
                            name = grantor.get("first_name", "") + " " + grantor.get("last_name", "")
                            if "-" in name:
                                validation_results.append({
                                    "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                                    "check_type": "Name Format",
                                    "status": "Warning",
                                    "details": f"Name '{name}' contains hyphens which should be removed"
                                })
        
        if self.validate_refs.isChecked():
            for package in packages:
                for doc in package.get("documents", []):
                    # Check for missing references
                    if doc.get("type") == "Deed - Timeshare" and not doc.get("reference_information"):
                        validation_results.append({
                            "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                            "check_type": "Reference Info",
                            "status": "Error",
                            "details": f"Deed document {doc.get('document_id', '')} is missing book/page reference"
                        })
                    elif doc.get("type") == "Mortgage Satisfaction" and not doc.get("reference_information"):
                        validation_results.append({
                            "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                            "check_type": "Reference Info",
                            "status": "Error",
                            "details": f"Mortgage Satisfaction {doc.get('document_id', '')} is missing book/page reference"
                        })
        
        if self.validate_docs.isChecked():
            for package in packages:
                docs = package.get("documents", [])
                # Check document types
                has_deed = any(doc.get("type") == "Deed - Timeshare" for doc in docs)
                has_mortgage = any(doc.get("type") == "Mortgage Satisfaction" for doc in docs)
                
                if not has_deed:
                    validation_results.append({
                        "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                        "check_type": "Document Set",
                        "status": "Warning",
                        "details": "Package is missing a Deed document"
                    })
                
                if not has_mortgage:
                    validation_results.append({
                        "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                        "check_type": "Document Set",
                        "status": "Warning",
                        "details": "Package is missing a Mortgage Satisfaction document"
                    })
        
        if self.validate_grantor.isChecked():
            for package in packages:
                for doc in package.get("documents", []):
                    # Check for proper grantors
                    grantors = doc.get("grantors", [])
                    
                    if doc.get("type") == "Deed - Timeshare":
                        # Check if KING CUNNINGHAM LLC TR is present
                        has_king_cunningham = any(
                            g.get("type") == "Organization" and 
                            g.get("name", "").upper() == "KING CUNNINGHAM LLC TR" 
                            for g in grantors
                        )
                        
                        if not has_king_cunningham:
                            validation_results.append({
                                "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                                "check_type": "Grantor",
                                "status": "Error",
                                "details": "Deed is missing KING CUNNINGHAM LLC TR as grantor"
                            })
                    
                    elif doc.get("type") == "Mortgage Satisfaction":
                        # Check that KING CUNNINGHAM LLC TR is NOT present
                        has_king_cunningham = any(
                            g.get("type") == "Organization" and 
                            g.get("name", "").upper() == "KING CUNNINGHAM LLC TR" 
                            for g in grantors
                        )
                        
                        if has_king_cunningham:
                            validation_results.append({
                                "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                                "check_type": "Grantor",
                                "status": "Warning",
                                "details": "Mortgage Satisfaction should not have KING CUNNINGHAM LLC TR as grantor"
                            })
                    
                    # Check if the document has any grantors
                    if not grantors:
                        validation_results.append({
                            "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                            "check_type": "Grantor",
                            "status": "Error",
                            "details": f"{doc.get('type')} has no grantors"
                        })
                    
                    # Check if the document has any grantees
                    if not doc.get("grantees", []):
                        validation_results.append({
                            "package": f"{package.get('package_id', '')}: {package.get('package_name', '')}",
                            "check_type": "Grantee",
                            "status": "Error",
                            "details": f"{doc.get('type')} has no grantees"
                        })
        
        # Display validation results
        self.validation_results.setRowCount(len(validation_results))
        
        for i, result in enumerate(validation_results):
            # Package
            self.validation_results.setItem(i, 0, QTableWidgetItem(result.get("package", "")))
            
            # Check Type
            self.validation_results.setItem(i, 1, QTableWidgetItem(result.get("check_type", "")))
            
            # Status
            status_item = QTableWidgetItem(result.get("status", ""))
            if result.get("status") == "Error":
                status_item.setBackground(QColor(255, 200, 200))
            elif result.get("status") == "Warning":
                status_item.setBackground(QColor(255, 255, 200))
            else:
                status_item.setBackground(QColor(200, 255, 200))
            self.validation_results.setItem(i, 2, status_item)
            
            # Details
            self.validation_results.setItem(i, 3, QTableWidgetItem(result.get("details", "")))
            
        # Show summary
        errors = sum(1 for result in validation_results if result.get("status") == "Error")
        warnings = sum(1 for result in validation_results if result.get("status") == "Warning")
        
        if errors > 0 or warnings > 0:
            QMessageBox.warning(
                self, 
                "Validation Complete", 
                f"Validation completed with {errors} errors and {warnings} warnings. "
                f"Review the results before proceeding with upload."
            )
        else:
            QMessageBox.information(
                self,
                "Validation Complete",
                "No issues found! The batch is ready for upload."
            )
    
    def export_preview(self):
        """Export preview data to CSV and JSON"""
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preview Data", "", "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Export to selected format
            if file_path.lower().endswith('.json'):
                # Save as JSON
                with open(file_path, 'w') as f:
                    json.dump(self.preview_data, f, indent=2)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Preview data exported to {file_path}"
                )
            else:
                # Default to CSV if not JSON
                if not file_path.lower().endswith('.csv'):
                    file_path += '.csv'
                
                # Extract package data to dataframe
                data = []
                for package in self.preview_data.get("packages", []):
                    package_id = package.get("package_id", "")
                    package_name = package.get("package_name", "")
                    excel_row = package.get("excel_row", "")
                    account_number = package.get("account_number", "")
                    grantor_grantee = package.get("grantor_grantee", "")
                    
                    for doc in package.get("documents", []):
                        # Build legal description
                        legal_desc = ""
                        for desc in doc.get("legal_descriptions", []):
                            if legal_desc:
                                legal_desc += " "
                            legal_desc += f"{desc.get('description', '')} {desc.get('parcel_id', '')}"
                        
                        # Build reference information
                        ref_book = ""
                        ref_page = ""
                        if doc.get("reference_information"):
                            ref = doc.get("reference_information")[0]
                            ref_book = ref.get("book", "")
                            ref_page = ref.get("page", "")
                        
                        data.append({
                            "Package ID": package_id,
                            "Package Name": package_name,
                            "Excel Row": excel_row,
                            "Account Number": account_number,
                            "Grantor/Grantee": grantor_grantee,
                            "Document ID": doc.get("document_id", ""),
                            "Document Name": doc.get("name", ""),
                            "Document Type": doc.get("type", ""),
                            "Page Range": doc.get("page_range", ""),
                            "Legal Description": legal_desc,
                            "Reference Book": ref_book,
                            "Reference Page": ref_page,
                            "Execution Date": doc.get("execution_date", "")
                        })
                
                # Convert to dataframe and save
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
                
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Preview data exported to {file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export preview data: {str(e)}"
            )