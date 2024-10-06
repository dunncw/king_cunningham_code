import sys
import os
import fitz
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import warnings
from PyQt6.QtCore import QThread, pyqtSignal
import pytesseract

def get_tesseract_path():
    if getattr(sys, 'frozen', False):
        # The application is running as a bundled executable
        application_path = sys._MEIPASS
    else:
        # The application is running in a normal Python environment
        application_path = os.path.dirname(os.path.abspath(__file__))

    # Try to find Tesseract in the application directory
    tesseract_path = os.path.join(application_path, 'tesseract.exe')
    
    if os.path.exists(tesseract_path):
        return tesseract_path
    else:
        # If not found in the application directory, try the default installation path
        default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(default_path):
            return default_path
        else:
            return None

tesseract_path = get_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print("Tesseract executable not found. OCR functionality will not work.")

def perform_ocr(image):
    if tesseract_path:
        return pytesseract.image_to_string(image)
    else:
        return "OCR unavailable: Tesseract not found"

class SuppressStderr:
    def __enter__(self):
        self._original_stderr = os.dup(2)
        os.close(2)
        os.open(os.devnull, os.O_WRONLY)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self._original_stderr, 2)
        os.close(self._original_stderr)

def perform_ocr(image):
    return pytesseract.image_to_string(image)


def extract_documents_by_barcode(pdf_path, output_dir, dpi=300, output_callback=None):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise Exception(f"Error opening PDF file: {str(e)}")
    
    barcode_pages = []
    mtg_page = None
    deed_page = None
    
    for page_num in range(len(doc)):
        try:
            pix = doc.load_page(page_num).get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                barcodes = decode(gray)
            
            if barcodes:
                barcode_pages.append(page_num)
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    if "MTG" in barcode_data:
                        mtg_page = page_num
                    if "DEED" in barcode_data:
                        deed_page = page_num
        except Exception as e:
            raise Exception(f"Error processing page {page_num + 1}: {str(e)}")
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(output_dir, exist_ok=True)
    
    def save_section(start_page, end_page, suffix):
        if start_page is not None:
            try:
                new_doc = fitz.open()
                for page_num in range(start_page, end_page):
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                dropped_info = ""
                if new_doc.page_count > 0:
                    # Perform OCR on the last page
                    last_page = new_doc.load_page(-1)
                    pix = last_page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = perform_ocr(img)
                    
                    if "NOTICE OF AVAILABILITY OF OWNER" in ocr_text:
                        # Remove the last page
                        new_doc.delete_page(-1)
                        dropped_info = f" Dropped last page (page {end_page} in original document) as it's 'NOTICE OF AVAILABILITY OF OWNER'S COVERAGE'"
                    
                    if new_doc.page_count > 0:
                        if suffix == 'deed':
                            output_filename = f"{base_name}.pdf"
                        elif suffix == 'mtg':
                            output_filename = f"{base_name}m.pdf"
                        else:
                            output_filename = f"{base_name}-{suffix}.pdf"

                        output_path = os.path.join(output_dir, output_filename)
                        new_doc.save(output_path)
                        new_doc.close()
                        return (start_page + 1, end_page, dropped_info)  # Return 1-based page numbers and dropped info
                    else:
                        return None
                else:
                    return None
            except Exception as e:
                raise Exception(f"Error saving {suffix} section: {str(e)}")
        return None

    mtg_saved = None
    deed_saved = None

    mtg_end = None
    deed_end = None

    if barcode_pages:
        barcode_pages_sorted = sorted(barcode_pages)
        total_pages = len(doc)
        
        if mtg_page is not None:
            next_pages = [p for p in barcode_pages_sorted if p > mtg_page]
            mtg_end = next_pages[0] if next_pages else total_pages
            mtg_saved = save_section(mtg_page, mtg_end, "mtg")
        if deed_page is not None:
            next_pages = [p for p in barcode_pages_sorted if p > deed_page]
            deed_end = next_pages[0] if next_pages else total_pages
            deed_saved = save_section(deed_page, deed_end, "deed")
    else:
        if output_callback:
            output_callback(f"No barcodes found in {base_name}.\n")

    doc.close()

    result = f"{base_name}:\n"
    if deed_saved:
        result += f"- DEED extracted (pages {deed_saved[0]} to {deed_saved[1]}){deed_saved[2]}\n"
    else:
        result += "- DEED: Not found or not extracted\n"
    if mtg_saved:
        result += f"- MTG extracted (pages {mtg_saved[0]} to {mtg_saved[1]}){mtg_saved[2]}\n"
    else:
        result += "- MTG: Not found or not extracted\n"

    if output_callback:
        output_callback(result)
    
    return deed_saved, mtg_saved

def process_files(input_path, output_dir, is_directory, progress_callback=None, output_callback=None):
    warnings.filterwarnings("ignore")
    
    total_files = 0
    total_deeds = 0
    total_mtgs = 0

    if is_directory:
        pdf_files = [f for f in os.listdir(input_path) if f.lower().endswith(".pdf")]
        total_files = len(pdf_files)
        
        if total_files == 0:
            raise Exception("No PDF files found in the specified directory.")
        
        if output_callback:
            output_callback(f"Starting batch processing of {total_files} PDF files.\n")
        
        for i, filename in enumerate(pdf_files):
            pdf_path = os.path.join(input_path, filename)
            try:
                deed, mtg = extract_documents_by_barcode(pdf_path, output_dir, output_callback=output_callback)
                total_deeds += 1 if deed else 0
                total_mtgs += 1 if mtg else 0
            except Exception as e:
                if output_callback:
                    output_callback(f"Error processing {filename}: {str(e)}\n")
            if progress_callback:
                progress_callback(int((i + 1) / total_files * 100))
    else:
        if not input_path.lower().endswith('.pdf'):
            raise Exception("The selected file is not a PDF.")
        
        total_files = 1
        if output_callback:
            output_callback(f"Processing single file: {os.path.basename(input_path)}\n")
        
        try:
            deed, mtg = extract_documents_by_barcode(input_path, output_dir, output_callback=output_callback)
            total_deeds = 1 if deed else 0
            total_mtgs = 1 if mtg else 0
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
        if progress_callback:
            progress_callback(100)
    
    summary = f"\nProcessing complete.\nSummary:\n"
    summary += f"Total files processed: {total_files}\n"
    summary += f"Total DEEDs extracted: {total_deeds}\n"
    summary += f"Total MTGs extracted: {total_mtgs}\n"
    
    if output_callback:
        output_callback(summary)

class OCRWorker(QThread):
    progress_update = pyqtSignal(int)
    output_update = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_path, output_dir, is_directory):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.is_directory = is_directory

    def run(self):
        try:
            process_files(
                self.input_path, 
                self.output_dir, 
                self.is_directory, 
                progress_callback=self.progress_update.emit, 
                output_callback=self.output_update.emit
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))