# Start the demo test service
# Run this in a separate terminal window

Write-Host "Starting Demo Test Service..." -ForegroundColor Green
Write-Host "This service will run on http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Cyan
Write-Host ""

cd pass_through_service
python app.py

