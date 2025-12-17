# File: web_automation/automation.py

import sys
import os
from PyQt6.QtCore import QThread
from .excel_processor import validate_and_extract_data
from .version_factory import create_automation_worker

def run_web_automation_thread(excel_path, browser, username, password, save_location, version, document_stacking=False):
    """
    Create and configure automation thread for the specified version
    """
    thread = QThread()
    
    worker = create_automation_worker(excel_path, browser, username, password, save_location, version, document_stacking)
    worker.moveToThread(thread)
    
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
            
            if self.worker.document_stacking:
                self.worker.status.emit("Document stacking ENABLED - PDFs will be combined")
                self.worker.pdf_stacker.clear_stack()
            else:
                self.worker.status.emit("Document stacking DISABLED - Individual PDFs will be saved")
            
            success, result = validate_and_extract_data(self.worker.excel_path, self.worker.version)
            
            if not success:
                self.worker.error.emit(f"Excel validation failed: {result}")
                return
            
            people_data = result
            self.worker.status.emit(f"Extracted {len(people_data)} records from Excel")
            
            self.worker.setup_webdriver()
            
            self.worker.navigate_to_login()
            self.worker.perform_login()
            
            for index, person in enumerate(people_data, start=1):
                self.worker.process_person(person, index, len(people_data))
            
            self.worker.status.emit("All records processed. Automation complete.")
            
            if self.worker.document_stacking:
                stack_info = self.worker.pdf_stacker.get_stack_info()
                self.worker.status.emit(f"Document stacking: {stack_info['total_files']} PDFs ready")
            
        except Exception as e:
            exc_type = type(e).__name__
            exc_msg = str(e).split('\n')[0][:100]
            error_msg = f"Automation error: {exc_type}: {exc_msg}"
            
            print(f"\n{'!'*60}")
            print(f"ORCHESTRATOR ERROR: {exc_type}")
            print(f"  Message: {exc_msg}")
            print(f"{'!'*60}\n")
            
            self.worker.keep_browser_open_on_error = True
            self.worker.error.emit(error_msg)
        finally:
            self.worker.cleanup()
            self.worker.finished.emit()

def add_run_method_to_worker(worker):
    """Add the run method to automation worker"""
    def run():
        orchestrator = PT61AutomationOrchestrator(worker)
        orchestrator.run()
    
    worker.run = run
    return worker

original_create_worker = create_automation_worker

def create_automation_worker_with_run(*args, **kwargs):
    worker = original_create_worker(*args, **kwargs)
    return add_run_method_to_worker(worker)

create_automation_worker = create_automation_worker_with_run

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    test_browser = "Chrome"
    test_username = "jcunningham@kingcunningham.com"
    test_password = "Kc123!@#"
    test_save_location = r"D:\repositorys\KC_appp\data\sorted\pt61"
    test_version = "PT-61 New Batch"
    test_document_stacking = True

    thread, worker = run_web_automation_thread(
        test_excel_path, test_browser, test_username, test_password, test_save_location, test_version, test_document_stacking
    )
    
    worker.status.connect(print)
    worker.progress.connect(lambda p: print(f"Progress: {p}%"))
    worker.error.connect(lambda e: print(f"Error: {e}"))

    thread.start()

    sys.exit(app.exec())