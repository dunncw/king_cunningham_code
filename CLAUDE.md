# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Building the Application
```bash
python build.py
```
This runs PyInstaller with the KC_app.spec configuration to create a Windows executable.

### Running the Application in Development
```bash
python src/main.py
```

### Testing
```bash
python test.py  # Basic test script for Excel highlighting
python tests/test_simplifile_api.py  # Simplifile API tests
python tests/test_update_checker.py  # Update checker tests
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Application Architecture

### Core Application Structure
- **Entry Point**: `src/main.py` - Main application entry with splash screen and update checking
- **Main Window**: `src/ui/main_window.py` - Central UI coordinator using QStackedWidget
- **Version**: Currently v0.0.5, defined in `src/main.py`

### Key Modules

#### Document Processing (`src/document_processor/`)
- OCR-based document processing using Tesseract and PyMuPDF
- Separates DEED and MTG (Mortgage) documents from PDFs
- Uses OpenCV for image processing and pyzbar for barcode detection

#### Simplifile Integration (`src/simplifile/`)
- **API Layer**: `api.py` - Handles Simplifile API interactions
- **Models**: `models.py` - Data structures for packages, documents, parties
- **County Config**: `county_config.py` - County-specific configurations and document types
- **Batch Processing**: `batch_processor.py` - Handles bulk document uploads
- **Excel Processing**: `excel_processor.py` - Reads document data from Excel files

#### Web Automation (`src/web_automation/`)
- Selenium-based web automation functionality
- Chrome WebDriver integration

#### Other Automation Modules
- **CRG Automation**: `src/crg_automation/` - CRG-specific processing
- **SCRA Automation**: `src/scra_automation/` - SCRA document processing and interpretation
- **PACER Automation**: `src/pacer_automation/` - PACER system integration

#### UI Components (`src/ui/`)
- PyQt6-based interface with modular UI components for each automation type
- Batch preview dialogs and specialized automation UIs

### External Dependencies
- **Tesseract OCR**: Required for document text extraction
- **Ghostscript**: Required for PDF processing
- **PyQt6**: UI framework
- **Selenium**: Web automation
- **PyMuPDF**: PDF manipulation
- **OpenCV**: Image processing

### Configuration Files
- **KC_app.spec**: PyInstaller configuration with Tesseract and Ghostscript paths
- **requirements.txt**: Python dependencies
- **resources/**: Application icons and splash images

### County-Specific Configurations
The Simplifile module uses a county configuration system where each county has specific document types and requirements. Key configurations include:
- Document type mappings (DEED_DOCUMENT_TYPE, MORTGAGE_DOCUMENT_TYPE)
- Required field configurations
- Grantee/Grantor handling rules
- Special processing requirements

### Threading Architecture
The application uses PyQt6's QThread for background processing:
- OCR operations run in separate threads
- Simplifile API calls are threaded
- Web automation runs in background threads
- All UI updates use Qt signals/slots pattern

### Error Handling
- Global exception hook in `src/main.py` captures unhandled exceptions
- QMessageBox dialogs for user-facing errors
- Status updates through Qt signals

## Development Notes

### Building for Distribution
1. Ensure Tesseract and Ghostscript are installed at paths specified in KC_app.spec
2. Update version number in `src/main.py`
3. Run `python build.py`
4. Executable will be in `dist/` folder

### Testing Simplifile Integration
Use `tests/test_simplifile_api.py` for API testing. Note: Contains test credentials that should be replaced with actual values.

### Adding New County Configurations
Extend the county configuration system in `src/simplifile/county_config.py` by creating new county-specific classes that inherit from CountyConfig.