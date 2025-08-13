# Simplifile Bulk Upload System - User Guide

## Overview

This system automates the bulk upload of legal documents to Simplifile, streamlining the process of filing large batches of deeds, mortgages, and related documents with various county recording offices.

## System Organization

The system is structured hierarchically by **County** → **Workflow Type**. Each combination has specific document requirements and data fields that must be provided.

### Currently Available Workflows

#### **Horry County, SC**
- **MTG-FCL Workflow** (Mortgage Foreclosure)
  - Upload Method: Document Stacks
  - Documents: Deed Stack (2 pages each), Affidavit Stack (2 pages each, optional), Mortgage Satisfaction Stack (1 page each)
  
- **HOA-FCL Workflow** (HOA Foreclosure with Condo Liens)
  - Upload Method: Document Stacks
  - Documents: Deed Stack (2 pages each), Affidavit Stack (2 pages each, optional), Condo Lien Satisfaction Stack (1 page each)

#### **Beaufort County, SC**
- **MTG-FCL Workflow** (Hilton Head Timeshare)
  - Upload Method: Document Stacks
  - Documents: Deed Stack (2 pages each), Affidavit Stack (2 pages each, optional), Mortgage Satisfaction Stack (1 page each)

#### **Fulton County, GA**
- **MTG-FCL Workflow** (Standard Foreclosure)
  - Upload Method: Document Stacks
  - Documents: Deed Stack (3 pages each), PT-61 Stack (1 page each), Mortgage Satisfaction Stack (1 page each)
  
- **Deedbacks Workflow**
  - Upload Method: Individual Files with Directory
  - Documents: Individual PDFs following naming convention (e.g., "LASTNAME DB CONTRACTNUM DB.pdf")

## Required Inputs

### 1. Excel Spreadsheet
Every workflow requires an Excel file with:
- **Specific column headers** (exact names required, but order doesn't matter)
- **One header row** followed by data rows
- **Each data row** represents one complete package/transaction
- **Required columns** vary by workflow but typically include:
  - Account/Contract numbers
  - Owner names (First/Last)
  - Reference information (Book/Page numbers)
  - Execution dates
  - Legal descriptions
  - Entity names

**Important**: Column headers must match exactly. For example, "KC File No." not "KC File #" or "KC File Number"

### 2. PDF Documents

The system supports two document upload methods:

#### **Method 1: Document Stacks** (Used by most workflows)
- Scan all documents of the same type into a single PDF file
- Documents must be in the exact order of the Excel rows
- Page counts must be consistent (e.g., all deeds are 2 pages)
- Create one stack per document type

**Example**: For 50 transactions requiring deeds and mortgages:
- One 100-page PDF containing all 50 deeds (2 pages each)
- One 50-page PDF containing all 50 mortgages (1 page each)

#### **Method 2: Individual Files with Directory** (Fulton Deedbacks only)
- Save each document as a separate PDF file
- Use specific naming convention that includes identifiers from Excel
- Place all files in a single directory/folder
- System matches files to Excel rows based on naming pattern

## Validation Process

Before uploading, the system performs comprehensive validation:

### Excel Validation
- ✓ Verifies all required columns are present
- ✓ Checks that required fields are not empty
- ✓ Validates date formats
- ✓ Ensures names are in ALL CAPS
- ✓ Confirms monetary values are properly formatted

### Document Validation

**For Document Stacks:**
- ✓ Verifies total page count matches expected count (rows × pages per document)
- ✓ Confirms each stack has correct number of pages per document
- ✓ Ensures all required stacks are provided
- ✓ Validates optional stacks if provided

**For Individual Files:**
- ✓ Checks that all required files exist based on Excel data
- ✓ Verifies file naming conventions are followed
- ✓ Confirms file accessibility and readability
- ✓ Reports any orphaned files (files without matching Excel rows)

### Validation Results
- **Pass**: Package proceeds to upload
- **Warning**: Non-critical issues logged, package may proceed
- **Fail**: Critical errors prevent upload, specific issues reported
- **Skip**: Rows with missing required data are skipped with notification

## Using the System

1. **Select County** - Choose the recording jurisdiction
2. **Select Workflow** - Choose the appropriate workflow type
3. **Load Excel File** - Import the prepared spreadsheet
4. **Add Documents** - Provide PDFs according to workflow requirements
5. **Run Validation** - System checks all inputs for completeness and accuracy
6. **Review Results** - System reports any issues found
7. **Process Upload** - Valid packages are formatted and sent to Simplifile

## Output and Results

The system provides:
- **Success count** - Number of packages successfully uploaded
- **Skip report** - List of skipped rows with reasons
- **Error log** - Detailed information about any failures
- **Validation summary** - Overview of all checks performed

## Best Practices

1. **Data Preparation**
   - Use provided templates when available
   - Ensure all names are in CAPITAL LETTERS
   - Mark organizations with "ORG:" prefix in Last Name field
   - Remove special characters from names (convert hyphens to spaces)

2. **Document Preparation**
   - Verify page counts before scanning
   - Maintain consistent order matching Excel rows
   - Check document quality and legibility

3. **Pre-Upload Checklist**
   - Verify column headers match exactly
   - Confirm all required fields have data
   - Check document counts match row counts
   - Review validation results before final upload

## Error Handling

Common issues and solutions:
- **"Missing required column"** → Check column header spelling/format
- **"Invalid page count"** → Verify all documents have correct number of pages
- **"File not found"** → Check file naming convention (for individual files)
- **"Empty required field"** → Review Excel for blank cells in required columns

## System Benefits

- **Efficiency**: Process hundreds of documents in minutes
- **Accuracy**: Automated validation reduces errors
- **Consistency**: Standardized formatting for all submissions
- **Flexibility**: Supports different document organization methods
- **Transparency**: Clear reporting of all actions and issues

For technical support or questions about specific workflow requirements, please consult the detailed workflow specifications or contact support.