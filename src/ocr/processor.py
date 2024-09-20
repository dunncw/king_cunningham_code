import os
import fitz
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import re
import warnings
from contextlib import redirect_stderr

class SuppressStderr:
    def __enter__(self):
        self._original_stderr = os.dup(2)
        os.close(2)
        os.open(os.devnull, os.O_WRONLY)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self._original_stderr, 2)
        os.close(self._original_stderr)

def extract_documents_by_barcode(pdf_path, output_dir, dpi=300, output_callback=None):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise Exception(f"Error opening PDF file: {str(e)}")
    
    barcode_pages = []
    mtg_page = deed_page = None
    
    for page_num in range(len(doc)):
        try:
            pix = doc.load_page(page_num).get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            with SuppressStderr():
                barcodes = decode(gray)
            
            if barcodes:
                barcode_pages.append(page_num)
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    if re.search(r'\d{2}MTG$', barcode_data):
                        mtg_page = page_num
                    elif re.search(r'\d{2}DEED$', barcode_data):
                        deed_page = page_num
        except Exception as e:
            raise Exception(f"Error processing page {page_num + 1}: {str(e)}")
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(output_dir, exist_ok=True)
    
    def save_section(start_page, end_page, suffix):
        if start_page is not None:
            try:
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page-1)
                output_path = os.path.join(output_dir, f"{base_name}-{suffix}.pdf")
                new_doc.save(output_path)
                new_doc.close()
                return True
            except Exception as e:
                raise Exception(f"Error saving {suffix} section: {str(e)}")
        return False
    
    mtg_saved = False
    deed_saved = False

    if mtg_page is not None:
        mtg_end = barcode_pages[barcode_pages.index(mtg_page) + 1] if mtg_page != barcode_pages[-1] else len(doc)
        mtg_saved = save_section(mtg_page, mtg_end, "mtg")
    
    if deed_page is not None:
        deed_end = barcode_pages[barcode_pages.index(deed_page) + 1] if deed_page != barcode_pages[-1] else len(doc)
        deed_saved = save_section(deed_page, deed_end, "deed")
    
    doc.close()

    result = f"{base_name}:\n- DEED: {'Yes' if deed_saved else 'No'}\n- MTG: {'Yes' if mtg_saved else 'No'}\n"
    if output_callback:
        output_callback(result)
    
    return deed_saved, mtg_saved

def process_files(input_path, output_dir, is_directory, progress_callback=None, output_callback=None):
    warnings.filterwarnings("ignore")
    
    total_files = 0
    total_deeds = 0
    total_mtgs = 0

    if is_directory:
        pdf_files = [f for f in os.listdir(input_path) if f.endswith(".pdf")]
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