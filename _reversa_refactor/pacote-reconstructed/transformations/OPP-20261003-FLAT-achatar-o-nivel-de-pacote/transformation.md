---
schema_version: 1
id: OPP-20261003-FLAT
verb: modularize
state: applied
safety_net:
  kind: existing
  green_before: true
  green_after: true
preservation:
  method: tests
  evidence:
    - safety-net/estrutura.txt
    - safety-net/suite-depois.txt
    - safety-net/paridade-depois.txt
measurement:
  before: "o nivel de pacote `reconstructed/` com quatro subpacotes dentro; 18 modulos; nenhum pacote de primeiro nivel em src/"
  after: "quatro pacotes de primeiro nivel em src/; `reconstructed/` apagado; 18 modulos; 12 imports relativos entre subpacotes convertidos em absolutos e 31 prefixos `reconstructed.` removidos"
change_set:
  - chg: CHG-001
    file: core/, parsers/, reporting/ e utils/ sobem para src/, e src/reconstructed/__init__.py e o diretorio sao apagados
    purpose: eliminar o nivel de pacote que expressava proveniencia e nao responsabilidade
  - chg: CHG-002
    file: seis modulos do nucleo
    purpose: `from ..X` deixa de ser valido quando os pacotes sao de primeiro nivel; os 12 imports entre subpacotes viram absolutos
  - chg: CHG-003
    file: src/app.py, oito arquivos de teste e dois scripts do harness
    purpose: o prefixo `reconstructed.` sai das 31 linhas de import
  - chg: CHG-004
    file: dez citacoes em prosa, o README e o pyrefly.toml
    purpose: ajustar os caminhos citados, incluindo as duas linhas de codigo do script de contraprova
  - chg: CHG-005
    file: _reversa_forward/003-renomear-pasta-app-para-src/regression-watch.md
    purpose: reescrever a condicao vigiada pelo `W001` para a nova identidade do nucleo
approval:
  by: user
  at: 2026-10-03
reversible_via:
  - CHG-001-movimentacao.diff
  - CHG-002-relativo-vira-absoluto.diff
  - CHG-003-prefixo-sai-do-import.diff
  - CHG-004-prosa-e-readme.diff
  - CHG-005-watch-w001.diff
---

## O que foi feito

Os quatro subpacotes subiram um nivel e o nivel que os continha foi apagado:

    ANTES                                   DEPOIS
    src/                                    src/
    ├── app.py                              ├── app.py
    ├── templates/                          ├── core/
    ├── uploads/                            ├── parsers/
    └── reconstructed/                      ├── reporting/
        ├── __init__.py        (apagado)    ├── utils/
        ├── core/                           ├── templates/
        ├── parsers/                        └── uploads/
        ├── reporting/
        └── utils/

`src/reconstructed/__init__.py` foi removido, e com ele o diretorio. **Nada entrou no lugar**: nenhum `src/__init__.py`, que a `RN-01` proibe.

## A consequencia que fica declarada

Os imports entre subpacotes **deixaram de poder ser relativos**. Antes, `parsers/` e `utils/` eram irmaos dentro de `reconstructed`, e `from ..utils.text_cleaning import demojibake` funcionava porque existia um pacote pai. Agora os quatro sao pacotes de **primeiro nivel**, sem pai, e `from ..algo` e invalido: os **12** imports que cruzam fronteira viraram **absolutos**.

Ficou relativo apenas o que nao cruza fronteira, como `from .gedcom_state import get_name`.

## Medicao

| Metrica | Antes | Depois |
|---|---|---|
| Niveis de pacote ate um modulo do nucleo | 2 | **1** |
| Pacotes de primeiro nivel em `src/` | 0 | **4** |
| `reconstructed/` | existe | **apagado** |
| Modulos | 18 | 18 |
| Imports relativos entre subpacotes | 12 | **0** |
| Imports com o prefixo `reconstructed.` | 31 | **0** |
| Citacoes em prosa ajustadas | 0 | 10 |
| Linhas de logica alteradas | 0 | **0** |

## O que nenhum gate enxerga, pela quarta vez

O `_reversa_sdd/parity/_verify_fix_gives_parity.py` tinha **codigo**, e nao comentario, apontando para o diretorio que esta transformacao apaga:

    SRC  = os.path.join(ROOT, "src", "reconstructed")
    STUB = os.path.join(ROOT, ".parity-stub", "reconstructed")

Depois do achatamento ele copiaria um diretorio inexistente e estouraria `FileNotFoundError`. **Nada avisaria**: ele nao e executado pela suite nem pelo harness de paridade, entao os dois gates ficariam verdes enquanto a ferramenta de contraprova apodrecia.

E a **quarta aparicao** dessa classe de defeito na serie, e a **segunda seguida no mesmo arquivo**: na `RAIZ` foi a linha do `alvo`, agora as duas de origem. As duas viraram `os.path.join(ROOT, "src")` e `os.path.join(ROOT, ".parity-stub")`, e a conferencia passou a verificar **os tres** caminhos montados pelo script, e nao so o `alvo`.

## O watch W001, reescrito

O `W001` vigiava o nome do pacote do nucleo, `reconstructed.*`, e esta transformacao apaga esse nome. Pela regra do framework, um watch disparado precisa ser avaliado, e a avaliacao e:

- **nenhuma regra de negocio muda**: as mensagens de contrato, os limiares e o grafo ficam intactos;
- **o comportamento e provado**: suite na linha de base e paridade em 100 por cento;
- **o que muda e a identidade do pacote**, e por isso a condicao vigiada foi reescrita para `parsers.*`, `core.*`, `reporting.*` e `utils.*`, direto de `src/`.

Sem isso o watch ficaria permanentemente vermelho e deixaria de servir de aviso. A observacao `O5` do mesmo arquivo perde o objeto, porque o `__init__.py` que ela cita deixou de existir, e isso esta anotado na atualizacao.

## Risco novo, medido

`core`, `parsers`, `reporting` e `utils` passaram a ser nomes de pacote de primeiro nivel. Medido em `.venv/Lib/site-packages`: **os quatro estao livres**. Nao ha colisao hoje.

O risco fica declarado e nao realizado: uma dependencia futura com um desses nomes disputaria a resolucao, e a disputa seria silenciosa. `search-path = ["src"]` no `pyrefly.toml` e o `sys.path.insert(0, .../src)` dos testes mantem `src` a frente.

## Fronteira da alma

| Fonte | Situacao |
|---|---|
| principio II (comportamento observavel preservado) | preservado: zero linha de logica alterada |
| regra dura do verbo (nao fundir o que o projeto separou) | respeitada: as quatro fronteiras de subpacote continuam intactas |
| `.reversa/soul.md#entidades-centrais` e `#decisoes-fundadoras` | preservadas: nenhuma entidade, nenhum grafo e nenhuma mensagem de contrato foi tocada |
| `RN-01` (o diretorio do codigo e raiz de caminho, nao pacote) | **reforcada**: e por ela que nao se cria `src/__init__.py`, e que `search-path = ["src"]` continua valendo |

## Rede de seguranca

| Instrumento | Antes | Depois |
|---|---|---|
| Suite de testes | 118 aprovados, 15 erros de ambiente | **118 aprovados, 15 erros de ambiente** |
| Paridade com o oraculo congelado | 100 por cento em 6 fixtures | **100 por cento, zero divergencia em 6 fixtures** |
| Resolucao de import por AST | instrumento da `RAIZ` | **134 imports em 30 arquivos, todos resolvem** |
| Coletores dentro de string | 5 + 2 imports | **todos resolvem** |
| `from ..` restante | 12 | **0**, conferido por varredura |
| `reconstructed.` em import | 31 | **0**, conferido por varredura |
| Caminhos dos scripts de instrumentacao | so o `alvo` | **`SRC`, `STUB` e `alvo`, os tres existem** |
| AST dos 18 arquivos | copia congelada antes de tocar | **codigo identico nos 18** |
| Arvore do README contra o disco | 14 x 14 | **bate, arquivo por arquivo** |
| Nome de primeiro nivel livre | 4 livres | **4 livres** |

## Nota de metodo

O estado anterior de `src/` veio da copia congelada em `before-after/src-antes/`, tirada antes do achatamento, com o nivel `reconstructed/` ainda no lugar. O dos arquivos fora de `src/` veio do inverso exato das duas regras de import, com a contagem conferida: 12 e 31. O `README.md`, o `pyrefly.toml` e o `regression-watch.md` vem do `HEAD`, que para esses tres e o estado anterior, porque nenhuma transformacao nao commitada os havia tocado.

## Pendencias

- `OPP-20261003-PAST`: os quatro nomes do exemplo, agora com as pastas no lugar definitivo.
- `OPP-20261003-INIT`: segue com recomendacao de nao rotear.
- `README.md` do registro de refactor continua dizendo que o harness "nao pode mais rodar" e que a suite tem 76 testes.
- `_reversa_sdd/` e `_reversa_docs/` continuam com os caminhos antigos, e agora tambem com o nivel `reconstructed`, que deixou de existir.
