@echo off
setlocal
cd /d "%~dp0"
title Analisador Genealogico

rem Console em UTF-8: o caminho do usuario pode ter acento, e mensagem embaralhada e
rem pior do que mensagem nenhuma. `PYTHONIOENCODING` cobre o que o Python imprime; o
rem `chcp` cobre o que este arquivo imprime.
chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"

rem === Modo de identidade (auditoria de 2026-10-30) ===
rem `local` = este computador, sem login: a aplicacao sobe e o dono e quem usa a
rem maquina. `google` exigiria as cinco variaveis do OAuth, que nao existem aqui.
rem Sem esta linha o app recusa subir: e o que impede o modo aberto por acidente.
set "ANALISADOR_MODO=local"

rem === `--verificar`: diz o que este arquivo usaria e sai, sem instalar nada ===
if /i "%~1"=="--verificar" set "SO_VERIFICAR=1"

rem === Smart App Control (medido em 2026-11-05) ===
rem O Windows 11 liga o Smart App Control sozinho, e ele bloqueia os `.pyd` NAO
rem ASSINADOS que o pip instala - `pandas` entre eles. O sintoma era um traceback
rem de `DLL load failed` depois de baixar 300 MB de bibliotecas. Avisar antes evita
rem a espera inteira perdida; a checagem e uma leitura do registro, nao instala nada.
call :ler_sac
if defined SO_VERIFICAR goto verificar
if "%SAC%"=="0x1" goto sac_ligado
goto achar

:sac_ligado
echo.
echo ATENCAO: o Smart App Control do Windows esta ligado neste computador.
echo Ele bloqueia as bibliotecas que este programa precisa baixar, e o programa
echo nao vai abrir. Para desligar, abra "Seguranca do Windows", entre em
echo "Controle de aplicativo e navegador" e procure "Smart App Control".
echo Se preferir, use outro computador que esteja com ele desligado.
echo.
choice /c SN /n /m "Continuar mesmo assim? (S/N) "
if errorlevel 2 goto sac_recusado
goto achar

:sac_recusado
echo.
echo Nada foi instalado. Desligue o Smart App Control e abra este arquivo de novo.
pause
exit /b 1

:achar
call :achar_python
if not defined PY goto sem_python
goto ambiente

:ambiente
call :hash_requirements

rem === Ambiente isolado: precisa ser o Python DESTA versao ===
rem Antes bastava o `.venv` existir. Um ambiente criado por outra versao era
rem reaproveitado e continuava quebrado - medido em 2026-11-05, com um `.venv`
rem 3.14 sob um Python 3.13. A checagem abaixo refaz o ambiente quando diverge.
if not exist ".venv\Scripts\python.exe" goto criar_venv
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,13) else 1)" >nul 2>&1
if not errorlevel 1 goto ambiente_pronto
echo O ambiente foi criado por outra versao do Python. Refazendo...
rmdir /s /q ".venv"
if exist ".venv" goto erro_venv
goto criar_venv

:ambiente_pronto

rem === Dependencias: reinstala quando o requirements.txt muda ===
rem O marcador guarda o HASH do requirements.txt, e nao um "ok": era o defeito que
rem deixava versao nova com dependencia nova rodar com as bibliotecas velhas.
if not exist ".venv\instalado.txt" goto instalar
set "INSTALADO="
set /p INSTALADO=<".venv\instalado.txt"
if /i not "%INSTALADO%"=="%REQ_HASH%" goto instalar
goto pronto

:criar_venv
echo Preparando o ambiente. Isso so acontece na primeira vez...
%PY% -m venv .venv
if errorlevel 1 goto erro_venv
goto instalar

:instalar
echo Instalando as bibliotecas...
rem Primeiro sem compilar nada: e o caminho rapido, e e o que da mensagem clara
rem quando falta pacote pronto para esta versao do Python. A segunda tentativa,
rem pelas fontes, existe para a primeira nao virar exigencia.
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: -r requirements.txt
if not errorlevel 1 goto marcar
echo.
echo Nao havia pacote pronto para esta versao do Python. Tentando pelas fontes...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto erro_pip

:marcar
> ".venv\instalado.txt" echo %REQ_HASH%
goto pronto

:pronto
echo.
echo Iniciando o Analisador Genealogico em http://127.0.0.1:5000
echo Para encerrar, feche esta janela.
rem O navegador abre quando a pagina RESPONDER, e nao depois de um tempo fixo: num
rem computador lento, 4 segundos abriam a aba antes de o servidor existir.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$u='http://127.0.0.1:5000'; for($i=0;$i -lt 90;$i++){ try { if((Invoke-WebRequest -UseBasicParsing $u -TimeoutSec 1).StatusCode -eq 200) { Start-Process $u; exit } } catch {}; Start-Sleep -Milliseconds 500 }"
".venv\Scripts\python.exe" src\app.py
if errorlevel 1 goto erro_programa
pause
exit /b 0

:verificar
call :achar_python
call :hash_requirements
if "%SAC%"=="0x1" echo Smart App ...: LIGADO (bloqueia as bibliotecas)
if not "%SAC%"=="0x1" echo Smart App ...: ok (%SAC%)
if not defined PY goto verificar_sem_python
echo Python ......: %PY%
%PY% --version
echo requirements: %REQ_HASH%
if not exist ".venv\Scripts\python.exe" goto verificar_sem_venv
for /f "tokens=2 delims= " %%V in ('.venv\Scripts\python.exe --version 2^>nul') do echo venv python .: %%V
goto verificar_com_venv

:verificar_sem_venv
echo venv python .: ausente

:verificar_com_venv
if not exist ".venv\instalado.txt" goto verificar_sem_marcador
set "INSTALADO="
set /p INSTALADO=<".venv\instalado.txt"
echo marcador ....: %INSTALADO%
if /i "%INSTALADO%"=="%REQ_HASH%" goto verificar_em_dia
echo situacao ....: reinstalaria as bibliotecas
exit /b 0

:verificar_sem_python
echo Python ......: NAO ENCONTRADO
exit /b 0

:verificar_em_dia
echo situacao ....: em dia
exit /b 0

:verificar_sem_marcador
echo marcador ....: ausente
echo situacao ....: instalaria as bibliotecas
exit /b 0

rem === Sem Python: instala pelo winget e procura de novo ===
:sem_python
echo.
echo Python 3.13 nao encontrado. Tentando instalar com o winget...
where winget >nul 2>&1
if errorlevel 1 goto sem_winget
winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto falha_winget
echo.
echo Instalacao concluida. Procurando o Python de novo...
call :achar_python
if not defined PY goto precisa_reabrir
goto ambiente

:sem_winget
echo.
echo O winget nao existe neste computador, entao nao consigo instalar o Python sozinho.
echo Baixe em https://www.python.org/downloads/ e marque "Add python.exe to PATH"
echo na primeira tela do instalador. Depois abra este arquivo de novo.
pause
exit /b 1

:falha_winget
echo.
echo O winget nao conseguiu instalar o Python.
echo Baixe em https://www.python.org/downloads/ e marque "Add python.exe to PATH"
echo na primeira tela do instalador. Depois abra este arquivo de novo.
pause
exit /b 1

:precisa_reabrir
echo.
echo O Python foi instalado, mas esta janela ainda nao o enxerga.
echo FECHE esta janela e abra este arquivo de novo. E normal, e so desta vez.
pause
exit /b 0

:erro_venv
echo.
echo Nao consegui criar o ambiente nesta pasta.
echo Extraia o zip numa pasta sua (Area de Trabalho, Documentos) e tente de novo:
echo a pasta do programa precisa permitir escrita na primeira execucao.
pause
exit /b 1

:erro_pip
echo.
echo Algo deu errado ao instalar as bibliotecas. Copie a mensagem acima e envie ao
echo desenvolvedor. Se o erro falar de internet, confira a conexao e tente de novo.
pause
exit /b 1

:erro_programa
echo.
echo O programa foi encerrado com erro. A mensagem acima diz o motivo.
pause
exit /b 1

rem === Sub-rotinas =========================================================

:ler_sac
rem `0x1` = ligado (bloqueia), `0x2` = em avaliacao (nao bloqueia), `0` = desligado.
rem Se a chave nao existir - Windows 10, por exemplo -, `SAC` fica `0` e nada muda.
set "SAC=0"
for /f "tokens=3" %%V in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState 2^>nul ^| find "VerifiedAndReputablePolicyState"') do set "SAC=%%V"
exit /b 0

:achar_python
rem Ordem: o lancador do Python, o `python` do PATH e os dois diretorios em que o
rem instalador grava. O winget instala em `Local\Python\pythoncore-...`, e nao no
rem `Programs\Python\Python314` classico: sem os dois, a instalacao terminava e o
rem arquivo mandava fechar a janela mesmo com o Python ja disponivel.
set "PY="
py -3.13 -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,13) else 1)" >nul 2>&1
if not errorlevel 1 (set "PY=py -3.13" & exit /b 0)
python -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,13) else 1)" >nul 2>&1
if not errorlevel 1 (set "PY=python" & exit /b 0)
for %%D in ("%LOCALAPPDATA%\Programs\Python\Python313" "%LOCALAPPDATA%\Python\pythoncore-3.13-64" "%ProgramFiles%\Python313") do (
  if not defined PY (
    if exist "%%~D\python.exe" (
      "%%~D\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2]==(3,13) else 1)" >nul 2>&1
      if not errorlevel 1 set PY="%%~D\python.exe"
    )
  )
)
exit /b 0

:hash_requirements
rem Identidade do requirements.txt. `certutil` existe desde o Windows 7; se faltar,
rem tamanho e data do arquivo ainda detectam a troca.
set "REQ_HASH="
for /f "skip=1 delims=" %%H in ('certutil -hashfile "requirements.txt" SHA256 2^>nul') do (
  if not defined REQ_HASH set "REQ_HASH=%%H"
)
if defined REQ_HASH set "REQ_HASH=%REQ_HASH: =%"
if not defined REQ_HASH (
  for %%F in ("requirements.txt") do set "REQ_HASH=%%~zF-%%~tF"
)
exit /b 0
