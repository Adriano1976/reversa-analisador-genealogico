@echo off
rem Sobe o Analisador com a entrada pelo Google (feature 051).
rem Existe porque a politica de execucao do Windows bloqueia .ps1 sem assinatura;
rem este atalho libera o script SO para esta chamada, sem mudar a politica da maquina.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar.ps1" %*
