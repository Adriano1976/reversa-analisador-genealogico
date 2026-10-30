<#
.SYNOPSIS
    Monta o pacote de distribuicao (analisador.zip) a partir de um commit.

.DESCRIPTION
    POR QUE `git archive`, E NAO `Compress-Archive`. O `Compress-Archive` le a pasta
    inteira: `.venv/` (330 MB), `.git/` (94 MB), `src/uploads/` (203 MB de GEDCOM real),
    `src/dados/contas.json` (e-mail e hash de senha) e `.env.local` (client secret do
    Google e senha de SMTP). O `git archive` so le o que esta COMMITADO, e nada disso
    esta commitado. A lista de caminhos abaixo e fechada de proposito: e a mesma ideia
    da lista de PERMISSAO do `.dockerignore`, que ja provou funcionar neste projeto.

    POR QUE O LAUNCHER E O LEIA-ME NAO VEM DO COMMIT. O `.gitattributes` marca `*.bat`
    e `LEIA-ME.txt` com `eol=crlf`, mas essa conversao vale para o CHECKOUT e nao para o
    `git archive`, que escreve o blob cru (LF). Um `.bat` com LF pode perder
    `goto`/rotulo — e o `iniciar-analisador.bat` usa `goto erro` —, e um `.txt` com LF
    vira uma linha so no Notepad antigo. Por isso os dois entram da ARVORE DE TRABALHO,
    e o script confere que o que entrou no zip tem CRLF.

    O QUE ELE RECUSA. Dado pessoal (`.ged`, `.csv`), segredo (`.env`, `contas.json`),
    bytecode e os diretorios que nunca podem viajar. Se qualquer um aparecer, o pacote e
    APAGADO: um zip invalido no disco acaba sendo distribuido.

    `$ErrorActionPreference = "Continue"`, e nao "Stop", pela mesma razao medida em
    `atualizar.ps1`: comando nativo que escreve em stderr (o `git` avisa, o `docker`
    narra o build) vira erro que aborta o script. O que interrompe aqui e explicito:
    cada passo confere `$LASTEXITCODE` ou o arquivo resultante.

.EXAMPLE
    .\publicar.ps1

    Gera `analisador.zip` na raiz do projeto, com o commit atual.

.EXAMPLE
    .\publicar.ps1 -Revisao v1.0 -Saida C:\Temp\analisador-1.0.zip

    Gera o pacote de uma tag, em outro lugar.

.EXAMPLE
    .\publicar.ps1 -Saida .\analisador.zip -SomenteVerificar

    Confere um pacote que ja existe, sem reconstruir — util para reconferir o zip
    depois de baixado. Nesse modo o arquivo NAO e apagado quando a verificacao
    falha: o pacote nao foi criado por este script, e apagar destruiria a evidencia.
#>
[CmdletBinding()]
param(
    [string]$Saida = "",
    [string]$Revisao = "HEAD",
    [switch]$SomenteVerificar
)

$ErrorActionPreference = "Continue"

$raiz = $PSScriptRoot
$prefixo = "analisador/"
# Arquivos que NAO vem do commit: eles saem da ARVORE DE TRABALHO, porque o
# `git archive` escreve o blob cru (LF) e ignora `eol=crlf`. `.bat` com LF perde
# `goto`/rotulo; `.txt` com LF vira uma linha so no Notepad antigo.
$daArvore = @("iniciar-analisador.bat", "LEIA-ME.txt")

# Os caminhos saem SEMPRE do commit. Lista fechada: nada entra por estar na pasta.
$caminhos = @("src", "requirements.txt", "LICENSE")

# O que o pacote precisa ter para ser um pacote.
#
# A montagem passa por `ForEach-Object` de proposito. Escrever `"$prefixo" + "src/app.py"`
# dentro do `@(...)` NAO produz seis itens: em PowerShell a virgula tem precedencia sobre
# o `+`, e o que sai e UMA string com tudo concatenado — medido na primeira execucao
# deste script, em que a verificacao acusou "faltando" os seis de uma vez so.
$relativosObrigatorios = @(
    "src/app.py",
    "src/templates/index.html",
    "src/assets/app.css",
    "requirements.txt",
    "LICENSE"
) + $daArvore
$obrigatorios = @($relativosObrigatorios | ForEach-Object { "$prefixo$_" })

if (-not $Saida) { $Saida = Join-Path $raiz "analisador.zip" }
$Saida = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Saida)

if (-not $SomenteVerificar) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "O comando 'git' nao esta no PATH. O pacote sai do commit: sem git, nao ha pacote."
    }

    foreach ($arquivo in $daArvore) {
        if (-not (Test-Path -LiteralPath (Join-Path $raiz $arquivo))) {
            throw "Arquivo da arvore ausente: $(Join-Path $raiz $arquivo). Ele entra da arvore de trabalho."
        }
    }
}

Push-Location $raiz
try {
    # As duas assemblies servem aos DOIS modos, e por isso ficam antes do desvio.
    #
    # DUAS, e nao uma: `ZipFile` vive em `System.IO.Compression.FileSystem`, mas o enum
    # `ZipArchiveMode` vive em `System.IO.Compression`. Carregar so a primeira faz o
    # `Open` falhar com "Nao e possivel localizar o tipo [System.IO.Compression.ZipArchiveMode]"
    # — medido na primeira execucao deste script.
    Add-Type -AssemblyName System.IO.Compression -ErrorAction Stop
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop

    $commit = "(pacote existente)"
    if ($SomenteVerificar) {
        if (-not (Test-Path -LiteralPath $Saida)) {
            throw "Pacote inexistente para verificar: $Saida"
        }
        Write-Host "Verificando o pacote existente: $Saida" -ForegroundColor Cyan
    }
    else {
        $null = git rev-parse --verify "$Revisao^{commit}" 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Revisao inexistente: '$Revisao'. Use uma tag, um branch ou um commit."
        }
        $commit = (git rev-parse --short $Revisao).Trim()

        if (Test-Path -LiteralPath $Saida) {
            Remove-Item -LiteralPath $Saida -Force
            if (Test-Path -LiteralPath $Saida) {
                throw "Nao foi possivel remover o pacote anterior: $Saida (esta aberto em outro programa?)"
            }
        }

        Write-Host "Montando o pacote do commit $commit ..." -ForegroundColor Cyan
        git archive --format=zip --prefix=$prefixo -o $Saida $Revisao -- @caminhos
        if ($LASTEXITCODE -ne 0) {
            throw "O 'git archive' falhou (codigo $LASTEXITCODE). Nada foi publicado."
        }
        if (-not (Test-Path -LiteralPath $Saida)) {
            throw "O 'git archive' terminou sem erro mas nao gravou $Saida."
        }

        # Os arquivos da arvore entram da ARVORE DE TRABALHO, e nao do commit. Ver o cabecalho.
        $zip = $null
        try {
            $zip = [System.IO.Compression.ZipFile]::Open($Saida, [System.IO.Compression.ZipArchiveMode]::Update)
            foreach ($arquivo in $daArvore) {
                $entrada = $zip.CreateEntry("$prefixo$arquivo")
                # Carimba o instante do ARQUIVO, e nao o "agora". Sem isto o zip muda a
                # cada execucao (o `git archive` ja usa a data do commit, mas a entrada
                # criada aqui nasceria com a hora corrente) e o sha256 publicado nao
                # serviria para reconferir um build.
                $entrada.LastWriteTime = (Get-Item -LiteralPath (Join-Path $raiz $arquivo)).LastWriteTime
                $destino = $entrada.Open()
                try {
                    $origem = [System.IO.File]::OpenRead((Join-Path $raiz $arquivo))
                    try { $origem.CopyTo($destino) } finally { $origem.Dispose() }
                } finally {
                    $destino.Dispose()
                }
            }
        } finally {
            if ($null -ne $zip) { $zip.Dispose() }
        }
    }

    # ---------------- verificacao ----------------
    $falhas = @()
    $zip = $null
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Saida)
        $nomes = @()
        foreach ($item in $zip.Entries) { $nomes += $item.FullName }

        foreach ($requisito in $obrigatorios) {
            if ($nomes -notcontains $requisito) { $falhas += "faltando no pacote: $requisito" }
        }

        $extensoesProibidas = @(".ged", ".csv", ".pyc", ".pyo")
        $nomesProibidos = @("contas.json")
        $segmentosProibidos = @(
            "__pycache__", "dados", "logs", "uploads", "tests",
            ".git", ".venv", "_reversa_sdd", "_reversa_forward", "docs"
        )

        foreach ($nome in $nomes) {
            if (-not $nome.StartsWith($prefixo)) { $falhas += "entrada fora do prefixo: $nome"; continue }
            $relativo = $nome.Substring($prefixo.Length)
            if (-not $relativo -or $relativo.EndsWith("/")) { continue }

            $segmentos = $relativo.Split("/")
            foreach ($segmento in $segmentos) {
                if ($segmentosProibidos -contains $segmento) {
                    $falhas += "diretorio proibido no pacote: $nome"
                }
            }

            $curto = [System.IO.Path]::GetFileName($relativo)
            if ($curto -eq ".env" -or $curto.StartsWith(".env.")) {
                $falhas += "segredo no pacote: $nome"
            }
            if ($nomesProibidos -contains $curto) {
                $falhas += "dado de conta no pacote: $nome"
            }
            $extensao = [System.IO.Path]::GetExtension($relativo).ToLowerInvariant()
            if ($extensoesProibidas -contains $extensao) {
                $falhas += "dado pessoal no pacote: $nome"
            }
        }

        foreach ($arquivo in $daArvore) {
            $entradaArvore = $zip.GetEntry("$prefixo$arquivo")
            if ($null -ne $entradaArvore) {
                $leitor = New-Object System.IO.StreamReader($entradaArvore.Open())
                try { $conteudo = $leitor.ReadToEnd() } finally { $leitor.Dispose() }
                if ($conteudo -notmatch "`r`n") {
                    $falhas += "'$arquivo' entrou sem CRLF: o cmd.exe perde 'goto'/rotulo e o Notepad antigo mostra tudo numa linha"
                }
            }
        }

        $quantidade = $nomes.Count
    } finally {
        if ($null -ne $zip) { $zip.Dispose() }
    }

    if ($falhas.Count -gt 0) {
        if ($SomenteVerificar) {
            Write-Host ""
            Write-Host "PACOTE RECUSADO (o arquivo foi mantido para inspecao):" -ForegroundColor Red
        }
        else {
            Remove-Item -LiteralPath $Saida -Force
            Write-Host ""
            Write-Host "PACOTE RECUSADO. Ele foi apagado para nao ser distribuido:" -ForegroundColor Red
        }
        foreach ($falha in $falhas) { Write-Host "  - $falha" -ForegroundColor Red }
        throw "O pacote nao passou na verificacao ($($falhas.Count) problema(s))."
    }

    $arquivo = Get-Item -LiteralPath $Saida
    $hash = (Get-FileHash -LiteralPath $Saida -Algorithm SHA256).Hash

    Write-Host ""
    Write-Host "Pacote pronto" -ForegroundColor Green
    Write-Host ("  arquivo : {0}" -f $arquivo.FullName)
    Write-Host ("  commit  : {0}" -f $commit)
    Write-Host ("  entradas: {0}" -f $quantidade)
    Write-Host ("  tamanho : {0:N0} KB" -f ($arquivo.Length / 1KB))
    Write-Host ("  sha256  : {0}" -f $hash)
    Write-Host ""
    Write-Host "Confira antes de publicar: sem .ged, sem .csv, sem .env, sem contas.json." -ForegroundColor DarkGray
}
finally {
    Pop-Location
}
