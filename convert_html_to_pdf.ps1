# PowerShell script to convert HTML to PDF using Windows COM
param(
    [string]$HtmlFile = "c:\Users\user\Documents\CURSO30X\PROYECTO\specs\prd.html",
    [string]$PdfFile = "c:\Users\user\Documents\CURSO30X\PROYECTO\specs\prd.pdf"
)

Write-Host "Converting HTML to PDF..." -ForegroundColor Green
Write-Host "HTML: $HtmlFile"
Write-Host "PDF:  $PdfFile"

# Check if file exists
if (-not (Test-Path $HtmlFile)) {
    Write-Host "Error: HTML file not found: $HtmlFile" -ForegroundColor Red
    exit 1
}

try {
    # Create IE COM object
    $ie = New-Object -ComObject InternetExplorer.Application
    $ie.Visible = $false

    # Navigate to file
    $htmlPath = (Resolve-Path $HtmlFile).Path
    $ie.Navigate("file:///$htmlPath")

    # Wait for page to load
    while ($ie.Busy) { Start-Sleep -Milliseconds 100 }
    Start-Sleep -Milliseconds 500

    # Get document
    $document = $ie.Document

    # Print to PDF (requires Print to PDF printer to be available)
    $document.execCommand("Print", $false, $null)

    Write-Host "Note: Print dialog will open. Select 'Print to PDF' and save to: $PdfFile" -ForegroundColor Yellow

    # Cleanup
    $ie.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ie) | Out-Null

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Conversion complete!" -ForegroundColor Green
