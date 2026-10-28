<#
.SYNOPSIS
    Atualiza o aplicativo que roda no container (porta 5080).

.DESCRIPTION
    O container NAO le o codigo do disco: a imagem e um RETRATO do dia em que foi construida.
    Editar qualquer arquivo de `src/` nao chega ate ele — e foi por isso que uma imagem de
    2026-10-09 serviu, por horas, o codigo anterior a feature 011 sem nada denunciar.

    Este atalho faz o que o README manda, na ordem, e mostra o resultado:

      1. pega a revisao do git e a entrega ao build, para o rotulo da imagem dizer o commit;
      2. carrega as variaveis de entrada do `.env.local` que nao estiverem no `.env` (o
         `docker compose` le apenas o `.env`) e valida a configuracao antes do build;
      3. reconstroi a imagem e recria o container (`docker compose up -d --build`);
      4. imprime as DUAS marcas de identidade do que subiu — o rotulo e o carimbo de data —,
         em vez de exigir que voce digite `docker inspect` na mao;
      5. confere que a aplicacao responde na 5080.

    O banco NAO e afetado: o container do PostgreSQL nao e recriado, e o historico das
    analises continua onde esta. Os arquivos enviados tambem nao: `src/uploads` e montada ao
    vivo dentro do container.

.EXAMPLE
    .\atualizar.ps1

    Reconstroi e mostra o que ficou no ar.

.EXAMPLE
    .\atualizar.ps1 -SemVerificacao

    Reconstroi sem conferir a resposta na 5080 — util quando a aplicacao sobe em outra porta.
#>
[CmdletBinding()]
param(
    [switch]$SemVerificacao
)

# `Continue`, e NAO `Stop`: o `docker compose` escreve o progresso do build em **stderr**, e
# sob `Stop` cada linha dessas vira um `NativeCommandError` que aborta o script — inclusive
# quando o operador apenas redireciona a saida (`.\atualizar.ps1 > log.txt`). Medido em
# 2026-10-11, nas duas formas. O que interrompe aqui e explicito: o codigo de saida do build e
# conferido logo abaixo, e as leituras de identidade degradam para um valor honesto.
$ErrorActionPreference = "Continue"

$PORTA = 5080
$URL = "http://127.0.0.1:$PORTA/"

function Passo {
    param([string]$Texto)
    Write-Host ""
    Write-Host "==> $Texto" -ForegroundColor Cyan
}

# As cinco variaveis da entrada pelo Google vivem no `.env.local`, que e o arquivo do
# `iniciar.ps1` local. O `docker compose` le o `.env`, nao o `.env.local`: sem esta ponte, o
# `${VAR:?}` do compose para a subida com "required variable ... is missing a value", e o
# atalho traduzia isso como "o build falhou". Medido em 2026-10-27.
#
# Precedencia: ambiente do processo > `.env` > `.env.local`, com uma excecao declarada:
# `ANALISADOR_URL_PUBLICA` vinda do `.env.local` e reescrita para a porta do Docker (5080), e
# nao para a 5000 do modo local. O `.env` continua sendo o arquivo do Docker (onboarding.md
# secao 3); o `.env.local` e apenas o fallback de quem ja preencheu o arquivo do `iniciar.ps1`.
function ImportarVariaveisDeEntrada {
    param([string]$ArquivoLocal, [string]$ArquivoDocker, [int]$PortaDocker)

    $noDocker = @{}
    if (Test-Path -LiteralPath $ArquivoDocker) {
        foreach ($linha in Get-Content -LiteralPath $ArquivoDocker -Encoding UTF8) {
            $texto = $linha.Trim()
            if (-not $texto -or $texto.StartsWith("#")) { continue }
            $partes = $texto -split "=", 2
            if ($partes.Count -eq 2) { $noDocker[$partes[0].Trim()] = $true }
        }
    }

    if (-not (Test-Path -LiteralPath $ArquivoLocal)) { return }
    foreach ($linha in Get-Content -LiteralPath $ArquivoLocal -Encoding UTF8) {
        $texto = $linha.Trim()
        if (-not $texto -or $texto.StartsWith("#")) { continue }
        $partes = $texto -split "=", 2
        if ($partes.Count -ne 2) { continue }
        $nome = $partes[0].Trim()
        $valor = $partes[1].Trim().Trim('"', "'")
        if (-not $valor) { continue }
        if ($noDocker.ContainsKey($nome)) { continue }
        # A URL publica e a excecao a precedencia: o `.env.local` traz a 5000 do modo local,
        # e o Docker publica na 5080. Se o `.env` tiver a chave, ele vence (tratado acima);
        # senao, o valor do `.env.local` e reescrito para a porta do Docker.
        if ($nome -eq "ANALISADOR_URL_PUBLICA") {
            Set-Item -Path "Env:$nome" -Value "http://127.0.0.1:$PortaDocker"
            continue
        }
        if (Test-Path "Env:$nome") { continue }
        Set-Item -Path "Env:$nome" -Value $valor
    }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "O comando 'docker' nao esta no PATH. Abra o Docker Desktop e rode de novo."
}

# A revisao entra no ROTULO da imagem. Sem `git`, o build segue com `desconhecida` — o carimbo
# de data e gravado de qualquer forma, entao a identidade da imagem nunca fica em branco.
$revisao = "desconhecida"
if (Get-Command git -ErrorAction SilentlyContinue) {
    $saida = git rev-parse --short HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $saida) {
        $revisao = "$saida".Trim()
    }
}

# `Push-Location` para a pasta DESTE arquivo: o `docker compose` le o `docker-compose.yml` do
# diretorio corrente, entao o atalho tem de funcionar de qualquer lugar. O `finally` devolve o
# shell ao lugar de onde voce chamou — um script que muda o diretorio da sua sessao e um
# incomodo que nao se justifica.
Push-Location $PSScriptRoot
try {
    $env:REVISAO = $revisao

    # A ponte com o `.env.local` e a pre-checagem acontecem ANTES do build. Sem isso, uma
    # variavel faltando derrubava o `up` com "required variable ... is missing a value" e o
    # operador lia "o build falhou" — a causa real ficava escondida no meio da saida.
    ImportarVariaveisDeEntrada -ArquivoLocal (Join-Path $PSScriptRoot ".env.local") `
        -ArquivoDocker (Join-Path $PSScriptRoot ".env") -PortaDocker $PORTA

    $configuracao = docker compose config --quiet 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "O compose nao conseguiu ler as variaveis obrigatorias:" -ForegroundColor Red
        $configuracao | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host "  Para o Docker, as cinco variaveis de entrada precisam estar no .env" -ForegroundColor Yellow
        Write-Host "  (ou no .env.local, que este atalho le como fallback)." -ForegroundColor Yellow
        Write-Host "  Veja onboarding.md secao 3; a URL publica do Docker e http://127.0.0.1:$PORTA." -ForegroundColor Yellow
        throw "Configuracao do compose incompleta. Nada foi trocado."
    }

    Passo "Reconstruindo a imagem com a revisao '$revisao' (na primeira vez pode demorar)"
    Write-Host "    O log abaixo e o do Docker. O resumo do que ficou no ar vem no fim."
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) {
        throw "O 'docker compose up -d --build' falhou (codigo $LASTEXITCODE). Nada foi trocado. O erro do Docker esta nas linhas acima."
    }

    Passo "O que ficou no ar"
    # O formato e `{{json .Config.Labels}}`, e NAO `{{index .Config.Labels "chave"}}`: aspas
    # DENTRO do argumento do formato sao comidas pelo PowerShell ao entregar a linha de comando
    # ao docker, e o `inspect` responde `function "org" not defined` deixando o campo VAZIO.
    # Medido em 2026-10-11, na primeira execucao deste atalho. Aqui as etiquetas vem em JSON e
    # quem separa a chave e o proprio PowerShell.
    $rotulo = "desconhecida"
    $etiquetas = docker image inspect genealogia-app --format '{{json .Config.Labels}}' |
        ConvertFrom-Json
    if ($etiquetas -and $etiquetas.'org.opencontainers.image.revision') {
        $rotulo = $etiquetas.'org.opencontainers.image.revision'
    }
    Write-Host "  imagem  : genealogia-app"
    Write-Host "  revisao : $rotulo"
    Write-Host "  construida em: $(docker compose exec -T app cat /app/CONSTRUIDO_EM)"
    docker compose ps --format "  {{.Service}}  {{.Status}}  {{.Ports}}"

    if (-not $SemVerificacao) {
        Passo "Conferindo $URL"
        $respondeu = $false
        foreach ($tentativa in 1..15) {
            try {
                $resposta = Invoke-WebRequest -Uri $URL -UseBasicParsing -TimeoutSec 5
                if ($resposta.StatusCode -eq 200) { $respondeu = $true; break }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        if ($respondeu) {
            Write-Host "  OK: respondeu 200." -ForegroundColor Green
        } else {
            Write-Host "  AVISO: o container subiu, mas $URL nao respondeu 200." -ForegroundColor Yellow
            Write-Host "         Veja o log com: docker compose logs --tail 30 app"
        }
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Pronto. Abra $URL (Ctrl+F5, para o navegador nao reaproveitar a pagina antiga)." `
    -ForegroundColor Green
