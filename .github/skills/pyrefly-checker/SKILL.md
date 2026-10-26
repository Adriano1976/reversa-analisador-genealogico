---
name: pyrefly-checker
description: Verificação de tipos com o Pyrefly sob a régua do pyrefly.toml. Use ao criar, alterar ou revisar qualquer arquivo Python — e diga sempre contra qual régua o resultado foi obtido.
---

# pyrefly-checker

## A régua está no projeto, não na skill

O que conta como erro vem do `pyrefly.toml` mais próximo:

- `preset` — o do projeto; `default` quando ninguém declara;
- `[[sub-config]]` — pode endurecer um subtree; neste repositório,
  `src/ports/**` trata `implicit-any-*` como erro;
- `project-excludes` — define o que nem entra na conta.

**Todo relatório cita a régua.** "0 erros" sem dizer contra o quê não significa nada.

## Como rodar

```powershell
# alvo da tarefa (o normal)
.\.venv\Scripts\python.exe .github\skills\pyrefly-checker\checker.py src\ports

# um arquivo
.\.venv\Scripts\python.exe .github\skills\pyrefly-checker\checker.py src\ports\adaptadores.py

# flags do check são repassadas
.\.venv\Scripts\python.exe .github\skills\pyrefly-checker\checker.py src\ports -p strict
```

O script usa `sys.executable -m pyrefly`: não depende do PATH nem de venv ativado.
Nesta máquina existe também o `pyrefly-verify` global, que imprime a régua e agrega
por diretório; o `checker.py` é a entrada portátil da skill.

## Códigos de saída

| Código | Significado | Ação |
|---|---|---|
| 0 | nenhum diagnóstico | concluído |
| 1 | problemas de tipo | corrija o que a mudança tocou |
| 2 | não deu para rodar (ambiente, config, caminho) | conserte o setup, **não** o código |

## Regras

1. Não declare concluído com exit 1 no alvo que você alterou.
2. Exit 2 não é erro de tipo — não altere código por causa dele.
3. `pyrefly check` no projeto inteiro tem passivo conhecido: 247 diagnósticos,
   todos em `tests/`. `src/` está em zero e é o portão — não zere `tests/` à força.
4. `# pyrefly: ignore[código]` é exceção justificada, não primeira escolha; quando
   usar, escreva o motivo no comentário.
5. O portão de CI (`tipos`) roda `pyrefly check src/ports` e o `checker.py`.
