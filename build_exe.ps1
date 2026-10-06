$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecFile = Join-Path $ProjectRoot "bom-monitor-builder.spec"

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

& $PythonExe -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing the PyInstaller build dependency into .venv..."
    & $PythonExe -m pip install "pyinstaller>=6.14.2,<7"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller installation failed."
    }
}

$BuildDirectory = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "build"))
$DistDirectory = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "dist"))
foreach ($Target in @($BuildDirectory, $DistDirectory)) {
    if (-not $Target.StartsWith($ProjectRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean a path outside the project: $Target"
    }
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}

Push-Location $ProjectRoot
try {
    & $PythonExe -m PyInstaller --noconfirm --clean $SpecFile
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

$Executable = Join-Path $DistDirectory "bom-monitor-builder.exe"
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "The expected executable was not created: $Executable"
}

$RootHelp = & $Executable --help 2>&1
if ($LASTEXITCODE -ne 0 -or ($RootHelp -join "`n") -notmatch "build") {
    throw "The generated executable failed its --help check."
}
$BuildHelp = & $Executable build --help 2>&1
if ($LASTEXITCODE -ne 0 -or ($BuildHelp -join "`n") -notmatch "--input") {
    throw "The generated executable failed its 'build --help' check."
}

Write-Host "EXE build and CLI smoke checks passed: $Executable"
