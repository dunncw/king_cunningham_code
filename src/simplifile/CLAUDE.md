# Simplifile Module

This module provides comprehensive integration with the Simplifile electronic recording platform, enabling automated submission of legal documents to county recording offices. It includes API integration, county-specific configurations, batch processing, and Excel data management.

## Architecture

### Core Components

#### SimplifileAPI
- **Location**: `api.py:15`
- **Purpose**: Primary API interface for Simplifile platform
- **Key Methods**:
  - `authenticate()` - Login and session management
  - `create_package()` - Package creation and submission
  - `upload_document()` - Document file upload
  - `submit_package()` - Final package submission
  - `get_package_status()` - Status tracking

#### Data Models

##### SimplifilePackage
- **Location**: `models.py:45`
- **Purpose**: Represents a recording package with county-aware behavior
- **Key Features**:
  - County-specific validation rules
  - Document type mappings
  - Party information management
  - Legal description handling

##### SimplifileDocument
- **Location**: `models.py:120`
- **Purpose**: Individual document representation with metadata
- **Attributes**:
  - Document type and classification
  - File path and content
  - Recording requirements
  - Validation status

##### Party
- **Location**: `models.py:200` 
- **Purpose**: Grantor/grantee representation for legal transactions
- **Features**:
  - Name validation and formatting
  - Address standardization
  - Role-based party types

#### County Configuration System

##### Base CountyConfig
- **Location**: `county_config.py:20`
- **Purpose**: Abstract base class for county-specific settings
- **Key Components**:
  - Document type mappings
  - Required field definitions
  - Validation rule sets
  - API endpoint configurations

##### Implemented Counties

###### HorryCountyConfig (SCCP49)
- **Location**: `county_config.py:85`
- **Features**:
  - Horry County, South Carolina specific rules
  - DEED_DOCUMENT_TYPE: "WD" (Warranty Deed)
  - MORTGAGE_DOCUMENT_TYPE: "MORT"
  - Special grantee/grantor handling

###### BeaufortCountyConfig (SCCY4G)
- **Location**: `county_config.py:145`
- **Features**:
  - Beaufort County, South Carolina rules
  - Enhanced party validation
  - Specific legal description requirements

###### WilliamsburgCountyConfig (SCCE6P)
- **Location**: `county_config.py:205`
- **Features**:
  - Williamsburg County, South Carolina rules
  - Simplified document type structure
  - Basic validation requirements

###### FultonCountyConfig (GAC3TH)
- **Location**: `county_config.py:265`
- **Features**:
  - Fulton County, Georgia rules
  - Georgia-specific document types
  - Enhanced recording requirements

###### ForsythCountyConfig (NCCHLB)
- **Location**: `county_config.py:325`
- **Features**:
  - Forsyth County, North Carolina rules
  - North Carolina recording standards
  - Specific fee structures

#### Batch Processing

##### SimplifileBatchProcessor
- **Location**: `batch_processor.py:25`
- **Purpose**: Orchestrates bulk document submission workflows
- **Key Features**:
  - Multi-document package creation
  - Progress tracking and reporting
  - Error handling and recovery
  - Threaded processing with Qt signals

##### SimplifileExcelProcessor
- **Location**: `excel_processor.py:20`
- **Purpose**: Excel data extraction and validation for batch operations
- **Capabilities**:
  - Column mapping and validation
  - Data type conversion and cleanup
  - Row-by-row processing
  - Error reporting with row context

## Key Features

### API Integration
- **Authentication**: Secure login with session management
- **RESTful API**: Standard HTTP methods for all operations
- **Error Handling**: Comprehensive API error interpretation
- **Rate Limiting**: Built-in request throttling
- **Environment Support**: QA and Production environment switching

### County-Specific Processing
- **Strategy Pattern**: County configurations implement specific business rules
- **Document Type Mapping**: Each county has unique document type codes
- **Validation Rules**: County-specific field requirements and formats
- **Fee Calculation**: County-based fee structures and calculations

### Document Management
- **PDF Processing**: Integration with document_processor for PDF splitting
- **File Upload**: Chunked upload for large documents
- **Metadata Extraction**: Automatic document property detection
- **Validation**: Pre-submission document validation

### Excel Integration
- **Data Import**: Flexible Excel column mapping
- **Validation**: Cell-level data validation with error reporting
- **Batch Creation**: Automatic package generation from Excel rows
- **Progress Tracking**: Row-by-row processing with status updates

## Configuration Management

### Environment Settings
```python
# API Endpoints
QA_ENDPOINT = "https://qa-api.simplifile.com"
PROD_ENDPOINT = "https://api.simplifile.com"

# Authentication
LOGIN_PATH = "/auth/login"
API_VERSION = "v1"
```

### County Registration
```python
COUNTY_CONFIGS = {
    "SCCP49": HorryCountyConfig,
    "SCCY4G": BeaufortCountyConfig,
    "SCCE6P": WilliamsburgCountyConfig,
    "GAC3TH": FultonCountyConfig,
    "NCCHLB": ForsythCountyConfig
}
```

## Data Processing Workflows

### Single Document Submission
1. **Document Preparation**: PDF processing and validation
2. **Package Creation**: Initialize package with county config
3. **Document Upload**: File upload with metadata
4. **Party Addition**: Add grantors/grantees with validation
5. **Legal Description**: Add property legal description
6. **Validation**: Pre-submission validation checks
7. **Submission**: Final package submission to county
8. **Status Tracking**: Monitor recording status

### Batch Processing Workflow
1. **Excel Import**: Load and validate Excel data
2. **County Detection**: Determine county config for each row
3. **Document Splitting**: Separate DEED and MORTGAGE documents
4. **Package Generation**: Create packages for each transaction
5. **Batch Upload**: Submit multiple packages with progress tracking
6. **Error Handling**: Individual package error management
7. **Results Reporting**: Comprehensive batch results summary

## Error Handling

### API Error Management
- **HTTP Status Codes**: Proper interpretation and user-friendly messages
- **Validation Errors**: Field-level error reporting with corrections
- **Network Errors**: Retry logic with exponential backoff
- **Authentication Errors**: Automatic re-authentication attempts

### Data Validation
- **Field Validation**: County-specific field format requirements
- **Document Validation**: File format and content validation
- **Party Validation**: Name and address format validation
- **Legal Description**: Property description format validation

### Batch Processing Errors
- **Row-Level Errors**: Individual row error tracking
- **Partial Success**: Continue processing on individual failures
- **Error Reporting**: Detailed error logs with Excel row references
- **Recovery Options**: Re-submit failed packages with corrections

## Performance Considerations

### API Optimization
- **Connection Pooling**: Reuse HTTP connections for multiple requests
- **Batch Operations**: Group related API calls where possible
- **Caching**: Cache county configurations and session tokens
- **Parallel Processing**: Multi-threaded document uploads

### Memory Management
- **Streaming Uploads**: Large document chunked uploading
- **Data Streaming**: Process Excel data row-by-row
- **Resource Cleanup**: Proper file handle and connection cleanup
- **Memory Monitoring**: Track memory usage during batch operations

## Security Considerations

### Authentication
- **Secure Storage**: Credentials stored securely (not in code)
- **Session Management**: Proper session lifecycle management
- **Token Expiration**: Automatic token refresh handling
- **Environment Separation**: QA/Production credential isolation

### Data Protection
- **Sensitive Data**: Proper handling of legal document content
- **Audit Trail**: Comprehensive logging of all operations
- **Error Sanitization**: Remove sensitive data from error messages
- **File Security**: Secure temporary file handling

## Integration Points

### Document Processor Integration
- **PDF Splitting**: Automatic DEED/MORTGAGE document separation
- **File Validation**: Document format and content validation
- **Metadata Extraction**: Automatic document property detection

### UI Integration
- **Progress Reporting**: Real-time batch processing updates
- **Error Display**: User-friendly error messages and corrections
- **Configuration UI**: County selection and settings management
- **Preview Functionality**: Batch preview before submission

### External Dependencies
- **Requests Library**: HTTP client for API communication
- **Pandas**: Excel data processing and manipulation
- **PyQt6**: Threading and signal/slot communication
- **OpenPyXL**: Excel file reading and writing

## Development Guidelines

### Adding New Counties
1. **Create County Config**: Inherit from `CountyConfig` base class
2. **Define Document Types**: Map county-specific document type codes
3. **Implement Validation**: Add county-specific validation rules
4. **Register Configuration**: Add to `COUNTY_CONFIGS` registry
5. **Test Integration**: Validate with county-specific test data

### API Enhancement
- **Version Management**: Support API version upgrades
- **New Endpoints**: Add support for new Simplifile features
- **Error Handling**: Enhance error interpretation and recovery
- **Performance**: Optimize API call patterns and caching

### Configuration Management
- **Environment Variables**: Use environment variables for sensitive config
- **Config Files**: Support external configuration files
- **Runtime Configuration**: Dynamic configuration updates
- **Validation**: Comprehensive configuration validation

## Testing Strategy

### Unit Testing
- **API Client**: Mock API responses for isolated testing
- **County Configs**: Validate all county-specific rules
- **Data Models**: Test data validation and transformation
- **Excel Processing**: Test various Excel formats and edge cases

### Integration Testing
- **API Integration**: Test against Simplifile QA environment
- **End-to-End**: Complete workflow testing with sample data
- **Error Scenarios**: Test error handling and recovery
- **Performance**: Load testing with large batch operations

### Data Validation Testing
- **County Rules**: Validate all county-specific validation rules
- **Document Types**: Test all supported document type mappings
- **Party Validation**: Test name and address validation rules
- **Excel Formats**: Test various Excel column layouts and formats