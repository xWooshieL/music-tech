#!/usr/bin/env pwsh
# Сборка presentation.pdf через pdflatex (Madrid + seahorse, T2A).

$ErrorActionPreference = "Stop"

if (Test-Path presentation.pdf) {
    Remove-Item presentation.pdf -Force -ErrorAction SilentlyContinue
}

# Два прогона для tableofcontents и счётчиков.
pdflatex -interaction=nonstopmode -halt-on-error presentation.tex | Out-Null
pdflatex -interaction=nonstopmode -halt-on-error presentation.tex | Out-Null

if (Test-Path presentation.pdf) {
    $size = (Get-Item presentation.pdf).Length / 1KB
    Write-Host ("OK: presentation.pdf built, {0:N0} KB" -f $size)
} else {
    Write-Host "ERROR: presentation.pdf was not produced. Check presentation.log."
    exit 1
}

Get-ChildItem -File | Where-Object {
    $_.Extension -in @('.aux', '.log', '.out', '.toc', '.snm', '.nav', '.vrb', '.fls', '.fdb_latexmk', '.synctex.gz')
} | Remove-Item -Force -ErrorAction SilentlyContinue
