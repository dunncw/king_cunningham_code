# File: web_automation/automation.py

import sys
import os
from PyQt6.QtCore import QThread
from .excel_processor import validate_and_extract_data
from .version_factory import create_automation_worker

def run_web_automation_thread(excel_path, browser, username, password, save_location, version, document_stacking=False):
    """
    Create and configure automation thread for the specified version
    
    Args:
        excel_path (str): Path to Excel file
        browser (str): Browser choice
        username (str): Login username  
        password (str): Login password
        save_location (str): Where to save PDFs
        version (str): Version display name
        document_stacking (bool): Whether to combine PDFs into one document
    
    Returns:
        tuple: (thread, worker) for the automation
    """
    thread = QThread()
    
    # Create version-specific worker using factory (with document stacking option)
    worker = create_automation_worker(excel_path, browser, username, password, save_location, version, document_stacking)
    worker.moveToThread(thread)
    
    # Connect thread signals
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    return thread, worker

class PT61AutomationOrchestrator:
    """Main orchestrator that coordinates the automation process"""
    
    def __init__(self, worker):
        self.worker = worker

    def run(self):
        """Main automation workflow"""
        try:
            self.worker.status.emit(f"Starting automation with version: {self.worker.version}")
            
            # NEW: Document stacking status
            if self.worker.document_stacking:
                self.worker.status.emit("Document stacking is ENABLED - PDFs will be combined into one file")
                # Clear any previous stack
                self.worker.pdf_stacker.clear_stack()
            else:
                self.worker.status.emit("Document stacking is DISABLED - Individual PDF files will be saved")
            
            # Step 1: Validate and extract Excel data
            success, result = validate_and_extract_data(self.worker.excel_path, self.worker.version)
            
            if not success:
                self.worker.error.emit(f"Excel validation failed: {result}")
                return
            
            people_data = result
            self.worker.status.emit(f"Extracted data for {len(people_data)} people from Excel file")
            
            # Step 2: Setup browser
            self.worker.setup_webdriver()
            
            # Step 3: Login
            self.worker.navigate_to_login()
            self.worker.perform_login()
            
            # Step 4: Process each person
            for index, person in enumerate(people_data, start=1):
                self.worker.process_person(person, index, len(people_data))
            
            self.worker.status.emit("All people processed. Automation complete.")
            
            # NEW: Document stacking summary
            if self.worker.document_stacking:
                stack_info = self.worker.pdf_stacker.get_stack_info()
                self.worker.status.emit(f"Document stacking: {stack_info['total_files']} PDFs ready for combining")
            
        except Exception as e:
            self.worker.error.emit(f"Automation error: {str(e)}")
        finally:
            self.worker.cleanup()  # This will handle document stacking if enabled
            self.worker.finished.emit()

# Add the run method to all automation workers
def add_run_method_to_worker(worker):
    """Add the run method to automation worker"""
    def run():
        orchestrator = PT61AutomationOrchestrator(worker)
        orchestrator.run()
    
    worker.run = run
    return worker

# Monkey patch the factory to add run method
original_create_worker = create_automation_worker

def create_automation_worker_with_run(*args, **kwargs):
    worker = original_create_worker(*args, **kwargs)
    return add_run_method_to_worker(worker)

# Replace the factory function
create_automation_worker = create_automation_worker_with_run

# For backwards compatibility and testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    test_browser = "Chrome"
    test_username = "jcunningham@kingcunningham.com"
    test_password = "Kc123!@#"
    test_save_location = r"D:\repositorys\KC_appp\data\sorted\pt61"
    test_version = "PT-61 New Batch"
    test_document_stacking = True  # NEW: Test with document stacking enabled

    thread, worker = run_web_automation_thread(
        test_excel_path, test_browser, test_username, test_password, test_save_location, test_version, test_document_stacking
    )
    
    worker.status.connect(print)  # Print status updates to console
    worker.progress.connect(lambda p: print(f"Progress: {p}%"))
    worker.error.connect(lambda e: print(f"Error: {e}"))

    thread.start()

    sys.exit(app.exec())