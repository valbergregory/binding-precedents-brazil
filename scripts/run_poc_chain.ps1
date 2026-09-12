# Phase 1 proof-of-concept chain (steps 2.1 -> 2.6) for one theme. Run from the repository root in a second
# PowerShell window:  .\scripts\run_poc_chain.ps1 -Tema 1132 -Subject 9582 -From 2022-08-01 -To 2024-08-31
# Every step is idempotent; re-running resumes. Log: logs/poc_chain.out
param([int]$Tema = 1132, [int]$Subject = 9582, [string]$From = "2022-08-01", [string]$To = "2024-08-31")
$py = ".\.venv\Scripts\python.exe"
& $py scripts/04_download_integras.py --from $From --to $To --resume; if ($LASTEXITCODE -ne 0) { Write-Host "step 04 reported failures (see logs/04_download_integras.json); continuing with what was copied" }
& $py scripts/05_load_integras.py --resume --from $From --to $To
& $py scripts/07_extract_citations.py --extractor-version v1 --resume
& $py scripts/08_recover_origin.py --resume
& $py scripts/09_poc_report.py --tema $Tema --subject $Subject
& $py scripts/90_export_overleaf.py
Write-Host "poc chain finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
