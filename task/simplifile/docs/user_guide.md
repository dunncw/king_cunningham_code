# Simplifile User Guide

## Getting Started

### 1. API Token Setup

Enter your Simplifile API token in the "API Token" field. Once saved, your API token is stored permanently on your computer and you won't need to enter it again.

#### Getting an API Key
[Instructions for obtaining API key from Simplifile]

Click **Save** to store your credentials locally, then click **Test** to verify the connection works.

### 2. Select Workflow

Choose your workflow from the dropdown menu. Each workflow handles different document types and counties. Click the **📖 Docs** button to view detailed documentation for your selected workflow.

### 3. Input Files

The file inputs will change based on your selected workflow. Browse and select the required files.

### 4. Process Documents

1. Click **Validate** to check your Excel data and file paths
2. If validation passes, the **Process** button will be enabled
3. Click **Process** to upload documents to Simplifile
4. Monitor the output log for progress and results

## References

### Configuration File Location

When you click **Save**, your API token is stored locally at:

```
%USERPROFILE%\.simplifile3_config.json
```

On Windows, this typically resolves to:
```
C:\Users\[USERNAME]\.simplifile3_config.json
```