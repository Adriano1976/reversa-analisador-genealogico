# Legacy Impact: Escolher arquivo da lista

> Identificador: `011-escolher-arquivo-da-lista`
> Data: `2026-10-09`
> Ancoragem: `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` (cenario de legado)
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Arquivos afetados

| Arquivo afetado | Componente (`architecture.md`) | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/ports/__init__.py` | Porta de armazenamento (container da aplicacao) | `regra-nova` | **HIGH** | `listar(dono)` e o **primeiro metodo novo em uma porta** desde a feature 007. O docstring do modulo afirmava que nenhum havia sido criado; a frase foi corrigida, e a de `EntradaArmazenada` entra no `__all__` |
| `src/ports/adaptadores.py` | Adaptador de disco | `regra-nova` | MEDIUM | `listar` le nome e atributos do diretorio, **sem abrir conteudo**. Pasta ausente devolve lista vazia, e nao excecao (`D-07`) |
| `src/utils/validate.py` | Validacao do upload (`domain.md` §3.5) | `regra-nova` | MEDIUM | `decompor_nome_armazenado`, `motivo_de_indisponibilidade` e `pode_ser_usado`. A forma do nome passou a ser montada de `_HEX16` + `_SEPARADOR`, reusados pelo prefixo: uma definicao, nao duas |
| `src/reporting/lista_de_arquivos.py` | Apresentacao (componente NOVO) | `componente-novo` | MEDIUM | Funcao pura que seleciona por extensao, agrupa pela chave, marca o sem-chave, decide o alcance e ordena por data |
| `src/app.py` | Borda HTTP, rota unica | `delta-de-contrato-externo` | **HIGH** | `matches_csv_filename` entra como campo opcional com **precedencia**, e as duas listas passam a alimentar toda renderizacao por processador de contexto |
| `src/templates/index.html` | Tela unica | `delta-de-contrato-externo` | **HIGH** | O ramo `{% if not gedcom_filename %}` deixa de ser formulario de envio e passa a ser as duas abas com as listas |
| `src/core/`, `src/parsers/`, `src/application/` | Nucleo | **sem mudanca** | — | `git diff --stat` **vazio** (T026). A paridade de 100 % e a prova |
| `_reversa_sdd/screens/golden/` | Goldens de tela | **sem mudanca** | — | `git status` vazio e sha256 `ec07f71b4084269a` (T027) |
| `_reversa_sdd/parity/harness.py` | Instrumento de paridade | **sem mudanca** | — | E a insensibilidade dele ao template que a T024 mediu em 100 % |

## 2. Diff conceitual por componente

**Porta e adaptador.** A listagem entra pela porta, e nao por `os.listdir` na rota, porque a feature
006 tirou o acesso a disco da borda. O que a listagem le do arquivo sao atributos do sistema de
arquivos, nunca o conteudo: e o que evita reler 29 MB por renderizacao.

**Apresentacao.** Toda regra de tela mora numa funcao **pura**: selecao por extensao do nome visivel,
agrupamento pela chave, marca do sem-chave, rotulo sem chave vazada e ordem por data decrescente. Ela
nao abre arquivo, entao e testavel sem disco e sem fronteira.

**Borda.** O `GET /` entrega as duas listas em toda renderizacao, e o ramo `dna_analysis` aceita a
referencia do CSV. O caminho antigo — arquivo em `files` — fica **intocado**: e aditivo de proposito,
para que a paridade e os testes de rota continuem exercitando o contrato de hoje.

## 3. Preservadas (regras 🟢 de `domain.md` que continuam intactas)

- `domain.md:139` — a **forma fechada** do nome (`^[0-9a-f]{16}__[A-Za-z0-9._-]+$`) continua sendo a
  defesa contra escape da pasta, e continua **sem lista negra**. A `011` a **reusa** em vez de
  reimplementar.
- `domain.md:140` — a extensao original e preservada no nome visivel. E a base factual de `RN-03`/`RN-09`.
- `domain.md:141` — a chave de conteudo e o identificador que circula entre requisicoes. A `011`
  **estende** o mecanismo ao CSV; nao inventa um segundo.
- `domain.md:164` — `GET /` renderiza a unica tela, **sem estado**. A feature nao cria rota nova.
- `domain.md:166` — qualquer outro `action` exige `gedcom_filename` com forma valida e arquivo existente.
- `domain.md:192` — `"Por favor, carregue o arquivo CSV de matches."` continua literal, e ha teste
  prendendo (T009).
- `RN-05` a `RN-08` — a aplicacao segue sem estado entre requisicoes, escolher nao altera nem copia
  arquivo, e as tres `action` mantem nome e campos.

## 4. Modificadas (regras 🟢 alteradas)

- **`domain.md` §4, linha de `action=dna_analysis`.** A pre-condicao 🟢 "CSV presente" passa a
  **"CSV presente ou referencia presente"**. O caminho antigo continua valido; o que deixa de valer e a
  leitura **literal** da linha, que vira uma disjuncao. Declarada no `roadmap.md` §5 como
  `regra-alterada`, e levada ao adendo pela `T032`.

## 5. Divergencia declarada, e o que NAO foi resolvido

**A aplicacao atual deixa de ter o estado inicial do legado** ("envie um arquivo antes de tudo"). O
pipeline de migracao foi desenhado sobre essa tela (`_reversa_sdd/migration/`, cenarios
`@paridade-visual` ancorados em `SCR-001`). Nada fica errado, mas quem ler o pipeline precisa saber
(`D-06`).

**Conflito entre features, RESOLVIDO em 2026-10-09.**
`tests/test_icone_de_atalho.py::test_a_tela_nao_mudou_um_byte` prendia o `GET /` por **SHA fixo**, e a
mensagem do proprio teste declarava que o sujeito da regra era a feature 009 ("Esta feature NAO pode
tocar no template"). Escrita como SHA do mundo, a assercao virou absoluta, e a `011` mudou a tela por
decisao declarada (`D-04`). **Resolucao:** a constante foi **atualizada** (`4b7f0b0c…` → `e18d1749…`, de
23.906 para 25.825 bytes) e o comentario dela passou a registrar quem mudou a tela e por que. Nao foi
afrouxamento — o comentario anterior da propria constante ja declarava o criterio: "qualquer mudanca
aqui e mudanca de tela, e nao desta feature". O teste segue prendendo que nenhuma mudanca de tela passe
despercebida. A suite final e **381 passed, 9 skipped, zero falhas**.

**Defeito de raiz fora do escopo, registrado como bug proprio.** O gravador preserva acento e espaco no
nome visivel, e o resolvedor os recusa: **7 dos 19 arquivos** ficaram inalcancaveis por referencia. A
`011` **marca** o item indisponivel (`RN-11`, `D-11`) e **nao** conserta o contrato do nome. Ver
`BUG-20261009-6RKP`.
