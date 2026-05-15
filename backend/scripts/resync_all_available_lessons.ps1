$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $PSScriptRoot
Set-Location $BackendDir

# Avoid a stale local proxy from breaking Gemini embedding calls.
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""
$env:all_proxy = ""

$env:PYTHONUNBUFFERED = "1"
$env:DB_MODE = "cloud"

$IntegratedChineseLangs = @(
    "en",
    "fr",
    "de",
    "es",
    "ja",
    "ko",
    "vi",
    "pt",
    "ru",
    "th",
    "it",
    "ar",
    "id",
    "ms"
)

Write-Host "== Integrated Chinese -> Aiven ==" -ForegroundColor Cyan
foreach ($lang in $IntegratedChineseLangs) {
    Write-Host ""
    Write-Host "---- Sync integrated_chinese lang=$lang ----" -ForegroundColor Yellow
    python database/sync_to_db.py --pipeline integrated_chinese --lang $lang
}

Write-Host ""
Write-Host "== Post-sync database checks ==" -ForegroundColor Cyan
@'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve()))
from database.connection import get_connection

conn = get_connection()
cur = conn.cursor()

queries = [
    ("database_size", "SELECT pg_size_pretty(pg_database_size(current_database()))"),
    ("lessons", "SELECT COUNT(*) FROM lessons"),
    ("language_items", "SELECT COUNT(*) FROM language_items"),
    ("answer_embeddings", "SELECT COUNT(*) FROM answer_embeddings"),
    ("embedding_dims", "SELECT vector_dims(primary_embedding), COUNT(*) FROM answer_embeddings GROUP BY 1 ORDER BY 1"),
]

for label, sql in queries:
    cur.execute(sql)
    print(f"\n[{label}]")
    for row in cur.fetchall():
        print(row)

cur.close()
conn.close()
'@ | python -

Write-Host ""
Write-Host "Done." -ForegroundColor Green
