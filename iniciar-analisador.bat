@echo off
setlocal
cd /d "%~dp0"
title Analisador Genealogico

rem === Modo de identidade (auditoria de 2026-10-30) ===
rem `local` = este computador, sem login: a aplicacao sobe e o dono e quem usa a
rem maquina. `google` exigiria as cinco variaveis do OAuth, que nao existem aqui.
rem Sem esta linha o app recusa subir: e o que impede o modo aberto por acidente.
set "ANALISADOR_MODO=local"

rem === Passo 2: procurar o Python 3.14 (instala com o winget se faltar) ===
set "PY="
py -3.14 --version >nul 2>&1
if %errorlevel%==0 set "PY=py -3.14"

if not defined PY (
  echo Python 3.14 nao encontrado. Tentando instalar com o winget...
  winget install -e --id Python.Python.3.14 --accept-package-agreements --accept-source-agreements
  echo.
  echo Quando a instalacao terminar, FECHE esta janela e abra este arquivo de novo.
  pause
  exit /b 0
)

rem === Ambiente isolado e dependencias (so na primeira vez) ===
if not exist ".venv\Scripts\python.exe" (
  echo Preparando o ambiente. Isso so acontece na primeira vez...
  %PY% -m venv .venv
  if errorlevel 1 goto erro
)
if not exist ".venv\instalado.txt" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto erro
  echo ok> ".venv\instalado.txt"
)

rem === Passo 3: abrir o navegador e iniciar o programa ===
echo.
echo Iniciando o Analisador Genealogico em http://127.0.0.1:5000
echo Para encerrar, feche esta janela.
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:5000"
".venv\Scripts\python.exe" src\app.py
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Copie a mensagem acima e envie ao desenvolvedor.
pause
exit /b 1
