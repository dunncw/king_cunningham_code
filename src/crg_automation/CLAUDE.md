# CRG Automation Module

This module provides automated interaction with the Capital IT Files system for court record gathering. It specializes in processing account numbers, filtering for Myrtle Beach-specific records, and automating bulk file downloads through web automation.

## Architecture

### Core Components

#### CRGAutomationWorker
- **Location**: `crg.py:20`
- **Purpose**: Main automation worker class extending QObject
- **Key Features**:
  - Selenium-based web automation
  - Account number filtering and processing
  - Bulk file download management
  - Progress tracking with Qt signals

#### ExcelProcessor
- **Location**: `excel_processor.py:15`
- **Purpose**: Excel data processing for account number extraction
- **Capabilities**:
  - Account number validation and filtering
  - Myrtle Beach specific account identification
  - Data cleaning and formatting
  - Error reporting and validation

## Key Features

### Account Number Processing
- **Myrtle Beach Filter**: Automatically identifies Myrtle Beach account numbers
- **Data Validation**: Validates account number formats and structure
- **Batch Processing**: Handles large datasets with progress tracking
- **Error Handling**: Comprehensive error reporting for invalid data

### Capital IT Files Integration
- **Automated Login**: Selenium-based authentication workflow
- **Search Automation**: Automated account number search functionality
- **File Selection**: Intelligent file selection and filtering
- **Bulk Download**: Automated bulk download with PyAutoGUI

### Web Automation Features
- **Browser Management**: Chrome WebDriver with automated management
- **Element Detection**: Robust web element identification and interaction
- **Download Management**: Automated file download handling
- **Session Management**: Proper login/logout workflow

## Data Processing Workflow

### Excel Data Extraction
1. **File Loading**: Load Excel file with account number data
2. **Column Identification**: Identify account number columns automatically
3. **Data Validation**: Validate account number format and structure
4. **Myrtle Beach Filtering**: Filter for Myrtle Beach specific accounts
5. **Data Cleaning**: Remove duplicates and invalid entries

### Account Number Filtering Logic
```python
def is_myrtle_beach_account(account_number):
    """
    Identifies Myrtle Beach account numbers based on specific patterns
    Myrtle Beach accounts typically follow specific formatting rules
    """
    # Implementation includes pattern matching for MB accounts
    # Returns True if account belongs to Myrtle Beach jurisdiction
```

### Capital IT Files Automation
1. **Browser Initialization**: Launch Chrome WebDriver with configuration
2. **Login Process**: Navigate to Capital IT Files and authenticate
3. **Search Interface**: Navigate to search functionality
4. **Account Processing**: Process each account number individually:
   - Enter account number in search field
   - Execute search and wait for results
   - Validate search results
   - Select relevant files for download
5. **Bulk Download**: Initiate and manage bulk download process
6. **Progress Tracking**: Report progress throughout the process

## File Download Management

### Download Configuration
```python
DOWNLOAD_SETTINGS = {
    "download_directory": "./crg_downloads",
    "file_timeout": 300,  # 5 minutes per file
    "retry_attempts": 3,
    "concurrent_downloads": 1  # Sequential downloads for stability
}
```

### PyAutoGUI Integration
- **Keyboard Automation**: Automated keyboard shortcuts for download dialogs
- **File Naming**: Systematic file naming based on account numbers
- **Download Monitoring**: Monitor download progress and completion
- **Error Recovery**: Handle download failures and retry logic

## Error Handling

### Account Number Validation
- **Format Validation**: Ensure account numbers meet expected format
- **Myrtle Beach Validation**: Verify account belongs to correct jurisdiction
- **Duplicate Detection**: Identify and handle duplicate account numbers
- **Missing Data**: Handle missing or incomplete account information

### Web Automation Errors
- **Login Failures**: Handle authentication errors and retry logic
- **Element Not Found**: Robust element detection with fallback strategies
- **Search Failures**: Handle search errors and invalid account responses
- **Download Errors**: Comprehensive download error handling and recovery

### File System Errors
- **Download Directory**: Ensure download directory exists and is writable
- **File Permissions**: Handle file permission issues
- **Disk Space**: Monitor available disk space for downloads
- **File Conflicts**: Handle filename conflicts and duplicates

## Performance Optimization

### Batch Processing
- **Sequential Processing**: Process accounts one at a time for reliability
- **Progress Batching**: Update progress in reasonable intervals
- **Memory Management**: Efficient memory usage for large datasets
- **Resource Cleanup**: Proper cleanup of browser resources

### Download Optimization
- **Download Monitoring**: Track download progress and status
- **Timeout Management**: Appropriate timeouts for various operations
- **Retry Logic**: Intelligent retry for failed operations
- **Bandwidth Management**: Consider bandwidth limitations

## Configuration Management

### Browser Configuration
```python
CHROME_OPTIONS = {
    "download_directory": "./crg_downloads",
    "disable_extensions": True,
    "disable_dev_shm_usage": True,
    "no_sandbox": False,
    "window_size": (1920, 1080)
}
```

### Account Processing Settings
```python
PROCESSING_CONFIG = {
    "batch_size": 50,  # Accounts per batch
    "delay_between_searches": 2,  # Seconds between searches
    "max_retries": 3,
    "timeout_per_account": 60  # Seconds per account processing
}
```

## Integration Points

### UI Integration
- **Progress Reporting**: Real-time progress updates via Qt signals
- **Error Display**: User-friendly error messages and recovery suggestions
- **File Selection**: Excel file selection and validation interface
- **Configuration**: User-configurable settings and preferences

### Excel Processor Integration
- **Data Extraction**: Seamless integration with Excel data processing
- **Column Mapping**: Flexible column identification and mapping
- **Data Validation**: Comprehensive data validation before processing
- **Error Reporting**: Detailed error reporting with row context

### File System Integration
- **Download Management**: Automated download directory management
- **File Organization**: Systematic file organization and naming
- **Progress Tracking**: File-level progress tracking and reporting
- **Cleanup Operations**: Automated cleanup of temporary files

## Security Considerations

### Credential Management
- **Secure Storage**: Avoid hardcoded credentials in source code
- **Environment Variables**: Use environment variables for sensitive data
- **Session Security**: Proper session management and cleanup
- **Authentication Tokens**: Secure handling of authentication tokens

### Data Protection
- **Account Information**: Secure handling of account number data
- **Downloaded Files**: Proper security for downloaded court records
- **Temporary Data**: Secure cleanup of temporary data
- **Audit Trail**: Comprehensive logging of automation activities

## Development Guidelines

### Adding New Account Types
1. **Pattern Analysis**: Analyze new account number patterns
2. **Filter Logic**: Implement filtering logic for new account types
3. **Validation Rules**: Add validation rules for new formats
4. **Testing**: Comprehensive testing with new account data
5. **Documentation**: Update documentation with new account specifications

### Web Automation Enhancement
- **Element Locators**: Use robust and maintainable element locators
- **Wait Strategies**: Implement appropriate wait strategies for dynamic content
- **Error Recovery**: Add comprehensive error recovery mechanisms
- **Browser Compatibility**: Ensure compatibility with browser updates

### Performance Improvement
- **Parallel Processing**: Consider parallel processing for independent operations
- **Caching**: Implement caching for frequently accessed data
- **Optimization**: Profile and optimize bottleneck operations
- **Resource Management**: Improve resource utilization and cleanup

## Testing Strategy

### Unit Testing
- **Account Filtering**: Test account number filtering logic
- **Data Validation**: Test data validation and cleaning functions
- **Error Handling**: Test error handling scenarios
- **Configuration**: Test configuration loading and validation

### Integration Testing
- **End-to-End Workflow**: Test complete automation workflow
- **Excel Integration**: Test Excel file processing integration
- **Web Automation**: Test web automation reliability
- **File Download**: Test file download and management

### Performance Testing
- **Large Dataset**: Test with large account number datasets
- **Memory Usage**: Monitor memory usage during processing
- **Download Performance**: Test download performance and reliability
- **Error Recovery**: Test error recovery under various failure scenarios

## Maintenance Considerations

### Capital IT Files Updates
- **Website Monitoring**: Monitor target website for changes
- **Element Updates**: Update web element locators as needed
- **Workflow Changes**: Adjust automation workflow for site updates
- **API Changes**: Handle any API or interface changes

### Browser Compatibility
- **WebDriver Updates**: Keep WebDriver updated with browser versions
- **Browser Updates**: Test compatibility with browser updates
- **Feature Deprecation**: Handle deprecated browser features
- **Performance Monitoring**: Monitor automation performance over time

### Data Format Changes
- **Account Number Formats**: Monitor for changes in account number formats
- **Excel Format Updates**: Handle changes in Excel data formats
- **Validation Rules**: Update validation rules as needed
- **Filter Logic**: Maintain and update filtering logic

## Troubleshooting Guide

### Common Issues
1. **Login Failures**: Check credentials and website availability
2. **Element Not Found**: Verify web element locators are current
3. **Download Failures**: Check download directory permissions and disk space
4. **Account Not Found**: Verify account number format and validity
5. **Browser Crashes**: Check browser compatibility and system resources

### Diagnostic Tools
- **Logging**: Comprehensive logging for troubleshooting
- **Debug Mode**: Enable debug mode for detailed operation tracking
- **Error Screenshots**: Capture screenshots on automation failures
- **Performance Metrics**: Track performance metrics for optimization

### Recovery Procedures
- **Manual Intervention**: Procedures for manual processing when automation fails
- **Data Recovery**: Recover and resume processing from failures
- **Backup Strategies**: Backup important data before processing
- **Rollback Procedures**: Rollback procedures for failed operations