$body = @{
    session_id = "session_test_xyz"
    user_id = "admin_user"
    event_type = "keystroke"
    timestamp = 123456789
    payload = @{
        keystrokes = @(
            @{ key = "A"; dwell = 120; flight = 90 }
        )
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/impersonator/event" -Method POST -Body $body -ContentType "application/json"
    Write-Output "SUCCESS"
    $response | ConvertTo-Json
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    $stream = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $responseBody = $reader.ReadToEnd()
    Write-Output "BODY: $responseBody"
}
