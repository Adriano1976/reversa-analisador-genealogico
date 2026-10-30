@echo off
rem Monta o pacote de distribuicao (analisador.zip) a partir do commit.
rem
rem Existe pelo mesmo motivo do `iniciar.cmd`: a politica de execucao do Windows
rem bloqueia .ps1 sem assinatura nesta maquina, e este atalho libera o script SO
rem para esta chamada, sem mudar a politica da maquina.
rem
rem Uso:  publicar.cmd
rem        publicar.cmd -Revisao v1.0 -Saida C:\Temp\analisador-1.0.zip
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publicar.ps1" %*
