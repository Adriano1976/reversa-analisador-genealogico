<#
.SYNOPSIS
    Sobe o Analisador com a entrada pelo Google (feature 051).

.DESCRIPTION
    Le as cinco variaveis de `.env.local` (que nao e versionado), valida e sobe
    `src/app.py`. Se `ANALISADOR_SECRET_KEY` estiver vazia, gera uma e grava no
    arquivo — a sessao sobrevive ao proximo inicio.

    Se `.env.local` nao existir, o script cria o modelo vazio e pede para preencher.
    Para usar outra porta, mude `ANALISADOR_URL_PUBLICA` e `ANALISADOR_PORT` no
    arquivo e cadastre a URI correspondente no Google Cloud Console.

.EXAMPLE
    .\iniciar.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$raiz = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$arquivo = Join-Path $raiz ".env.local"
$python = Join-Path $raiz ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python do .venv nao encontrado em $python. Crie o ambiente com: python -m venv .venv"
}

$modelo = @"
# Entrada pelo Google (feature 051) - NAO versionar este arquivo.
#
# 1. No Google Cloud Console, crie o cliente OAuth "Aplicativo da Web" e cadastre
#    http://127.0.0.1:5000/callback como URI de redirecionamento autorizado.
# 2. Preencha as linhas abaixo e rode:  .\iniciar.ps1
# 3. ANALISADOR_SECRET_KEY pode ficar vazia: o script gera e grava na primeira vez.
#
# ANALISADOR_DONO_INICIAL e o e-mail da conta que herda os arquivos anteriores.

# ANALISADOR_MODO decide o que a aplicacao monta (auditoria de 2026-10-30):
#   google -> entrada pelo Google e conta com senha (o caso deste arquivo)
#   local  -> sem login, um dono por maquina (e o que o instalador usa)
ANALISADOR_MODO=google

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ANALISADOR_SECRET_KEY=
ANALISADOR_URL_PUBLICA=http://127.0.0.1:5000
ANALISADOR_DONO_INICIAL=

# Recuperacao de senha e confirmacao de e-mail (feature 053) - OPCIONAL.
# Sem HOST e REMETENTE, o cadastro nao conclui e a recuperacao avisa que o envio
# nao esta configurado; a entrada de conta ja confirmada continua funcionando.
# Para Gmail: smtp.gmail.com, porta 587, starttls, usuario = o endereco e senha =
# senha de aplicativo (a conta precisa ter verificacao em duas etapas).
# ANALISADOR_SMTP_HOST=
# ANALISADOR_SMTP_PORT=587
# ANALISADOR_SMTP_USUARIO=
# ANALISADOR_SMTP_SENHA=
# ANALISADOR_SMTP_REMETENTE=
# ANALISADOR_SMTP_SEGURANCA=starttls
"@

if (-not (Test-Path -LiteralPath $arquivo)) {
    Set-Content -LiteralPath $arquivo -Value $modelo -Encoding UTF8
    Write-Host "Criei $arquivo com o modelo. Preencha as quatro linhas e rode de novo." -ForegroundColor Yellow
    exit 1
}

$obrigatorias = @(
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "ANALISADOR_SECRET_KEY",
    "ANALISADOR_URL_PUBLICA",
    "ANALISADOR_DONO_INICIAL"
)
$valores = @{}

foreach ($linha in Get-Content -LiteralPath $arquivo -Encoding UTF8) {
    $texto = $linha.Trim()
    if (-not $texto -or $texto.StartsWith("#")) { continue }
    $partes = $texto -split "=", 2
    if ($partes.Count -ne 2) { continue }
    $nome = $partes[0].Trim()
    $valor = $partes[1].Trim().Trim('"', "'")
    if ($valor) { $valores[$nome] = $valor }
}

if (-not $valores["ANALISADOR_SECRET_KEY"]) {
    $novo = (& $python -c "import secrets; print(secrets.token_urlsafe(48))").Trim()
    if (-not $novo) { throw "Nao foi possivel gerar ANALISADOR_SECRET_KEY." }
    Add-Content -LiteralPath $arquivo -Value "ANALISADOR_SECRET_KEY=$novo" -Encoding UTF8
    $valores["ANALISADOR_SECRET_KEY"] = $novo
    Write-Host "ANALISADOR_SECRET_KEY gerada e gravada em .env.local." -ForegroundColor Green
}

$faltantes = @($obrigatorias | Where-Object { -not $valores[$_] })
if ($faltantes.Count -gt 0) {
    Write-Host "Falta preencher em $arquivo :" -ForegroundColor Yellow
    foreach ($nome in $faltantes) { Write-Host "  - $nome" }
    exit 1
}

# O modo e OBRIGATORIO desde a auditoria de 2026-10-30: `create_app` recusa subir sem
# ele. Este atalho existe para a entrada pelo Google, entao `google` e o modo que ele
# pressupoe — e o arquivo antigo, que ainda nao tem a linha, continua funcionando.
if (-not $valores["ANALISADOR_MODO"]) {
    $valores["ANALISADOR_MODO"] = "google"
}

foreach ($nome in $valores.Keys) {
    Set-Item -Path "Env:$nome" -Value $valores[$nome]
}

if (-not $valores["ANALISADOR_SMTP_HOST"] -or -not $valores["ANALISADOR_SMTP_REMETENTE"]) {
    Write-Host "Aviso: ANALISADOR_SMTP_HOST e ANALISADOR_SMTP_REMETENTE nao estao em .env.local. O cadastro nao conclui e a recuperacao de senha avisa que o envio nao esta configurado." -ForegroundColor Yellow
}

Write-Host "Subindo em $($valores['ANALISADOR_URL_PUBLICA']) - Ctrl+C encerra." -ForegroundColor Green
& $python (Join-Path $raiz "src\app.py")
exit $LASTEXITCODE
