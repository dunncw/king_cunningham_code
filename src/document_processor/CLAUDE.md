# Document Processor Module

This module handles OCR-based document processing, barcode detection, and automatic document separation for legal documents. It specializes in splitting DEED and MORTGAGE documents from multi-page PDFs.

## Architecture

### Core Components

#### OCRWorker (QThread)
- **Location**: `processor.py:20`
- **Purpose**: Threading wrapper for document processing operations
- **Key Methods**:
  - `run()` - Main thread execution
  - Emits `progress_updated`, `finished`, `error` signals

#### Main Processing Functions

##### extract_documents_by_barcode()
- **Location**: `processor.py:45`
- **Purpose**: Core document separation logic using barcode detection
- **Process**:
  1. Opens PDF with PyMuPDF (fitz)
  2. Processes each page for barcode detection using pyzbar
  3. Identifies DEED and MTG document markers
  4. Splits documents into separate PDFs
  5. Removes "NOTICE OF AVAILABILITY" pages automatically

##### perform_ocr()
- **Location**: `processor.py:180`
- **Purpose**: Tesseract OCR text extraction from PDF pages
- **Features**:
  - Cross-platform Tesseract path detection
  - Image preprocessing with OpenCV
  - Error handling for OCR failures

##### process_files()
- **Location**: `processor.py:220`
- **Purpose**: Batch processing for multiple PDF files
- **Workflow**:
  1. Iterates through selected files
  2. Calls barcode extraction for each
  3. Reports progress via Qt signals
  4. Handles individual file errors gracefully

## Key Features

### Barcode Detection
- Uses **pyzbar** library for barcode reading
- Supports Code 128 and Code 39 barcode types
- Identifies document type markers:
  - "MTG" barcodes for mortgage documents
  - "DEED" barcodes for deed documents

### Document Splitting Logic
- **2-Page Rule**: Creates 2-page documents when barcodes are detected
- **Page Range Detection**: Automatically determines start/end pages
- **File Naming**: Generates descriptive filenames based on document type

### OCR Integration
- **Tesseract OCR**: Text extraction for content validation
- **Image Processing**: OpenCV preprocessing for better OCR accuracy
- **Content Analysis**: Detects and removes notice pages

### Threading Architecture
- **Background Processing**: All OCR operations run in separate QThread
- **Progress Reporting**: Real-time progress updates via Qt signals
- **Error Handling**: Thread-safe error reporting to UI

## Dependencies

### Required External Tools
- **Tesseract OCR**: Text extraction engine
  - Windows: Typically at `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - Linux/Mac: Available via package managers
- **Ghostscript**: PDF processing support

### Python Libraries
- **PyMuPDF (fitz)**: PDF manipulation and rendering
- **pyzbar**: Barcode detection and decoding
- **OpenCV (cv2)**: Image processing and preprocessing
- **Pillow (PIL)**: Image format conversions
- **PyQt6**: Threading and signal/slot communication

## Configuration

### Tesseract Path Detection
```python
def get_tesseract_path():
    # Attempts multiple common installation paths
    # Returns first valid executable found
```

### Document Processing Settings
- **Page Range**: 2-page documents by default
- **Barcode Types**: Code 128, Code 39
- **Image DPI**: 300 DPI for OCR processing
- **Output Format**: PDF with original formatting preserved

## Usage Patterns

### Basic Document Processing
1. Select PDF files via UI
2. OCRWorker processes files in background thread
3. Barcode detection identifies document boundaries
4. Separate PDFs created for DEED and MTG documents
5. Progress updates sent to UI via signals

### Batch Processing
- Supports multiple file selection
- Individual file error handling
- Aggregate progress reporting
- Preserves original file structure

## Error Handling

### Common Error Scenarios
- **Missing Tesseract**: Graceful fallback with user notification
- **Invalid PDF**: Skip corrupted files, continue batch
- **No Barcodes Found**: Process as single document
- **OCR Failures**: Continue without text extraction

### Error Reporting
- Thread-safe error signals to UI
- Detailed error messages with file context
- Non-blocking error handling for batch operations

## File Output Structure

### Generated Files
- `{original_name}_DEED.pdf` - Deed documents
- `{original_name}_MTG.pdf` - Mortgage documents
- Preserves original directory structure
- Maintains PDF formatting and quality

### Processing Metadata
- Page ranges extracted
- Barcode locations recorded
- OCR confidence scores (when available)
- Processing timestamps

## Performance Considerations

### Optimization Strategies
- **Threading**: Background processing prevents UI blocking
- **Memory Management**: Process pages individually to reduce RAM usage
- **Batch Efficiency**: Minimal file I/O operations
- **Error Recovery**: Continue processing on individual failures

### Typical Performance
- **Processing Speed**: ~2-3 seconds per page
- **Memory Usage**: ~50MB per PDF
- **Barcode Detection**: <1 second per page
- **OCR Processing**: 1-2 seconds per page

## Integration Points

### UI Integration
- Connects to `DocumentProcessorUI` via Qt signals/slots
- Progress bar updates during processing
- Error dialog displays for user feedback

### File System Integration
- Preserves original file permissions
- Creates output files in same directory as source
- Handles file naming conflicts automatically

## Development Notes

### Adding New Document Types
1. Extend barcode detection logic in `extract_documents_by_barcode()`
2. Add new document type constants
3. Update file naming conventions
4. Test with representative documents

### OCR Enhancement
- Adjust image preprocessing parameters in `perform_ocr()`
- Experiment with different OCR engines if needed
- Add OCR confidence thresholds for quality control

### Performance Tuning
- Consider parallel processing for multiple files
- Implement page caching for large documents
- Add memory usage monitoring and cleanup