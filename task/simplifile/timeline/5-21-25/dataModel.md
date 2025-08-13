# Simplifile Data Models

## 1. Unified Input Data Model

This represents all data collected from input sources that might be used in any county's upload process.

```json
{
  "package": {
    "package_id": "String - Unique identifier for the package",
    "package_name": "String - Display name for the package",
    "account_number": "String - Account identifier (e.g., 93-525153)",
    "kc_file_no": "String - King Cunningham file number (e.g., 93-24)",
    "draft_on_errors": "Boolean - Whether to create drafts when errors occur",
    "submit_immediately": "Boolean - Whether to submit package immediately",
    "verify_page_margins": "Boolean - Whether to verify page margins"
  },
  "parties": {
    "primary_owner": {
      "first_name": "String - First name of primary owner (ALL CAPS)",
      "last_name": "String - Last name of primary owner (ALL CAPS)",
      "is_organization": "Boolean - Whether this is an organization"
    },
    "secondary_owner": {
      "exists": "Boolean - Whether there is a secondary owner (& column)",
      "first_name": "String - First name of secondary owner (ALL CAPS)",
      "last_name": "String - Last name of secondary owner (ALL CAPS)",
      "is_organization": "Boolean - Whether this is an organization"
    },
    "grantor_grantee_entity": "String - Entity name for grantor/grantee (e.g., OCEAN CLUB VACATIONS LLC)"
  },
  "property": {
    "legal_description": "String - Property legal description",
    "suite": "String - Property unit identifier (e.g., U214-W10E)",
    "parcel_id": "String - Parcel identification (if separate from legal description)"
  },
  "deed": {
    "document_id": "String - Unique identifier for the deed document",
    "document_name": "String - Display name for the deed document",
    "document_type": "String - Type of deed document",
    "execution_date": "String - Date the deed was executed (MM/DD/YYYY)",
    "consideration": "String - Monetary consideration amount (typically 0.00)",
    "reference_book": "String - Book number for deed reference",
    "reference_page": "String - Page number for deed reference",
    "recorded_date": "String - Date the original deed was recorded (MM/DD/YYYY)",
    "file_path": "String - Path to the document file",
    "page_range": "String - Range of pages in the PDF (e.g., 1-2)",
    "page_count": "Number - Count of pages in the document"
  },
  "mortgage_satisfaction": {
    "document_id": "String - Unique identifier for the mortgage document",
    "document_name": "String - Display name for the mortgage document",
    "document_type": "String - Type of mortgage document",
    "execution_date": "String - Date the mortgage satisfaction was executed (MM/DD/YYYY)",
    "reference_book": "String - Book number for mortgage reference",
    "reference_page": "String - Page number for mortgage reference",
    "file_path": "String - Path to the document file",
    "page_range": "String - Range of pages in the PDF (e.g., 1)",
    "page_count": "Number - Count of pages in the document"
  }
}
```

## 2. County-Specific Upload Models

### Horry County, SC Upload Model

```json
{
  "package": {
    "package_id": "String - Typically {KC File No.}-{Account}",
    "package_name": "String - {Account} {Last Name #1} TD {KC File No.}",
    "draft_on_errors": true,
    "submit_immediately": false,
    "verify_page_margins": true,
    "recipient": "SCCP49"
  },
  "documents": [
    {
      "document_id": "String - {D-{Account}-TD}",
      "name": "String - {Account} {Last Name #1} TD",
      "type": "Deed - Timeshare",
      "file_bytes": "Base64 encoded PDF content",
      "indexing_data": {
        "execution_date": "String - From Execution Date column (YYYY-MM-DD)",
        "consideration": "Number - From Consideration column",
        "grantors": [
          {
            "type": "Organization",
            "nameUnparsed": "KING CUNNINGHAM LLC TR"
          },
          {
            "type": "Organization",
            "nameUnparsed": "String - From GRANTOR/GRANTEE column"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #1",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #1",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #1"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #2 (if exists)",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #2 (if exists)",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #2 (if exists)"
          }
        ],
        "grantees": [
          {
            "type": "Organization",
            "nameUnparsed": "String - From GRANTOR/GRANTEE column"
          }
        ],
        "legalDescriptions": [
          {
            "description": "String - From LEGAL DESCRIPTION + Suite columns",
            "parcelId": ""
          }
        ],
        "referenceInformation": [
          {
            "documentType": "Deed - Timeshare",
            "book": "String - From Deed Book column",
            "page": "Number - From Deed Page column"
          }
        ]
      }
    },
    {
      "document_id": "String - {D-{Account}-SAT}",
      "name": "String - {Account} {Last Name #1} SAT",
      "type": "Mortgage Satisfaction",
      "file_bytes": "Base64 encoded PDF content",
      "indexing_data": {
        "execution_date": "String - From Execution Date column (YYYY-MM-DD)",
        "grantors": [
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #1",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #1",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #1"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #2 (if exists)",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #2 (if exists)",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #2 (if exists)"
          }
        ],
        "grantees": [
          {
            "type": "Organization",
            "nameUnparsed": "String - From GRANTOR/GRANTEE column"
          }
        ],
        "legalDescriptions": [
          {
            "description": "String - From LEGAL DESCRIPTION + Suite columns",
            "parcelId": ""
          }
        ],
        "referenceInformation": [
          {
            "documentType": "Mortgage Satisfaction",
            "book": "String - From Mortgage Book column",
            "page": "Number - From Mortgage Page column"
          }
        ]
      }
    }
  ]
}
```

### Beaufort County, GA Upload Model

```json
{
  "package": {
    "package_id": "String - Typically {KC File No.}-{Account}",
    "package_name": "String - {Account} {Last Name #1} TD {KC File No.}",
    "draft_on_errors": true,
    "submit_immediately": false,
    "verify_page_margins": true,
    "recipient": "SCCY4G"
  },
  "documents": [
    {
      "document_id": "String - {D-{Account}-TD}",
      "name": "String - {Account} {Last Name #1} TD",
      "type": "DEED - HILTON HEAD TIMESHARE",
      "file_bytes": "Base64 encoded PDF content",
      "indexing_data": {
        "consideration": "Number - From Consideration column",
        "grantors": [
          {
            "type": "Organization",
            "nameUnparsed": "KING CUNNINGHAM LLC TR"
          },
          {
            "type": "Organization",
            "nameUnparsed": "String - From GRANTOR/GRANTEE column"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #1",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #1",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #1"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #2 (if exists)",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #2 (if exists)",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #2 (if exists)"
          }
        ],
        "grantees": [
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #1",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #1",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #1"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #2 (if exists)",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #2 (if exists)",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #2 (if exists)"
          }
        ]
      }
    },
    {
      "document_id": "String - {D-{Account}-SAT}",
      "name": "String - {Account} {Last Name #1} SAT",
      "type": "MORT - SATISFACTION",
      "file_bytes": "Base64 encoded PDF content",
      "indexing_data": {
        "grantors": [
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #1",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #1",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #1"
          },
          {
            "type": "Individual/Organization",
            "firstName": "String - If individual: From First Name #2 (if exists)",
            "middleName": "",
            "lastName": "String - If individual: From Last Name #2 (if exists)",
            "nameSuffix": "",
            "nameUnparsed": "String - If organization: From First Name #2 (if exists)"
          }
        ],
        "grantees": [
          {
            "type": "Organization",
            "nameUnparsed": "String - From GRANTOR/GRANTEE column"
          }
        ]
      }
    }
  ]
}
```

## 3. Key Differences Between Counties

| Feature | Horry County, SC | Beaufort County, GA |
|---------|------------------|---------------------|
| **Deed Document Type** | "Deed - Timeshare" | "DEED - HILTON HEAD TIMESHARE" |
| **Mortgage Document Type** | "Mortgage Satisfaction" | "MORT - SATISFACTION" |
| **Recipient ID** | "SCCP49" | "SCCY4G" |
| **Deed Execution Date** | Required | Not required |
| **Deed Legal Description** | Required | Not required |
| **Deed Reference Information** | Required | Not required |
| **Deed Grantees** | GRANTOR/GRANTEE entity | Individual owners (same as grantors) |
| **Mortgage Execution Date** | Required | Not required |
| **Mortgage Legal Description** | Required | Not required |
| **Mortgage Reference Information** | Required | Not required |

## 4. Implementation Strategy

1. Create a base `SimplifilePackage` class that contains all possible fields from the unified data model
2. Create county-specific formatter classes that transform the base package into the correct format:
   - `HorryCountyFormatter`
   - `BeaufortCountyFormatter`
3. Use a factory pattern to select the appropriate formatter based on the county:
   ```python
   def get_county_formatter(county_id):
       formatters = {
           "SCCP49": HorryCountyFormatter,
           "SCCY4G": BeaufortCountyFormatter
       }
       return formatters.get(county_id, HorryCountyFormatter)
   ```
4. Apply the formatter before API submission:
   ```python
   formatter = get_county_formatter(recipient_id)
   api_payload = formatter.format_package(package)
   ```

This approach maintains a single source of truth for the data model while allowing for county-specific variations in the API payload.