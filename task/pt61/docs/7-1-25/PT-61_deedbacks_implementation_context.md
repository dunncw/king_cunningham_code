# PT61 Deedbacks Requirements Summary

## Overview
- **Target URL**: https://apps.gsccca.org/pt61efiling/
- **Purpose**: PT61 form automation for deedback processing
- **User**: Office workers for speeding up repetitive form entry

## Excel File Structure
- **Format**: Variable structure, but must contain required headers
- **Processing**: Each row = one form submission
- **Required Columns** (from config):
  - Contract Num
  - Last 1, First 1, Middle 1
  - Sales Price
  - Date on Deed
  - DB To

## Form Flow & Data Mapping

### Section A: Seller Information (Individual)
- **Primary Name**: Pulled from Excel columns (Last 1, First 1, Middle 1)
- **Note**: Only first person's information used (no additional sellers)
- **Primary Mailing Address**: Always the same constant address

### Section B: Buyer Information (Business)
- **Business Type**: Always Business entity
- **Primary Name**: Dynamic based on "DB To" column (AX):
  - CENTENNIAL → CENTENNIAL PARK DEVELOPMENT LLC
  - WYNDHAM → WYNDHAM VACATION RESORTS, INC.
- **Primary Mailing Address**: Always the same constant address

### Section C: Property Information
- **Date of Sale**: Column AV (Date on Deed)
- **Street Number**: Always 155
- **Street Name**: Always Centennial Olympic Park
- **Street Type**: Always Drive
- **Post Direction**: Always NW
- **County**: Always Fulton
- **Map & Parcel Number**: Always 14-0078-0007-096-9

### Section D: Financial Information
- **Exempt Code**: Always None
- **Field 1**: Column P (Sales Price)
- **Field 2**: Always 0
- **Field 3**: Always 0

### Final Steps
- Check all required boxes
- Submit form
- Save PDF as: `{last_name}_{contract_number}_PT61.pdf`
- Example: `DEMAYO_0392400442_PT61.pdf`

## Key Differences from New Batch
1. **Seller**: Individual person (vs Business)
2. **Buyer**: Dynamic business selection (vs fixed)
3. **No Additional Sellers**: Single person only
4. **Date Column**: "Date on Deed" (vs "date on deed")
5. **File Naming**: Same pattern as new batch

## Implementation Notes
- Use config-driven approach from `pt61_config.py`
- Shared functionality in `base_automation.py`
- Deedbacks-specific logic in `deedbacks_automation.py`
- Excel validation via `version_validator.py`