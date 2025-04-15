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
        self.preview_data = preview_data if isinstance(preview_data, dict) else json.loads(preview_data)
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
        
        # Package selector (reuse the same one from details tab)
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
        
        # Create a sample API payload based on package data
        api_payload = self.create_api_payload_preview(package)
        
        # Format as JSON with indentation
        formatted_json = json.dumps(api_payload, indent=2)
        
        # Set text
        self.api_preview_text.setText(formatted_json)

    def create_api_payload_preview(self, package):
        """Create a preview of what the API payload would look like"""
        # Simplified version of the actual API payload creation logic
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
            
            # Add grantors - UPDATED to only include KING CUNNINGHAM LLC TR first
            if doc.get("type") == "Deed - Timeshare":
                # Only one default grantor organization
                document["indexingData"]["grantors"] = [
                    {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "Organization"}
                ]
                
                # Add grantor/grantee from Excel
                grantor_grantee = package.get("grantor_grantee")
                document["indexingData"]["grantors"].append({
                    "nameUnparsed": grantor_grantee,
                    "type": "Organization"
                })
                
                # Add Individual grantors - check for "ORG:" prefix
                grantor_name1 = package.get("grantor_name1", "")
                if grantor_name1:
                    # Check if this might be an organization (name starts with "ORG:")
                    if "last_name1" in package and package["last_name1"].startswith("ORG:"):
                        # Use first_name1 as the organization name without adding "ORG:"
                        first_name1 = package.get("first_name1", "")
                        document["indexingData"]["grantors"].append({
                            "nameUnparsed": first_name1,
                            "type": "Organization"
                        })
                    elif grantor_name1:
                        parts = grantor_name1.split()
                        if len(parts) > 1:
                            document["indexingData"]["grantors"].append({
                                "firstName": parts[0],
                                "lastName": " ".join(parts[1:]),
                                "type": "Individual"
                            })

                grantor_name2 = package.get("grantor_name2", "")
                if grantor_name2:
                    # Check if this might be an organization (name starts with "ORG:")
                    if "last_name2" in package and package["last_name2"].startswith("ORG:"):
                        # Use first_name2 as the organization name without adding "ORG:"
                        first_name2 = package.get("first_name2", "")
                        document["indexingData"]["grantors"].append({
                            "nameUnparsed": first_name2,
                            "type": "Organization"
                        })
                    elif grantor_name2:
                        parts = grantor_name2.split()
                        if len(parts) > 1:
                            document["indexingData"]["grantors"].append({
                                "firstName": parts[0],
                                "lastName": " ".join(parts[1:]),
                                "type": "Individual"
                            })

            elif doc.get("type") == "Mortgage Satisfaction":
                # Mortgage grantors only include Individuals
                grantor_name1 = package.get("grantor_name1", "")
                if grantor_name1:
                    # Check if this might be an organization (name starts with "ORG:")
                    if "last_name1" in package and package["last_name1"].startswith("ORG:"):
                        document["indexingData"]["grantors"].append({
                            "nameUnparsed": grantor_name1,
                            "type": "Organization"
                        })
                    elif grantor_name1:
                        parts = grantor_name1.split()
                        if len(parts) > 1:
                            document["indexingData"]["grantors"].append({
                                "firstName": parts[0],
                                "lastName": " ".join(parts[1:]),
                                "type": "Individual"
                            })
                
                grantor_name2 = package.get("grantor_name2", "")
                if grantor_name2:
                    # Check if this might be an organization (name starts with "ORG:")
                    if "last_name2" in package and package["last_name2"].startswith("ORG:"):
                        document["indexingData"]["grantors"].append({
                            "nameUnparsed": grantor_name2,
                            "type": "Organization"
                        })
                    elif grantor_name2:
                        parts = grantor_name2.split()
                        if len(parts) > 1:
                            document["indexingData"]["grantors"].append({
                                "firstName": parts[0],
                                "lastName": " ".join(parts[1:]),
                                "type": "Individual"
                            })
            
            # Add grantees (same for both document types)
            document["indexingData"]["grantees"] = [
                {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "Organization"}
            ]
            
            # Add legal descriptions - UPDATED to append parcelId to description
            legal_desc = doc.get("legal_description", package.get("legal_description", ""))
            parcel_id = doc.get("parcel_id", package.get("tms_number", ""))
            
            # Combine description and parcel_id if parcel_id exists
            combined_description = legal_desc
            if parcel_id:
                combined_description = f"{legal_desc} {parcel_id}"
                
            document["indexingData"]["legalDescriptions"].append({
                "description": combined_description,
                "parcelId": ""  # Leave parcelId blank as requested
            })
            
            # Add reference information
            ref_info = []
            if doc.get("type") == "Deed - Timeshare":
                ref_book = doc.get("reference_book", "")
                ref_page = doc.get("reference_page", "")
                if ref_book and ref_page:
                    ref_info.append({
                        "documentType": "Deed - Timeshare",
                        "book": ref_book,
                        "page": ref_page
                    })
            elif doc.get("type") == "Mortgage Satisfaction":
                ref_book = doc.get("reference_book", "")
                ref_page = doc.get("reference_page", "")
                if ref_book and ref_page:
                    ref_info.append({
                        "documentType": "Mortgage Satisfaction",
                        "book": ref_book,
                        "page": ref_page
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
        
        # Format grantor list - UPDATED to show correct grantors
        grantors = [
            "KING CUNNINGHAM LLC TR (Organization)"
        ]
        
        # Add grantor/grantee from package
        grantor_grantee = package.get('grantor_grantee')
        grantors.append(f"{grantor_grantee} (Organization)")
        
        # Add individual grantors
        grantor_name1 = package.get('grantor_name1', '')
        if grantor_name1:
            # Check if this is an organization
            is_org = False
            if "last_name1" in package and package["last_name1"].startswith("ORG:"):
                is_org = True
                grantors.append(f"{grantor_name1} (Organization)")
            else:
                grantors.append(f"{grantor_name1} (Individual)")
            
        grantor_name2 = package.get('grantor_name2', '')
        if grantor_name2:
            # Check if this is an organization
            is_org = False
            if "last_name2" in package and package["last_name2"].startswith("ORG:"):
                is_org = True
                grantors.append(f"{grantor_name2} (Organization)")
            else:
                grantors.append(f"{grantor_name2} (Individual)")
        
        grantor_list = "<br>".join(grantors)
        
        # Grantees are always the same
        grantee_list = "OCEAN CLUB VACATIONS LLC (Organization)"
        
        # Reference information
        ref_info = ""
        if doc.get("reference_book") and doc.get("reference_page"):
            ref_info = f"Book {doc.get('reference_book')}, Page {doc.get('reference_page')}"
        else:
            ref_info = "Not provided"
        
        # Format the legal description to show how it will be submitted
        legal_desc = doc.get('legal_description', 'Not provided')
        parcel_id = doc.get('parcel_id', '')
        
        # UPDATED: Combine legal description and parcel ID
        if parcel_id:
            combined_description = f"{legal_desc} {parcel_id}"
        else:
            combined_description = legal_desc
        
        # Create simplified preview content
        html_content = f"""
        <p>Document Name: {doc.get('name', 'Document')}</p>
        <p>Document Type: {doc.get('type', '')}</p>
        <p>Document Length: {doc.get('page_count', '')} page(s)</p>
        <p>{parent_doc_info}</p>
        <p>Execution Date: {doc.get('execution_date', 'Not provided')}</p>
        <p>Legal Description: {combined_description}</p>
        <p>Parcel ID/TMS: {parcel_id} (will be included in description field, parcelId will be blank)</p>
        <p>Reference Information: {ref_info}</p>
        <p>Consideration: {doc.get('consideration', 'Not provided')}</p>
        
        <p>Grantors:</p>
        <p>{grantor_list}</p>
        
        <p>Grantees:</p>
        <p>{grantee_list}</p>
        """
        
        self.doc_preview.setHtml(html_content)
        
    def create_validation_tab(self):
        """Create the validation tab for data checks"""
        widget = QWidget()
        layout = QVBoxLayout()
        
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
        
        # Validation results
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout()
        
        self.validation_results = QTableWidget()
        self.validation_results.setColumnCount(4)
        self.validation_results.setHorizontalHeaderLabels([
            "Package", "Check Type", "Status", "Details"
        ])
        
        # Configure table
        self.validation_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.validation_results.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        results_layout.addWidget(self.validation_results)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group, 1)
        
        widget.setLayout(layout)
        return widget
    
    def update_package_details(self, index):
        """Update the package details view"""
        if index < 0:
            return
            
        packages = self.preview_data.get("packages", [])
        if index >= len(packages):
            return
            
        package = packages[index]
        documents = package.get("documents", [])
        
        # Update details table
        self.details_table.setRowCount(len(documents))
        
        for i, doc in enumerate(documents):
            # Document ID
            self.details_table.setItem(i, 0, QTableWidgetItem(doc.get("document_id", "")))
            
            # Name
            self.details_table.setItem(i, 1, QTableWidgetItem(doc.get("name", "")))
            
            # Type
            self.details_table.setItem(i, 2, QTableWidgetItem(doc.get("type", "")))
            
            # Pages
            self.details_table.setItem(i, 3, QTableWidgetItem(doc.get("page_range", "")))
            
            # Legal Description
            legal_desc = doc.get("legal_description", "")
            parcel_id = doc.get("parcel_id", "")
            combined = f"{legal_desc} {parcel_id}" if parcel_id else legal_desc
            self.details_table.setItem(i, 4, QTableWidgetItem(combined))
            
            # Reference Info
            ref_book = doc.get("reference_book", "")
            ref_page = doc.get("reference_page", "")
            ref_info = f"Book {ref_book}, Page {ref_page}" if ref_book and ref_page else ""
            self.details_table.setItem(i, 5, QTableWidgetItem(ref_info))
            
            # Parties (would need to extract from actual payload)
            grantor_grantee = package.get('grantor_grantee', 'OCEAN CLUB VACATIONS LLC')
            self.details_table.setItem(i, 6, QTableWidgetItem(f"KING CUNNINGHAM LLC TR, {grantor_grantee}, and owner(s)"))
        
        # Connect row click to show document preview
        self.details_table.cellClicked.connect(self.show_document_preview)

    def show_document_preview(self, row, column):
            """Show document preview when clicked in details table"""
            if row < 0:
                return
                
            # Get current package
            package_index = self.package_selector.currentIndex()
            packages = self.preview_data.get("packages", [])
            
            if package_index < 0 or package_index >= len(packages):
                return
                
            package = packages[package_index]
            documents = package.get("documents", [])
            
            if row >= len(documents):
                return
                
            doc = documents[row]
            
            # Create formatted preview with updated grantor information and legal description handling
            legal_desc = doc.get('legal_description', '')
            parcel_id = doc.get('parcel_id', '')
            
            # Combine description and parcel_id
            if parcel_id:
                combined_description = f"{legal_desc} {parcel_id}"
            else:
                combined_description = legal_desc
                
            # Get grantor/grantee value from package
            grantor_grantee = package.get("grantor_grantee", "OCEAN CLUB VACATIONS LLC")
            
            html_content = f"""
            <h2>{doc.get('name', 'Document')}</h2>
            <hr>
            <p><b>Document ID:</b> {doc.get('document_id', '')}</p>
            <p><b>Document Type:</b> {doc.get('type', '')}</p>
            <p><b>Pages:</b> {doc.get('page_range', '')}</p>
            
            <h3>Metadata</h3>
            <p><b>Legal Description:</b> {combined_description}</p>
            <p><b>Parcel ID:</b> {parcel_id} (will be included in description field, parcelId will be blank)</p>
            <p><b>Consideration:</b> {doc.get('consideration', '')}</p>
            
            <h3>Reference Information</h3>
            <p><b>Book:</b> {doc.get('reference_book', '')}</p>
            <p><b>Page:</b> {doc.get('reference_page', '')}</p>
            
            <h3>Parties</h3>
            <p>Based on the configuration, this document will include the following parties:</p>
            <ul>
                <li><b>Default Grantors:</b> KING CUNNINGHAM LLC TR</li>
                <li><b>Additional Grantor Organization:</b> {grantor_grantee}</li>
            """
            
            # Add individual grantors with ORG: checking
            grantor_name1 = package.get('grantor_name1', '')
            last_name1 = package.get('last_name1', '')
            first_name1 = package.get('first_name1', '')


            if grantor_name1:
                if last_name1.startswith("ORG:"):
                    # For organizations, display the first name (which contains the org name)
                    # Don't include "ORG:" in the displayed text
                    html_content += f"<li><b>Organization Grantor:</b> {first_name1}</li>"
                else:
                    html_content += f"<li><b>Individual Grantor:</b> {grantor_name1}</li>"

            grantor_name2 = package.get('grantor_name2', '')
            last_name2 = package.get('last_name2', '')
            first_name2 = package.get('first_name2', '')

            if grantor_name2:
                if last_name2.startswith("ORG:"):
                    # For organizations, display the first name (which contains the org name)
                    # Don't include "ORG:" in the displayed text
                    html_content += f"<li><b>Organization Grantor:</b> {first_name2}</li>"
                else:
                    html_content += f"<li><b>Individual Grantor:</b> {grantor_name2}</li>"

            html_content += f"""
                <li><b>Grantees:</b> OCEAN CLUB VACATIONS LLC</li>
            </ul>
            """
            
            self.doc_preview.setHtml(html_content)
    
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
        packages = self.preview_data.get("packages", [])
        validation_results = []
        
        # Clear previous results
        self.validation_results.setRowCount(0)
        
        # Run enabled validations
        for package in packages:
            package_id = package.get("package_id", "")
            package_name = package.get("package_name", "")
            
            # Validate names if enabled
            if self.validate_names.isChecked():
                # Check if names are uppercase
                grantor_name1 = package.get("grantor_name1", "")
                if grantor_name1 and grantor_name1 != grantor_name1.upper():
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Name Format",
                        "status": "Warning",
                        "details": f"Name '{grantor_name1}' is not in uppercase format"
                    })
                
                # Check for hyphenated names
                if "-" in grantor_name1:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Name Format",
                        "status": "Warning",
                        "details": f"Name '{grantor_name1}' contains hyphens which should be removed"
                    })
                    
                # Check for ORG: prefix format
                last_name1 = package.get("last_name1", "")
                if last_name1.startswith("ORG:") and not grantor_name1:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Organization Format",
                        "status": "Error",
                        "details": f"Last name has 'ORG:' prefix but first name (organization name) is missing"
                    })
            
            # Validate references if enabled
            if self.validate_refs.isChecked():
                documents = package.get("documents", [])
                
                for doc in documents:
                    doc_type = doc.get("type", "")
                    doc_id = doc.get("document_id", "")
                    
                    # Check for missing reference information
                    if doc_type == "Deed - Timeshare":
                        if not doc.get("reference_book") or not doc.get("reference_page"):
                            validation_results.append({
                                "package": f"{package_id}: {package_name}",
                                "check_type": "Reference Info",
                                "status": "Error",
                                "details": f"Deed document {doc_id} is missing book/page reference"
                            })
                    
                    if doc_type == "Mortgage Satisfaction":
                        if not doc.get("reference_book") or not doc.get("reference_page"):
                            validation_results.append({
                                "package": f"{package_id}: {package_name}",
                                "check_type": "Reference Info",
                                "status": "Error",
                                "details": f"Mortgage Satisfaction {doc_id} is missing book/page reference"
                            })
            
            # Validate documents if enabled
            if self.validate_docs.isChecked():
                documents = package.get("documents", [])
                
                # Check if package has both deed and Mortgage Satisfaction
                has_deed = any(doc.get("type") == "Deed - Timeshare" for doc in documents)
                has_mortgage = any(doc.get("type") == "Mortgage Satisfaction" for doc in documents)
                
                if not has_deed:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Document Set",
                        "status": "Warning",
                        "details": "Package is missing a Deed document"
                    })
                
                if not has_mortgage:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Document Set",
                        "status": "Warning",
                        "details": "Package is missing a Mortgage Satisfaction document"
                    })
            
            # Validate grantors if enabled
            if self.validate_grantor.isChecked():
                grantor_name1 = package.get("grantor_name1", "")
                
                if not grantor_name1:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Grantor",
                        "status": "Error",
                        "details": "Package is missing primary grantor name"
                    })
                    
                # Check if the GRANTOR/GRANTEE field is present
                grantor_grantee = package.get("grantor_grantee", "")
                if not grantor_grantee:
                    validation_results.append({
                        "package": f"{package_id}: {package_name}",
                        "check_type": "Grantor/Grantee",
                        "status": "Warning",
                        "details": "Missing GRANTOR/GRANTEE value, will use default 'OCEAN CLUB VACATIONS LLC'"
                    })
        
            if "validation" in self.preview_data and "format_issues" in self.preview_data["validation"]:
                for issue in self.preview_data["validation"]["format_issues"]:
                    validation_results.append({
                        "package": "Global",
                        "check_type": "Data Format",
                        "status": "Warning",
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
                    for doc in package.get("documents", []):
                        # Prepare legal description with suite combined
                        legal_desc = doc.get("legal_description", "")
                        parcel_id = doc.get("parcel_id", "")
                        combined_desc = f"{legal_desc} {parcel_id}" if parcel_id else legal_desc
                        
                        data.append({
                            "Package ID": package.get("package_id", ""),
                            "Package Name": package.get("package_name", ""),
                            "Account Number": package.get("account_number", ""),
                            "Grantor Name": package.get("grantor_name1", ""),
                            "Second Grantor": package.get("grantor_name2", ""),
                            "Grantor/Grantee": package.get("grantor_grantee", "OCEAN CLUB VACATIONS LLC"),
                            "Document ID": doc.get("document_id", ""),
                            "Document Name": doc.get("name", ""),
                            "Document Type": doc.get("type", ""),
                            "Page Range": doc.get("page_range", ""),
                            "Legal Description (Combined)": combined_desc,
                            "Parcel ID": parcel_id,
                            "Reference Book": doc.get("reference_book", ""),
                            "Reference Page": doc.get("reference_page", ""),
                            "Excel Row": package.get("excel_row", "")
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