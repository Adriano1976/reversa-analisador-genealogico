<#
.SYNOPSIS
    Atualiza o aplicativo que roda no container (porta 5080).

.DESCRIPTION
    O container NAO le o codigo do disco: a imagem e um RETRATO do dia em que foi construida.
    Editar qualquer arquivo de `src/` nao chega ate ele — e foi por isso que uma imagem de
    2026-10-09 serviu, por horas, o codigo anterior a feature 011 sem nada denunciar.

    Este atalho faz o que o README manda, na ordem, e mostra o resultado:

      1. pega a revisao do git e a entrega ao build, para o rotulo da imagem dizer o commit;
      2. reconstroi a imagem e recria o container (`docker compose up -d --build`);
      3. imprime as DUAS marcas de identidade do que subiu — o rotulo e o carimbo de data —,
         em vez de exigir que voce digite `docker inspect` na mao;
      4. confere que a aplicacao responde na 5080.

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

    Passo "Reconstruindo a imagem com a revisao '$revisao' (na primeira vez pode demorar)"
    Write-Host "    O log abaixo e o do Docker. O resumo do que ficou no ar vem no fim."
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) {
        throw "O 'docker compose up -d --build' falhou (codigo $LASTEXITCODE). Nada foi trocado."
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
