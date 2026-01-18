# Fetch external HTML and save to file
$response = Invoke-WebRequest -Uri "https://demozone.surpaascompaas.com/surpaas/" -Headers @{"Accept-Encoding"="identity"}
$response.Content | Out-File -FilePath "test_external.html" -Encoding UTF8
Write-Host "HTML saved to test_external.html"
Write-Host "File size: $((Get-Item 'test_external.html').Length) bytes"