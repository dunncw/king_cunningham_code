# KC_app

OCR Document Processor for processing legal documents. This application extracts and separates DEED and MTG (Mortgage) documents from PDF files.

## Download and Installation

1. Go to the [Releases](https://github.com/dunncw/KC_app/releases) page of this repository.
2. Download the latest release ZIP file.
3. Extract the ZIP file to a location on your computer.
4. Run the `KC_app.exe` file to start the application.

## Requirements

- Windows 10 or later

## Usage

1. Launch the application by running `KC_app.exe`.
2. Choose between "Single File Processing" or "Batch Processing (Directory)".
3. Select the input file or directory using the "Select Input" button.
4. Choose an output directory using the "Select Output Directory" button.
5. Click "Process Documents" to start the OCR and document extraction process.
6. View the progress and results in the application window.
7. Use the "Save Output" button to save the processing log if needed.

## Building from Source

If you want to build the application from source:

1. Clone this repository:
   ```
   git clone https://github.com/dunncw/KC_app.git
   cd KC_app
   ```

2. Install Python 3.8 or later.

3. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

6. Ensure you have Tesseract and Ghostscript installed on your system. Update the paths in `KC_app.spec` file to match your installation locations:
   ```python
   tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path
   ghostscript_path = r'C:\Program Files\gs\gs9.54.0\bin\gswin64c.exe'  # Update this path
   ```

7. Run the build script:
   ```
   python build.py
   ```

8. The packaged application will be in the `dist` folder.

## Creating a Release

To create a release for distribution:

1. Build the application using the steps above.
2. Zip the contents of the `dist` folder.
3. Go to the [Releases page](https://github.com/dunncw/KC_app/releases) on GitHub.
4. Click "Draft a new release".
5. Tag the release with a version number (e.g., v1.0.0).
6. Provide a title and description for the release.
7. Upload the zipped file as a binary attachment.
8. Publish the release.

## Dependencies

This application relies on several open-source projects:

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Ghostscript](https://www.ghostscript.com/)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [OpenCV](https://opencv.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

Please refer to their respective licenses for terms of use.