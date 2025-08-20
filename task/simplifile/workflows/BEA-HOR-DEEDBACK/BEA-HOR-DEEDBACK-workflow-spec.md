# `BEA-HOR-DEEDBACK` Specification

## Overview

### Purpose
The BEA-HOR-DEEDBACK workflow processes timeshare deedback documents across multiple counties based on project numbers. It handles variable-length PDF documents and automatically routes submissions to either Beaufort County or Horry County based on the project type, while consolidating multi-unit contracts into single packages.

### User Expectations
**Input Requirements**: Excel file with package data including page counts, and a single PDF stack containing all deed documents with variable page lengths

**Processing Results**: Creates Simplifile packages containing deed documents submitted to either Beaufort County (Project 95) or Horry County (Projects 93, 94, 96). Project 98 entries are skipped. Multi-unit contracts are automatically consolidated into single packages.

---

## Specification

### Input Requirements

#### Excel Document
**File Description**: Excel spreadsheet containing one row per deedback document with contract details, unit information, and PDF page counts for variable-length document extraction.

##### Required Columns
| Column Name | Data Type | Description | Validation Rules |
|-------------|-----------|-------------|------------------|
| `Project` | String | Project number for county routing | Must be 93, 94, 95, 96, or 98 |
| `Number` | String | Contract number for package grouping | Required, non-empty |
| `Lead 1 First` | String | Primary grantor first name | Required, converted to UPPERCASE |
| `LEAD 1 LAST` | String | Primary grantor last name | Required, converted to UPPERCASE |
| `Lead 2 First` | String | Secondary grantor first name | Optional |
| `Lead 2 Last` | String | Secondary grantor last name | Optional |
| `Unit Code` | String | Property unit identifier | Required, non-empty |
| `Week` | String | Timeshare week | Required, non-empty |
| `OEB Code` | String | Additional identifier for Project 93 | Optional, used only for Anderson Ocean Club |
| `DB Date` | String | Document execution date (M/D/YYYY) | Required for Horry County projects |
| `DB Pages` | Integer | Number of pages for this document | Required, must be positive integer |
| `Consideration` | String | Monetary consideration amount | Required, $ and commas removed during processing |
| `Package Name` | String | Custom package name (Column AK) | Optional, auto-generated if empty |

##### Column Processing Rules
**Project**: 
- 93, 94, 96 → Route to Horry County (SCCP49)
- 95 → Route to Beaufort County (SCCY4G)
- 98 → Skip processing entirely

**Number**: 
- Combined with Project to create contract key for multi-unit grouping
- Used in package ID generation

**Lead Names**: 
- All names converted to UPPERCASE
- Lead 2 names optional but both first and last required if either provided
- Used as grantors in API payload

**Consideration**: 
- Just remove leading '$'. example '$67,980.00' -> '67,980.00'

**Package Name**: 
- If Column AK (Package Name) provided, use that value
- Otherwise auto-generate: `{LEAD 1 LAST} {Unit Code}-{Week}{OEB Code} {Project}-{Number}`

##### Excel Validation
- **Structure Validation**: All required columns must be present
- **Data Validation**: Required fields must not be empty, Project must be valid integer, DB Pages must be positive
- **Row Validation**: Each row must have valid project number and complete required data for target county

##### Multi-Row Processing Rules
**Single Record Processing**: Each row represents one deedback document with specified page count

**Multi-Unit Contract Processing**:
- Rows with same Project + Number combination are treated as multi-unit contracts
- Only the first row is processed for package creation and PDF extraction
- Subsequent rows contribute only to legal description and TMS combination
- Legal descriptions are combined: first unit gets full description, additional units get abbreviated format separated by semicolons
- Package naming and all other metadata use first row's information only
- PDF extraction occurs only at first row's position, subsequent positions are skipped

**Skip Conditions**: 
- Project = 98 (per specification)
- Missing required fields for target county
- Invalid page count values

#### Document Files

##### Document Structure
**File Type**: Variable PDF Stack
**Organization**: Single PDF file containing all deed documents concatenated in row order, with each document having the page count specified in the corresponding Excel row's DB Pages column

##### Document Requirements
- **Deed Documents**: Variable pages per document (1-6+ pages typical), contains complete deedback deed document

##### Document Validation
- **File Existence**: Deed Stack PDF must exist and be readable
- **Document Alignment**: Total PDF pages must equal or exceed sum of all DB Pages values for valid rows
- **Page Count Validation**: Each DB Pages value must be positive integer

##### Document Processing Rules
- **Extraction Method**: Use DB Pages column to determine document boundaries, extract pages sequentially starting from page 1
- **Multi-Unit Handling**: For duplicate contracts (same Project + Number), skip PDF extraction for 2nd+ occurrences but advance position counter
- **Special Handling**: Variable page lengths require dynamic position tracking through PDF stack

### Payload Requirements

#### Data Gathering Rules
Data from Excel rows and extracted PDF documents are combined to create county-specific API payloads with project-based routing and business rule application.

##### County Routing
**Routing Logic**: Project number determines target county
- Projects 93, 94, 96 → Horry County (SCCP49)
- Project 95 → Beaufort County (SCCY4G)
- Project 98 → Skip (no processing)

##### Data Transformation
**Field Mapping**: Excel columns mapped to internal fields, names converted to UPPERCASE, consideration cleaned of currency symbols
**Business Logic**: Project-specific grantee assignment, legal description formatting, TMS number lookup for Project 93

##### Package Organization
**Package Naming**: Custom name from Excel Column AK or auto-generated format using first row data for multi-unit contracts
**Document Grouping**: One deed document per package, multi-unit contracts consolidated into single package with combined legal descriptions
**Metadata**: Package ID format P-{Contract Number}, Document ID format D-{Contract Number}

##### Payload Validation
- **Package Structure**: Valid JSON with required Simplifile API fields
- **Required Fields**: County-specific required fields must be present and properly formatted
- **Document Attachments**: Base64 PDF data must be present and valid

#### County-Specific Requirements

##### Horry County (Projects 93, 94, 96)
**County ID**: SCCP49
**Document Types**: 
- Deed Document: "Deed - Timeshare"

**Required Fields**:
- Execution Date: DB Date → executionDate (MM/DD/YYYY format)
- Legal Description: Project-specific format → legalDescriptions[0].description
- TMS/Parcel ID: Project-specific lookup → legalDescriptions[0].parcelId
- Reference Information: Ref DEED BOOK/PAGE → referenceInformation

**Project-Specific Business Rules**:

**Project 93 (Anderson Ocean Club)**:
- Grantee: "OCEAN CLUB VACATIONS LLC"
- Legal Description: "ANDERSON OCEAN CLUB HPR UNIT {Unit Code} WK {Week}{OEB Code}"
- Additional Units: "; UNIT {Unit Code} WK {Week}{OEB Code}"
- TMS Number: Unit-to-TMS conversion table lookup

**Project 94 (Ocean 22)**:
- Grantee: "OCEAN 22 DEVELOPMENT LLC"  
- Legal Description: "OCEAN 22 VACATION SUITES U {Unit Code} W {Week}"
- Additional Units: "; U {Unit Code} W {Week}"
- TMS Number: Always "1810418003"

**Project 96 (OE Vacation Suites)**:
- Grantee: "NUM 1600 DEVELOPMENT LLC"
- Legal Description: "OE VACATION SUITES U {Unit Code} W {Week}" 
- Additional Units: "; U {Unit Code} W {Week}"
- TMS Number: Always "1810732008"

##### Beaufort County (Project 95)
**County ID**: SCCY4G
**Document Types**: 
- Deed Document: "DEED - HILTON HEAD TIMESHARE"

**Required Fields**:
- Consideration: Consideration → consideration (decimal format)
- Grantors: Lead names → grantors (Individual type)
- Grantees: Fixed organization → grantees (Organization type)

**Business Rules**:
- Grantee: Always "HII DEVELOPMENT LLC"
- Simplified Requirements: No execution date, legal descriptions, or reference information required
- No project-specific variations

### API Payload Structure

#### Package-Level Structure
```json
{
  "documents": [/* Single deed document */],
  "recipient": "{SCCP49 or SCCY4G}",
  "submitterPackageID": "P-{Contract Number}",
  "name": "{Package Name from Excel or auto-generated}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

#### Document Structure Templates

##### Horry County Deed Document
```json
{
  "submitterDocumentID": "D-{Contract Number}",
  "name": "{Package Name}",
  "kindOfInstrument": ["Deed - Timeshare"],
  "indexingData": {
    "executionDate": "{DB Date in MM/DD/YYYY format}",
    "consideration": "{Cleaned consideration as decimal}",
    "grantors": [
      {
        "firstName": "{Lead 1 First}",
        "lastName": "{LEAD 1 LAST}",
        "type": "Individual"
      },
      {
        "firstName": "{Lead 2 First}",
        "lastName": "{Lead 2 Last}",
        "type": "Individual"
      }
    ],
    "grantees": [
      {
        "nameUnparsed": "{Project-specific grantee organization}",
        "type": "Organization"
      }
    ],
    "legalDescriptions": [
      {
        "description": "{Project-specific legal description, combined for multi-unit}",
        "parcelId": "{TMS number(s), semicolon-separated for multi-unit}"
      }
    ],
    "referenceInformation": [
      {
        "documentType": "Deed - Timeshare",
        "book": "{Ref DEED BOOK}",
        "page": "{Ref DEED PAGE as integer}"
      }
    ]
  },
  "fileBytes": ["{Base64 PDF data from deed stack}"]
}
```

##### Beaufort County Deed Document
```json
{
  "submitterDocumentID": "D-{Contract Number}",
  "name": "{Package Name}",
  "kindOfInstrument": ["DEED - HILTON HEAD TIMESHARE"],
  "indexingData": {
    "consideration": "{Cleaned consideration as decimal}",
    "grantors": [
      {
        "firstName": "{Lead 1 First}",
        "lastName": "{LEAD 1 LAST}",
        "type": "Individual"
      },
      {
        "firstName": "{Lead 2 First}",
        "lastName": "{Lead 2 Last}",
        "type": "Individual"
      }
    ],
    "grantees": [
      {
        "nameUnparsed": "HII DEVELOPMENT LLC",
        "type": "Organization"
      }
    ]
  },
  "fileBytes": ["{Base64 PDF data from deed stack}"]
}
```

### Error Handling

#### Fail-Fast Scenarios
Conditions that stop processing immediately:
- Missing Excel file or Deed Stack PDF
- Invalid Excel structure (missing required columns)
- PDF page count mismatch (insufficient pages for all documents)
- Invalid project numbers outside allowed range

#### Skip Scenarios
Conditions that cause individual rows to be skipped:
- Project = 98 (per specification)
- Missing required fields for target county (e.g., DB Date for Horry projects)
- Invalid DB Pages value (non-numeric or negative)
- Unable to route row to supported county

#### Warning Scenarios
Conditions that generate warnings but don't stop processing:
- Non-standard name formatting (not all UPPERCASE)
- Missing optional fields (Lead 2 names, OEB Code for non-Project 93)
- Duplicate contract processing (multiple rows with same Project + Number)

## Multi-Unit Contract Example

### Input Rows:
```
Row 1: Project 93, Number 512565, Unit 210, Week 13, OEB Code B, DB Pages 6
Row 2: Project 93, Number 512565, Unit 300, Week 19, OEB Code B, DB Pages 6
```

### Processing Result:
- **Single Package Created**: Using first row's data for package name
- **Package Name**: `CROXALL 210-13B 93-512565`
- **PDF Used**: Only the 6-page document from Row 1 (Row 2's PDF position skipped)
- **Legal Description**: `ANDERSON OCEAN CLUB HPR UNIT 210 WK 13B; UNIT 300 WK 19B`
- **TMS Numbers**: `18104152410; 18104154830` (semicolon-separated)

## Reference Data

### Unit to TMS Conversion Table (Project 93 Only)
```python
unit_to_tms = {
    200: "18104154760",
    201: "18104154770",
    202: "18104154780",
    203: "18104152360",
    204: "18104154790",
    205: "18104152370",
    206: "18104154800",
    209: "18104152400",
    210: "18104152410",
    212: "18104152430",
    213: "18104154810",
    214: "18104154820",
    215: "18104152440",
    300: "18104154830",
    301: "18104154840",
    302: "18104154850",
    303: "18104152450",
    308: "18104152500",
    309: "18104152510",
    310: "18104152520",
    313: "18104154860",
    314: "18104154870",
    315: "18104154880",
    400: "18104152550",
    404: "18104154900",
    405: "18104152580",
    407: "18104152600",
    409: "18104152620",
    410: "18104152630",
    412: "18104152650",
    413: "18104154910",
    500: "18104152680",
    503: "18104152710",
    504: "18104152720",
    505: "18104152730",
    510: "18104152780",
    511: "18104152790",
    515: "18104154930",
    600: "18104154940",
    601: "18104154950",
    603: "18104152830",
    605: "18104152850",
    607: "18104152870",
    609: "18104152890",
    610: "18104152900",
    611: "18104154960",
    612: "18104152910",
    700: "18104154970",
    702: "18104154990",
    703: "18104152950",
    705: "18104152970",
    707: "18104155010",
    708: "18104152980",
    709: "18104152990",
    710: "18104153000",
    711: "18104153010",
    714: "18104153020",
    715: "18104155040",
    800: "18104155050",
    802: "18104155060",
    803: "18104153040",
    805: "18104153060",
    811: "18104153120",
    812: "18104153130",
    813: "18104155070",
    815: "18104155080",
    900: "18104155090",
    901: "18104153150",
    902: "18104153160",
    903: "18104153170",
    904: "18104153180",
    910: "18104153240",
    911: "18104155100",
    912: "18104153250",
    915: "18104153280",
    1000: "18104155110",
    1002: "18104155120",
    1003: "18104153300",
    1004: "18104153310",
    1005: "18104153320",
    1007: "18104153340",
    1008: "18104153350",
    1011: "18104153380",
    1012: "18104153390",
    1014: "18104153400",
    1015: "18104153410",
    1100: "18104155140",
    1101: "18104155150",
    1102: "18104155160",
    1104: "18104153430",
    1105: "18104153440",
    1108: "18104153470",
    1111: "18104153500",
    1115: "18104153530",
    1200: "18104153540",
    1201: "18104153550",
    1202: "18104155180",
    1205: "18104153580",
    1210: "18104155190",
    1211: "18104153630",
    1212: "18104155200",
    1213: "18104153640",
    1400: "18104153670",
    1402: "18104155210",
    1403: "18104153690",
    1404: "18104153700",
    1405: "18104153710",
    1408: "18104153740",
    1411: "18104153770",
    1412: "18104153780",
    1500: "18104153810",
    1501: "18104153820",
    1502: "18104155230",
    1503: "18104153830",
    1504: "18104153840",
    1505: "18104153850",
    1506: "18104153860",
    1509: "18104153890",
    1512: "18104153920",
    1515: "18104153940",
    1600: "18104155250",
    1601: "18104155260",
    1603: "18104153950",
    1604: "18104153960",
    1605: "18104153970",
    1606: "18104153980",
    1608: "18104154000",
    1609: "18104154010",
    1612: "18104154020",
    1613: "18104155300",
    1615: "18104154040",
    1700: "18104154050",
    1704: "18104154080",
    1705: "18104154090",
    1707: "18104154110",
    1709: "18104154130",
    1710: "18104154140",
    1711: "18104155320",
    1713: "18104155340",
    1800: "18104155350",
    1802: "18104155370",
    1806: "18104154200",
    1809: "18104155390",
    1811: "18104154230",
    1812: "18104155400",
    1815: "18104154250",
    1900: "18104154260",
    1902: "18104155420",
    1903: "18104154280",
    1904: "18104155430",
    1905: "18104154290",
    1907: "18104154310",
    1908: "18104155440",
    1911: "18104154330",
    1912: "18104154340",
    1913: "18104154350",
    2006: "18104154410",
    2008: "18104154430",
    2009: "18104154440",
    2010: "18104154450",
    2011: "18104154460",
    2012: "18104154470",
    2103: "18104154480",
    2104: "18104154490",
    2105: "18104155500",
    2108: "18104154520",
    2111: "18104154550",
    2112: "18104154560",
    "PH05": "18104154580",
    "PH06": "18104154590",
    "PH10": "18104154630",
    "PH11": "18104154640"
}
```