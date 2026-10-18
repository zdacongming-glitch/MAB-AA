$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    & latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
    if ($LASTEXITCODE -ne 0) { throw 'Main manuscript compilation failed.' }
    & latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
    if ($LASTEXITCODE -ne 0) { throw 'Supplement compilation failed.' }
} finally {
    Pop-Location
}
