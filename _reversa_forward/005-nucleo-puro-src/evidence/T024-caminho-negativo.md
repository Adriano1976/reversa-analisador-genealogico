# T024 — caminho negativo das guardas de dependência

**Data:** 2026-10-07
**Ação:** `T024` — verificar o caminho negativo do teste de dependências: introduzir
de propósito um import proibido em `src/core/` e confirmar que `T005` falha; depois
revertê-lo.
**Alvo:** `tests/test_dependencias_nucleo.py`

## Por que esta ação existe

Uma asserção estrutural responde "o que este arquivo declara?" — e a resposta pode
ser "nada" por dois motivos opostos: porque o núcleo está limpo, ou porque a
asserção está olhando para o lugar errado. Os dois casos passam. A única forma de
distinguir é fazer a asserção encontrar uma violação real.

Este é o mesmo defeito que o `parity_harness.md` registrou na suíte antiga, onde a
asserção `in ("Sem Nome", "")` não podia falhar. Uma guarda que não pode falhar não
guarda nada — e é pior que nenhuma, porque produz confiança.

## O que foi feito

Diferente das ações `T005`/`T006`/`T007` como escritas, que provam o caminho
negativo contra uma **string sintética** (`ast.parse("import flask")`), aqui a
sonda foi um **módulo real dentro de `src/core/`**. A diferença importa: a string
sintética prova que o predicado funciona, mas não prova que a guarda o aplica aos
arquivos certos — só o módulo real no diretório real prova isso.

Foi criado `src/core/_sonda_t024.py` com três violações simultâneas:

| Violação | O que ela deveria disparar |
| --- | --- |
| `import flask` | `test_core_nao_importa_framework` (`RF-08`) |
| `open(caminho)` | `test_core_nao_faz_io` (`RN-04`) |
| `people = {}` e `versao = 0` em nível de módulo | `test_core_nao_declara_estado_mutavel_de_modulo` (`RF-01`) |

## Resultado medido

```text
FAILED tests/test_dependencias_nucleo.py::test_core_nao_importa_framework
FAILED tests/test_dependencias_nucleo.py::test_core_nao_faz_io
FAILED tests/test_dependencias_nucleo.py::test_core_nao_declara_estado_mutavel_de_modulo
3 failed, 7 passed in 1.19s
```

As três reprovaram, e cada uma apontou o achado concreto em vez de falhar por
acidente:

```text
AssertionError: o nucleo passou a depender de infraestrutura; a paridade deixa
de ser isolavel e a Onda 0 perde valor
AssertionError: o nucleo passou a fazer I/O ou a depender de plataforma; ele deve
ser executavel sobre estruturas em memoria
AssertionError: o nucleo voltou a declarar estado mutavel de modulo. Ele deve
receber a arvore por parametro (RF-01):
    _sonda_t024.py:16  people
    _sonda_t024.py:17  versao
```

## Depois de remover a sonda

`src/core/_sonda_t024.py` apagado — `Test-Path` devolve `False`. As guardas voltam
ao verde por mérito próprio, sem o `xfail` que a de estado carregou até `T023`:

```text
..........                                                               [100%]
10 passed in 0.84s
```

## Conclusão

As três guardas estruturais do núcleo são **discriminantes**. Elas não passam por
vacidade: aplicadas a um módulo que viola as três regras, elas encontram as três —
e no diretório real, que é o que a `T007` precisava garantir e não garantia.

A guarda de estado, em particular, deixou de ser uma afirmação que se sabia falsa
(`xfail`) e passou a ser uma afirmação verdadeira e verificada nos dois sentidos:
passa com o núcleo limpo, falha quando o estado volta.
