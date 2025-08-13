# Beaufort hilton head timeshare Workflow Spec

## Overview
The Beaufort HiltonHead Timeshare Workflow processes Excel data and 3 PDF document stacks to create Simplifile packages containing both **DEED - HILTON HEAD TIMESHARE** and **MORT - SATISFACTION** documents for Beaufort County, SC.

## Input Files (4 total)
1. **Excel File**: Row data for each package
2. **Deed Stack PDF**: All deed documents in order (2 pages each)
3. **Affidavit Stack PDF**: All affidavit documents in order (2 pages each) - Optional
4. **Mortgage Satisfaction Stack PDF**: All mortgage satisfaction documents in order (1 page each)

**Note**: Row 1 in Excel corresponds to Document 1 from each PDF stack. Just think of it as a stack data structure that we are only popping from.

## ETL Methodology

### PDF Processing (Extract)

#### Document Stack Structure
1. **Deed Stack PDF**: Multiple 2-page deed documents concatenated
2. **Affidavit Stack PDF**: Multiple 2-page affidavit documents concatenated (optional)
3. **Mortgage Satisfaction Stack PDF**: Multiple 1-page satisfaction documents concatenated

#### Document Extraction Logic
- **Row N in Excel** → Extract documents at position N from each stack:
  - Deed: Pages `(N-1)*2 + 1` through `N*2` from Deed Stack
  - Affidavit: Pages `(N-1)*2 + 1` through `N*2` from Affidavit Stack (if provided)
  - Mortgage Satisfaction: Page `N` from Mortgage Satisfaction Stack

#### Deed and Affidavit Merging
- If both Deed and Affidavit stacks are provided, merge them:
  - Combined document = Deed pages (2) + Affidavit pages (2) = 4 pages total
  - This creates a single 4-page document for upload as the deed

#### Required Excel Columns
| Column Name | Required | Notes |
|-------------|----------|-------|
| `KC File No.` | Yes | King Cunningham file number |
| `Account` | Yes | Account identifier |
| `Last Name #1` | Yes | Primary owner's last name |
| `First Name #1` | Yes | Primary owner's first name |
| `&` | No | If value is "&", indicates second owner exists |
| `Last Name #2` | No | Required only if `&` column contains "&" |
| `First Name #2` | No | Required only if `&` column contains "&" |
| `GRANTOR/GRANTEE` | Yes | Entity name for grantor/grantee |

**Note on Validation**: If any of the required columns are empty for a particular row, that row should be skipped (not processed). Log a warning message about the skipped row and continue processing with the next valid row.

**Note on Beaufort Simplifications**: Beaufort County does not require execution dates, legal descriptions, or reference information, making the workflow significantly simpler than other counties.

## Transform

### Excel to API Field Mapping

The following mapping is used to transform Excel column headers to internal API field names:

```json
{
  "KC File No.": "kc_file_no",
  "Account": "account_number",
  "Last Name #1": "owner_1_last_name",
  "First Name #1": "owner_1_first_name",
  "&": "has_second_owner",
  "Last Name #2": "owner_2_last_name",
  "First Name #2": "owner_2_first_name",
  "GRANTOR/GRANTEE": "grantor_grantee_entity"
}
```

### Workflow Constants

```python
COUNTY_ID = "SCCY4G"
COUNTY_NAME = "Beaufort County, SC"
DEED_DOCUMENT_TYPE = "DEED - HILTON HEAD TIMESHARE"
MORTGAGE_DOCUMENT_TYPE = "MORT - SATISFACTION"
KING_CUNNINGHAM_REQUIRED = True
DEED_REQUIRES_EXECUTION_DATE = False
DEED_REQUIRES_LEGAL_DESCRIPTION = False
DEED_REQUIRES_REFERENCE_INFO = False
MORTGAGE_REQUIRES_EXECUTION_DATE = False
MORTGAGE_REQUIRES_LEGAL_DESCRIPTION = False
MORTGAGE_REQUIRES_REFERENCE_INFO = False
```

### Document Structure Per Package

### Package Naming Convention
- **Format**: `{Account} {Last Name #1} TD {KC File No.}`
- **Special Case**: If `Last Name #1` starts with "ORG:", use `{Account} {First Name #1} TD {KC File No.}`

### Documents Created (2 per package)

#### 1. Deed Document
- **Type**: `DEED - HILTON HEAD TIMESHARE` (Beaufort County specific)
- **PDF Source**: Deed Stack (2 pages) + Affidavit Stack (2 pages) if provided = 4 pages total
- **Grantors**:
  - `KING CUNNINGHAM LLC TR` (Organization)
  - Entity from `GRANTOR/GRANTEE` column (Organization)
  - Individual owners from Excel (First Name #1 Last Name #1, First Name #2 Last Name #2)
- **Grantees**:
  - Entity from `GRANTOR/GRANTEE` column (Organization)
- **Required Fields**:
  - None beyond grantors/grantees (Beaufort County simplification)

#### 2. Mortgage Satisfaction Document
- **Type**: `MORT - SATISFACTION` (Beaufort County specific)
- **PDF Source**: Mortgage Satisfaction Stack (1 page per document)
- **Grantors**:
  - Individual owners only (First Name #1 Last Name #1, First Name #2 Last Name #2)
  - **Note**: KING CUNNINGHAM LLC TR is NOT included as grantor
- **Grantees**:
  - Entity from `GRANTOR/GRANTEE` column (Organization)
- **Required Fields**:
  - None beyond grantors/grantees (Beaufort County simplification)

## API Payload Structure (Load)

```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{account_number}-TD",
      "name": "{owner_1_last_name} {account_number} TD",
      "kindOfInstrument": ["DEED - HILTON HEAD TIMESHARE"],
      "indexingData": {
        "grantors": [
          {
            "nameUnparsed": "KING CUNNINGHAM LLC TR",
            "type": "Organization"
          },
          {
            "nameUnparsed": "{grantor_grantee_entity}",
            "type": "Organization"
          },
          {
            "firstName": "{owner_1_first_name}",
            "lastName": "{owner_1_last_name}",
            "type": "Individual"
          },
          {
            "firstName": "{owner_2_first_name}",
            "lastName": "{owner_2_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{grantor_grantee_entity}",
            "type": "Organization"
          }
        ]
      },
      "fileBytes": ["{merged_deed_pdf}"]
    },
    {
      "submitterDocumentID": "D-{account_number}-SAT",
      "name": "{owner_1_last_name} {account_number} SAT",
      "kindOfInstrument": ["MORT - SATISFACTION"],
      "indexingData": {
        "grantors": [
          {
            "firstName": "{owner_1_first_name}",
            "lastName": "{owner_1_last_name}",
            "type": "Individual"
          },
          {
            "firstName": "{owner_2_first_name}",
            "lastName": "{owner_2_last_name}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{grantor_grantee_entity}",
            "type": "Organization"
          }
        ]
      },
      "fileBytes": ["{mortgage_pdf}"]
    }
  ],
  "recipient": "SCCY4G",
  "submitterPackageID": "P-{kc_file_no}-{account_number}",
  "name": "{account_number} {owner_1_last_name} TD {kc_file_no}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

**Note:** Entire second owner object only included if second owner exists

## Error & Validation Handling

### Fail Fast Scenarios
- Missing required Excel columns
- Invalid PDF structure (deed documents not divisible by 2 pages)
- Missing required data fields
- Invalid data formats

### Recoverable Warnings
- Missing optional affidavit documents
- Non-standard name formatting
- Missing second owner information

### Validations (Fail Fast)
1. **Excel Structure**: Required columns must exist
2. **Data Completeness**: KC File No., Account, names cannot be empty
3. **PDF Structure**: 
   - Deed stack must have page count divisible by 2
   - If affidavit stack provided, must have same document count as deed stack
   - Mortgage stack must have same document count as deed stack
4. **Name Format**: All names must be in ALL CAPS
5. **Organization Format**: Organizations should use "ORG:" prefix in Last Name field

### Special Handling
- **Organization Names**: If `Last Name #1` starts with "ORG:", treat as organization where `First Name #1` contains the full organization name
- **Hyphenated Names**: Remove hyphens and convert to spaces (e.g., "SMITH-JOHNSON" becomes "SMITH JOHNSON")
- **Merged Documents**: When affidavits are provided, the final deed document will be 4 pages (2 deed + 2 affidavit)
- **Simplified Requirements**: Beaufort County does not require execution dates, legal descriptions, consideration amounts, or reference information, making validation and processing significantly simpler

## Key Differences from Other Counties

### Beaufort County Simplifications
1. **No Execution Date Required**: Documents do not need execution dates
2. **No Legal Description Required**: Property descriptions are not required in the indexing data
3. **No Reference Information Required**: Book and page references are not required
4. **No Consideration Amount**: Monetary consideration is not required for deeds
5. **Minimal Validation**: Only basic party information and document structure validation needed

### Benefits of Simplified Workflow
- **Faster Processing**: Fewer fields to validate and populate
- **Reduced Error Risk**: Fewer required fields means fewer opportunities for validation failures
- **Easier Data Preparation**: Excel files can be simpler with fewer required columns
- **Streamlined API Payloads**: Smaller, simpler JSON structures for API requests