# Batch convert HTML files to PDF using browser print functionality
Write-Host "Batch HTML to PDF Converter for Notion" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$htmlDir = "Orbit_Documentation_HTML_For_PDF"
if (-not (Test-Path $htmlDir)) {
    Write-Host "ERROR: HTML directory not found!" -ForegroundColor Red
    Write-Host "Please run convert-to-html-for-pdf.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Create PDF output directory
$pdfDir = "Orbit_Documentation_PDFs_For_Notion"
if (Test-Path $pdfDir) { Remove-Item $pdfDir -Recurse -Force }
New-Item -ItemType Directory -Path $pdfDir -Force | Out-Null

Write-Host "Starting batch PDF conversion..." -ForegroundColor Yellow
Write-Host "This will open each HTML file in your default browser" -ForegroundColor Cyan
Write-Host "You'll need to manually print each to PDF" -ForegroundColor Yellow
Write-Host ""

# Get all HTML files
$htmlFiles = Get-ChildItem -Path $htmlDir -Recurse -Filter "*.html" | Where-Object { $_.Name -ne "PDF_CONVERSION_INSTRUCTIONS.md" }

Write-Host "Found $($htmlFiles.Count) HTML files to convert" -ForegroundColor Green
Write-Host ""

# Create a batch conversion script
$batchScript = @"
# Batch PDF Conversion Script
# Run this script to open all HTML files for PDF conversion

Write-Host "Opening HTML files for PDF conversion..." -ForegroundColor Cyan
Write-Host "For each file that opens:" -ForegroundColor Yellow
Write-Host "1. Press Ctrl+P to print" -ForegroundColor White
Write-Host "2. Select 'Save as PDF'" -ForegroundColor White
Write-Host "3. Save in the PDFs_For_Notion folder with same name" -ForegroundColor White
Write-Host "4. Close the browser tab" -ForegroundColor White
Write-Host ""

"@

$counter = 1
foreach ($file in $htmlFiles) {
    $relativePath = $file.FullName.Replace("$PWD\$htmlDir\", "")
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $folderPath = Split-Path $relativePath -Parent

    # Create folder structure in PDF directory
    if ($folderPath) {
        $outputFolder = Join-Path $pdfDir $folderPath
        New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
    }

    Write-Host "$counter. Opening: $relativePath" -ForegroundColor Green

    # Add to batch script
    $batchScript += "Write-Host 'Opening: $relativePath' -ForegroundColor Green`n"
    $batchScript += "Start-Process '$($file.FullName)'`n"
    $batchScript += "Write-Host 'Press any key to continue to next file...' -ForegroundColor Yellow`n"
    $batchScript += "Read-Host`n`n"

    $counter++
}

# Save batch script
Set-Content -Path "open-html-for-pdf.ps1" -Value $batchScript

Write-Host ""
Write-Host "Created batch script: open-html-for-pdf.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "To convert all files to PDF:" -ForegroundColor Yellow
Write-Host "1. Run: .\open-html-for-pdf.ps1" -ForegroundColor White
Write-Host "2. For each file that opens, press Ctrl+P and save as PDF" -ForegroundColor White
Write-Host "3. Save PDFs in: $pdfDir\" -ForegroundColor White
Write-Host ""
Write-Host "Alternative: Open HTML files manually in browser and print to PDF" -ForegroundColor Cyan

# Create final instructions
$finalInstructions = @"
# Final PDF Conversion Instructions

## Quick Method:
1. Run: .\open-html-for-pdf.ps1
2. For each file: Ctrl+P → Save as PDF → Save in Orbit_Documentation_PDFs_For_Notion\

## Manual Method:
1. Open each HTML file in Orbit_Documentation_HTML_For_PDF\
2. Press Ctrl+P (Print)
3. Select "Save as PDF"
4. Save in Orbit_Documentation_PDFs_For_Notion\ with same folder structure

## After Conversion:
1. Create ZIP of PDF folder: Orbit_Documentation_PDFs_For_Notion.zip
2. Upload ZIP to Notion for AI ingestion
3. Delete temporary HTML files

## Files to Convert:
"@

foreach ($file in $htmlFiles) {
    $relativePath = $file.FullName.Replace("$PWD\$htmlDir\", "")
    $finalInstructions += "`n- $relativePath"
}

Set-Content -Path "FINAL_PDF_INSTRUCTIONS.md" -Value $finalInstructions

Write-Host "Created: FINAL_PDF_INSTRUCTIONS.md" -ForegroundColor Green
Write-Host ""
Write-Host "Ready for PDF conversion!" -ForegroundColor Green
