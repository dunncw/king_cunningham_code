# UI Module

This module provides the complete user interface for the legal automation application using PyQt6. It features a modern dark theme, modular design with specialized interfaces for each automation type, and comprehensive progress tracking and error handling.

## Architecture

### Core Components

#### MainWindow
- **Location**: `main_window.py:20`
- **Purpose**: Central UI coordinator and application entry point
- **Key Features**:
  - QStackedWidget-based navigation system
  - Module launcher with card-based interface
  - Dark theme with modern styling
  - Thread management for background operations

#### Specialized UI Modules

##### DocumentProcessorUI
- **Location**: `document_processor_ui.py:15`
- **Purpose**: Interface for OCR and document processing operations
- **Features**:
  - PDF file selection and validation
  - Progress tracking for OCR operations
  - Barcode detection status display
  - Error reporting with file context

##### SimplifileUI
- **Location**: `simplifile_ui.py:20`
- **Purpose**: Interface for Simplifile electronic recording
- **Features**:
  - County selection and configuration
  - Excel file import and validation
  - Batch processing with progress tracking
  - API connection status monitoring

##### WebAutomationUI
- **Location**: `web_automation_ui.py:25`
- **Purpose**: Interface for PT-61 web automation
- **Features**:
  - Browser selection (Chrome, Firefox, Edge)
  - Excel data mapping and validation
  - Automation progress monitoring
  - PDF generation status tracking

##### CRGAutomationUI
- **Location**: `crg_automation_ui.py:20`
- **Purpose**: Interface for Capital IT Files automation
- **Features**:
  - Account number filtering interface
  - Myrtle Beach account identification
  - Download progress monitoring
  - File organization management

##### SCRAAutomationUI
- **Location**: `scra_automation_ui.py:25`
- **Purpose**: Interface for SCRA processing
- **Features**:
  - Name and SSN validation interface
  - Fixed-width format generation
  - Results interpretation display
  - Military status reporting

##### PACERAutomationUI
- **Location**: `pacer_automation_ui.py:20`
- **Purpose**: Interface for PACER bankruptcy searches
- **Features**:
  - PACER credential management
  - SSN-based search configuration
  - Bankruptcy status display
  - Results export functionality

#### BatchPreviewDialog
- **Location**: `batch_preview_dialog.py:15`
- **Purpose**: Preview and validation dialog for batch operations
- **Features**:
  - Data preview with validation status
  - Error highlighting and correction suggestions
  - Batch operation configuration
  - Progress tracking during processing

## UI Design Principles

### Dark Theme Implementation
```python
DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 10pt;
}

QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #666666;
    border-radius: 5px;
    padding: 8px 16px;
    min-height: 25px;
}

QPushButton:hover {
    background-color: #5a5a5a;
    border-color: #888888;
}
"""
```

### Card-Based Layout
- **Module Cards**: Each automation module represented by a descriptive card
- **Visual Hierarchy**: Clear visual separation between different functions
- **Hover Effects**: Interactive feedback for better user experience
- **Consistent Spacing**: Uniform spacing and alignment throughout interface

### Responsive Design
- **Flexible Layouts**: Layouts adapt to different window sizes
- **Minimum Sizes**: Appropriate minimum window sizes for usability
- **Scalable Elements**: UI elements scale appropriately with system settings
- **Accessibility**: Support for system accessibility features

## Navigation Architecture

### QStackedWidget Structure
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Add all module UIs to stack
        self.add_module_pages()
        
    def add_module_pages(self):
        """Add all automation module UIs to the stack"""
        self.main_page = self.create_main_page()
        self.document_processor_ui = DocumentProcessorUI()
        self.simplifile_ui = SimplifileUI()
        # ... additional modules
```

### Module Navigation
- **Main Menu**: Central launcher with module selection
- **Back Navigation**: Consistent back button functionality
- **Module Switching**: Direct switching between related modules
- **Context Preservation**: Maintain state when switching between modules

## Threading Architecture

### Background Processing
- **QThread Integration**: All long-running operations use QThread
- **Worker Objects**: Separate worker objects for each automation type
- **Signal/Slot Communication**: Thread-safe communication with UI
- **Progress Reporting**: Real-time progress updates via signals

### Thread Management Pattern
```python
class AutomationUIBase(QWidget):
    def start_automation(self):
        """Generic pattern for starting background automation"""
        self.worker = AutomationWorker(self.get_configuration())
        self.thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.automation_finished)
        self.worker.error.connect(self.handle_error)
        
        # Start thread
        self.thread.started.connect(self.worker.run)
        self.thread.start()
```

### UI Responsiveness
- **Non-Blocking Operations**: UI remains responsive during processing
- **Progress Indicators**: Clear progress indication for all operations
- **Cancellation Support**: Ability to cancel long-running operations
- **Status Updates**: Comprehensive status reporting throughout operations

## Error Handling and User Feedback

### Error Display Strategy
```python
def display_error(self, title, message, details=None):
    """Standardized error display with optional details"""
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.setWindowTitle(title)
    error_dialog.setText(message)
    
    if details:
        error_dialog.setDetailedText(details)
    
    error_dialog.exec()
```

### Progress Reporting
- **Progress Bars**: Visual progress indication for all operations
- **Status Labels**: Textual status updates with operation details
- **Log Display**: Optional detailed log display for advanced users
- **Completion Notifications**: Clear indication of operation completion

### Validation Feedback
- **Real-Time Validation**: Immediate feedback on user input
- **Field Highlighting**: Visual indication of validation errors
- **Tooltip Guidance**: Helpful tooltips with correction guidance
- **Batch Validation**: Comprehensive validation for batch operations

## File Management Integration

### File Selection Interfaces
```python
def select_excel_file(self):
    """Standard Excel file selection dialog"""
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Select Excel File",
        "",
        "Excel Files (*.xlsx *.xls);;All Files (*)"
    )
    return file_path
```

### File Validation
- **Format Validation**: Ensure files meet expected format requirements
- **Content Validation**: Validate file contents before processing
- **Access Validation**: Verify file access permissions
- **Size Validation**: Check file sizes for processing limitations

### Output Management
- **Save Dialogs**: Standardized save dialogs for output files
- **Directory Selection**: Batch output directory selection
- **File Organization**: Automatic organization of output files
- **Naming Conventions**: Consistent file naming across modules

## Configuration Management

### Settings Persistence
```python
class SettingsManager:
    def __init__(self):
        self.settings = QSettings('KingCunningham', 'LegalAutomation')
    
    def save_configuration(self, module, config):
        """Save module-specific configuration"""
        self.settings.beginGroup(module)
        for key, value in config.items():
            self.settings.setValue(key, value)
        self.settings.endGroup()
```

### User Preferences
- **Theme Settings**: User preference for theme selection
- **Default Directories**: Remember commonly used directories
- **Module Preferences**: Save preferences for each automation module
- **Window State**: Remember window size and position

### Configuration Validation
- **Startup Validation**: Validate configuration on application startup
- **Migration Support**: Handle configuration migration between versions
- **Default Fallbacks**: Provide sensible defaults for missing configuration
- **Error Recovery**: Recover from corrupted configuration files

## Accessibility Features

### Keyboard Navigation
- **Tab Order**: Logical tab order throughout all interfaces
- **Keyboard Shortcuts**: Standard keyboard shortcuts for common operations
- **Access Keys**: Alt key access for menu and button operations
- **Focus Indicators**: Clear visual focus indicators

### Screen Reader Support
- **ARIA Labels**: Appropriate labels for screen reader compatibility
- **Role Definitions**: Proper role definitions for UI elements
- **Status Announcements**: Screen reader announcements for status changes
- **Alternative Text**: Alternative text for visual elements

### Visual Accessibility
- **High Contrast**: High contrast color scheme for better visibility
- **Font Scaling**: Support for system font scaling settings
- **Color Independence**: Information not solely dependent on color
- **Focus Enhancement**: Enhanced focus indicators for better visibility

## Performance Optimization

### UI Responsiveness
- **Lazy Loading**: Load UI components only when needed
- **Event Batching**: Batch frequent events to reduce UI updates
- **Widget Reuse**: Reuse widgets where possible to reduce memory usage
- **Efficient Layouts**: Use efficient layout managers for better performance

### Memory Management
- **Resource Cleanup**: Proper cleanup of resources when switching modules
- **Image Optimization**: Optimize images and icons for memory efficiency
- **Thread Cleanup**: Ensure proper cleanup of background threads
- **Cache Management**: Intelligent caching of frequently used data

## Integration Testing

### UI Component Testing
- **Unit Testing**: Test individual UI components in isolation
- **Integration Testing**: Test UI integration with business logic
- **User Workflow Testing**: Test complete user workflows
- **Error Scenario Testing**: Test error handling and recovery

### Automation Testing
- **Automated UI Testing**: Automated testing of UI interactions
- **Screenshot Testing**: Visual regression testing with screenshots
- **Performance Testing**: UI performance and responsiveness testing
- **Accessibility Testing**: Automated accessibility compliance testing

## Development Guidelines

### Adding New UI Modules
1. **Inherit from Base**: Use common base classes for consistency
2. **Follow Patterns**: Follow established patterns for threading and error handling
3. **Style Compliance**: Ensure compliance with application style guidelines
4. **Accessibility**: Include accessibility features from the start
5. **Testing**: Comprehensive testing of new UI components

### UI Enhancement
- **User Feedback**: Incorporate user feedback for improvements
- **Performance Monitoring**: Monitor UI performance and optimize as needed
- **Accessibility Audits**: Regular accessibility audits and improvements
- **Design Updates**: Keep UI design current with modern standards

### Maintenance Considerations
- **PyQt Updates**: Handle PyQt version updates and API changes
- **Platform Compatibility**: Ensure compatibility across different platforms
- **Theme Maintenance**: Maintain and update theme styling
- **Documentation**: Keep UI documentation current with changes

## Deployment Considerations

### Application Packaging
- **Resource Bundling**: Bundle all UI resources with application
- **Icon Management**: Ensure all icons are properly included
- **Font Handling**: Handle font dependencies for consistent appearance
- **Theme Distribution**: Include all theme assets in distribution

### Platform-Specific Considerations
- **Windows Integration**: Proper Windows integration (taskbar, file associations)
- **macOS Integration**: macOS-specific UI guidelines and integration
- **Linux Integration**: Linux desktop environment integration
- **Cross-Platform Testing**: Test UI across all target platforms

### User Training and Support
- **User Documentation**: Comprehensive user interface documentation
- **Video Tutorials**: Create video tutorials for complex workflows
- **Help System**: Built-in help system with contextual assistance
- **Support Resources**: Provide resources for user support and troubleshooting