import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from typing import List
from PyQt6.QtCore import QObject, pyqtSignal

class PT61PDFStacker(QObject):
    """Handles combining PT61 PDFs into a single document"""
    
    progress_update = pyqtSignal(str)  # Status updates
    
    def __init__(self):
        super().__init__()
        self.pdf_files = []  # Track PDFs in order
    
    def add_pdf(self, file_path: str):
        """Add a PDF file to the stack (in order of creation)"""
        if os.path.exists(file_path):
            self.pdf_files.append(file_path)
    
    def clear_stack(self):
        """Clear the PDF stack for new batch"""
        self.pdf_files = []
    
    def create_stacked_pdf(self, save_location: str, version_display_name: str) -> str:
        """
        Combine all tracked PDFs into one document
        
        Args:
            save_location (str): Directory to save the combined PDF
            version_display_name (str): Version name for filename
            
        Returns:
            str: Path to the created combined PDF
        """
        if not self.pdf_files:
            raise ValueError("No PDF files to combine")
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%y%m%d-%H%M")  # YYMMDD-HHMM
        # Clean version name for filename (remove spaces, special chars)
        clean_version = version_display_name.replace(" ", "_").replace("-", "_")
        filename = f"PT61_{clean_version}_{timestamp}.pdf"
        output_path = os.path.join(save_location, filename)
        
        self.progress_update.emit(f"Creating combined PDF: {filename}")
        
        try:
            # Create PDF writer
            output_pdf = PdfWriter()
            total_files = len(self.pdf_files)
            
            # Process each PDF file in order
            for i, pdf_path in enumerate(self.pdf_files):
                self.progress_update.emit(f"Adding PDF {i+1} of {total_files}: {os.path.basename(pdf_path)}")
                
                if not os.path.exists(pdf_path):
                    self.progress_update.emit(f"Warning: File not found, skipping: {pdf_path}")
                    continue
                
                try:
                    # Read the PDF
                    pdf_reader = PdfReader(pdf_path)
                    
                    # Add all pages from this PDF
                    for page_num, page in enumerate(pdf_reader.pages):
                        output_pdf.add_page(page)
                    
                    self.progress_update.emit(f"Added {len(pdf_reader.pages)} pages from {os.path.basename(pdf_path)}")
                    
                except Exception as e:
                    self.progress_update.emit(f"Error reading {pdf_path}: {str(e)}")
                    continue
            
            # Write the combined PDF
            self.progress_update.emit(f"Saving combined PDF to: {output_path}")
            with open(output_path, "wb") as output_file:
                output_pdf.write(output_file)
            
            self.progress_update.emit(f"Successfully created combined PDF with {len(output_pdf.pages)} total pages")
            return output_path
            
        except Exception as e:
            error_msg = f"Error creating combined PDF: {str(e)}"
            self.progress_update.emit(error_msg)
            raise Exception(error_msg)
    
    def get_stack_info(self) -> dict:
        """Get information about the current PDF stack"""
        total_files = len(self.pdf_files)
        existing_files = [f for f in self.pdf_files if os.path.exists(f)]
        
        return {
            "total_files": total_files,
            "existing_files": len(existing_files),
            "missing_files": total_files - len(existing_files),
            "file_list": self.pdf_files
        }