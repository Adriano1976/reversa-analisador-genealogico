param(
  [Parameter(Mandatory = $true)][string]$Path
)

# Finaliza o front-matter de um artefato do Reversa:
#  - normaliza o arquivo para LF (sem CRLF)
#  - calcula sha256 do corpo (tudo abaixo do 2o '---'), normalizado (LF, sem \n final)
#  - substitui o valor 'hash:' do front-matter
# Uso: ./_set-hash.ps1 -Path "_reversa_sdd/migration/foo.md"

$ErrorActionPreference = "Stop"

$resolved = (Resolve-Path -LiteralPath $Path).Path
$raw = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8

# 1) normaliza CRLF -> LF
$lf = $raw -replace "`r`n", "`n"

$lines = $lf -split "`n", -1

# 2) localiza o fechamento do front-matter
if ($lines[0] -ne "---") { throw "front-matter ausente em $resolved (linha 1 nao e '---')" }
$close = -1
for ($i = 1; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -eq "---") { $close = $i; break }
}
if ($close -lt 0) { throw "front-matter nao fechado em $resolved" }

# 3) corpo = linhas apos o fechamento, normalizado
$bodyLines = $lines[($close + 1)..($lines.Count - 1)]
$body = ($bodyLines -join "`n").TrimEnd("`n")

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$sha = [System.Security.Cryptography.SHA256]::Create()
$hex = ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""

# 4) injeta o hash no front-matter
$updated = $false
for ($i = 1; $i -lt $close; $i++) {
  if ($lines[$i] -match '^hash:\s*"?.*"?\s*$') {
    $lines[$i] = 'hash: "sha256:' + $hex + '"'
    $updated = $true
    break
  }
}
if (-not $updated) { throw "campo 'hash:' nao encontrado no front-matter de $resolved" }

$out = ($lines -join "`n")
[System.IO.File]::WriteAllText($resolved, $out, (New-Object System.Text.UTF8Encoding($false)))

Write-Output ("hash: sha256:" + $hex)
Write-Output ("file: " + $resolved)
Write-Output ("bodyBytes: " + $bytes.Length)
