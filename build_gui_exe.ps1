$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecFile = Join-Path $ProjectRoot "bom-monitor-builder-gui.spec"
$BuildDirectory = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "build-gui"))
$DistDirectory = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
$Executable = Join-Path $DistDirectory "bom-monitor-builder-gui.exe"

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Virtual environment Python was not found: $PythonExe"
}
if (-not (Test-Path -LiteralPath $SpecFile -PathType Leaf)) {
    throw "PyInstaller spec was not found: $SpecFile"
}

& $PythonExe --version
if ($LASTEXITCODE -ne 0) {
    throw "The virtual environment Python could not start."
}
$BasePrefix = (& $PythonExe -c "import sys; print(sys.base_prefix)").Trim()
$SourceTclRoot = Join-Path $BasePrefix "tcl"
$TclSource = Get-ChildItem -LiteralPath $SourceTclRoot -Directory -Filter "tcl*" |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "init.tcl") -PathType Leaf } |
    Select-Object -First 1 -ExpandProperty FullName
$TkSource = Get-ChildItem -LiteralPath $SourceTclRoot -Directory -Filter "tk*" |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "tk.tcl") -PathType Leaf } |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $TclSource -or -not $TkSource) {
    throw "Tcl/Tk script directories could not be found under $SourceTclRoot."
}
$TclData = Join-Path $ProjectRoot ".venv\tcl"
New-Item -ItemType Directory -Force -Path $TclData | Out-Null
Copy-Item -LiteralPath $TclSource -Destination $TclData -Recurse -Force
Copy-Item -LiteralPath $TkSource -Destination $TclData -Recurse -Force
$TclLibrary = Join-Path $TclData (Split-Path $TclSource -Leaf)
$TkLibrary = Join-Path $TclData (Split-Path $TkSource -Leaf)
if (-not (Test-Path -LiteralPath (Join-Path $TclLibrary "init.tcl") -PathType Leaf)) {
    throw "Tcl runtime copy is incomplete: $TclLibrary"
}
if (-not (Test-Path -LiteralPath (Join-Path $TkLibrary "tk.tcl") -PathType Leaf)) {
    throw "Tk runtime copy is incomplete: $TkLibrary"
}
$env:TCL_LIBRARY = $TclLibrary
$env:TK_LIBRARY = $TkLibrary
& $PythonExe (Join-Path $ProjectRoot "scripts\check_tkinter_runtime.py") 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Tcl/Tk could not initialize using project-local copies. No GUI EXE was built."
}
& $PythonExe -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing the PyInstaller build dependency into .venv..."
    & $PythonExe -m pip install "pyinstaller>=6.14.2,<7"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller installation failed."
    }
}

$RootPrefix = $ProjectRoot + [System.IO.Path]::DirectorySeparatorChar
foreach ($Target in @($BuildDirectory, $DistDirectory)) {
    if (-not $Target.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to use a path outside the project: $Target"
    }
}
if (Test-Path -LiteralPath $BuildDirectory) {
    Remove-Item -LiteralPath $BuildDirectory -Recurse -Force
}
if (Test-Path -LiteralPath $Executable) {
    Remove-Item -LiteralPath $Executable -Force
}

Push-Location $ProjectRoot
try {
    & $PythonExe -m PyInstaller --noconfirm --clean `
        --workpath $BuildDirectory `
        --distpath $DistDirectory `
        $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "The GUI executable was not created: $Executable"
}
Write-Host "GUI EXE build completed: $Executable"
