# Convert Markdown to HTML for easy PDF conversion
Write-Host "Converting Markdown to HTML for PDF creation..." -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if ZIP exists
$zipFile = "Orbit_Documentation_For_Notion.zip"
if (-not (Test-Path $zipFile)) {
    Write-Host "ERROR: $zipFile not found!" -ForegroundColor Red
    exit 1
}

# Create directories
$tempDir = "temp_docs_extraction"
$htmlDir = "Orbit_Documentation_HTML_For_PDF"

# Clean up previous runs
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
if (Test-Path $htmlDir) { Remove-Item $htmlDir -Recurse -Force }

Write-Host "Extracting documentation ZIP..." -ForegroundColor Yellow
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipFile, $tempDir)

# Create HTML output directory
New-Item -ItemType Directory -Path $htmlDir -Force | Out-Null

Write-Host "Converting MD files to HTML..." -ForegroundColor Yellow
Write-Host ""

# Get all MD files
$mdFiles = Get-ChildItem -Path $tempDir -Recurse -Filter "*.md"
$successCount = 0
$totalCount = $mdFiles.Count

foreach ($file in $mdFiles) {
    $relativePath = $file.FullName.Replace("$PWD\$tempDir\", "")
    $folderPath = Split-Path $relativePath -Parent
    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)

    # Create folder structure in output
    if ($folderPath) {
        $outputFolder = Join-Path $htmlDir $folderPath
        New-Item -ItemType Directory -Path $outputFolder -Force | Out-Null
        $outputFile = Join-Path $outputFolder "$fileName.html"
    } else {
        $outputFile = Join-Path $htmlDir "$fileName.html"
    }

    try {
        # Read markdown content
        $mdContent = Get-Content $file.FullName -Raw -Encoding UTF8

        # Create HTML wrapper with proper styling
        $htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$fileName</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        h1 { border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        blockquote {
            border-left: 4px solid #95a5a6;
            margin: 20px 0;
            padding-left: 20px;
            color: #7f8c8d;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #bdc3c7;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #ecf0f1;
            font-weight: bold;
        }
        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        li {
            margin: 5px 0;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        @media print {
            body { margin: 0; padding: 15px; }
            h1 { page-break-before: always; }
            h1:first-child { page-break-before: avoid; }
        }
    </style>
</head>
<body>
    <div class="markdown-content">
        $($mdContent -replace '\r?\n', '<br>')
    </div>
</body>
</html>
"@

        # Save HTML file
        Set-Content -Path $outputFile -Value $htmlContent -Encoding UTF8

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
    Write-Host "HTML files created in: $htmlDir\" -ForegroundColor Green
    Write-Host ""

    # Create instructions file
    $instructions = @"
# PDF Conversion Instructions

## Files Ready for PDF Conversion:
"@

    Get-ChildItem -Path $htmlDir -Recurse -Filter "*.html" | ForEach-Object {
        $relativePath = $_.FullName.Replace("$PWD\$htmlDir\", "")
        $instructions += "`n- $relativePath"
    }

    $instructions += @"

## How to Convert to PDF:

### Option 1: Browser Print to PDF (Recommended)
1. Open each HTML file in your browser
2. Press Ctrl+P (Print)
3. Select "Save as PDF" as destination
4. Save with the same filename but .pdf extension

### Option 2: Batch Conversion with PowerShell
```powershell
# Install Chrome or Edge for headless PDF generation
# Then run this command for each file:
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --print-to-pdf="output.pdf" "file:///path/to/input.html"
```

### Option 3: Online HTML to PDF Converter
1. Go to html-pdf-converter.com or similar
2. Upload each HTML file
3. Download as PDF

## Next Steps:
1. Convert all HTML files to PDF using your preferred method
2. Upload PDFs to Notion for AI ingestion
3. Delete temporary HTML files when done

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@

    Set-Content -Path "$htmlDir\PDF_CONVERSION_INSTRUCTIONS.md" -Value $instructions

    Write-Host "Created PDF conversion instructions: $htmlDir\PDF_CONVERSION_INSTRUCTIONS.md" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ready for PDF conversion!" -ForegroundColor Green
    Write-Host "Open HTML files in browser and print to PDF" -ForegroundColor Yellow
}

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host ""
Write-Host "HTML conversion complete!" -ForegroundColor Green
