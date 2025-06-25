# Installer Conversion Guide: From Standalone .exe to Professional Installer

This guide outlines the complete process for converting the King Cunningham Legal Automation Suite from a PyInstaller standalone executable to a professional installer-based distribution.

## Overview

**Current State**: Single 200-500MB executable built with PyInstaller  
**Target State**: Professional installer with proper Windows integration  
**Estimated Timeline**: 12-16 weeks  
**Complexity Level**: Medium-High  
**Recommended Technology**: Inno Setup

## Phase 1: Preparation and Planning (2-3 weeks)

### 1.1 Dependency Analysis and Mapping

#### Create Comprehensive Dependency Inventory
1. **Python Dependencies** (from requirements.txt):
   ```
   PyQt6==6.6.1
   selenium==4.15.2
   webdriver-manager==4.0.1
   opencv-python==4.8.1.78
   Pillow==10.1.0
   PyMuPDF==1.23.8
   pytesseract==0.3.10
   pyzbar==0.1.9
   requests==2.31.0
   pandas==2.1.3
   openpyxl==3.1.2
   numpy==1.25.2
   pyautogui==0.9.54
   ```

2. **External Tool Dependencies**:
   ```
   Tesseract OCR:
   - Executable: tesseract.exe (~15MB)
   - Language Data: tessdata/ (~50-100MB)
   - Current Path: C:\Program Files\Tesseract-OCR\
   
   Ghostscript:
   - Executable: gswin64c.exe (~20MB)  
   - Libraries: Additional DLLs (~30MB)
   - Current Path: C:\Program Files\gs\gs10.04.0\bin\
   
   Chrome WebDriver:
   - Managed by webdriver-manager
   - Downloads to user cache directory
   - Auto-updating mechanism
   ```

3. **Application Resources**:
   ```
   /resources/
   ├── app_icon.ico
   ├── splash_image.png
   └── spinner.gif
   ```

#### Document Current Architecture
1. **Entry Points**:
   - Main: `src/main.py`
   - Version: Currently v0.0.5 (hardcoded in main.py)
   - Build: `python build.py` → `KC_app.exe`

2. **External Tool Detection**:
   - Current: `get_tesseract_path()` in `src/document_processor/processor.py`
   - Hardcoded Windows paths
   - PyInstaller resource path: `sys._MEIPASS`

### 1.2 Design New Installation Architecture

#### Target Installation Structure
```
Program Files/King Cunningham Legal Suite/
├── bin/
│   ├── KC_app.exe                    # Main application
│   ├── python311.dll                # Python runtime
│   ├── _internal/                    # Python libraries
│   └── version.txt                   # Version tracking
├── tools/
│   ├── tesseract/
│   │   ├── tesseract.exe
│   │   └── tessdata/                 # OCR language models
│   └── ghostscript/
│       ├── gswin64c.exe
│       └── lib/                      # GS libraries
├── resources/
│   ├── app_icon.ico
│   ├── splash_image.png
│   └── spinner.gif
└── config/
    ├── counties.json                 # County configurations
    └── default_settings.json

%APPDATA%/King Cunningham Legal Suite/
├── logs/
│   ├── application.log
│   └── automation_*.log
├── cache/
│   ├── webdrivers/                   # Chrome/Firefox drivers
│   └── temp_files/
├── settings/
│   ├── user_preferences.json
│   └── window_state.json
└── data/
    └── recent_files.json
```

#### Registry Integration Plan
```
HKEY_LOCAL_MACHINE\SOFTWARE\King Cunningham Software\Legal Suite\
├── InstallPath = "C:\Program Files\King Cunningham Legal Suite\"
├── Version = "1.0.0"
├── TesseractPath = "tools\tesseract\tesseract.exe"
└── GhostscriptPath = "tools\ghostscript\gswin64c.exe"

HKEY_CURRENT_USER\SOFTWARE\King Cunningham Software\Legal Suite\
├── FirstRun = true/false
├── LastUpdateCheck = "2024-01-01"
└── UserDataPath = "%APPDATA%\King Cunningham Legal Suite\"
```

### 1.3 Technology Selection and Setup

#### Install Inno Setup
1. Download Inno Setup 6.2.2+ from https://jrsoftware.org/isinfo.php
2. Install Inno Setup Compiler and optional tools:
   - Inno Setup Preprocessor (ISPP)
   - Inno Setup QuickStart Pack
   - Unicode support

#### Create Development Environment
```bash
# Create installer development directory
installer/
├── inno_setup/
│   ├── king_cunningham_setup.iss    # Main installer script
│   ├── custom_pages.iss             # Custom installation pages
│   └── dependencies.iss             # Dependency management
├── resources/
│   ├── installer_icon.ico
│   ├── installer_banner.bmp
│   └── installer_sidebar.bmp
├── dependencies/
│   ├── vcredist_x64.exe             # Visual C++ Redistributable
│   ├── tesseract-ocr-setup.exe     # Tesseract installer
│   └── ghostscript-setup.exe       # Ghostscript installer
└── build_scripts/
    ├── prepare_installer.py
    └── build_installer.bat
```

## Phase 2: Core Code Refactoring (3-4 weeks)

### 2.1 Path Resolution System Overhaul

#### Replace PyInstaller Path Detection
**Current code in multiple files:**
```python
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller bundle
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
```

**New installer-aware path system:**
```python
# New file: src/utils/path_manager.py
import os
import sys
import winreg
from pathlib import Path

class PathManager:
    def __init__(self):
        self._install_path = None
        self._user_data_path = None
        self._detect_installation_type()
    
    def _detect_installation_type(self):
        """Detect if running from installation or development"""
        if getattr(sys, 'frozen', False):
            # Running from installed executable
            self._install_path = Path(sys.executable).parent.parent
            self._load_registry_paths()
        else:
            # Running from development environment
            self._install_path = Path(__file__).parent.parent.parent
            self._user_data_path = Path.home() / "AppData" / "Local" / "KingCunningham_Dev"
    
    def _load_registry_paths(self):
        """Load paths from Windows registry"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\King Cunningham Software\Legal Suite") as key:
                self._install_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
                
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"SOFTWARE\King Cunningham Software\Legal Suite") as key:
                self._user_data_path = Path(winreg.QueryValueEx(key, "UserDataPath")[0])
        except FileNotFoundError:
            # Fallback to executable location
            self._install_path = Path(sys.executable).parent.parent
            self._user_data_path = Path.home() / "AppData" / "Roaming" / "King Cunningham Legal Suite"
    
    def get_resource_path(self, relative_path):
        """Get path to application resource"""
        return self._install_path / "resources" / relative_path
    
    def get_tool_path(self, tool_name):
        """Get path to external tool"""
        tool_paths = {
            "tesseract": "tools/tesseract/tesseract.exe",
            "ghostscript": "tools/ghostscript/gswin64c.exe"
        }
        if tool_name in tool_paths:
            return self._install_path / tool_paths[tool_name]
        raise ValueError(f"Unknown tool: {tool_name}")
    
    def get_user_data_path(self, relative_path=""):
        """Get path to user data directory"""
        path = self._user_data_path / relative_path
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_cache_path(self, relative_path=""):
        """Get path to cache directory"""
        return self.get_user_data_path("cache" / relative_path)
    
    def get_log_path(self, log_name="application.log"):
        """Get path to log file"""
        return self.get_user_data_path("logs" / log_name)

# Global path manager instance
path_manager = PathManager()
```

#### Update All Path References
1. **Document Processor** (`src/document_processor/processor.py`):
   ```python
   # Replace get_tesseract_path() function
   def get_tesseract_path():
       from ..utils.path_manager import path_manager
       return str(path_manager.get_tool_path("tesseract"))
   ```

2. **Main Application** (`src/main.py`):
   ```python
   # Replace resource loading
   from src.utils.path_manager import path_manager
   
   splash_image_path = path_manager.get_resource_path("splash_image.png")
   app_icon_path = path_manager.get_resource_path("app_icon.ico")
   ```

3. **All UI Modules**: Update resource loading to use new path manager

### 2.2 Configuration Management System

#### Create Settings Manager
```python
# New file: src/utils/settings_manager.py
import json
import winreg
from pathlib import Path
from .path_manager import path_manager

class SettingsManager:
    def __init__(self):
        self.settings_file = path_manager.get_user_data_path("settings/user_preferences.json")
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Load settings from JSON file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._get_default_settings()
    
    def _get_default_settings(self):
        """Get default application settings"""
        return {
            "window_state": {
                "width": 1200,
                "height": 800,
                "maximized": False
            },
            "default_directories": {
                "excel_files": str(Path.home() / "Documents"),
                "output_files": str(Path.home() / "Documents"),
                "pdf_files": str(Path.home() / "Documents")
            },
            "automation_preferences": {
                "default_browser": "Chrome",
                "batch_size": 50,
                "auto_save_progress": True
            },
            "ui_preferences": {
                "theme": "dark",
                "show_tooltips": True,
                "confirm_deletions": True
            }
        }
    
    def save_settings(self):
        """Save settings to JSON file"""
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get(self, key_path, default=None):
        """Get setting value using dot notation (e.g., 'window_state.width')"""
        keys = key_path.split('.')
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        """Set setting value using dot notation"""
        keys = key_path.split('.')
        setting = self.settings
        for key in keys[:-1]:
            if key not in setting:
                setting[key] = {}
            setting = setting[key]
        setting[keys[-1]] = value
        self.save_settings()

# Global settings manager
settings_manager = SettingsManager()
```

### 2.3 Logging System Implementation

#### Create Centralized Logging
```python
# New file: src/utils/logging_manager.py
import logging
import logging.handlers
from datetime import datetime
from .path_manager import path_manager

class LoggingManager:
    def __init__(self):
        self.log_dir = path_manager.get_user_data_path("logs")
        self.setup_logging()
    
    def setup_logging(self):
        """Configure application logging"""
        # Main application logger
        self.app_logger = logging.getLogger('king_cunningham')
        self.app_logger.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "application.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING)
        
        # Add handlers
        self.app_logger.addHandler(file_handler)
        self.app_logger.addHandler(console_handler)
    
    def get_logger(self, name):
        """Get logger for specific module"""
        return logging.getLogger(f'king_cunningham.{name}')
    
    def log_automation_session(self, module_name, session_data):
        """Log automation session details"""
        session_logger = logging.getLogger(f'king_cunningham.automation.{module_name}')
        session_file = self.log_dir / f"automation_{module_name}_{datetime.now().strftime('%Y%m%d')}.log"
        
        session_handler = logging.FileHandler(session_file)
        session_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        session_logger.addHandler(session_handler)
        session_logger.info(f"Session started: {session_data}")

# Global logging manager
logging_manager = LoggingManager()
```

## Phase 3: Installer Development (4-6 weeks)

### 3.1 Basic Inno Setup Script

#### Main Installer Script
```pascal
; File: installer/inno_setup/king_cunningham_setup.iss
#define MyAppName "King Cunningham Legal Suite"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "King Cunningham Software"
#define MyAppURL "https://www.kingcunningham.com"
#define MyAppExeName "KC_app.exe"
#define MyAppID "{{8D5B5F91-8B4A-4B4F-9C5A-1234567890AB}"

[Setup]
AppId={#MyAppID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=license.txt
InfoBeforeFile=readme.txt
OutputDir=output
OutputBaseFilename=KingCunninghamLegalSuite_Setup_v{#MyAppVersion}
SetupIconFile=resources\installer_icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardImageFile=resources\installer_sidebar.bmp
WizardSmallImageFile=resources\installer_banner.bmp
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\resources\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files
Source: "build\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "build\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

; External tools
Source: "dependencies\tesseract\*"; DestDir: "{app}\tools\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dependencies\ghostscript\*"; DestDir: "{app}\tools\ghostscript"; Flags: ignoreversion recursesubdirs createallsubdirs

; Visual C++ Redistributable
Source: "dependencies\vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Registry]
; Application registration
Root: HKLM; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}\"
Root: HKLM; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: HKLM; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: string; ValueName: "TesseractPath"; ValueData: "{app}\tools\tesseract\tesseract.exe"
Root: HKLM; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: string; ValueName: "GhostscriptPath"; ValueData: "{app}\tools\ghostscript\gswin64c.exe"

; User-specific settings
Root: HKCU; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: string; ValueName: "UserDataPath"; ValueData: "{userappdata}\King Cunningham Legal Suite\"
Root: HKCU; Subkey: "SOFTWARE\King Cunningham Software\Legal Suite"; ValueType: dword; ValueName: "FirstRun"; ValueData: 1

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\bin\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\bin\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\bin\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Install Visual C++ Redistributable
Filename: "{tmp}\vcredist_x64.exe"; Parameters: "/quiet"; StatusMsg: "Installing Visual C++ Redistributable..."; Check: VCRedistNeedsInstall

; First run of application
Filename: "{app}\bin\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\King Cunningham Legal Suite"

[Code]
function VCRedistNeedsInstall: Boolean;
begin
  // Check if Visual C++ 2019-2022 Redistributable is installed
  Result := not RegKeyExists(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64');
end;

procedure InitializeWizard;
begin
  // Custom initialization code
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  // Pre-installation checks
  Result := '';
end;
```

### 3.2 Dependency Management

#### External Tool Integration
```pascal
; File: installer/inno_setup/dependencies.iss

[Files]
; Tesseract OCR with language data
Source: "dependencies\tesseract-5.3.3\tesseract.exe"; DestDir: "{app}\tools\tesseract"; Flags: ignoreversion
Source: "dependencies\tesseract-5.3.3\tessdata\eng.traineddata"; DestDir: "{app}\tools\tesseract\tessdata"; Flags: ignoreversion
Source: "dependencies\tesseract-5.3.3\tessdata\osd.traineddata"; DestDir: "{app}\tools\tesseract\tessdata"; Flags: ignoreversion

; Ghostscript
Source: "dependencies\ghostscript-10.02.1\bin\gswin64c.exe"; DestDir: "{app}\tools\ghostscript"; Flags: ignoreversion
Source: "dependencies\ghostscript-10.02.1\lib\*"; DestDir: "{app}\tools\ghostscript\lib"; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
function CheckDependencies: Boolean;
var
  Version: String;
begin
  Result := True;
  
  // Check Windows version
  if not (GetWindowsVersion >= $0A000000) then begin
    MsgBox('This application requires Windows 10 version 1809 or later.', mbError, MB_OK);
    Result := False;
  end;
  
  // Check available disk space (500MB minimum)
  if GetSpaceOnDisk(ExpandConstant('{app}')) < 500 * 1024 * 1024 then begin
    MsgBox('At least 500MB of free disk space is required.', mbError, MB_OK);
    Result := False;
  end;
end;
```

### 3.3 Custom Installation Pages

#### License and Configuration Pages
```pascal
; File: installer/inno_setup/custom_pages.iss

var
  ConfigPage: TInputQueryWizardPage;
  ProgressPage: TOutputProgressWizardPage;

procedure InitializeWizard;
begin
  // Create custom configuration page
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Configuration', 'Configure application settings',
    'Please specify configuration options for the application.');
    
  ConfigPage.Add('Default output directory:', False);
  ConfigPage.Values[0] := ExpandConstant('{userdocs}');
  
  ConfigPage.Add('Enable automatic updates:', True);
  ConfigPage.Values[1] := 'True';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = ConfigPage.ID then begin
    // Validate configuration inputs
    if not DirExists(ConfigPage.Values[0]) then begin
      MsgBox('Please specify a valid output directory.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then begin
    // Create initial configuration file
    SaveStringToFile(ExpandConstant('{app}\config\initial_setup.json'),
      Format('{"output_directory": "%s", "auto_updates": %s}',
        [ConfigPage.Values[0], LowerCase(ConfigPage.Values[1])]), False);
  end;
end;
```

### 3.4 Build Automation Scripts

#### Python Build Preparation Script
```python
# File: installer/build_scripts/prepare_installer.py
import os
import sys
import shutil
import subprocess
from pathlib import Path

def prepare_application_files():
    """Prepare application files for installer"""
    print("Preparing application files...")
    
    # Create build directory structure
    build_dir = Path("installer/build")
    build_dir.mkdir(exist_ok=True)
    
    # Build application with PyInstaller
    spec_path = Path("KC_app.spec")
    subprocess.run([
        sys.executable, "-m", "PyInstaller", 
        "--clean", "--noconfirm", str(spec_path)
    ], check=True)
    
    # Copy built files to installer build directory
    dist_dir = Path("dist")
    shutil.copytree(dist_dir, build_dir / "bin", dirs_exist_ok=True)
    
    # Copy resources
    shutil.copytree("resources", build_dir / "resources", dirs_exist_ok=True)
    
    # Create config directory with default files
    config_dir = build_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Copy county configurations
    import json
    from src.simplifile.county_config import COUNTY_CONFIGS
    
    counties_data = {}
    for code, config_class in COUNTY_CONFIGS.items():
        config = config_class()
        counties_data[code] = {
            "name": config.county_name,
            "state": config.state,
            "deed_document_type": config.DEED_DOCUMENT_TYPE,
            "mortgage_document_type": config.MORTGAGE_DOCUMENT_TYPE
        }
    
    with open(config_dir / "counties.json", "w") as f:
        json.dump(counties_data, f, indent=2)

def download_dependencies():
    """Download and prepare external dependencies"""
    print("Downloading external dependencies...")
    
    deps_dir = Path("installer/dependencies")
    deps_dir.mkdir(exist_ok=True)
    
    # Download Tesseract OCR
    tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    tesseract_installer = deps_dir / "tesseract-ocr-setup.exe"
    
    if not tesseract_installer.exists():
        print("Downloading Tesseract OCR...")
        import urllib.request
        urllib.request.urlretrieve(tesseract_url, tesseract_installer)
    
    # Extract Tesseract files (would need 7-zip or similar)
    # For now, assume manual extraction to dependencies/tesseract/
    
    # Download Visual C++ Redistributable
    vcredist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    vcredist_path = deps_dir / "vcredist_x64.exe"
    
    if not vcredist_path.exists():
        print("Downloading Visual C++ Redistributable...")
        urllib.request.urlretrieve(vcredist_url, vcredist_path)

def create_installer():
    """Build the installer using Inno Setup"""
    print("Building installer...")
    
    inno_setup_compiler = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")
    if not inno_setup_compiler.exists():
        print("Error: Inno Setup not found. Please install Inno Setup.")
        return False
    
    script_path = Path("installer/inno_setup/king_cunningham_setup.iss")
    subprocess.run([str(inno_setup_compiler), str(script_path)], check=True)
    
    print("Installer created successfully!")
    return True

if __name__ == "__main__":
    try:
        prepare_application_files()
        download_dependencies()
        create_installer()
        print("Build process completed successfully!")
    except Exception as e:
        print(f"Build process failed: {e}")
        sys.exit(1)
```

#### Batch Build Script
```batch
REM File: installer/build_scripts/build_installer.bat
@echo off
echo Building King Cunningham Legal Suite Installer...

REM Set environment variables
set PYTHON_PATH=python
set PROJECT_ROOT=%~dp0..\..

REM Change to project root directory
cd /d "%PROJECT_ROOT%"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install/update build dependencies
echo Installing build dependencies...
%PYTHON_PATH% -m pip install --upgrade pip
%PYTHON_PATH% -m pip install -r requirements.txt
%PYTHON_PATH% -m pip install pyinstaller

REM Run the installer preparation script
echo Preparing installer...
%PYTHON_PATH% installer\build_scripts\prepare_installer.py

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo Build completed successfully!
echo Installer can be found in: installer\inno_setup\output\
pause
```

## Phase 4: Testing and Deployment (2-4 weeks)

### 4.1 Testing Strategy

#### Automated Testing Script
```python
# File: tests/installer_tests.py
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

class InstallerTests(unittest.TestCase):
    
    def setUp(self):
        self.test_install_dir = Path(tempfile.mkdtemp())
        self.installer_path = Path("installer/inno_setup/output/KingCunninghamLegalSuite_Setup_v1.0.0.exe")
    
    def test_silent_installation(self):
        """Test silent installation"""
        if not self.installer_path.exists():
            self.skipTest("Installer not found")
        
        # Run silent installation
        result = subprocess.run([
            str(self.installer_path),
            "/SILENT",
            f"/DIR={self.test_install_dir}"
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, "Silent installation failed")
        
        # Verify installation
        self.assertTrue((self.test_install_dir / "bin" / "KC_app.exe").exists())
        self.assertTrue((self.test_install_dir / "tools" / "tesseract" / "tesseract.exe").exists())
        self.assertTrue((self.test_install_dir / "resources").exists())
    
    def test_registry_entries(self):
        """Test registry entries after installation"""
        import winreg
        
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\King Cunningham Software\Legal Suite") as key:
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                version = winreg.QueryValueEx(key, "Version")[0]
                
                self.assertTrue(Path(install_path).exists())
                self.assertEqual(version, "1.0.0")
        except FileNotFoundError:
            self.fail("Registry entries not created")
    
    def test_application_startup(self):
        """Test application starts correctly after installation"""
        app_path = self.test_install_dir / "bin" / "KC_app.exe"
        
        if not app_path.exists():
            self.skipTest("Application not installed")
        
        # Start application and check if it responds
        proc = subprocess.Popen([str(app_path)], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        
        # Give it time to start
        import time
        time.sleep(5)
        
        # Check if process is running
        self.assertIsNone(proc.poll(), "Application failed to start")
        
        # Terminate the process
        proc.terminate()
        proc.wait(timeout=10)
    
    def tearDown(self):
        # Cleanup test installation
        if self.test_install_dir.exists():
            import shutil
            shutil.rmtree(self.test_install_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
```

#### Manual Testing Checklist
```markdown
# Manual Testing Checklist

## Pre-Installation
- [ ] Windows 10/11 compatibility check
- [ ] Administrator privileges verification
- [ ] Disk space availability (500MB+)
- [ ] Visual C++ Redistributable detection

## Installation Process
- [ ] Installer launches correctly
- [ ] License agreement display
- [ ] Custom configuration page functionality
- [ ] Directory selection works
- [ ] Progress indication during installation
- [ ] External tool installation (Tesseract, Ghostscript)
- [ ] Registry entries created correctly
- [ ] Desktop/Start Menu shortcuts created

## Post-Installation
- [ ] Application launches successfully
- [ ] All modules load correctly
- [ ] External tools detected properly (OCR, PDF processing)
- [ ] File dialogs work correctly
- [ ] Settings persistence (after restart)
- [ ] Log files created in correct location
- [ ] User data directory structure created

## Functionality Testing
- [ ] Document processor works with installed Tesseract
- [ ] PDF processing works with installed Ghostscript
- [ ] Web automation WebDriver management
- [ ] Excel file processing
- [ ] All UI modules functional
- [ ] Error handling and user feedback

## Uninstallation
- [ ] Uninstaller launches from Control Panel
- [ ] Application files removed completely
- [ ] Registry entries cleaned up
- [ ] User data handling (keep/remove option)
- [ ] Desktop/Start Menu shortcuts removed
- [ ] External tools handling during uninstall
```

### 4.2 Version Management and Updates

#### Update Mechanism Redesign
```python
# File: src/utils/update_manager.py
import json
import requests
import subprocess
import tempfile
from pathlib import Path
from .path_manager import path_manager
from .settings_manager import settings_manager

class UpdateManager:
    def __init__(self):
        self.github_api_url = "https://api.github.com/repos/yourusername/king-cunningham-app/releases"
        self.current_version = self._get_current_version()
    
    def _get_current_version(self):
        """Get currently installed version"""
        try:
            version_file = path_manager._install_path / "bin" / "version.txt"
            if version_file.exists():
                return version_file.read_text().strip()
        except Exception:
            pass
        return "1.0.0"  # Default version
    
    def check_for_updates(self):
        """Check for available updates"""
        try:
            response = requests.get(self.github_api_url, timeout=10)
            response.raise_for_status()
            releases = response.json()
            
            if releases:
                latest_release = releases[0]
                latest_version = latest_release["tag_name"].lstrip("v")
                
                if self._is_newer_version(latest_version, self.current_version):
                    return {
                        "available": True,
                        "version": latest_version,
                        "download_url": self._get_installer_download_url(latest_release),
                        "release_notes": latest_release.get("body", "")
                    }
            
            return {"available": False}
            
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _is_newer_version(self, latest, current):
        """Compare version strings"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        return version_tuple(latest) > version_tuple(current)
    
    def _get_installer_download_url(self, release):
        """Get installer download URL from release assets"""
        for asset in release.get("assets", []):
            if asset["name"].endswith("_Setup.exe"):
                return asset["browser_download_url"]
        return None
    
    def download_and_install_update(self, download_url):
        """Download and install update"""
        try:
            # Download installer to temp directory
            with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                
                temp_installer_path = temp_file.name
            
            # Launch installer with update parameters
            subprocess.Popen([
                temp_installer_path,
                "/SILENT",
                "/SUPPRESSMSGBOXES",
                "/RESTARTEXITCODE=3010"
            ])
            
            # Exit current application to allow update
            import sys
            sys.exit(0)
            
        except Exception as e:
            raise Exception(f"Update failed: {e}")

# Integration with main application
class UpdateChecker:
    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.update_manager = UpdateManager()
    
    def check_for_updates_async(self):
        """Check for updates in background thread"""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class UpdateCheckWorker(QThread):
            update_available = pyqtSignal(dict)
            
            def __init__(self, update_manager):
                super().__init__()
                self.update_manager = update_manager
            
            def run(self):
                result = self.update_manager.check_for_updates()
                self.update_available.emit(result)
        
        self.worker = UpdateCheckWorker(self.update_manager)
        self.worker.update_available.connect(self.handle_update_check_result)
        self.worker.start()
    
    def handle_update_check_result(self, result):
        """Handle update check result"""
        if result.get("available"):
            self.show_update_dialog(result)
        elif result.get("error"):
            # Log error but don't show to user unless explicitly checking
            pass
    
    def show_update_dialog(self, update_info):
        """Show update available dialog"""
        from PyQt6.QtWidgets import QMessageBox, QPushButton
        
        msg = QMessageBox(self.parent_window)
        msg.setWindowTitle("Update Available")
        msg.setText(f"Version {update_info['version']} is available.")
        msg.setDetailedText(update_info.get('release_notes', ''))
        
        update_btn = msg.addButton("Update Now", QMessageBox.ButtonRole.AcceptRole)
        later_btn = msg.addButton("Update Later", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == update_btn:
            self.start_update(update_info['download_url'])
    
    def start_update(self, download_url):
        """Start the update process"""
        try:
            self.update_manager.download_and_install_update(download_url)
        except Exception as e:
            QMessageBox.critical(self.parent_window, "Update Error", 
                               f"Failed to install update: {e}")
```

### 4.3 Documentation and Distribution

#### User Installation Guide
```markdown
# King Cunningham Legal Suite - Installation Guide

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 version 1809 (October 2018 Update) or later
- **Processor**: Intel/AMD x64 processor
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 500 MB available disk space
- **Additional**: Administrator privileges for installation

### Recommended Requirements
- **Operating System**: Windows 11
- **Memory**: 8 GB RAM or more
- **Storage**: 1 GB available disk space for optimal performance
- **Network**: Internet connection for updates and web automation features

## Installation Process

### Step 1: Download
1. Download the latest installer from the official website
2. File name: `KingCunninghamLegalSuite_Setup_v1.0.0.exe`
3. Verify file integrity (checksums available on download page)

### Step 2: Run Installer
1. Right-click the installer and select "Run as administrator"
2. If Windows SmartScreen appears, click "More info" then "Run anyway"
3. Follow the installation wizard steps:
   - Accept the license agreement
   - Choose installation directory (default recommended)
   - Configure initial settings
   - Wait for installation to complete

### Step 3: First Launch
1. Launch the application from Desktop shortcut or Start Menu
2. The application will perform first-time setup
3. Verify all modules load correctly
4. Check that external tools (OCR, PDF processing) are working

## Post-Installation Configuration

### User Data Locations
- **Application Files**: `C:\Program Files\King Cunningham Legal Suite\`
- **User Settings**: `%APPDATA%\King Cunningham Legal Suite\settings\`
- **Log Files**: `%APPDATA%\King Cunningham Legal Suite\logs\`
- **Cache Files**: `%APPDATA%\King Cunningham Legal Suite\cache\`

### Initial Configuration
1. Set default directories for input/output files
2. Configure automation preferences
3. Test each module with sample data
4. Review and adjust settings as needed

## Troubleshooting

### Common Installation Issues

**Issue**: "Installation failed - insufficient privileges"
**Solution**: Run installer as administrator

**Issue**: "Missing Visual C++ Redistributable"
**Solution**: The installer should install this automatically. If not, download from Microsoft.

**Issue**: "Tesseract OCR not found"
**Solution**: 
1. Verify installation completed successfully
2. Check that `C:\Program Files\King Cunningham Legal Suite\tools\tesseract\` exists
3. Reinstall if necessary

### Getting Support
- **Documentation**: Check the built-in help system
- **Log Files**: Check log files in `%APPDATA%\King Cunningham Legal Suite\logs\`
- **Support**: Contact support@kingcunningham.com with log files attached
```

#### Developer Deployment Guide
```markdown
# Developer Deployment Guide

## Build Environment Setup

### Prerequisites
1. **Python 3.11+** with pip
2. **Inno Setup 6.2.2+** installed
3. **Git** for version control
4. **Visual Studio Build Tools** (for some dependencies)

### Build Process

#### 1. Prepare Build Environment
```bash
# Clone repository
git clone https://github.com/yourusername/king-cunningham-app.git
cd king-cunningham-app

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller
```

#### 2. Build Application
```bash
# Run the automated build script
installer\build_scripts\build_installer.bat
```

#### 3. Manual Build Steps (if needed)
```bash
# Build with PyInstaller
python -m PyInstaller --clean --noconfirm KC_app.spec

# Prepare installer files
python installer\build_scripts\prepare_installer.py

# Compile installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\inno_setup\king_cunningham_setup.iss
```

## Release Process

### Version Management
1. Update version in `src/main.py`
2. Update version in installer script `king_cunningham_setup.iss`
3. Create version tag in git
4. Update CHANGELOG.md

### Testing Checklist
- [ ] Build completes without errors
- [ ] Silent installation works
- [ ] All modules function correctly
- [ ] External tools work properly
- [ ] Uninstallation is clean
- [ ] Update mechanism works

### Distribution
1. Upload installer to release hosting
2. Update website download links
3. Generate and publish checksums
4. Update documentation
5. Announce release
```

## Summary and Next Steps

This comprehensive guide provides a complete roadmap for converting your King Cunningham Legal Suite from a standalone executable to a professional installer-based distribution. The conversion will significantly improve user experience while maintaining all current functionality.

### Key Benefits of This Approach:
- **Professional Installation**: Standard Windows installer experience
- **Better Resource Management**: Efficient handling of external tools
- **Improved Updates**: Proper update mechanism for installed applications
- **User Data Management**: Organized user data and settings storage
- **Enterprise Ready**: Professional deployment suitable for business environments

### Recommended Implementation Order:
1. **Start with Phase 1**: Focus on path management refactoring first
2. **Develop incrementally**: Test each phase thoroughly before proceeding
3. **Maintain compatibility**: Keep the current PyInstaller build working during development
4. **User testing**: Get feedback from actual users during the process

The total estimated timeline of 12-16 weeks is realistic for a high-quality conversion that will serve as a solid foundation for future development and professional distribution.