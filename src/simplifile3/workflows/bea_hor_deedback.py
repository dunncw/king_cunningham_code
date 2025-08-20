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
        200: "18104154760", 201: "18104154770", 202: "18104154780", 203: "18104152360",
        204: "18104154790", 205: "18104152370", 206: "18104154800", 209: "18104152400",
        210: "18104152410", 212: "18104152430", 213: "18104154810", 214: "18104154820",
        215: "18104152440", 300: "18104154830", 301: "18104154840", 302: "18104154850",
        303: "18104152450", 308: "18104152500", 309: "18104152510", 310: "18104152520",
        313: "18104154860", 314: "18104154870", 315: "18104154880", 400: "18104152550",
        404: "18104154900", 405: "18104152580", 407: "18104152600", 409: "18104152620",
        410: "18104152630", 412: "18104152650", 413: "18104154910", 500: "18104152680",
        503: "18104152710", 504: "18104152720", 505: "18104152730", 510: "18104152780",
        511: "18104152790", 515: "18104154930", 600: "18104154940", 601: "18104154950",
        603: "18104152830", 605: "18104152850", 607: "18104152870", 609: "18104152890",
        610: "18104152900", 611: "18104154960", 612: "18104152910", 700: "18104154970",
        702: "18104154990", 703: "18104152950", 705: "18104152970", 707: "18104155010",
        708: "18104152980", 709: "18104152990", 710: "18104153000", 711: "18104153010",
        714: "18104153020", 715: "18104155040", 800: "18104155050", 802: "18104155060",
        803: "18104153040", 805: "18104153060", 811: "18104153120", 812: "18104153130",
        813: "18104155070", 815: "18104155080", 900: "18104155090", 901: "18104153150",
        902: "18104153160", 903: "18104153170", 904: "18104153180", 910: "18104153240",
        911: "18104155100", 912: "18104153250", 915: "18104153280", 1000: "18104155110",
        1002: "18104155120", 1003: "18104153300", 1004: "18104153310", 1005: "18104153320",
        1007: "18104153340", 1008: "18104153350", 1011: "18104153380", 1012: "18104153390",
        1014: "18104153400", 1015: "18104153410", 1100: "18104155140", 1101: "18104155150",
        1102: "18104155160", 1104: "18104153430", 1105: "18104153440", 1108: "18104153470",
        1111: "18104153500", 1115: "18104153530", 1200: "18104153540", 1201: "18104153550",
        1202: "18104155180", 1205: "18104153580", 1210: "18104155190", 1211: "18104153630",
        1212: "18104155200", 1213: "18104153640", 1400: "18104153670", 1402: "18104155210",
        1403: "18104153690", 1404: "18104153700", 1405: "18104153710", 1408: "18104153740",
        1411: "18104153770", 1412: "18104153780", 1500: "18104153810", 1501: "18104153820",
        1502: "18104155230", 1503: "18104153830", 1504: "18104153840", 1505: "18104153850",
        1506: "18104153860", 1509: "18104153890", 1512: "18104153920", 1515: "18104153940",
        1600: "18104155250", 1601: "18104155260", 1603: "18104153950", 1604: "18104153960",
        1605: "18104153970", 1606: "18104153980", 1608: "18104154000", 1609: "18104154010",
        1612: "18104154020", 1613: "18104155300", 1615: "18104154040", 1700: "18104154050",
        1704: "18104154080", 1705: "18104154090", 1707: "18104154110", 1709: "18104154130",
        1710: "18104154140", 1711: "18104155320", 1713: "18104155340", 1800: "18104155350",
        1802: "18104155370", 1806: "18104154200", 1809: "18104155390", 1811: "18104154230",
        1812: "18104155400", 1815: "18104154250", 1900: "18104154260", 1902: "18104155420",
        1903: "18104154280", 1904: "18104155430", 1905: "18104154290", 1907: "18104154310",
        1908: "18104155440", 1911: "18104154330", 1912: "18104154340", 1913: "18104154350",
        2006: "18104154410", 2008: "18104154430", 2009: "18104154440", 2010: "18104154450",
        2011: "18104154460", 2012: "18104154470", 2103: "18104154480", 2104: "18104154490",
        2105: "18104155500", 2108: "18104154520", 2111: "18104154550", 2112: "18104154560",
        "PH05": "18104154580", "PH06": "18104154590", "PH10": "18104154630", "PH11": "18104154640"
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
            "grantee": "HII DEVELOPMENT LLC",
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