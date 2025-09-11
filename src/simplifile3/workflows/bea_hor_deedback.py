"""BEA-HOR-COUNTYS-DEEDBACK workflow implementation with multi-unit contract support."""

import pandas as pd
from typing import Dict, Any, List
from .base import BaseWorkflow


class BeaHorDeedbackWorkflow(BaseWorkflow):
    """Beaufort/Horry multi-county deedback workflow with multi-unit contract consolidation."""
    
    name = "BEA_HOR_DEEDBACK"
    display_name = "BEA_HOR_DEEDBACK"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/BEA-HOR-DEEDBACK/BEA-HOR-DEEDBACK-workflow-spec.md"
    
    required_columns = [
        "Project", "Number", "Lead 1 First", "LEAD 1 LAST",
        "Unit Code", "Week", "DB Pages", "Consideration"
    ]
    
    field_mappings = {
        "Project": "project",
        "Number": "number",
        "Lead 1 First": "first_1",
        "LEAD 1 LAST": "last_1",
        "Lead 2 First": "first_2",
        "Lead 2 Last": "last_2",
        "Unit Code": "unit",
        "Week": "week",
        "OEB Code": "oeb",
        "DB Date": "db_date",
        "DB Pages": "pages",
        "Consideration": "consideration",
        "Package Name": "package_name_excel"  # Column AK - optional custom name
    }
    
    # Unit to TMS lookup for Project 93
    UNIT_TO_TMS = {
        200: "1810415476", 201: "1810415477", 202: "1810415478", 203: "1810415236",
        204: "1810415479", 205: "1810415237", 206: "1810415480", 209: "1810415240",
        210: "1810415241", 212: "1810415243", 213: "1810415481", 214: "1810415482",
        215: "1810415244", 300: "1810415483", 301: "1810415484", 302: "1810415485",
        303: "1810415245", 308: "1810415250", 309: "1810415251", 310: "1810415252",
        313: "1810415486", 314: "1810415487", 315: "1810415488", 400: "1810415255",
        404: "1810415490", 405: "1810415258", 407: "1810415260", 409: "1810415262",
        410: "1810415263", 412: "1810415265", 413: "1810415491", 500: "1810415268",
        503: "1810415271", 504: "1810415272", 505: "1810415273", 510: "1810415278",
        511: "1810415279", 515: "1810415493", 600: "1810415494", 601: "1810415495",
        603: "1810415283", 605: "1810415285", 607: "1810415287", 609: "1810415289",
        610: "1810415290", 611: "1810415496", 612: "1810415291", 700: "1810415497",
        702: "1810415499", 703: "1810415295", 705: "1810415297", 707: "1810415501",
        708: "1810415298", 709: "1810415299", 710: "1810415300", 711: "1810415301",
        714: "1810415302", 715: "1810415504", 800: "1810415505", 802: "1810415506",
        803: "1810415304", 805: "1810415306", 811: "1810415312", 812: "1810415313",
        813: "1810415507", 815: "1810415508", 900: "1810415509", 901: "1810415315",
        902: "1810415316", 903: "1810415317", 904: "1810415318", 910: "1810415324",
        911: "1810415510", 912: "1810415325", 915: "1810415328", 1000: "1810415511",
        1002: "1810415512", 1003: "1810415330", 1004: "1810415331", 1005: "1810415332",
        1007: "1810415334", 1008: "1810415335", 1011: "1810415338", 1012: "1810415339",
        1014: "1810415340", 1015: "1810415341", 1100: "1810415514", 1101: "1810415515",
        1102: "1810415516", 1104: "1810415343", 1105: "1810415344", 1108: "1810415347",
        1111: "1810415350", 1115: "1810415353", 1200: "1810415354", 1201: "1810415355",
        1202: "1810415518", 1205: "1810415358", 1210: "1810415519", 1211: "1810415363",
        1212: "1810415520", 1213: "1810415364", 1400: "1810415367", 1402: "1810415521",
        1403: "1810415369", 1404: "1810415370", 1405: "1810415371", 1408: "1810415374",
        1411: "1810415377", 1412: "1810415378", 1500: "1810415381", 1501: "1810415382",
        1502: "1810415523", 1503: "1810415383", 1504: "1810415384", 1505: "1810415385",
        1506: "1810415386", 1509: "1810415389", 1512: "1810415392", 1515: "1810415394",
        1600: "1810415525", 1601: "1810415526", 1603: "1810415395", 1604: "1810415396",
        1605: "1810415397", 1606: "1810415398", 1608: "1810415400", 1609: "1810415401",
        1612: "1810415402", 1613: "1810415530", 1615: "1810415404", 1700: "1810415405",
        1704: "1810415408", 1705: "1810415409", 1707: "1810415411", 1709: "1810415413",
        1710: "1810415414", 1711: "1810415532", 1713: "1810415534", 1800: "1810415535",
        1802: "1810415537", 1806: "1810415420", 1809: "1810415539", 1811: "1810415423",
        1812: "1810415540", 1815: "1810415425", 1900: "1810415426", 1902: "1810415542",
        1903: "1810415428", 1904: "1810415543", 1905: "1810415429", 1907: "1810415431",
        1908: "1810415544", 1911: "1810415433", 1912: "1810415434", 1913: "1810415435",
        2006: "1810415441", 2008: "1810415443", 2009: "1810415444", 2010: "1810415445",
        2011: "1810415446", 2012: "1810415447", 2103: "1810415448", 2104: "1810415449",
        2105: "1810415550", 2108: "1810415452", 2111: "1810415455", 2112: "1810415456",
        "PH05": "1810415458", "PH06": "1810415459", "PH10": "1810415463", "PH11": "1810415464"
    }
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.pdf_position = 0  # Track current PDF position
    
    def validate_excel(self, df: pd.DataFrame) -> List[str]:
        """Pre-process Excel data to handle multi-unit contracts, then validate."""
        # First do basic structure validation
        errors = super().validate_excel(df)
        if errors:
            return errors
        
        # Ensure we have all required columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            return [f"Missing required columns: {missing_cols}"]
        
        try:
            # Pre-process the DataFrame to handle multi-unit contracts
            self.processed_df = self._preprocess_multi_unit_contracts(df)
            self.logger.info(f"Pre-processed {len(df)} rows into {len(self.processed_df)} packages")
            return []
        except Exception as e:
            return [f"Multi-unit pre-processing failed: {str(e)}"]
    
    def _preprocess_multi_unit_contracts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pre-process DataFrame to consolidate multi-unit contracts."""
        # Convert to list of dicts for easier processing
        rows = df.to_dict('records')
        
        # Group by Project + Number
        contract_groups = {}
        for i, row in enumerate(rows):
            project = row.get("Project", "")
            number = row.get("Number", "")
            contract_key = f"{project}-{number}"
            
            if contract_key not in contract_groups:
                contract_groups[contract_key] = []
            contract_groups[contract_key].append((i, row))
        
        # Process each group
        processed_rows = []
        pdf_position = 0
        
        for contract_key, group in contract_groups.items():
            if len(group) == 1:
                # Single unit - process normally
                idx, row = group[0]
                
                # Skip project 98
                if int(row.get("Project", 0)) == 98:
                    pages = int(row.get("DB Pages", 0))
                    pdf_position += pages
                    self.logger.info(f"Skipping Project 98: Row {idx + 2}")
                    continue
                
                # Add PDF position info
                row["_pdf_start_position"] = pdf_position
                row["_pages_to_skip"] = 0
                row["_combined_legal"] = ""
                row["_combined_tms"] = ""
                row["_is_multi_unit"] = False
                row["_unit_count"] = 1
                pages = int(row.get("DB Pages", 0))
                pdf_position += pages
                
                processed_rows.append(row)
            else:
                # Multi-unit contract - combine into single package
                base_idx, base_row = group[0]
                
                # Skip project 98
                if int(base_row.get("Project", 0)) == 98:
                    total_pages = sum(int(row.get("DB Pages", 0)) for _, row in group)
                    pdf_position += total_pages
                    self.logger.info(f"Skipping Project 98 multi-unit: Rows {[idx + 2 for idx, _ in group]}")
                    continue
                
                # Use base row as foundation
                combined_row = base_row.copy()
                combined_row["_pdf_start_position"] = pdf_position
                
                # Combine legal descriptions and TMS numbers
                legal_descriptions = []
                tms_numbers = []
                
                # For multi-unit, there's only ONE document in the PDF stack
                # Use the first row's page count and advance by that amount only
                first_row_pages = int(group[0][1].get("DB Pages", 0))
                pdf_position += first_row_pages
                
                for i, (idx, row) in enumerate(group):
                    # Build legal description for this unit
                    project = int(row.get("Project", 0))
                    unit = row.get("Unit Code", "")
                    week = row.get("Week", "")
                    oeb = row.get("OEB Code", "")
                    
                    if i == 0:
                        # First unit gets full description
                        if project == 93:
                            legal_descriptions.append(f"ANDERSON OCEAN CLUB HPR UNIT {unit} WK {week}{oeb}")
                            tms = self.UNIT_TO_TMS.get(int(unit) if unit.isdigit() else unit, "")
                        elif project == 94:
                            legal_descriptions.append(f"OCEAN 22 VACATION SUITES U {unit} W {week}")
                            tms = "1810418003"
                        elif project == 96:
                            legal_descriptions.append(f"OE VACATION SUITES U {unit} W {week}")
                            tms = "1810732008"
                        else:
                            legal_descriptions.append(f"UNIT {unit} WK {week}{oeb}")
                            tms = ""
                        tms_numbers.append(tms)
                    else:
                        # Additional units get abbreviated description
                        if project == 93:
                            legal_descriptions.append(f"UNIT {unit} WK {week}{oeb}")
                            tms = self.UNIT_TO_TMS.get(int(unit) if unit.isdigit() else unit, "")
                        elif project == 94:
                            legal_descriptions.append(f"U {unit} W {week}")
                            tms = "1810418003"
                        elif project == 96:
                            legal_descriptions.append(f"U {unit} W {week}")
                            tms = "1810732008"
                        else:
                            legal_descriptions.append(f"UNIT {unit} WK {week}{oeb}")
                            tms = ""
                        tms_numbers.append(tms)
                
                # Store combined data
                combined_row["_combined_legal"] = "; ".join(legal_descriptions)
                combined_row["_combined_tms"] = "; ".join(filter(None, tms_numbers))
                combined_row["_pages_to_skip"] = 0  # No pages to skip for multi-unit
                combined_row["_is_multi_unit"] = True
                combined_row["_unit_count"] = len(group)
                
                self.logger.info(f"Combined multi-unit contract {contract_key}: {len(group)} units -> 1 package")
                processed_rows.append(combined_row)
        
        # Convert back to DataFrame
        return pd.DataFrame(processed_rows)
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed - Project 98 already filtered out."""
        return super().is_row_valid(row)
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with routing logic and multi-unit support."""
        data = super().transform_row(row)
        
        # Clean up nan values for optional fields
        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip()
        
        # Uppercase names (clean nan values first)
        data["first_1"] = clean_value(data.get("first_1", "")).upper()
        data["last_1"] = clean_value(data.get("last_1", "")).upper()
        data["first_2"] = clean_value(data.get("first_2", "")).upper()
        data["last_2"] = clean_value(data.get("last_2", "")).upper()
        
        # Clean other optional fields
        data["oeb"] = clean_value(data.get("oeb", ""))
        data["db_date"] = clean_value(data.get("db_date", ""))
        data["package_name_excel"] = clean_value(data.get("package_name_excel", ""))
        
        # Determine county
        project = int(data["project"])
        if project in [93, 94, 96]:
            data["county"] = "SCCP49"  # Horry
        elif project == 95:
            data["county"] = "SCCY4G"  # Beaufort
        else:
            data["county"] = ""
        
        # Package naming - check for Excel column AK first
        excel_package_name = data["package_name_excel"]
        if excel_package_name:
            data["package_name"] = excel_package_name
        else:
            # Auto-generate package name (always uses first unit info)
            oeb_suffix = data["oeb"]
            if project == 93 and oeb_suffix:
                data["package_name"] = f"{data['last_1']} {data['unit']}-{data['week']}{oeb_suffix} {project}-{data['number']}"
            else:
                data["package_name"] = f"{data['last_1']} {data['unit']}-{data['week']} {project}-{data['number']}"
        
        data["package_id"] = f"P-{data['number']}"
        data["document_id"] = f"D-{data['number']}"
        
        # Clean consideration
        data["consideration"] = self.clean_money(data.get("consideration", "0"))
        
        # County-specific data
        if data["county"] == "SCCP49":
            data.update(self._horry_specific(data, project, row))
        elif data["county"] == "SCCY4G":
            data.update(self._beaufort_specific(data))
        
        # PDF positioning info
        data["pdf_start_position"] = row.get("_pdf_start_position", 0)
        data["pages_to_skip"] = row.get("_pages_to_skip", 0)
        
        return data
    
    def _horry_specific(self, data: Dict[str, Any], project: int, row: Dict[str, Any]) -> Dict[str, Any]:
        """Horry-specific transformations."""
        result = {}
        
        # Use combined legal description if available (multi-unit)
        if row.get("_is_multi_unit", False):
            result["legal"] = row["_combined_legal"]
            result["tms"] = row["_combined_tms"]
        else:
            # Single unit
            if project == 93:
                result["legal"] = f"ANDERSON OCEAN CLUB HPR UNIT {data['unit']} WK {data['week']}{data.get('oeb', '')}"
                result["tms"] = self.UNIT_TO_TMS.get(int(data["unit"]) if data["unit"].isdigit() else data["unit"], "")
            elif project == 94:
                result["legal"] = f"OCEAN 22 VACATION SUITES U {data['unit']} W {data['week']}"
                result["tms"] = "1810418003"
            elif project == 96:
                result["legal"] = f"OE VACATION SUITES U {data['unit']} W {data['week']}"
                result["tms"] = "1810732008"
        
        # Grantee based on project
        if project == 93:
            result["grantee"] = "OCEAN CLUB VACATIONS LLC"
        elif project == 94:
            result["grantee"] = "OCEAN 22 DEVELOPMENT LLC"
        elif project == 96:
            result["grantee"] = "NUM 1600 DEVELOPMENT LLC"
        
        result["doc_type"] = "Deed - Timeshare"
        return result
    
    def _beaufort_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Beaufort-specific transformations."""
        return {
            "grantee": "HHI DEVELOPMENT LLC",
            "doc_type": "DEED - HILTON HEAD TIMESHARE"
        }
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract PDF using pre-calculated position and skip info."""
        start_position = row_data.get("pdf_start_position", 0)
        page_count = int(row_data["pages"])
        
        # Extract PDF from specific position
        pdf = self.extract_pages_at_position(pdf_paths["deed_stack"], start_position, page_count)
        
        return {"deed": pdf}
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build county-specific payload."""
        package = super().build_payload(package_data, pdfs)
        
        indexing = {
            "consideration": package_data["consideration"],
            "grantors": [{
                "firstName": package_data["first_1"],
                "lastName": package_data["last_1"],
                "type": "Individual"
            }],
            "grantees": [{
                "nameUnparsed": package_data["grantee"],
                "type": "Organization"
            }]
        }
        
        # Add second grantor if present
        if package_data.get("first_2") and package_data.get("last_2"):
            indexing["grantors"].append({
                "firstName": package_data["first_2"],
                "lastName": package_data["last_2"],
                "type": "Individual"
            })
        
        # Horry needs more fields
        if package_data["county"] == "SCCP49":
            indexing["executionDate"] = package_data.get("db_date", "")
            indexing["legalDescriptions"] = [{
                "description": package_data["legal"],
                "parcelId": package_data["tms"]
            }]
        
        document = {
            "submitterDocumentID": package_data["document_id"],
            "name": package_data["package_name"],
            "kindOfInstrument": [package_data["doc_type"]],
            "indexingData": indexing,
            "fileBytes": [self.to_base64(pdfs["deed"])]
        }
        
        package["documents"] = [document]
        package["recipient"] = package_data["county"]
        
        return package