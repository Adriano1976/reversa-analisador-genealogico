param(
  [Parameter(Mandatory = $true)][string]$Path,
  [Parameter(Mandatory = $true)][string]$Block,
  [Parameter(Mandatory = $true)][string]$Decision
)

# Fecha os itens BR-HUMANA-001..009 / AMB-006..014 de um artefato:
#  - troca "- **Status**: PENDENTE" por "- **Status**: RESOLVIDA" no bloco do item
#  - anexa a decisao do usuario ao final do bloco

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path -LiteralPath $Path).Path
$raw = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8
$lf = $raw -replace "`r`n", "`n"

$lines = $lf -split "`n", -1
$first = -1; $last = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -eq ("### " + $Block)) { $first = $i }
  elseif ($first -ge 0 -and $lines[$i] -match '^#{2,3} ') { $last = $i - 1; break }
}
if ($first -lt 0) { throw "bloco '$Block' nao encontrado em $resolved" }
if ($last -lt 0) { $last = $lines.Count - 1 }

$found = $false
for ($i = $first; $i -le $last; $i++) {
  if ($lines[$i] -match '^- \*\*Status\*\*: PENDENTE\s*$') {
    if ($Block -like 'AMB-*') {
      $lines[$i] = '- **Status**: RESOLVIDO COM DECISÃO HUMANA'
    } else {
      $lines[$i] = '- **Status**: RESOLVIDA'
    }
    $found = $true
    break
  }
}
if (-not $found) { throw "linha 'Status: PENDENTE' nao encontrada no bloco '$Block' de $resolved" }

# anexa a decisao ao final do bloco
$out = @()
$out += $lines[0..$last]
$out += $Decision
if ($last + 1 -lt $lines.Count) { $out += $lines[($last + 1)..($lines.Count - 1)] }

[System.IO.File]::WriteAllText($resolved, ($out -join "`n"), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("OK " + $Block + " em " + (Split-Path $resolved -Leaf))
