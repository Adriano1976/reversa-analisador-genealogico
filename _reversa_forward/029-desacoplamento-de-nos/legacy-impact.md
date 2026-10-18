# Legacy Impact: desacoplamento de nós e gerações virtuais

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/cirurgia_do_grafo.py` | `core.cirurgia_do_grafo` | componente-novo | HIGH | Novo núcleo de decisão sobre a **estrutura** do grafo — a primeira função do projeto que produz uma variante da árvore |
| `src/application/correcao.py` | `application.correcao` | componente-novo | MEDIUM | Fachada de leitura sobre arquivos; não é ligada à borda HTTP e não persiste nada |
| `src/application/validacao.py` | `application.validacao` | regra-nova | HIGH | Ganha o parâmetro aditivo `incluir_documental`; sem ele, o retorno é o mesmo de antes |
| `tests/fixtures/arvore_para_cirurgia.py` | `tests.fixtures` | artefato-novo | LOW | Quatro GEDCOMs sintéticos e quatro CSVs; nenhum dado real |
| `tests/test_cirurgia_do_grafo.py` | `tests` | artefato-novo | LOW | 16 testes unitários das funções de cirurgia |
| `tests/test_sugestao_de_correcao.py` | `tests` | artefato-novo | LOW | 14 testes do contrato e dos códigos de aviso |
| `tests/test_fronteira_da_cirurgia.py` | `tests` | artefato-novo | LOW | 3 testes de pureza do núcleo |
| `tests/test_correcao_de_arquivos.py` | `tests` | artefato-novo | LOW | 5 testes de integração da fachada |
| `tests/test_validacao_de_arquivos.py` | `tests` | regra-alterada | LOW | Um teste novo fixa a emenda aditiva da `028` |

**Arquivos que NÃO mudaram:** `src/app.py`, `src/templates/index.html`, `src/assets/app.css`,
`init.sql`, `requirements.txt`, `docker-compose.yml`, `src/parsers/*`, `src/core/validator.py`,
`src/core/documentary_relationship.py`, `src/core/path_finding.py` e todas as tabelas do PostgreSQL.

## 2. Diff conceitual por componente

### 2.1 `core.cirurgia_do_grafo` (novo)

O sistema até aqui só **lia** o grafo: extração, busca de caminho, parentesco documental e
validação nunca produziam uma variante da árvore. Este componente é o primeiro que transforma
estrutura, e por isso carrega três invariantes explícitos:

- o **ramo base** (doador → ancestral, com as famílias do caminho) é protegido: ids, rótulos e
  datas não mudam, e as arestas internas dele não são removidas — só a aresta da junção fica de
  fora, porque é ela que a cirurgia corta;
- a **árvore recebida não é mutada**: `desacoplar_identidade` devolve `grafo.copy()` e
  `injetar_geracoes` é o único ponto que escreve, sempre sobre a cópia;
- os nós sintéticos usam `type="virtual"` / `"virtual-family"`, id derivado do conteúdo
  (`VIRTUAL:<doador>:<ancestral>:<lado>:<k>`) e **não** têm nome, sexo nem data exata.

A representação bipartida do grafo é o que determina o desenho: como não existe aresta
pessoa↔pessoa, cada geração virtual precisa de um nó de pessoa **e** de um nó-família. A última
ligação reaproveita a família de origem, para não deixar o filho do ancestral órfão.

### 2.2 `application.correcao` (novo)

Fachada fina: chama `validar_arquivos` com `incluir_documental=True` e monta uma sugestão por
comparação. Não tem parser, não tem matching e não tem veredito próprios — se tivesse, haveria
duas verdades sobre a mesma pergunta.

### 2.3 `application.validacao` (emenda aditiva)

`validar_arquivos` ganha `incluir_documental: bool = False`. Com `True`:

- cada item de `comparacoes` recebe a chave `documental` (o **mesmo** dicionário já montado no
  laço, sem cópia);
- o retorno recebe a chave `arvore` (a tupla já parseada).

Com `False`, nada muda: são as mesmas chaves de antes, o que o teste
`test_incluir_documental_e_aditivo_e_desligado_por_padrao` congela.

## 3. Preservadas

Regras 🟢 do `_reversa_sdd/domain.md` que continuam intactas:

| Regra | Onde | Por que não foi tocada |
|-------|------|------------------------|
| Os três eixos não se contaminam | `domain.md#2` | O DNA continua não reescrevendo o vínculo do GEDCOM: a sugestão é um valor à parte |
| Os quatro estados do confronto | `domain.md#21` | `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e `INCONCLUSIVO` não são lidos nem escritos |
| Caminho por filiação, teto de 20 iterações | `domain.md#31` | A cirurgia usa o caminho que já existe; não faz busca própria |
| 12–70 por salto não invalida o vínculo | `domain.md#31` | A faixa é usada só para **conferir** a cadeia sugerida; o vínculo do GEDCOM segue como está |
| Caminhos múltiplos nunca são descartados | `domain.md#31` | A cirurgia altera o caminho principal; os alternativos não são reescritos |
| cM por kit, nunca somado | `domain.md#32` | A sugestão é por comparação, um kit por vez |
| SCP 4.0 com 27 relações publicadas | `domain.md#33` | A estimativa vem de `core.validator`, sem tabela nova |
| `core/` não importa `parsers/` | `architecture.md#3` | Garantido pelo teste de fronteira, e o módulo só importa `core/` e `math` |
| `None` significa "não sei" | `architecture.md#4` | `grafo=None` e `nascimento_estimado=None` seguem a mesma convenção |
| A árvore não é duplicada no banco | `architecture.md#4` | Nenhuma escrita; a cópia vive só em memória |
| Aposentar em vez de apagar | `ADR-30` | A cirurgia não remove nó nenhum do GEDCOM; só muda a ligação externa do ramo |
| Os três status da `028` | `addenda/028-...` | `VALIDADO`, `INCONCLUSIVO` e `ERRO CRONICO / QUEBRA DE LINHA` mantêm texto e uso |

## 4. Modificadas

| Regra | Onde | O que mudou | Severidade |
|-------|------|-------------|------------|
| Contrato de `validar_arquivos` | `addenda/028-validador-de-dados-dna.md`; `requirements.md#45-contrato-do-resultado` da 028 | Ganhou o parâmetro `incluir_documental` e, com ele, as chaves `documental` (por comparação) e `arvore` (no topo). **Aditiva e desligada por padrão**: sem o parâmetro, o retorno é idêntico | HIGH |

Nenhuma regra de domínio foi alterada ou removida. A única modificação é de **contrato interno**,
e ela existe porque o resultado da `028` não carrega `path.ids` — sem isso, a etapa de correção
teria de refazer o laço de matching.

## 5. Verificação de execução

| Verificação | Resultado |
|-------------|-----------|
| Suíte completa no `.venv` | **1122 passam, 9 pulados, 0 falham** (101,46 s) |
| Baseline antes da feature | 1083 passam, 9 pulados |
| Testes novos | **39** (16 + 14 + 3 + 5 + 1) |
| `git status` | apenas os arquivos de §1 e os artefatos de `_reversa_forward/029-*` |
| `app.py`, template, CSS, `init.sql`, `requirements.txt` | intocados |
| Dependência nova | nenhuma (`networkx==3.7` já estava em `requirements.txt:22`) |
