function Show-TreeWithExclusions {
    param (
        [string]$path = ".",
        [string[]]$excludeDirs = @("data", ".venv", ".git", "utils", "build", "dist"),
        [string[]]$excludeExtensions = @(".pyc"),
        [int]$level = 0
    )

    $items = Get-ChildItem -Path $path -Force

    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            if ($excludeDirs -notcontains $item.Name) {
                Write-Output ("  " * $level + "+ " + $item.Name)
                Show-TreeWithExclusions -path $item.FullName -excludeDirs $excludeDirs -excludeExtensions $excludeExtensions -level ($level + 1)
            }
        } else {
            if ($excludeExtensions -notcontains $item.Extension) {
                Write-Output ("  " * $level + "- " + $item.Name)
            }
        }
    }
}

# Run the function
Show-TreeWithExclusions