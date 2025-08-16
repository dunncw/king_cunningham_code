# `{Workflow Name}` Specification

## Overview

### Purpose
Brief description of what this workflow accomplishes and the business problem it solves.

### User Expectations
**Input Requirements**: List of files/data user must provide
**Processing Results**: What the workflow will produce and which counties will receive submissions

---

## Specification

### Input Requirements

#### Excel Document
**File Description**: {Description of the Excel file purpose and structure}

##### Required Columns
| Column Name | Data Type | Description | Validation Rules |
|-------------|-----------|-------------|------------------|
| Column 1    | String    | Purpose     | Rules            |
| Column 2    | Integer   | Purpose     | Rules            |

##### Column Processing Rules
**{Column Name}**:
- Processing rule 1
- Processing rule 2
- Special handling cases

**{Column Name}**:
- Processing rule 1
- Processing rule 2

##### Excel Validation
- **Structure Validation**: Required columns must be present
- **Data Validation**: Required fields must not be empty, proper data types
- **Row Validation**: Each row must pass business rule validation

##### Multi-Row Processing Rules
Description of how multiple Excel rows are handled:
- **Single Record Processing**: How individual rows are processed
- **Grouped Processing**: Rules for combining multiple rows (if applicable)
- **Skip Conditions**: When rows should be ignored

#### Document Files

##### Document Structure
**File Type**: {PDF Stack/Directory/Variable PDF}
**Organization**: {How documents are organized in the file(s)}

##### Document Requirements
- **Document 1**: {Pages per document}, {Purpose}
- **Document 2**: {Pages per document}, {Purpose}

##### Document Validation
- **File Existence**: All required document files must exist and be readable
- **Document Alignment**: PDF documents must align with Excel row count
- **Page Count Validation**: Total pages must match expected document count

##### Document Processing Rules
- **Extraction Method**: How individual documents are extracted
- **Special Handling**: Any unique processing requirements

### Payload Requirements

#### Data Gathering Rules
Description of how data from Excel and documents is combined to create API payloads:

##### County Routing
**Routing Logic**: How the workflow determines which county to submit to
- Rule 1: Condition → County
- Rule 2: Condition → County

##### Data Transformation
**Field Mapping**: How Excel columns map to API fields
**Business Logic**: Rules applied during data transformation

##### Package Organization
**Package Naming**: How packages are named
**Document Grouping**: How documents are organized within packages
**Metadata**: Additional information attached to packages

##### Payload Validation
- **Package Structure**: API payload must be valid JSON
- **Required Fields**: All county-required fields must be present
- **Document Attachments**: All documents must have valid PDF data

#### County-Specific Requirements

##### {County Name 1}
**County ID**: {ID}
**Document Types**: 
- Document Type 1: {API document type name}
- Document Type 2: {API document type name}

**Required Fields**:
- Field 1: {Source} → {API field name}
- Field 2: {Source} → {API field name}

**Business Rules**:
- Rule 1
- Rule 2

##### {County Name 2}
**County ID**: {ID}
**Document Types**: 
- Document Type 1: {API document type name}

**Required Fields**:
- Field 1: {Source} → {API field name}

**Business Rules**:
- Rule 1
- Rule 2

### API Payload Structure

#### Package-Level Structure
```json
{
  "documents": [/* Array of document objects */],
  "recipient": "{County ID}",
  "submitterPackageID": "{Package ID format}",
  "name": "{Package name format}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

#### Document Structure Template

##### {Document Type 1}
```json
{
  "submitterDocumentID": "{Format}",
  "name": "{Format}",
  "kindOfInstrument": ["{County-specific document type}"],
  "indexingData": {
    "field1": "{Source and format}",
    "field2": "{Source and format}",
    "grantors": [
      {
        "firstName": "{Source}",
        "lastName": "{Source}",
        "type": "Individual"
      }
    ],
    "grantees": [
      {
        "nameUnparsed": "{Source}",
        "type": "Organization"
      }
    ]
  },
  "fileBytes": ["{Base64 PDF data}"]
}
```

##### {Document Type 2}
```json
{
  "submitterDocumentID": "{Format}",
  "name": "{Format}",
  "kindOfInstrument": ["{County-specific document type}"],
  "indexingData": {
    "field1": "{Source and format}",
    "field2": "{Source and format}"
  },
  "fileBytes": ["{Base64 PDF data}"]
}
```

### Error Handling

#### Fail-Fast Scenarios
Conditions that stop processing immediately:
- Missing required files
- Invalid Excel structure
- Critical data validation failures

#### Skip Scenarios
Conditions that cause individual rows to be skipped:
- Invalid row data
- Unable to route to county
- Missing required fields for specific row

#### Warning Scenarios
Conditions that generate warnings but don't stop processing:
- Non-standard data formats
- Optional field validation issues