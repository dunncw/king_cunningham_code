# `FULTON-MTG-FCL` Workflow Spec

## Overview
The Fulton Foreclosure Workflow processes Excel data and 3 PDF document stacks to create Simplifile packages containing both **Deed** and **Mortgage Satisfaction** documents for Fulton County, GA.

## Input Files (4 total)
1. **Excel File**: Row data for each package
2. **Deed Stack PDF**: All deed documents in order (3 pages each)
3. **PT-61 Stack PDF**: All PT-61 helper documents in order (1 page each)
4. **Mortgage Satisfaction Stack PDF**: All mortgage satisfaction documents in order (1 page each)

**Note**: Row 1 in Excel corresponds to Document 1 from each PDF stack. Just think of it as a stack data structure that we are only popping from.

## ETL Methodology

### PDF Processing (Extract)

#### Document Stack Structure
1. **Deed Stack PDF**: Multiple 3-page deed documents concatenated
2. **PT-61 Stack PDF**: Multiple 1-page PT-61 documents concatenated
3. **Mortgage Satisfaction Stack PDF**: Multiple 1-page satisfaction documents concatenated

#### Document Extraction Logic
- **Row N in Excel** → Extract documents at position N from each stack:
  - Deed: Pages `(N-1)*3 + 1` through `N*3` from Deed Stack
  - PT-61: Page `N` from PT-61 Stack
  - Mortgage Satisfaction: Page `N` from Mortgage Satisfaction Stack

#### Required Excel Columns
| Column Name | Required | Notes |
|-------------|----------|-------|
| `Contract Num` | Yes | Used in package naming |
| `First 1` | Yes | Individual owner |
| `Middle 1` | No | Optional, include only if not empty |
| `Last 1` | Yes | Individual owner |
| `&` | Yes | If value is "&", indicates second owner exists |
| `First 2` | No | Required only if `&` column contains "&". May contain whole name for second person so Last 2 can be empty but ensure First 2 contains something. |
| `Middle 2` | No | Optional, include only if not empty |
| `Last 2` | No | Required only if `&` column contains "&" |
| `Sales Price` | Yes | May contain $ and commas (e.g., "$21,369.55") |

**Note on Validation**: If any of the required columns are empty for a particular row, that row should be skipped (not processed). Log a warning message about the skipped row and continue processing with the next valid row.

## Transfrom

### Excel to API Field Mapping

The following mapping is used to transform Excel column headers to internal API field names:

```json
{
  "Contract Num": "contract_number",
  "First 1": "grantor_1_first_name",
  "Middle 1": "grantor_1_middle_name",
  "Last 1": "grantor_1_last_name",
  "&": "has_second_owner",
  "First 2": "grantor_2_first_name",
  "Middle 2": "grantor_2_middle_name",
  "Last 2": "grantor_2_last_name",
  "Sales Price": "consideration_amount"
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
FIXED_DEED_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"
FIXED_SAT_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"
```

### Document Structure Per Package

### Package Naming Convention
- **Format**: `{Contract Num} {Last 1} FCL DEED`

### Documents Created (2 per package)

#### 1. Deed Document
- **Type**: `DEED` (Fulton County specific)
- **PDF Source**: Deed Stack (3 pages per document)
- **Grantors**:
  - Individual owners from Excel (First 1 Last 1, First 2 Last 2)
- **Grantees**:
  - `CENTENNIAL PARK DEVELOPMENT LLC` (Organization)
- **Required Fields**:
  - Consideration: From `Sales Price` column (strip $ and commas)
  - Tax Exempt: Always `true`
  - Parcel ID: Always `14-0078-0007-096-9`
- **Helper Documents**:
  - PT-61: Attached as nested document (1 page from PT-61 Stack)

#### 2. Mortgage Satisfaction Document
- **Type**: `SATISFACTION` (Fulton County specific)
- **PDF Source**: Mortgage Satisfaction Stack (1 page per document)
- **Grantors**:
  - Same individual owners as deed (First 1 Last 1, First 2 Last 2)
- **Grantees**:
  - `CENTENNIAL PARK DEVELOPMENT LLC` (Organization)
- **Required Fields**:
  - None beyond grantors/grantees

## API Payload Structure (Load)

```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{contract_number}-DEED",
      "name": "{grantor_1_last_name} {contract_number} DEED",
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
          },
          {
            "firstName": "{grantor_2_first_name}",
            "middleName": "{grantor_2_middle_name}",
            "lastName": "{grantor_2_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{deed_grantee_name}",
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
      "name": "{grantor_1_last_name} {contract_number} SAT",
      "kindOfInstrument": ["SATISFACTION"],
      "indexingData": {
        "grantors": [
          {
            "firstName": "{grantor_1_first_name}",
            "middleName": "{grantor_1_middle_name}",
            "lastName": "{grantor_1_last_name}",
            "type": "Individual"
          },
          {
            "firstName": "{grantor_2_first_name}",
            "middleName": "{grantor_2_middle_name}",
            "lastName": "{grantor_2_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{sat_grantee_name}",
            "type": "Organization"
          }
        ]
      },
      "fileBytes": ["{mortgage_pdf}"]
    }
  ],
  "recipient": "GAC3TH",
  "submitterPackageID": "P-{contract_number}",
  "name": "{contract_number} {grantor_1_last_name} FCL DEED",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

**Note:** Entire second grantor object only included if second owner exists

## Error & Validation Handling

### Fail Fast Scenarios
- Missing required Excel columns
- Invalid PDF structure
- Missing required data fields
- Invalid data formats

### Recoverable Warnings
- Missing optional middle names
- Non-standard name formatting
- Missing second owner information

### Validations (Fail Fast)
1. **Excel Structure**: Required columns must exist
2. **Data Completeness**: Contract Num, names, sales price cannot be empty
3. **PDF Structure**: All 3 stacks must have correct page counts for extraction. All PDF stacks must have same number of documents
4. **Name Format**: All names must be in ALL CAPS
5. **Sales Price Format**: Must be valid number after removing $ and commas