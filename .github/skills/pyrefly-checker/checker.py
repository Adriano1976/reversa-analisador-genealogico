#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
from pathlib import Path

def run_pyrefly_analysis():
    # Caminho da raiz do projeto ancorada a partir de .agents/skills/pyrefly_checker/
    root_dir = Path(__file__).resolve().parents[3]
    toml_config = root_dir / "pyrefly.toml"
    
    print(f"[*] [Pyrefly Universal] Iniciando verificação de tipos na raiz: {root_dir}")
    if not toml_config.exists():
        print("[!] Aviso: pyrefly.toml não localizado na raiz. Usando definições padrão do interpretador.")

    try:
        # Execução segura adaptada para o ambiente Windows e tratamento do ciclo de vida do Harness
        result = subprocess.run(
            ["pyrefly", "check"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode == 0:
            print("\n[SUCESSO] Todos os arquivos Python (.py) estão em conformidade estrita de tipos! 0 erros.")
            sys.exit(0)
        else:
            print("\n[FALHA DE VALIDAÇÃO] O Pyrefly detectou inconsistências de tipo no código:")
            print("-" * 70)
            print(result.stdout)
            print(result.stderr)
            print("-" * 70)
            print("[DIRETRIZ AGENTE] Analise as linhas apontadas, ajuste as anotações de tipo e re-execute a validação.")
            sys.exit(1)
            
    except FileNotFoundError:
        print("[ERRO CRÍTICO] Executável 'pyrefly' não encontrado. Certifique-se de que o .venv está ativo.")
        sys.exit(2)

if __name__ == "__main__":
    run_pyrefly_analysis()
