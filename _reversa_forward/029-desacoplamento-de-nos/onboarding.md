# Onboarding: como testar a árvore sugerida pela primeira vez

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Público: quem vai rodar a feature pela primeira vez, sem conhecer o código.
> Tempo estimado: 10 minutos, dos quais 2 são da suíte.

## 1. Antes de começar

| Item | Como conferir |
|------|----------------|
| Python oficial do projeto | `.venv\Scripts\python --version` → `3.14.6` |
| `networkx` presente | `.venv\Scripts\python -c "import networkx; print(networkx.__version__)"` → `3.7` |
| Diretório correto | o terminal está na raiz do projeto (a pasta que contém `src/` e `tests/`) |
| Banco de dados | **não é necessário**. A feature não lê nem grava banco |

> ⚠️ **A árvore sugerida não corrige o GEDCOM.** Ela é uma hipótese em memória, com gerações
> numeradas (`Geração 1`, `Geração 2`, …) que **não são pessoas**. Nada é gravado em disco: nem o
> arquivo enviado, nem um `.ged` novo, nem uma linha no banco. Se você mostrar a sugestão para
> alguém, diga que é sugestão.

## 2. Rodar só os testes da feature

```powershell
.venv\Scripts\python -m pytest tests/test_cirurgia_do_grafo.py tests/test_sugestao_de_correcao.py tests/test_fronteira_da_cirurgia.py tests/test_correcao_de_arquivos.py -q
```

Esperado: todos passam. Se algum falhar, o nome do teste diz qual invariante quebrou:

| Teste que falha | Invariante violado |
|-----------------|--------------------|
| `test_nao_muta_o_grafo_recebido` | A cirurgia mexeu no grafo original (RN-02) |
| `test_ramo_base_fica_intacto` | O ramo do doador foi alterado (RN-01) |
| `test_ids_sao_deterministicos` | Id depende de hash, `id()` ou ordem de inserção (RN-10) |
| `test_casamento_nao_e_cortado` | Aresta de afinidade tratada como filiação (RN-05) |
| `test_virtual_nao_tem_nome_nem_data` | Nó virtual fabricou pessoa (RN-11) |
| `test_sem_sugestao_quando_validado` | Sugestão emitida para status que não é erro (RN-03) |

## 3. Rodar a suíte inteira

```powershell
.venv\Scripts\python -m pytest -q
```

Baseline antes desta feature: **1083 passam, 9 pulados, 0 falham**. A contagem sobe com os testes
novos; nenhum teste antigo pode passar a falhar.

## 4. Ver a sugestão nascer, passo a passo

Cole o bloco abaixo na raiz do projeto (`.venv\Scripts\python -` ou um arquivo `teste_rapido.py`):

```python
import sys, tempfile
sys.path.insert(0, ".")      # para `tests.fixtures...`
sys.path.insert(0, "src")    # para `core`, `application`, `parsers`

from core.cirurgia_do_grafo import arvore_sugerida
from core.documentary_relationship import documentary_relationship
from core.registro import get_name
from core.validator import ComparacaoParaValidar, validar_comparacao
from parsers.gedcom_parser import carregar_arvore
from tests.fixtures.arvore_para_cirurgia import GED_SALTO_IMPOSSIVEL

# 1. O GEDCOM sintético vira arquivo temporário (o parser lê caminho, não texto).
with tempfile.NamedTemporaryFile("w", suffix=".ged", delete=False, encoding="utf-8") as fh:
    fh.write(GED_SALTO_IMPOSSIVEL)
    caminho = fh.name

# 2. A árvore é carregada UMA vez e o resto trabalha sobre ela.
arvore = carregar_arvore(caminho)
doador_id = next(pid for pid, p in arvore[0].items() if "Doador" in get_name(p))
match_id = next(pid for pid, p in arvore[0].items() if "Match" in get_name(p))

# 3. O parentesco documental: é daqui que sai o `path` que a cirurgia precisa.
documental = documentary_relationship(arvore, doador_id, match_id)
print("caminho:", documental["path"]["names"], "graus:", documental["degrees"])

# 4. O veredito da feature 028 — é ele que dispara a sugestão.
resultado = validar_comparacao(ComparacaoParaValidar(
    doador={"id": doador_id, "nome": get_name(arvore[0][doador_id]), "nascimento": "1985"},
    match={"id": match_id, "nome": get_name(arvore[0][match_id]), "nascimento": "1950"},
    documental=documental,
    kit={"kit": "A1", "total_cm": 25.0},
    ano_referencia=2026,
    intervalo_de_geracao=25.0,
))
print("status:", resultado["status"], "| códigos:", [c["codigo"] for c in resultado["codigos"]])

# 5. A sugestão.
sugestao = arvore_sugerida(arvore, documental, resultado, doador_id)
print("natureza:", sugestao["natureza"])
print("hiato:", sugestao["hiato"])
print("junção:", sugestao["juncao"])
print("gerações virtuais:", [g["label"] for g in sugestao["geracoes_virtuais"]])
print("grafo tem", sugestao["grafo"].number_of_nodes(), "nós e", sugestao["grafo"].number_of_edges(), "arestas")
```

### O que olhar no resultado

1. **`status`** deve ser `ERRO CRONICO / QUEBRA DE LINHA` — se for `VALIDADO`, a sugestão vem `None`
   com `SUGESTAO_INDISPONIVEL`, e isso é o comportamento correto.
2. **`natureza`** é sempre `"sugestao"`. Se algum dia vier outra coisa, o contrato foi quebrado.
3. **`hiato`** mostra `calculado` (o que o cM pediu) e `aplicado` (quantos nós entraram). Se vier
   `SUGESTAO_INSUFICIENTE` nos avisos, a cadeia injetada ainda não fecha a conta dos 12–70 anos por
   geração — a sugestão é curta por construção, não por defeito.
4. **`ramo_base.intacto`** deve ser `True`. É a prova de que o ramo do doador não foi tocado.
5. **`geracoes_virtuais[*].label`** são `Geração 1`, `Geração 2`, … — nunca nomes de pessoa.

## 5. Provar que o original não mudou

No mesmo processo, antes e depois da chamada:

```python
antes = (sorted(arvore[2].nodes()), sorted(arvore[2].edges()))
sugestao = arvore_sugerida(arvore, documental, resultado, doador_id)
depois = (sorted(arvore[2].nodes()), sorted(arvore[2].edges()))
print("original intacto:", antes == depois)   # tem de ser True
```

## 6. Testar com o seu GEDCOM (opcional)

1. Copie o arquivo para uma pasta **fora do repositório** (nunca em `uploads/`, nunca commitado —
   princípio I do projeto).
2. Troque `caminho` pelo caminho absoluto do seu arquivo e ajuste `nome_doador` para o seu nome.
3. Rode os passos 2 a 5.
4. Confira de olho: o `juncao` aponta para a família que você reconhece como a fronteira do erro? Se
   apontar para outro lugar, o caminho documental escolhido foi outro — comece conferindo
   `documental["path"]["names"]`.

## 7. O que **não** fazer

| Não faça | Por quê |
|----------|---------|
| Passar `sugestao["grafo"]` para `documentary_relationship` | Os nós virtuais não existem em `people`; os leitores devolveriam `[]` em silêncio |
| Gravar `sugestao` em `uploads/` | A pasta é imutável por conteúdo; um `.ged` com pessoa sem nome é lido como arquivo corrompido |
| Tratar `Geração 3` como pessoa ao citar o resultado | É posição estimada, não indivíduo |
| Editar o GEDCOM original para "aplicar" a sugestão | O sistema não corrige documento; a decisão é do operador, no arquivo dele |

## 8. Problemas comuns

| Sintoma | Causa provável | Saída |
|---------|----------------|-------|
| `ModuleNotFoundError: core` | faltou `sys.path.insert(0, "src")` | ver passo 4 |
| `ModuleNotFoundError: tests` | rodou de dentro de `tests/` | rode da raiz do projeto |
| `sugestao["grafo"] is None` | status não é erro, ou hiato ≤ 0, ou caminho por afinidade | leia `sugestao["avisos"]`: o código diz qual dos casos é |
| `JUNCAO_NAO_LOCALIZADA` | o salto não tem família localizável (`FAMC`/`CHIL` ausente) | é limitação do GEDCOM, não da cirurgia; o aviso cita o salto |
| `SUGESTAO_INSUFICIENTE` | o cM estimou menos gerações do que a janela exigiria | comportamento declarado; a sugestão não finge resolver |
| pytest aborta a coleta com `PermissionError` | diretório preso sob `tests/` | ver `tests/conftest.py` §4 |

## 9. Onde ler mais

- Regras e contrato: `_reversa_forward/029-desacoplamento-de-nos/requirements.md` (§4 e §4.7)
- Decisões técnicas: `_reversa_forward/029-desacoplamento-de-nos/roadmap.md` (§3)
- Por que cópia, família sintética e id por conteúdo:
  `_reversa_forward/029-desacoplamento-de-nos/investigation.md`
- Estruturas e atributos: `_reversa_forward/029-desacoplamento-de-nos/data-delta.md`
- O veredito que dispara tudo: `_reversa_sdd/addenda/028-validador-de-dados-dna.md`
