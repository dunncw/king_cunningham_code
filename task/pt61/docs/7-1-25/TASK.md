# PT61 Multi-Version Implementation Game Plan

## Phase 1: Configuration System (Foundation)

### 1.1 Create Configuration Module
**New File:** `web_automation/pt61_config.py`
```python
PT61_VERSIONS = {
    "new_batch": {
        "display_name": "PT-61 New Batch",
        "required_columns": [
            "Contract Num", "Last 1", "First 1", "Middle 1",
            "Last 2", "First 2", "Middle 2", "Sales Price", "date on deed"
        ],
        "constants": {
            "seller_address": {...},
            "buyer": {...},
            "property": {...},
            # etc.
        }
    },
    "deedbacks": {...},
    "foreclosures": {...}
}
```

### 1.2 Create Version Validator
**New File:** `web_automation/version_validator.py`
- Validate Excel files against required columns for selected version
- Return validation errors if columns are missing
- Handle case-insensitive column matching

## Phase 2: Excel Processing Updates

### 2.1 Modify `excel_processor.py`
**Changes needed:**
```python
def extract_data_from_excel(excel_path, version_key):
    """Extract data based on version configuration"""
    config = PT61_VERSIONS[version_key]
    # Validate columns exist
    # Extract only required columns
    # Apply version-specific data formatting
    return people_data

def validate_excel_structure(excel_path, version_key):
    """Validate Excel has required columns for version"""
    # Check headers against config
    # Return validation results
```

### 2.2 Update Data Structure
**Current structure works, but add:**
- Version-aware field mapping
- Dynamic field extraction based on config
- Better error handling for missing columns

## Phase 3: UI Updates

### 3.1 Modify `web_automation_ui.py`
**Add version selection:**
```python
# Add version dropdown
version_layout = QHBoxLayout()
self.version_combo = QComboBox()
self.version_combo.addItems([
    "PT-61 New Batch", 
    "PT-61 Deedbacks", 
    "PT61 Foreclosures"
])
self.version_combo.currentTextChanged.connect(self.on_version_changed)
```

**Add template download:**
```python
template_button = QPushButton("Download Excel Template")
template_button.clicked.connect(self.download_template)
```

**Add validation feedback:**
- Show required columns for selected version
- Display validation errors
- Real-time Excel file validation

### 3.2 Update Signal Emission
**Change from:**
```python
start_automation = pyqtSignal(str, str, str, str, str)
```
**To:**
```python
start_automation = pyqtSignal(str, str, str, str, str, str)  # Add version
```

## Phase 4: Automation Engine Refactor

### 4.1 Create Version-Specific Automation Classes
**New File:** `web_automation/version_handlers.py`
```python
class BaseVersionHandler:
    def __init__(self, config, person_data):
        self.config = config
        self.person_data = person_data
    
    def fill_seller_section(self, driver):
        # Base implementation
        pass
    
    def fill_buyer_section(self, driver):
        # Base implementation
        pass

class NewBatchHandler(BaseVersionHandler):
    def fill_buyer_section(self, driver):
        # Always CENTENNIAL PARK DEVELOPMENT LLC
        
class DeedbacksHandler(BaseVersionHandler):
    def fill_buyer_section(self, driver):
        # Dynamic based on DB To column
        
class ForeclosuresHandler(BaseVersionHandler):
    def fill_exempt_code(self, driver):
        # Always "First Transferee Foreclosure"
```

### 4.2 Refactor `automation.py`
**Key changes:**
1. **Add version parameter** to `run_web_automation`
2. **Factory pattern** for version handlers
3. **Dynamic form filling** based on version config
4. **Version-specific file naming**

```python
class WebAutomationWorker(QObject):
    def __init__(self, excel_path, browser, username, password, save_location, version_key):
        # Add version_key parameter
        self.version_key = version_key
        self.version_config = PT61_VERSIONS[version_key]
        self.handler = self.create_version_handler()
    
    def create_version_handler(self):
        handlers = {
            "new_batch": NewBatchHandler,
            "deedbacks": DeedbacksHandler, 
            "foreclosures": ForeclosuresHandler
        }
        return handlers[self.version_key](self.version_config)
```

## Phase 5: Form Filling Logic Updates

### 5.1 Dynamic Form Filling
**Replace hardcoded values with config-driven approach:**
```python
def fill_form_section(self, driver, section_name, person_data):
    section_config = self.version_config[section_name]
    
    if section_config['type'] == 'constant':
        # Fill with constant values
        self.fill_constant_fields(driver, section_config['values'])
    elif section_config['type'] == 'variable':
        # Fill with Excel data
        self.fill_variable_fields(driver, section_config['mapping'], person_data)
    elif section_config['type'] == 'conditional':
        # Fill based on condition
        self.fill_conditional_fields(driver, section_config, person_data)
```

### 5.2 Version-Specific Logic
- **New Batch:** Support additional sellers (First 2, Middle 2, Last 2)
- **Deedbacks:** Dynamic buyer selection based on "DB To" column
- **Foreclosures:** Different exempt code and file naming

## Phase 6: File Management

### 6.1 Template Generation
**New File:** `web_automation/template_generator.py`
```python
def generate_excel_template(version_key, save_path):
    """Generate Excel template for specific version"""
    config = PT61_VERSIONS[version_key]
    # Create Excel with required headers
    # Add sample data
    # Save to specified path
```

### 6.2 Dynamic File Naming
**Update file naming logic:**
```python
def generate_filename(self, person_data):
    naming_pattern = self.version_config['file_naming']
    # Parse pattern like "{last_name} {contract_num} PT61"
    # Replace placeholders with actual data
    return formatted_filename
```

## Phase 7: Integration Updates

### 7.1 Update `main_window.py`
**Modify signal connection:**
```python
def start_web_automation(self, excel_path, browser, username, password, save_location, version):
    self.thread, self.worker = run_web_automation_thread(
        excel_path, browser, username, password, save_location, version
    )
```

### 7.2 Update Thread Function
**Modify `run_web_automation_thread`:**
```python
def run_web_automation_thread(excel_path, browser, username, password, save_location, version_key):
    worker = WebAutomationWorker(excel_path, browser, username, password, save_location, version_key)
    # Rest of thread setup
```

## Phase 8: Testing & Validation

### 8.1 Unit Tests
- Test each version handler independently
- Validate Excel processing for each version
- Test file naming patterns

### 8.2 Integration Tests
- End-to-end testing with real Excel files
- UI workflow testing
- Error handling validation

### 8.3 User Acceptance Testing
- Test with Shannon and Brittany's real data
- Verify correct form filling for each version
- Validate file outputs

## Phase 9: Documentation & Deployment

### 9.1 Update Documentation
- User guide for each version
- Excel template requirements
- Troubleshooting guide

### 9.2 Migration Plan
- Backup current implementation
- Gradual rollout of new versions
- Fallback strategy

## Implementation Priority

### Week 1: Foundation
- Configuration system
- Excel processor updates
- Version validator

### Week 2: UI Updates
- Version selection dropdown
- Template download
- Validation feedback

### Week 3: Core Logic
- Version handlers
- Form filling refactor
- File naming updates

### Week 4: Integration & Testing
- Connect all components
- Testing with real data
- Bug fixes and refinements

## Risk Mitigation

1. **Backwards Compatibility:** Keep existing "New Batch" working exactly as is
2. **Gradual Rollout:** Deploy one version at a time
3. **Validation:** Extensive Excel validation before processing
4. **Logging:** Detailed logging for debugging
5. **Error Recovery:** Graceful handling of form filling errors

## Success Metrics

- All 3 versions working correctly
- Users can switch between versions seamlessly
- Excel template download working
- File naming correct for each version
- No regression in existing functionality