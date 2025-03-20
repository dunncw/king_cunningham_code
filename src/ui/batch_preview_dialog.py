from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSplitter, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QWidget,
    QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
import json

class BatchPreviewDialog(QDialog):
    """Dialog to display batch preview results"""
    
    def __init__(self, preview_data, parent=None):
        super().__init__(parent)
        self.preview_data = preview_data
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Batch Processing Preview")
        self.setMinimumSize(900, 700)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Summary section
        summary = self.preview_data.get("summary", {})
        summary_layout = QHBoxLayout()
        
        # Format summary info
        total_packages = summary.get("total_packages", 0)
        deed_docs = summary.get("deed_documents", 0)
        mortgage_docs = summary.get("mortgage_documents", 0)
        excel_rows = summary.get("excel_rows", 0)
        
        summary_text = f"<b>Summary:</b> {total_packages} packages will be created "
        summary_text += f"with {deed_docs} deed documents and {mortgage_docs} mortgage documents. "
        
        if excel_rows < total_packages:
            summary_text += f"<span style='color:red'>Warning: Excel only has {excel_rows} rows but {total_packages} packages are needed.</span>"
        
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        layout.addLayout(summary_layout)
        
        # Tab widget to switch between views
        tab_widget = QTabWidget()
        
        # Package list tab
        package_list_tab = QWidget()
        package_list_layout = QVBoxLayout()
        
        # Package table
        self.package_table = QTableWidget()
        self.package_table.setColumnCount(5)
        self.package_table.setHorizontalHeaderLabels([
            "Excel Row", "Package ID", "Account Number", "Name", "Documents"
        ])
        self.package_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.package_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Populate package table
        packages = self.preview_data.get("packages", [])
        self.package_table.setRowCount(len(packages))
        
        for i, package in enumerate(packages):
            excel_row = QTableWidgetItem(str(package.get("excel_row", i+2)))
            package_id = QTableWidgetItem(package.get("package_id", ""))
            account = QTableWidgetItem(package.get("account_number", ""))
            
            # Format name
            grantor1 = package.get("grantor_name1", "")
            grantor2 = package.get("grantor_name2", "")
            name_text = grantor1
            if grantor2:
                name_text += f" & {grantor2}"
            name = QTableWidgetItem(name_text)
            
            # Count documents
            docs = package.get("documents", [])
            doc_count = QTableWidgetItem(f"{len(docs)} document(s)")
            
            # Add to table
            self.package_table.setItem(i, 0, excel_row)
            self.package_table.setItem(i, 1, package_id)
            self.package_table.setItem(i, 2, account)
            self.package_table.setItem(i, 3, name)
            self.package_table.setItem(i, 4, doc_count)
        
        self.package_table.selectionModel().selectionChanged.connect(self.on_package_selected)
        
        package_list_layout.addWidget(self.package_table)
        package_list_tab.setLayout(package_list_layout)
        tab_widget.addTab(package_list_tab, "Package List")
        
        # Package details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout()
        
        # Create a splitter to show packages on left, details on right
        splitter = QSplitter()
        
        # Package tree on the left
        self.package_tree = QTreeWidget()
        self.package_tree.setHeaderLabels(["Package"])
        self.package_tree.setMinimumWidth(250)
        
        # Populate tree with all packages
        for i, package in enumerate(packages):
            package_id = package.get("package_id", "")
            account_number = package.get("account_number", "")
            
            # Create parent item for package
            package_item = QTreeWidgetItem(self.package_tree)
            package_item.setText(0, f"Package {i+1}: {account_number}")
            package_item.setData(0, Qt.ItemDataRole.UserRole, i)  # Store package index
            
            # Add documents as child items
            documents = package.get("documents", [])
            for doc in documents:
                doc_item = QTreeWidgetItem(package_item)
                doc_name = doc.get("name", "")
                doc_type = doc.get("type", "")
                doc_item.setText(0, f"{doc_name} ({doc_type})")
                doc_item.setData(0, Qt.ItemDataRole.UserRole, doc)  # Store document data
            
            package_item.setExpanded(True)
        
        self.package_tree.itemClicked.connect(self.on_tree_item_clicked)
        
        # Detail panel on the right
        self.detail_panel = QTextEdit()
        self.detail_panel.setReadOnly(True)
        self.detail_panel.setMinimumWidth(600)
        
        # Add the widgets to the splitter
        splitter.addWidget(self.package_tree)
        splitter.addWidget(self.detail_panel)
        
        details_layout.addWidget(splitter)
        details_tab.setLayout(details_layout)
        tab_widget.addTab(details_tab, "Package Details")
        
        # Add the tab widget to the main layout
        layout.addWidget(tab_widget)
        
        # Raw JSON tab (for debugging)
        json_tab = QWidget()
        json_layout = QVBoxLayout()
        
        json_text = QTextEdit()
        json_text.setReadOnly(True)
        json_text.setPlainText(json.dumps(self.preview_data, indent=2))
        json_layout.addWidget(json_text)
        
        json_tab.setLayout(json_layout)
        tab_widget.addTab(json_tab, "Raw Data")
        
        # Buttons at the bottom
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Preview as JSON")
        save_btn.clicked.connect(self.save_preview)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_package_selected(self, selected, deselected):
        """Handle package selection in the table"""
        indexes = selected.indexes()
        if not indexes:
            return
        
        # Get the row of the selected item
        row = indexes[0].row()
        
        # Get the corresponding package
        packages = self.preview_data.get("packages", [])
        if 0 <= row < len(packages):
            package = packages[row]
            self.show_package_details(package)
    
    def on_tree_item_clicked(self, item, column):
        """Handle tree item click"""
        # Check if it's a package or document item
        parent = item.parent()
        
        if parent is None:
            # This is a package item
            index = item.data(0, Qt.ItemDataRole.UserRole)
            packages = self.preview_data.get("packages", [])
            if 0 <= index < len(packages):
                self.show_package_details(packages[index])
        else:
            # This is a document item
            doc_data = item.data(0, Qt.ItemDataRole.UserRole)
            if doc_data:
                self.show_document_details(doc_data)
    
    def show_package_details(self, package):
        """Show package details in the detail panel"""
        package_id = package.get("package_id", "")
        package_name = package.get("package_name", "")
        account_number = package.get("account_number", "")
        grantor_name1 = package.get("grantor_name1", "")
        grantor_name2 = package.get("grantor_name2", "")
        tms_number = package.get("tms_number", "")
        excel_row = package.get("excel_row", "")
        
        html = f"""
        <h2>Package Details</h2>
        <p><b>Package ID:</b> {package_id}</p>
        <p><b>Package Name:</b> {package_name}</p>
        <p><b>Account Number:</b> {account_number}</p>
        <p><b>Excel Row:</b> {excel_row}</p>
        <p><b>Primary Name:</b> {grantor_name1}</p>
        """
        
        if grantor_name2:
            html += f"<p><b>Secondary Name:</b> {grantor_name2}</p>"
        
        if tms_number:
            html += f"<p><b>TMS Number:</b> {tms_number}</p>"
        
        # Document summary
        documents = package.get("documents", [])
        html += f"<h3>Documents ({len(documents)})</h3>"
        
        if documents:
            html += "<ul>"
            for doc in documents:
                doc_name = doc.get("name", "")
                doc_type = doc.get("type", "")
                pages = doc.get("page_range", "")
                html += f"<li><b>{doc_name}</b> ({doc_type}) - Pages: {pages}</li>"
            html += "</ul>"
        else:
            html += "<p>No documents found in this package.</p>"
        
        self.detail_panel.setHtml(html)
    
    def show_document_details(self, doc):
        """Show document details in the detail panel"""
        doc_id = doc.get("document_id", "")
        doc_name = doc.get("name", "")
        doc_type = doc.get("type", "")
        page_range = doc.get("page_range", "")
        page_count = doc.get("page_count", "")
        reference_book = doc.get("reference_book", "")
        reference_page = doc.get("reference_page", "")
        legal_description = doc.get("legal_description", "")
        parcel_id = doc.get("parcel_id", "")
        consideration = doc.get("consideration", "")
        
        html = f"""
        <h2>Document Details</h2>
        <p><b>Document ID:</b> {doc_id}</p>
        <p><b>Document Name:</b> {doc_name}</p>
        <p><b>Document Type:</b> {doc_type}</p>
        <p><b>Page Range:</b> {page_range}</p>
        <p><b>Page Count:</b> {page_count}</p>
        """
        
        if reference_book and reference_page:
            html += f"<p><b>Reference Book/Page:</b> {reference_book}/{reference_page}</p>"
        
        if legal_description:
            html += f"<p><b>Legal Description:</b> {legal_description}</p>"
        
        if parcel_id:
            html += f"<p><b>Parcel ID:</b> {parcel_id}</p>"
        
        if consideration:
            html += f"<p><b>Consideration:</b> ${consideration}</p>"
        
        self.detail_panel.setHtml(html)
    
    def save_preview(self):
        """Save preview data as JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preview Data", "batch_preview.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.preview_data, f, indent=2)
                self.detail_panel.setHtml(f"<p>Preview data saved to {file_path}</p>")
            except Exception as e:
                self.detail_panel.setHtml(f"<p>Error saving preview data: {str(e)}</p>")