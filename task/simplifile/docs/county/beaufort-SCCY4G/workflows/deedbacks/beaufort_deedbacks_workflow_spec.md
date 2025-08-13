Every week there is a batch of beaufort deedbacks that need to be uploaded to simplifile

there will be two inputs for this workflow a excel spreadsheet and a document stack of variable length deeds.

I have a couple questions for the client that are wrapped in ?? question ??

?? we need to pick an offical workflow name for this that i can put in the application ??

New things we are dealing with in this workflow:

# Multi-County Workflow

they are doing cross county upload (column project):
- 95 is beaufort county
- 93, 94, 95, 96 is horry county. horry county has sub requirements based on the project number.
- always ignore 98s simply skip these rows

## Beaufort County

doc type - 

grantors - as person "Lead 1 First"+"LEAD 1 LAST", "Lead 2 First"+"Lead 2 Last"
grantees - always "HII DEVELOPMENT LLC"

Consideration - from "Consideration" example "$5,484.76"

?? are we doing: book and page, execution date or any other feilds that need to be input ??

## Horry County

doc type - "Deed - Timeshare"

grantors - as person "Lead 1 First"+"LEAD 1 LAST", "Lead 2 First"+"Lead 2 Last"
grantees - as entity pull from hard coded "legal name" based on project number

execution date - pull form "DB Date" example "6/17/2025"

Consideration - from "Consideration" example "$5,484.76"

?? are we adding book and page number in simplifile as thats not shown in screenshot ??

### 93
County-HORRY COUNTY
Legal Name: OCEAN CLUB VACATIONS LLC
Contract Numbers start with 93
Legal/Property Description ({} - from excel): ANDERSON OCEAN CLUB HPR UNIT {Unit Code} WK {Week}{OEB Code}
TMS # 1810415_ _ _ (Use AOC Unit to TMS # Conversion)
Example of a double unit or multiples…..
Legal/Property Description: ANDERSON OCEAN CLUB HPR UNIT 1512 WK 12B; UNIT 1512 WK 13B
TMS # 1810415_ _ _  ; 1810415_ _ _ (Use AOC Unit to TMS # Conversion)

### 94
County-HORRY COUNTY
Legal Name: OCEAN 22 DEVELOPMENT LLC
Contract Numbers start with 94
TMS # 1810418003 Always the same for all!
Legal/Property Description: OCEAN 22 VACATION SUITES U {Unit Code} W {Week}
Example of a double unit or multiples…..
OCEAN 22 VACATION SUITES U 905 W 12; U 905 W 13

### 95
HHI (File Named MBV)
County- BEAUFORT COUNTY
Legal Name: HHI DEVELOPMENT LLC
Contract Numbers start with 95
TMS # ON AFFIDAVIT…. NEVER HAVE TO TYPE IT IN
Legal/Property Description: …. NEVER HAVE TO TYPE IT IN

### 96
County-HORRY COUNTY
Legal Name: 1600 DEVELOPMENT LLC **(you have to add NUM to the legal name, so it gets indexed like this…. NUM 1600 DEVELOPMENT LLC)
?? not sure i understand am i pulling num from somewhere or is it going to be "NUM 1600 DEVELOPMENT LLC" in as grantor entity ??
Contract Numbers start with 96
TMS # 1810732008 Always the same for all!
Legal/Property Description: OE VACATION SUITES U {Unit Code} W {Week}
Example of a double unit or multiples…..
OE VACATION SUITES U 905 W 12; U 905 W 13
TMS NUMBER THE SAME FOR ALL

##
they will scan in a document stack of deedbacks only. this will be first instance of vairable page uploads. we are going to add a new column with the length of each document(column "DB Pages"). so we will search variable pages in document stack. and index by just saving where we left of in stack to grab the subdocuments.

## Reference

### Excel Headers
["A", "BATCH"],
["B", "Project"],
["C", "Number"],
["D", "Upgrade Project"],
["E", "New"],
["F", "Upgrade / Reload"],
["G", "Split"],
["H", "Resales"],
["I", "Lead 1 First"],
["J", "LEAD 1 LAST"],
["K", "Lead 2 First"],
["L", "Lead 2 Last"],
["M", "Points"],
["N", "Element"],
["O", "Unit Code"],
["P", "Week"],
["Q", "Unit Type"],
["R", "OEB Code"],
["S", "Season"],
["T", "Phase"],
["U", "Lockoff Unit 1"],
["V", "Purchase Price"],
["W", "Loan Payoff"],
["X", "MTG BOOK"],
["Y", "MTG PAGE"],
["Z", "Mortgage Book And Page"],
["AA", " Ref DEED BOOK"],
["AB", "Ref DEED PAGE"],
["AC", "DB Date"],
["AD", "DB Pages"],
["AE", "Deed Back Record Date"],
["AF", "DEED B/P"],
["AG", "Upgrade Batch #"],
["AH", " Recordeing Fees"],
["AI", "Notes:"],
["AJ", "Execution  Date"],
["AK", "Package Name"],
["AL", ""],
["AM", "Consideration"],
["AN", ""],
["AO", "Tax Stamps"]

### unit to tms dict
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


## Deed timeshare options
```
{
    "recipientRequirements": {
        "apiRequirementsNotes": [],
        "enumerations": [
            {
                "options": [
                    "Individual",
                    "Organization"
                ],
                "path": "grantors[].type"
            },
            {
                "options": [
                    "Individual",
                    "Organization"
                ],
                "path": "grantees[].type"
            },
            {
                "options": [
                    "Deed - Timeshare",
                ],
                "path": "referenceInformation[].documentType"
            }
        ],
        "instruments": [
            {
                "instrument": "Deed - Timeshare",
                "requirements": [
                    {
                        "label": "Grantor Type",
                        "path": "grantors[].type",
                        "required": "ALWAYS",
                        "type": "ENUMERATED"
                    },
                    {
                        "label": "Grantor Name",
                        "path": "grantors[].nameUnparsed",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantor First",
                        "path": "grantors[].firstName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantor Middle",
                        "path": "grantors[].middleName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantor Last",
                        "path": "grantors[].lastName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantor Suffix",
                        "path": "grantors[].nameSuffix",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantee Type",
                        "path": "grantees[].type",
                        "required": "ALWAYS",
                        "type": "ENUMERATED"
                    },
                    {
                        "label": "Grantee Name",
                        "path": "grantees[].nameUnparsed",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantee First",
                        "path": "grantees[].firstName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantee Middle",
                        "path": "grantees[].middleName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantee Last",
                        "path": "grantees[].lastName",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Grantee Suffix",
                        "path": "grantees[].nameSuffix",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Execution Date",
                        "path": "executionDate",
                        "required": "ALWAYS",
                        "type": "DATE"
                    },
                    {
                        "label": "Legal Description",
                        "path": "legalDescriptions[].description",
                        "required": "ALWAYS",
                        "type": "STRING"
                    },
                    {
                        "label": "Tax Map Number",
                        "path": "legalDescriptions[].parcelId",
                        "required": "IF_AVAILABLE",
                        "type": "STRING"
                    },
                    {
                        "label": "Unit",
                        "path": "legalDescriptions[].unitNumber",
                        "required": "IF_AVAILABLE",
                        "type": "INTEGER"
                    },
                    {
                        "label": "Consideration",
                        "path": "consideration",
                        "required": "ALWAYS",
                        "type": "DECIMAL"
                    },
                    {
                        "label": "Document Type",
                        "path": "referenceInformation[].documentType",
                        "required": "IF_AVAILABLE",
                        "type": "ENUMERATED"
                    },
                    {
                        "label": "Book",
                        "path": "referenceInformation[].book",
                        "required": "CONDITIONAL",
                        "type": "STRING"
                    },
                    {
                        "label": "Page",
                        "path": "referenceInformation[].page",
                        "required": "CONDITIONAL",
                        "type": "INTEGER"
                    }
                ]
            }
        ]
    },
    "responseMillis": 350,
    "resultCode": "SUCCESS",
    "resultType": "RECIPIENT_REQUIREMENTS",
    "timestamp": "2025-03-19T23:56:14.184Z"
}
```