# Simplifile Batch Upload Process Guide

## Excel Spreadsheet Schema Structure

The process relies on a spreadsheet with the following column structure:

| Column Name | Description | Required | Notes |
|-------------|-------------|----------|-------|
| KC File No. | King Cunningham file number | Yes | Format example: "93-24" |
| Account | Account identifier | Yes | Format example: "93-525153" |
| Last Name #1 | Primary owner's last name | Yes | ALL CAPS required |
| First Name #1 | Primary owner's first name | Yes | ALL CAPS required |
| & | Indicator for additional owner | No | Contains "&" if there's a second owner |
| Last Name #2 | Secondary owner's last name | No | Required only if second owner exists |
| First Name #2 | Secondary owner's first name | No | Required only if second owner exists |
| Deed Book | Reference book number for deed | Yes | Used for reference information |
| Deed Page | Reference page number for deed | Yes | Used for reference information |
| Recorded Date | Date the original deed was recorded | Yes | Format: MM/DD/YYYY |
| Mortgage Book | Reference book number for mortgage | Yes | Used for mortgage satisfaction reference |
| Mortgage Page | Reference page number for mortgage | Yes | Used for mortgage satisfaction reference |
| Suite | Property unit identifier | Yes | Format example: "U214-W10E" |
| Consideration | Monetary consideration amount | Yes | Typically "0.00" |
| Execution Date | Date document was executed | Yes | Format: MM/DD/YYYY |
| GRANTOR/GRANTEE | Entity name for grantor/grantee | Yes | Typically "OCEAN CLUB VACATIONS LLC" |
| LEGAL DESCRIPTION | Property legal description | Yes | Example: "ANDERSON OCEAN CLUB HPR" |

## Detailed Process Flow

### 1. Preparation Phase

1. Collect required files:
   - Excel spreadsheet with the schema detailed above
   - Deed PDF file (contains multiple 2-page deeds)
   - Affidavit PDF file (contains multile 2-page affidavits)
   - Mortgage Satisfaction PDF file (contains multiple 1-page documents)

2. Verify county for processing (default is Horry County)

### 2. Document Processing Phase

1. Split the Deed PDF and Affidavit PDF and merge:
   - Break the Deed and Affidavit PDFs into 2-page segments
   - combind the first two pages of deed and first two pages of Affidavit to get a new 1 page document that will be uploaded as the deed. repeat this for the number of deeds.
   - First deed = pages 1-4, second deed = pages 5-8, etc.
   - Name each file using data from Excel: "{Account} {Last Name #1} TD"

2. Split the Mortgage Satisfaction PDF:
   - Break the large PDF into 1-page segments
   - First satisfaction = page 1, second satisfaction = page 2, etc.
   - Name each file using data from Excel: "{Account} {Last Name #1} SAT"

3. Maintain sequential alignment:
   - First row in Excel corresponds to first deed and first mortgage satisfaction
   - Second row corresponds to second deed and second mortgage satisfaction, etc.

### 3. Simplifile Upload Process (Per Document Pair)

For each row in the spreadsheet:

1. Create a new package:
   - Package name: "{Account} {Last Name #1} TD {KC File No.}"
   - Example: "93-525153 MALLOTT TD 93-24"
   - ALL CAPS required

1.1 for the excel file if the last name contains "ORG:" then we should upload it as an organiztion and the value of first name should be an orginization.

2. Upload and configure Deed document:
   - Document type: 'Deed - Timeshare'
   - Document name: "{Account} {Last Name #1} TD"
   - Grantors (add all that apply):
     * Always add "KING CUNNINGHAM LLC TR" as an orginization.
     * Add value from GRANTOR/GRANTEE column
     * Add owners from spreadsheet:
       - First owner: {First Name #1} + {Last Name #1}
       - Second owner (if "&" is present): {First Name #2} + {Last Name #2}
         * if either owner name is org the upload value of just first name as an orginizaiton. 
   - Grantee: Value from GRANTOR/GRANTEE column
   - Execution date: Value from Execution Date column
   - Legal description: Value from LEGAL DESCRIPTION column append the parcelid to the end of it.
   - Consideration: Value from Consideration column (typically "0.00")
   - Reference information:
     * Type: "Deed - Timeshare"
     * Book: Value from Deed Book column
     * Page: Value from Deed Page column

3. Add Mortgage Satisfaction document:
   - Document type: 'Mortgage Satisfaction
   - Document name: "{Account} {Last Name #1} SAT"
   - Grantors (owners from spreadsheet):
     * First owner: {First Name #1} + {Last Name #1}
     * Second owner (if "&" is present): {First Name #2} + {Last Name #2}
   - Grantee: Value from GRANTOR/GRANTEE column
   - Execution date: Value from Execution Date column
   - Legal description: Same as used for deed document
   - Reference information:
     * Type: "Mortgage Satisfaction"
     * Book: Value from Mortgage Book column
     * Page: Value from Mortgage Page column

4. Save package as draft (do not submit)

### 4. Name Formatting Rules

1. All text must be uppercase in Simplifile
2. Special name handling:
   - For hyphenated names, remove hyphens (e.g., "SMITH-JOHNSON" becomes "SMITH JOHNSON")

### 5. API Implementation Considerations

1. Each document pair is processed as a single package
2. Documents are associated with spreadsheet rows by position/sequence
3. All packages should be created as drafts (not auto-submitted)
4. Name formatting rules must be applied programmatically
5. All text fields must be converted to uppercase before submission