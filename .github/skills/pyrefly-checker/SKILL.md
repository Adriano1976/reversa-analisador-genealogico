---
name: pyrefly-checker
description: Ferramenta ultra-rápida de verificação de tipos estáticos (Type Checking) em Python. Use sempre que gerar, refatorar ou modificar arquivos em src/ antes de realizar commits.
---

# Instruções de Execução
Sempre que você terminar de criar ou alterar uma lógica ou fachada em Python, execute o Pyrefly para garantir conformidade com as regras estritas de tipos do projeto:

```bash
pyrefly check
```

## Tratamento de Falhas
- Se o comando retornar erros de tipo, você **DEVE** analisar as linhas apontadas, corrigir as assinaturas ou anotações de tipo no arquivo correspondente e rodar `pyrefly check` novamente.
- Não declare um caso de uso ou refatoração como concluído até que o Pyrefly retorne 0 erros.
