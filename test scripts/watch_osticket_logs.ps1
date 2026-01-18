# Watch OS TICKET HANDLER logs only
# Run this in a separate PowerShell window

Get-Content -Path "osticket_handler.log" -Wait -Tail 50

