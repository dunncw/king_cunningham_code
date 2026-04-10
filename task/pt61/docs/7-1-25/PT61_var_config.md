# PT61 Version Configuration Specifications

## Version 1: PT-61 New Batch (Current - No Changes)

### Required Excel Columns
```
'Contract Num'      // File naming
'Last 1'            // Seller last name
'First 1'           // Seller first name
'Middle 1'          // Seller middle name
'Last 2'            // Additional seller last name (if exists)
'First 2'           // Additional seller first name (if exists)
'Middle 2'          // Additional seller middle name (if exists)
'Sales Price'       // Section D financial
'date on Deed'      // Section C date of sale
```

### Constants
```json
{
  "seller_address": {
    "line1": "CENTENNIAL PARK DEVELOPMENT LLC",
    "line2": "c/o 155 CENTENNIAL OLYMPIC PARK DR. NW",
    "city": "ATLANTA",
    "state": "GA",
    "zip": "30313"
  },
  "buyer": {
    "name": "CENTENNIAL PARK DEVELOPMENT LLC",
    "type": "Business"
  },
  "buyer_address": "same_as_seller",
  "property": {
    "street_number": "155",
    "street_name": "Centennial Olympic Park",
    "street_type": "Drive",
    "post_direction": "NW", 
    "county": "Fulton",
    "map_parcel": "14-0078-0007-096-9"
  },
  "financial": {
    "exempt_code": "None",
    "field_2": "0",
    "field_3": "0"
  },
  "file_naming": "{last_name} {contract_num} PT61"
}
```

---

## Version 2: PT-61 Deedbacks

### Required Excel Columns
```
'Contract Num'      // File naming
'Last 1'            // Seller last name
'First 1'           // Seller first name  
'Middle 1'          // Seller middle name
'Sales Price'       // Section D financial
'Date on Deed'      // Section C date of sale
'DB To'             // Section B buyer determination
```

### Constants
```json
{
  "seller_address": {
    "line1": "c/o 155 CENTENNIAL OLYMPIC PARK DR. NW",
    "city": "ATLANTA",
    "state": "GA", 
    "zip": "30313"
  },
  "buyer_options": {
    "centennial": "CENTENNIAL PARK DEVELOPMENT LLC",
    "wyndham": "WYNDHAM VACATION RESORTS, INC."
  },
  "buyer_address": "same_as_seller",
  "property": {
    "street_number": "155",
    "street_name": "Centennial Olympic Park",
    "street_type": "Drive", 
    "post_direction": "NW",
    "county": "Fulton",
    "map_parcel": "14-0078-0007-096-9"
  },
  "financial": {
    "exempt_code": "None",
    "field_4": "0",
    "field_5": "0"
  },
  "file_naming": "{last_name} {contract_num} PT61"
}
```

---

## Version 3: PT61 Foreclosures

### Required Excel Columns
```
'Contract Num'      // File naming
'First 1'           // Seller first name
'Middle 1'          // Seller middle name
'Last 1'            // Seller last name
'date on deed'      // Section C date of sale
'Sales Price'       // Section D financial
```

### Constants
```json
{
  "seller_address": {
    "line1": "c/o 155 CENTENNIAL OLYMPIC PARK DR. NW",
    "city": "ATLANTA", 
    "state": "GA",
    "zip": "30313"
  },
  "buyer": {
    "name": "CENTENNIAL PARK DEVELOPMENT LLC",
    "type": "Business"
  },
  "buyer_address": "same_as_seller",
  "additional_buyers": "clear_auto_fill",
  "property": {
    "county": "Fulton",
    "map_parcel": "14-0078-0007-096-9"
  },
  "financial": {
    "exempt_code": "First Transferee Foreclosure",
    "auto_fill_fields": ["4", "5"]
  },
  "file_naming": "{contract_num} {last_name} PT61"
}
```

---

## Backend Configuration Structure

### Suggested JSON Schema
```json
{
  "pt61_versions": {
    "new_batch": {
      "display_name": "PT-61 New Batch",
      "required_columns": [...],
      "constants": {...}
    },
    "deedbacks": {
      "display_name": "PT-61 Deedbacks", 
      "required_columns": [...],
      "constants": {...}
    },
    "foreclosures": {
      "display_name": "PT61 Foreclosures",
      "required_columns": [...], 
      "constants": {...}
    }
  }
}
```

### Benefits of This Structure
- Easy to add new versions without code changes
- Clear separation of variable vs constant data
- Version validation against required columns
- Consistent file naming patterns
- Scalable for future requirements

---

## Notes
- **PT-61 New Batch** constants need to be extracted from current implementation
- All versions use same login credentials
- File naming patterns differ between versions
- Column validation should check for required headers before processing
- Constants can be updated via config without code deployment