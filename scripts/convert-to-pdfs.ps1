# Convert Markdown Documentation to PDFs for Notion
Write-Host "Orbit Documentation to PDF Converter" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if ZIP exists
$zipFile = "Orbit_Documentation_For_Notion.zip"
if (-not (Test-Path $zipFile)) {
    Write-Host "ERROR: $zipFile not found!" -ForegroundColor Red
    Write-Host "Please ensure the ZIP file exists in the current directory." -ForegroundColor Yellow
    exit 1
}

# Create temp directory for extraction
$tempDir = "temp_docs_extraction"
$pdfDir = "Orbit_Documentation_PDFs"

# Clean up previous runs
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
if (Test-Path $pdfDir) { Remove-Item $pdfDir -Recurse -Force }

Write-Host "Extracting documentation ZIP..." -ForegroundColor Yellow
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $tempDir)

Write-Host "Extraction complete!" -ForegroundColor Green
Write-Host ""

# Check for conversion tools
$pandocPath = Get-Command "pandoc" -ErrorAction SilentlyContinue

if (-not $pandocPath) {
    Write-Host "WARNING: Pandoc not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Pandoc:" -ForegroundColor Cyan
    Write-Host "choco install pandoc" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative: Use VS Code Markdown PDF extension" -ForegroundColor Yellow
    Write-Host ""

    # Create manual conversion guide
    $mdFiles = Get-ChildItem -Path $tempDir -Recurse -Filter "*.md"
    $guideContent = "Manual PDF Conversion Guide`n`nFiles to convert:`n"

    foreach ($file in $mdFiles) {
        $relativePath = $file.FullName.Replace("$PWD\$tempDir\", "")
        $guideContent += "- $relativePath`n"
    }

    Set-Content -Path "Manual_Conversion_Guide.md" -Value $guideContent
    Write-Host "Created Manual_Conversion_Guide.md with file list" -ForegroundColor Green

    # Clean up
    Remove-Item $tempDir -Recurse -Force
    exit 0
}

# Create PDF output directory
New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null

Write-Host "Converting MD files to PDFs using Pandoc..." -ForegroundColor Yellow
Write-Host ""

# Convert all MD files
$mdFiles = Get-ChildItem -Path $tempDir -Recurse -Filter "*.md"
$successCount = 0
$totalCount = $mdFiles.Count

foreach ($file in $mdFiles) {
    $relativePath = $file.FullName.Replace("$PWD\$tempDir\", "")
    $folderPath = Split-Path $relativePath -Parent
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)

    # Create folder structure in output
    if ($folderPath) {
        $outputFolder = Join-Path $pdfDir $folderPath
        New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
        $outputFile = Join-Path $outputFolder "$fileName.pdf"
    } else {
        $outputFile = Join-Path $pdfDir "$fileName.pdf"
    }

    try {
        # Convert using pandoc
        & pandoc $file.FullName -o $outputFile --pdf-engine=wkhtmltopdf

        if (Test-Path $outputFile) {
            Write-Host "Converted: $relativePath" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "Failed: $relativePath" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error converting $relativePath" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Conversion Summary:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "Successfully converted: $successCount/$totalCount files" -ForegroundColor Green

if ($successCount -gt 0) {
    Write-Host ""
    Write-Host "PDFs created in: $pdfDir\" -ForegroundColor Green
    Write-Host ""
    Write-Host "Folder Structure:" -ForegroundColor Yellow
    Get-ChildItem -Path $pdfDir -Recurse -Filter "*.pdf" | ForEach-Object {
        $relativePath = $_.FullName.Replace("$PWD\$pdfDir\", "")
        Write-Host "   $relativePath" -ForegroundColor White
    }

    # Create final ZIP for Notion
    $pdfZipFile = "Orbit_Documentation_PDFs_For_Notion.zip"
    if (Test-Path $pdfZipFile) { Remove-Item $pdfZipFile -Force }

    Write-Host ""
    Write-Host "Creating PDF ZIP for Notion..." -ForegroundColor Yellow
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($pdfDir, $pdfZipFile)

    $zipSize = (Get-Item $pdfZipFile).Length
    $zipSizeKB = [math]::Round($zipSize/1KB, 2)
    Write-Host "Created: $pdfZipFile ($zipSizeKB KB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready for Notion AI ingestion!" -ForegroundColor Green
    Write-Host "Upload $pdfZipFile to your Notion workspace" -ForegroundColor Cyan
}

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "Conversion complete!" -ForegroundColor Green