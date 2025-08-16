# simplifile3/workflows/bea_hor_countys_deedback/workflow.py - Multi-county deedback workflow
import re
from typing import Dict, List, Any, Tuple
import pandas as pd
from datetime import datetime

from ...workflows.base import BaseWorkflow


class BeaHorCountysDeedbackWorkflow(BaseWorkflow):
    """Beaufort/Horry Multi-County Deedback workflow"""

    def __init__(self, logger=None):
        super().__init__(logger)

        # Unit to TMS conversion table for Project 93 (Anderson Ocean Club)
        # NOTE: This is where the full conversion table should be added
        self.unit_to_tms_93 = {
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

    def get_workflow_id(self) -> str:
        return "bea_hor_countys_deedback"


    def get_supported_counties(self) -> List[str]:
        return ["SCCP49", "SCCY4G"]  # Horry and Beaufort


    def get_required_excel_columns(self) -> List[str]:
        """Required columns for BEA-HOR-COUNTYS-DEEDBACK workflow"""
        return [
            "Project",
            "Number",
            "Lead 1 First",
            "LEAD 1 LAST",
            "Unit Code",
            "Week",
            "DB Date",
            "DB Pages",
            "Consideration"
        ]


    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel columns to internal field names"""
        return {
            "Project": "project_number",
            "Number": "contract_number",
            "Lead 1 First": "lead_1_first",
            "LEAD 1 LAST": "lead_1_last",
            "Lead 2 First": "lead_2_first",
            "Lead 2 Last": "lead_2_last",
            "Unit Code": "unit_code",
            "Week": "week",
            "OEB Code": "oeb_code",
            "DB Date": "execution_date",
            "DB Pages": "document_pages",
            "Consideration": "consideration",
            "Package Name": "package_name_excel"  # Column AK - optional
        }


    def route_to_county(self, excel_row: Dict[str, Any]) -> str:
        """Route based on Project number per spec"""
        try:
            project = int(excel_row.get("Project", 0))

            if project in [93, 94, 96]:
                return "SCCP49"  # Horry County
            elif project == 95:
                return "SCCY4G"  # Beaufort County
            elif project == 98:
                return "SKIP"  # Skip processing
            else:
                raise ValueError(f"Invalid project number: {project}")

        except (ValueError, TypeError):
            raise ValueError(f"Invalid or missing project number: {excel_row.get('Project')}")


    def _combine_legal_descriptions(self, grouped_rows: List[Dict]) -> str:
        """Combine legal descriptions for multi-unit contracts"""
        if len(grouped_rows) == 1:
            # Single unit - use full description
            return self._build_single_legal_description(grouped_rows[0])

        # Multi-unit - first gets full description, rest get abbreviated
        descriptions = []
        first_row = grouped_rows[0]

        # First unit gets full description
        descriptions.append(self._build_single_legal_description(first_row))

        # Additional units get abbreviated format
        for row in grouped_rows[1:]:
            unit_code = row["unit_code"]
            week = row["week"]
            oeb_code = row.get("oeb_code", "")
            descriptions.append(f"UNIT {unit_code} WK {week}{oeb_code}")

        return "; ".join(descriptions)


    def _build_single_legal_description(self, row_data: Dict) -> str:
        """Build legal description for a single unit"""
        project = row_data["project_number"]
        unit_code = row_data["unit_code"]
        week = row_data["week"]
        oeb_code = row_data.get("oeb_code", "")

        if project == "93":
            return f"ANDERSON OCEAN CLUB HPR UNIT {unit_code} WK {week}{oeb_code}"
        elif project == "94":
            return f"OCEAN 22 VACATION SUITES U {unit_code} W {week}"
        elif project == "96":
            return f"OE VACATION SUITES U {unit_code} W {week}"
        else:
            return f"UNIT {unit_code} WK {week}{oeb_code}"


    def transform_row_data(self, excel_row: Dict[str, Any], target_county: str) -> Dict[str, Any]:
        """Transform Excel row data for target county"""
        # Map Excel columns to internal fields
        mapping = self.get_excel_mapping()
        transformed = {}

        for excel_col, internal_field in mapping.items():
            value = excel_row.get(excel_col, "")
            if pd.isna(value):
                value = ""
            transformed[internal_field] = str(value).strip()

        # Convert and validate key fields
        try:
            transformed["project_number"] = int(transformed["project_number"])
            transformed["document_pages"] = int(transformed["document_pages"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric field in Excel row: {str(e)}")

        # Uppercase names
        transformed["lead_1_first"] = transformed["lead_1_first"].upper()
        transformed["lead_1_last"] = transformed["lead_1_last"].upper()
        transformed["lead_2_first"] = transformed["lead_2_first"].upper()
        transformed["lead_2_last"] = transformed["lead_2_last"].upper()

        # Determine if second lead exists
        transformed["has_second_lead"] = bool(
            transformed["lead_2_first"] and transformed["lead_2_last"]
        )

        # Generate package name
        transformed["package_name"] = self._generate_package_name(transformed)

        # Package and document IDs
        transformed["package_id"] = f"P-{transformed['contract_number']}"
        transformed["document_id"] = f"D-{transformed['contract_number']}"

        # Clean consideration amount
        transformed["consideration_amount"] = self._clean_consideration(transformed["consideration"])

        # County-specific processing
        if target_county == "SCCP49":  # Horry County
            transformed.update(self._process_horry_specific(transformed))
        elif target_county == "SCCY4G":  # Beaufort County
            transformed.update(self._process_beaufort_specific(transformed))

        # Format execution date for API
        if target_county == "SCCP49":  # Only Horry needs execution date
            transformed["execution_date_formatted"] = self._format_date_for_api(transformed["execution_date"])

        return transformed


    def _generate_package_name(self, data: Dict[str, Any]) -> str:
        """Generate package name - Excel column AK takes precedence"""
        # Check if package name provided in Excel (column AK)
        excel_package_name = data.get("package_name_excel", "").strip()
        if excel_package_name:
            return excel_package_name

        # Auto-generate package name
        last_name = data["lead_1_last"]
        unit_code = data["unit_code"]
        week = data["week"]
        oeb_code = data.get("oeb_code", "")
        project = data["project_number"]
        contract = data["contract_number"]

        if data["project_number"] == 93:  # Anderson Ocean Club includes OEB Code
            return f"{last_name} {unit_code}-{week}{oeb_code} {project}-{contract}"
        else:
            return f"{last_name} {unit_code}-{week} {project}-{contract}"


    def _process_horry_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Horry County specific requirements"""
        result = {}
        project = data["project_number"]

        # Determine grantee and legal description based on project
        if project == 93:  # Anderson Ocean Club
            result["grantee_organization"] = "OCEAN CLUB VACATIONS LLC"
            result["legal_description"] = f"ANDERSON OCEAN CLUB HPR UNIT {data['unit_code']} WK {data['week']}{data.get('oeb_code', '')}"
            result["tms_number"] = self._get_tms_for_unit_93(data["unit_code"])
        elif project == 94:  # Ocean 22
            result["grantee_organization"] = "OCEAN 22 DEVELOPMENT LLC"
            result["legal_description"] = f"OCEAN 22 VACATION SUITES U {data['unit_code']} W {data['week']}"
            result["tms_number"] = "1810418003"
        elif project == 96:  # OE Vacation Suites
            result["grantee_organization"] = "NUM 1600 DEVELOPMENT LLC"
            result["legal_description"] = f"OE VACATION SUITES U {data['unit_code']} W {data['week']}"
            result["tms_number"] = "1810732008"
        else:
            raise ValueError(f"Unsupported Horry project: {project}")

        # Document type for Horry
        county_config = self.get_county_config("SCCP49")
        result["document_type"] = county_config.DOCUMENT_TYPES["DEED_TIMESHARE"]

        return result


    def _process_beaufort_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Beaufort County specific requirements"""
        result = {}

        # Beaufort is always HII DEVELOPMENT LLC
        result["grantee_organization"] = "HII DEVELOPMENT LLC"

        # Document type for Beaufort
        county_config = self.get_county_config("SCCY4G")
        result["document_type"] = county_config.DOCUMENT_TYPES["DEED_HILTON_HEAD_TIMESHARE"]

        # Beaufort doesn't need legal description, TMS, or execution date

        return result


    def _get_tms_for_unit_93(self, unit_code: str) -> str:
        """Get TMS number for Anderson Ocean Club unit"""
        try:
            unit_num = int(unit_code) if unit_code.isdigit() else unit_code
            if unit_num in self.unit_to_tms_93:
                return self.unit_to_tms_93[unit_num]
            else:
                raise ValueError(f"Unknown unit code for Project 93: {unit_code}")
        except ValueError:
            # Handle string unit codes like "PH05"
            if unit_code in self.unit_to_tms_93:
                return self.unit_to_tms_93[unit_code]
            else:
                raise ValueError(f"Unknown unit code for Project 93: {unit_code}")


    def _clean_consideration(self, consideration_str: str) -> float:
        """Clean consideration amount by removing $ and commas"""
        if not consideration_str:
            return 0.0

        # Remove $ and commas, keep only digits and decimal point
        cleaned = re.sub(r'[\$,]', '', str(consideration_str))

        try:
            return float(cleaned)
        except ValueError:
            return 0.0


    def _format_date_for_api(self, date_str: str) -> str:
        """Format date string for API (MM/DD/YYYY format)"""
        if not date_str:
            return datetime.now().strftime('%m/%d/%Y')

        try:
            # Input format from DB Date should be M/D/YYYY, output MM/DD/YYYY
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%m/%d/%Y')
        except ValueError:
            try:
                # Try other common formats
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%m/%d/%Y')
            except ValueError:
                # Return current date as fallback
                return datetime.now().strftime('%m/%d/%Y')


    def is_row_valid(self, excel_row: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a row has all required data and should be processed"""
        # Check routing first
        try:
            target_county = self.route_to_county(excel_row)
            if target_county == "SKIP":
                return False, "Project 98 - skipping per specification"
        except Exception as e:
            return False, f"County routing failed: {str(e)}"

        # Check required fields
        required_fields = {
            "Project": excel_row.get("Project"),
            "Number": excel_row.get("Number"),
            "Lead 1 First": excel_row.get("Lead 1 First"),
            "LEAD 1 LAST": excel_row.get("LEAD 1 LAST"),
            "Unit Code": excel_row.get("Unit Code"),
            "Week": excel_row.get("Week"),
            "DB Pages": excel_row.get("DB Pages"),
            "Consideration": excel_row.get("Consideration")
        }

        for field_name, value in required_fields.items():
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"

        # Validate DB Pages is numeric and positive
        try:
            pages = int(excel_row.get("DB Pages", 0))
            if pages <= 0:
                return False, "DB Pages must be a positive number"
        except (ValueError, TypeError):
            return False, "DB Pages must be a valid number"

        # Additional validation for Horry County (execution date required)
        if target_county == "SCCP49":
            db_date = excel_row.get("DB Date")
            if pd.isna(db_date) or str(db_date).strip() == "":
                return False, "DB Date is required for Horry County"

        return True, ""


    def group_multi_unit_contracts(self, excel_data: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Identify multi-unit contracts (same Project + Number)

        Returns:
            Dictionary mapping "project-number" to list of row indices
        """
        contract_groups = {}

        for i, row in enumerate(excel_data):
            project = row.get("Project", "")
            number = row.get("Number", "")
            contract_key = f"{project}-{number}"

            if contract_key not in contract_groups:
                contract_groups[contract_key] = []
            contract_groups[contract_key].append(i)

        # Return only groups with multiple rows
        return {k: v for k, v in contract_groups.items() if len(v) > 1}


    def combine_multi_unit_data(self, rows: List[Dict[str, Any]], target_county: str) -> Dict[str, Any]:
        """
        Combine multiple rows for same contract into single package
        Uses first row as base, combines legal descriptions and TMS numbers
        """
        if not rows:
            raise ValueError("No rows provided for combination")

        # Use first row as base
        base_row = rows[0]
        combined_data = self.transform_row_data(base_row, target_county)

        if target_county == "SCCP49":  # Only Horry needs legal description combination
            # Combine legal descriptions and TMS numbers with semicolons
            legal_descriptions = []
            tms_numbers = []

            for i, row in enumerate(rows):
                row_data = self.transform_row_data(row, target_county)

                if i == 0:
                    # First entry gets the full legal description
                    legal_descriptions.append(row_data["legal_description"])
                else:
                    # Subsequent entries get abbreviated format
                    project = row_data["project_number"]
                    unit_code = row.get("Unit Code", "")
                    week = row.get("Week", "")
                    oeb_code = row.get("OEB Code", "")

                    if project == 93:  # Anderson Ocean Club
                        abbreviated = f"UNIT {unit_code} WK {week}{oeb_code}"
                    elif project == 94:  # Ocean 22
                        abbreviated = f"U {unit_code} W {week}"
                    elif project == 96:  # OE Vacation Suites
                        abbreviated = f"U {unit_code} W {week}"
                    else:
                        # Fallback to full description if unknown project
                        abbreviated = row_data["legal_description"]

                    legal_descriptions.append(abbreviated)

                tms_numbers.append(row_data["tms_number"])

            combined_data["legal_description"] = "; ".join(legal_descriptions)
            combined_data["tms_number"] = "; ".join(tms_numbers)

        return combined_data