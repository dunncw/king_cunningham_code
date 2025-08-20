# `FULTON-DEEDBACKS` Workflow Spec

## Overview
The Fulton Deedbacks Workflow processes Excel data and a directory of PDF documents to create Simplifile packages containing **Deed** documents and optional **Mortgage Satisfaction** documents for Fulton County, GA.

## Input Files (2 total)
1. **Excel File**: Row data for each package
2. **Documents Directory**: Folder containing all PDF documents with specific naming convention

**Note**: Each row in Excel corresponds to a set of documents in the directory identified by naming convention.

## ETL Methodology

### Document Directory Structure
The documents directory contains PDF files following this naming convention:
- **Deedback Document**: `{Last 1} DB {Contract Num} DB.pdf`
- **PT-61 Helper Document**: `{Last 1} DB {Contract Num} DB PT61.pdf`
- **Satisfaction Document** (Optional): `{Last 1} DB {Contract Num} DB SAT.pdf`

#### Document Matching Logic
- **Row N in Excel** → Find documents using pattern matching:
  - Deedback: `{Last 1} DB {Contract Num} DB.pdf`
  - PT-61: `{Last 1} DB {Contract Num} DB PT61.pdf`
  - Satisfaction: `{Last 1} DB {Contract Num} DB SAT.pdf` (if exists)

#### Required Excel Columns
| Column Name | Required | Notes |
|-------------|----------|-------|
| `Contract Num` | Yes | Used in package naming and file matching |
| `First 1` | Yes | Individual owner |
| `Middle 1` | No | Optional, include only if not empty |
| `Last 1` | Yes | Individual owner, used in file matching |
| `First 2` | No | Second owner (if exists) |
| `Middle 2` | No | Optional, include only if not empty |
| `Last 2` | No | Second owner last name (if exists) |
| `Sales Price` | Yes | May contain $ and commas (e.g., "$21,369.55") |
| `DB To` | Yes | Grantee organization name |

**Note on Validation**: If any of the required columns are empty for a particular row, that row should be skipped (not processed). Log a warning message about the skipped row and continue processing with the next valid row.

## Transform

### Excel to API Field Mapping

The following mapping is used to transform Excel column headers to internal API field names:

```json
{
  "Contract Num": "contract_number",
  "First 1": "grantor_1_first_name",
  "Middle 1": "grantor_1_middle_name",
  "Last 1": "grantor_1_last_name",
  "First 2": "grantor_2_first_name",
  "Middle 2": "grantor_2_middle_name",
  "Last 2": "grantor_2_last_name",
  "Sales Price": "consideration_amount",
  "DB To": "grantee_name"
}
```

### Workflow Constants

```python
COUNTY_ID = "GAC3TH"
COUNTY_NAME = "Fulton County, GA"
DEED_DOCUMENT_TYPE = "DEED"
MORTGAGE_DOCUMENT_TYPE = "SATISFACTION"
FIXED_PARCEL_ID = "14-0078-0007-096-9"
FIXED_TAX_EXEMPT = True
# Grantee comes from Excel "DB To" column instead of fixed value
```

### Document Structure Per Package

### Package Naming Convention
- **Format**: `{Last 1} DB {Contract Num}`

### Documents Created (1-2 per package)

#### 1. Deed Document (Always Present)
- **Type**: `DEED` (Fulton County specific)
- **PDF Source**: `{Last 1} DB {Contract Num} DB.pdf` from documents directory
- **Grantors**:
  - Individual owners from Excel (First 1 Last 1, First 2 Last 2)
- **Grantees**:
  - From `DB To` column (Organization)
- **Required Fields**:
  - Consideration: From `Sales Price` column (strip $ and commas)
  - Tax Exempt: Always `true`
  - Parcel ID: Always `14-0078-0007-096-9`
- **Helper Documents**:
  - PT-61: `{Last 1} DB {Contract Num} DB PT61.pdf` (attached as nested document)

#### 2. Mortgage Satisfaction Document (Optional)
- **Type**: `SATISFACTION` (Fulton County specific)
- **PDF Source**: `{Last 1} DB {Contract Num} DB SAT.pdf` from documents directory (if exists)
- **Grantors**:
  - From `DB To` column (Organization)
- **Grantees**:
  - Same individual owners as deed (First 1 Last 1, First 2 Last 2)
- **Required Fields**:
  - None beyond grantors/grantees

**Note**: Satisfaction document is only created if the corresponding SAT PDF file exists in the directory.

## API Payload Structure (Load)

### Single Document Package (Deed Only)
```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{contract_number}-DEED",
      "name": "{grantor_1_last_name} DB {contract_number} DEED",
      "kindOfInstrument": ["DEED"],
      "indexingData": {
        "consideration": "{consideration_amount}",
        "exempt": true,
        "grantors": [
          {
            "firstName": "{grantor_1_first_name}",
            "middleName": "{grantor_1_middle_name}",
            "lastName": "{grantor_1_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{grantee_name}",
            "type": "Organization"
          }
        ],
        "legalDescriptions": [
          {
            "description": "",
            "parcelId": "{parcel_id}"
          }
        ]
      },
      "fileBytes": ["{deed_pdf}"],
      "helperDocuments": [
        {
          "fileBytes": ["{pt61_pdf}"],
          "helperKindOfInstrument": "PT-61",
          "isElectronicallyOriginated": false
        }
      ]
    }
  ],
  "recipient": "GAC3TH",
  "submitterPackageID": "P-{contract_number}",
  "name": "{grantor_1_last_name} DB {contract_number}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

### Two Document Package (Deed + Satisfaction)
```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{contract_number}-DEED",
      "name": "{grantor_1_last_name} DB {contract_number} DEED",
      "kindOfInstrument": ["DEED"],
      "indexingData": {
        "consideration": "{consideration_amount}",
        "exempt": true,
        "grantors": [
          {
            "firstName": "{grantor_1_first_name}",
            "middleName": "{grantor_1_middle_name}",
            "lastName": "{grantor_1_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{grantee_name}",
            "type": "Organization"
          }
        ],
        "legalDescriptions": [
          {
            "description": "",
            "parcelId": "{parcel_id}"
          }
        ]
      },
      "fileBytes": ["{deed_pdf}"],
      "helperDocuments": [
        {
          "fileBytes": ["{pt61_pdf}"],
          "helperKindOfInstrument": "PT-61",
          "isElectronicallyOriginated": false
        }
      ]
    },
    {
      "submitterDocumentID": "D-{contract_number}-SAT",
      "name": "{grantor_1_last_name} DB {contract_number} SAT",
      "kindOfInstrument": ["SATISFACTION"],
      "indexingData": {
        "grantors": [
          {
            "nameUnparsed": "{grantee_name}",
            "type": "Organization"
          }
        ],
        "grantees": [
          {
            "firstName": "{grantor_1_first_name}",
            "middleName": "{grantor_1_middle_name}",
            "lastName": "{grantor_1_last_name}",
            "type": "Individual"
          }
        ]
      },
      "fileBytes": ["{mortgage_pdf}"]
    }
  ],
  "recipient": "GAC3TH",
  "submitterPackageID": "P-{contract_number}",
  "name": "{grantor_1_last_name} DB {contract_number}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

**Note:** Second grantor/grantee objects only included if second owner exists (determined by non-empty "First 2" field in Excel)

## Error & Validation Handling

### Fail Fast Scenarios
- Missing required Excel columns
- Documents directory doesn't exist or is empty
- Missing required document files for valid Excel rows
- Invalid data formats

### Recoverable Warnings
- Missing optional middle names
- Non-standard name formatting
- Missing SAT documents (these are optional)
- Extra PDF files in directory that don't match any Excel rows

### Validations (Fail Fast)
1. **Excel Structure**: Required columns must exist
2. **Data Completeness**: Contract Num, names, sales price, DB To cannot be empty
3. **Directory Structure**: Documents directory must exist and be readable
4. **File Matching**: Required files (Deed + PT-61) must exist for each valid Excel row
5. **Name Format**: All names must be in ALL CAPS
6. **Sales Price Format**: Must be valid number after removing $ and commas

### Document Matching Algorithm
1. For each valid Excel row, construct expected filenames:
   - Deed: `{Last 1} DB {Contract Num} DB.pdf`
   - PT-61: `{Last 1} DB {Contract Num} DB PT61.pdf`
   - SAT: `{Last 1} DB {Contract Num} DB SAT.pdf`

2. Check if required files (Deed + PT-61) exist in directory
3. Log warning if SAT file is missing (optional)
4. Skip row if required files are missing

### File Discovery Process
1. **Scan Directory**: Get list of all PDF files in documents directory
2. **Parse Filenames**: Extract Last Name and Contract Number from each filename
3. **Match to Excel**: For each Excel row, find corresponding files
4. **Validate Completeness**: Ensure required files exist for processing
5. **Report Orphans**: Log any PDF files that don't match Excel rows

## Processing Flow
1. Load and validate Excel file
2. Scan documents directory and catalog all PDF files
3. Match Excel rows to document files
4. Process each valid row:
   - Extract documents from directory
   - Transform Excel data
   - Build API payload
   - Upload to Simplifile
5. Report results and statistics