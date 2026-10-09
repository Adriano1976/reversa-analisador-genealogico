# Adendo 011: Escolher arquivo da lista

> Vigente desde 2026-10-09.
> Feature: `_reversa_forward/011-escolher-arquivo-da-lista/`
> Convergido por `/reversa-sync` (`T032`).

## 1. O que esta feature muda na spec efetiva

Esta e a **primeira feature que altera a tela de entrada desde a reconstrucao do legado**, e ela muda
tres contratos ao mesmo tempo. O nucleo nao e tocado.

| Artefato | Secao | Tipo de impacto | O que muda |
|---|---|---|---|
| `upload-gedcom/contracts.md` | §2.1 (nome armazenado) | `delta-de-dados` | **Nada muda no formato.** A feature passa a **ler** a pasta que ja existia, e o nome continua `<16 hex>__<nome visivel>` |
| `analise-dna/contracts.md` | §1 (requisicao da analise) | `delta-de-contrato-externo` | A analise passa a aceitar o CSV por **referencia** (`matches_csv_filename`), alem do arquivo. O campo de arquivo **permanece**, e a referencia tem **precedencia** |
| `openapi/index.yaml` | `RequisicaoAnaliseDna` (linhas 164-186) | `delta-de-contrato-externo` | `matches_csv` deixa de ser **sempre** obrigatorio: a pre-condicao vira disjuncao. O `required` da linha 167 passa a ser condicional |
| `_reversa_sdd/domain.md` | §4, linha de `action=dna_analysis` | `regra-alterada` | A pre-condicao 🟢 **"CSV presente"** passa a **"CSV presente ou referencia presente"**. A leitura literal da linha deixa de valer |
| `_reversa_sdd/architecture.md` | §7, divida 8 (estado entre requisicoes) | `regra-removida` | **Nada e removido.** Esta linha existe para declarar que a divida **continua aberta** e que a feature nao a fechou: a escolha do operador nao sobrevive ao fechamento da pagina |
| `src/templates/index.html` | ramo `{% if not gedcom_filename %}` | `componente-extinto` | O **estado inicial de envio obrigatorio** deixa de existir: o `GET /` entrega as duas abas com as listas, e o envio se muda para dentro da aba |
| `interfaces/formulario-http.md` · `openapi/index.yaml` | contrato do formulario | `delta-de-contrato-externo` | **Quarta `action`**: `selecionar_arvore`, com `gedcom_filename` no `form`. Acrescentada em 2026-10-09, depois de medida a tela: a lista era **texto puro** e nao havia como escolher arvore nenhuma. O `RN-08` passa a falar de quatro `action`, e nenhum campo existente mudou |
| `_reversa_sdd/screens/golden/SCR-001` | golden da tela inicial | `delta-de-dados` | **Nao e recapturado.** Ele captura o **oraculo legado congelado**, e um oraculo congelado nao deixa de valer porque o candidato mudou. O que existe e divergencia declarada |

## 2. O que NAO muda, e por que isso importa

- **O nucleo.** `src/core/`, `src/parsers/` e `src/application/` com `git diff --stat` **vazio** (`T026`).
- **Os goldens.** `git status` do diretorio vazio, sha256 `ec07f71b4084269a` (`T027`).
- **O instrumento de paridade.** `harness.py` byte a byte igual, e a **paridade continua 100 %** (`T024`).
  A premissa de que ele e insensivel ao template foi lida no codigo na investigacao e **medida por
  execucao** nesta rodada.
- **A pasta de uploads.** Nenhuma acao da feature escreve nela: o conjunto de `sha256` e **identico**
  antes e depois de percorrer todas as telas (`T025`, `RF-08`).
- **As tres `action`.** `upload_gedcom`, `path_search` e `dna_analysis` mantem nome e campos (`RN-08`).

## 3. Regras novas que a feature cria

| Regra | Enunciado | Origem |
|---|---|---|
| `RN-03` | A aba de arvore lista o nome visivel que termina em `.ged`; a de DNA, `.csv` | requisito |
| `RN-09` | A lista seleciona por extensao do nome visivel, **sem ler conteudo**; a recusa acontece no uso | decisao da §9 |
| `RN-10` | Arquivo **sem chave** no nome vira item proprio, marcado | decisao da §9 |
| `RN-11` | Item cujo arquivo **nao pode ser usado por referencia** e exibido com a marca de indisponivel e o motivo, e **continua na lista** | **auditoria de 2026-10-09**, apos medir 7 de 19 arquivos inalcancaveis |
| `RN-12` | O item da lista de arvores e um **controle submetivel** (`action=selecionar_arvore`); o item indisponivel continua listado e **nao** ganha botao de escolha | **medicao no navegador em 2026-10-09**: a lista era texto puro, sem `select`, radio, link ou formulario, e o `RF-02` nao estava satisfeito |
| `RF-09` | A lista marca o item inalcancavel, com o motivo, sem esconde-lo | idem |

## 4. Divergencias declaradas

1. **A aplicacao atual perde o estado inicial do legado.** O pipeline de migracao
   (`_reversa_sdd/migration/`, 35 arquivos, cenarios `@paridade-visual` ancorados em `SCR-001`) foi
   desenhado sobre a tela antiga. Nada fica errado, mas a divergencia precisa ser lida (`D-06`).
2. **Conflito com a feature 009, RESOLVIDO em 2026-10-09.** `test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte`
   prendia o `GET /` por SHA fixo. A constante foi **atualizada** (`4b7f0b0c…` → `e18d1749…`, de 23.906
   para 25.825 bytes), com o comentario registrando quem mudou a tela e por que. Nao foi afrouxamento: o
   comentario anterior da propria constante declarava o criterio — "qualquer mudanca aqui e mudanca de
   tela, e nao desta feature". A suite final e **381 passed, 9 skipped, zero falhas**.

## 5. O que este adendo NAO faz

- **Nao fecha o `BUG-20261009-6RKP`.** O gravador preserva acento e espaco no nome visivel, o resolvedor
  os recusa, e 7 dos 19 arquivos ficam inalcancaveis por referencia. A `011` **marca** o item
  indisponivel e **nao** conserta o contrato do nome — consertar mexe na defesa contra escape de
  caminho, e isso e trabalho do bug, com auditoria propria.
- **Nao recaptura golden nenhum.**
- **Nao fecha a divida 8** (`architecture.md` §7): a aplicacao continua sem estado entre requisicoes.
