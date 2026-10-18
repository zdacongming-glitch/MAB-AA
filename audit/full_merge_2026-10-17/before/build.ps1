$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $revisionBuild = Join-Path $PSScriptRoot 'build'
    New-Item -ItemType Directory -Path $revisionBuild -Force | Out-Null
    # Two passes settle cross-document references from a clean build.
    foreach ($entry in @('supplement.tex', 'manuscript.tex', 'supplement.tex', 'manuscript.tex')) {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error '-outdir=build' $entry
        if ($LASTEXITCODE -ne 0) { throw "Compilation failed: $entry" }
        # Generate this build's own bibliography even if legacy root-level
        # products are present. No historical build products are deleted.
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($entry)
        & bibtex "build/$stem"
        if ($LASTEXITCODE -ne 0) { throw "Bibliography failed: $entry" }
        & latexmk -g -pdf -interaction=nonstopmode -halt-on-error '-outdir=build' $entry
        if ($LASTEXITCODE -ne 0) { throw "Compilation failed after bibliography: $entry" }
    }
    Copy-Item -LiteralPath (Join-Path $revisionBuild 'manuscript.pdf') -Destination (Join-Path $PSScriptRoot 'manuscript.pdf') -Force
    Copy-Item -LiteralPath (Join-Path $revisionBuild 'supplement.pdf') -Destination (Join-Path $PSScriptRoot 'supplement.pdf') -Force
} finally {
    Pop-Location
}
