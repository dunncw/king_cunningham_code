# Beaufort/Horry Multi-County Deedback Workflow Specification

## Overview
The Multi-County Deedback Workflow processes Excel data and a single PDF document stack containing variable-length deed documents to create Simplifile packages for both Beaufort County and Horry County, SC. This workflow handles cross-county uploads based on project numbers.

**Workflow Name**: `BEA-HOR-COUNTYS-DEEDBACK`

## Input Files (2 total)
1. **Excel File**: Row data for each package with document page counts
2. **Deed Stack PDF**: All deed documents concatenated (variable page lengths per document)

## County Routing Logic
Based on the `Project` column value:
- **93, 94, 96**: Route to Horry County
- **95**: Route to Beaufort County  
- **98**: Skip these rows entirely (do not process)

## PDF Processing Strategy

### Variable Page Document Extraction
Unlike previous workflows with fixed page counts, this workflow uses the `DB Pages` column to determine document length:
- Track current position in PDF stack (starting at page 1)
- For each row N in Excel:
  - Extract pages from `current_position` to `current_position + DB_Pages - 1`
  - Update `current_position += DB_Pages`
  - Continue to next row

### Multi-Unit/Week Handling (Same Contract Number)
When multiple rows share the same `Project` and `Number` (contract number):
1. **Group Detection**: Scan Excel to identify all rows with matching Project + Number combinations
2. **Single Package Creation**: Create ONE package using the first row's data
3. **PDF Selection**: Use ONLY the first row's PDF document (subsequent PDFs for same contract are duplicates)
4. **Legal Description Combination**: Combine all units/weeks into a single legal description with semicolon separators
5. **Package Naming**: Use the first row's unit/week for the package name

## Package Naming Convention
**Two Options Available:**
1. **Auto-Generated Format**: `{LEAD 1 LAST} {Unit Code}-{Week}{OEB Code} {Project}-{Number}`
2. **From Excel**: Use value from `Package Name` column (AK) if provided

**Note**: For multi-unit contracts, the package name uses the first row's data.

## County-Specific Requirements

### Beaufort County (Project 95)

#### Document Configuration
- **County ID**: `SCCY4G`
- **Document Type**: `DEED - HILTON HEAD TIMESHARE`
- **Package Naming**: Auto-generated or from Excel column AK

#### Indexing Data
- **Grantors** (Individual type):
  - `{Lead 1 First} {LEAD 1 LAST}`
  - `{Lead 2 First} {Lead 2 Last}` (if present)
- **Grantees** (Organization type):
  - Always `HII DEVELOPMENT LLC`
- **Consideration**: Value from `Consideration` column (e.g., "$5,484.76")
- **No Additional Fields Required**: Beaufort only needs Grantor(s), Grantee, and Consideration

### Horry County (Projects 93, 94, 96)

#### Document Configuration
- **County ID**: `SCCP49`
- **Document Type**: `Deed - Timeshare`
- **Package Naming**: Auto-generated or from Excel column AK

#### Indexing Data
- **Grantors** (Individual type):
  - `{Lead 1 First} {LEAD 1 LAST}`
  - `{Lead 2 First} {Lead 2 Last}` (if present)
- **Grantees** (Organization type):
  - Based on project number (see below)
- **Execution Date**: From `DB Date` column (format: "6/17/2025")
- **Consideration**: Value from `Consideration` column
- **Legal Description**: Project-specific, combined for multi-unit contracts
- **TMS/Parcel ID**: Project-specific, combined for multi-unit contracts
- **Reference Information**: Book/page from Excel columns

## Horry County Project-Specific Rules

### Project 93 - Anderson Ocean Club
- **Grantee**: `OCEAN CLUB VACATIONS LLC`
- **Legal Description**: `ANDERSON OCEAN CLUB HPR UNIT {Unit Code} WK {Week}{OEB Code}` for additional units append `;UNIT {Unit Code} WK {Week}{OEB Code}`
- **TMS #**: Use unit-to-TMS conversion table (see reference section)

### Project 94 - Ocean 22
- **Grantee**: `OCEAN 22 DEVELOPMENT LLC`
- **Legal Description**: `OCEAN 22 VACATION SUITES U {Unit Code} W {Week}` for additional units append `;U {Unit Code} W {Week}`
- **TMS #**: Always `1810418003`

### Project 96 - OE Vacation Suites
- **Grantee**: `NUM 1600 DEVELOPMENT LLC`
- **Legal Description**: `OE VACATION SUITES U {Unit Code} W {Week}` for additional units append `;U {Unit Code} W {Week}`
- **TMS #**: Always `1810732008`

## Multi-Unit Contract Example

For contracts with multiple units/weeks (same Project + Number):

### Input Rows:
```
Row 1: Project 93, Number 512565, Unit 210, Week 13, OEB Code B
Row 2: Project 93, Number 512565, Unit 300, Week 19, OEB Code B
```

### Processing Result:
- **Single Package Created**: Using first row's data for package name
- **Package Name**: `CROXALL 210-13B 93-512565`
- **PDF Used**: Only the 6-page document from Row 1 (Row 2's PDF is skipped)
- **Legal Description**: `ANDERSON OCEAN CLUB HPR UNIT 210 WK 13B; UNIT 300 WK 19B`
- **TMS Numbers**: `18104152410; 18104154830`

## Excel Column Mapping

### Required Columns
| Column | Internal Field | Usage |
|--------|---------------|--------|
| `Project` | `project_number` | County routing (93,94,95,96,98) |
| `Number` | `contract_number` | Package identifier |
| `Lead 1 First` | `lead_1_first` | Primary grantor first name |
| `LEAD 1 LAST` | `lead_1_last` | Primary grantor last name |
| `Lead 2 First` | `lead_2_first` | Secondary grantor first name (if present) |
| `Lead 2 Last` | `lead_2_last` | Secondary grantor last name (if present) |
| `Unit Code` | `unit_code` | Property unit identifier |
| `Week` | `week` | Timeshare week |
| `OEB Code` | `oeb_code` | Additional identifier (Project 93 only) |
| `DB Date` | `execution_date` | Document execution date (Horry only) |
| `DB Pages` | `document_pages` | Number of pages for this document |
| `Consideration` | `consideration` | Monetary consideration |

## API Payload Structure

### Beaufort County (Project 95)
```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{contract_number}",
      "name": "{package_name}",
      "kindOfInstrument": ["DEED - HILTON HEAD TIMESHARE"],
      "indexingData": {
        "grantors": [
          {
            "firstName": "{lead_1_first}",
            "lastName": "{lead_1_last}",
            "type": "Individual"
          },
          {
            "firstName": "{lead_2_first}",
            "lastName": "{lead_2_last}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "HII DEVELOPMENT LLC",
            "type": "Organization"
          }
        ],
        "consideration": "{consideration}"
      },
      "fileBytes": ["{extracted_pdf}"]
    }
  ],
  "recipient": "SCCY4G",
  "submitterPackageID": "P-{contract_number}",
  "name": "{package_name}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

### Horry County (Projects 93, 94, 96)
```json
{
  "documents": [
    {
      "submitterDocumentID": "D-{contract_number}",
      "name": "{package_name}",
      "kindOfInstrument": ["Deed - Timeshare"],
      "indexingData": {
        "executionDate": "{execution_date}",
        "consideration": "{consideration}",
        "grantors": [
          {
            "firstName": "{lead_1_first}",
            "lastName": "{lead_1_last}",
            "type": "Individual"
          },
          {
            "firstName": "{lead_2_first}",
            "lastName": "{lead_2_last}",
            "type": "Individual"
          }
        ],
        "grantees": [
          {
            "nameUnparsed": "{project_specific_grantee}",
            "type": "Organization"
          }
        ],
        "legalDescriptions": [
          {
            "description": "{combined_legal_description}",
            "parcelId": "{combined_tms_numbers}"
          }
        ],
        "referenceInformation": [
          {
            "documentType": "Deed - Timeshare",
            "book": "{deed_book}",
            "page": "{deed_page}"
          }
        ]
      },
      "fileBytes": ["{extracted_pdf_from_first_row_only}"]
    }
  ],
  "recipient": "SCCP49",
  "submitterPackageID": "P-{contract_number}",
  "name": "{package_name}",
  "operations": {
    "draftOnErrors": true,
    "submitImmediately": false,
    "verifyPageMargins": true
  }
}
```

## Validation Rules

### Fail Fast Scenarios
1. Missing required Excel columns
2. Invalid project number (not 93, 94, 95, 96, or 98)
3. Missing `DB Pages` value or non-numeric value
4. PDF page count mismatch (total pages < sum of all `DB Pages`)
5. Missing lead 1 name information
6. Invalid date format in `DB Date` (Horry County)
7. Invalid unit code for TMS lookup (Project 93)

### Skip Row/PDF Scenarios
1. Project number = 98 (skip entire row)
2. Empty required fields for the specific county
3. Invalid or missing page count
4. Duplicate contract (same Project + Number) - skip PDF extraction for 2nd+ occurrences

## Special Handling

### Name Processing
- All names should be converted to UPPERCASE
- Handle missing Lead 2 gracefully (not all records have second grantor)

### Consideration Formatting
- Remove currency symbols and commas
- Convert to decimal format for API

### Date Formatting
- Convert `DB Date` from "M/D/YYYY" to "MM/DD/YYYY" format

### Package Name Generation
- Check Excel column AK (`Package Name`) first
- If empty, auto-generate using format specified
- For multi-unit contracts, always use first row's package name

### Multi-Unit Contract Processing
1. **Pre-scan Excel**: Identify all rows with duplicate Project + Number combinations
2. **Group Processing**: Process each unique Project + Number once
3. **PDF Extraction**: Only extract PDF for the first occurrence
4. **Legal Description Building**: Concatenate all units/weeks with semicolons
5. **TMS Handling**: Concatenate all TMS numbers with semicolons (Project 93 only)
6. **Skip Duplicate PDFs**: Advance the PDF position counter for duplicate rows but don't extract

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


## Implementation Notes

- First workflow with variable-length documents requiring dynamic page extraction
- Cross-county routing based on project numbers
- Unit-to-TMS conversion table must be used for Project 93 (Anderson Ocean Club)
- Multi-unit contract detection and combination is critical for proper processing
- Only first PDF used for duplicate contracts (all deedbacks are identical)
- Package names can come from Excel or be auto-generated
- All validation and error handling follows established patterns from previous workflows