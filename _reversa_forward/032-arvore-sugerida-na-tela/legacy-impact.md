# Legacy Impact: árvore sugerida na tela

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/data-dictionary.md`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/cirurgia_do_grafo.py` | `core.cirurgia_do_grafo` | contrato-novo | HIGH | Ganha `resumo_da_sugestao`: o hiato em O(1), sem copiar o grafo |
| `src/core/dna_analysis.py` | `core.dna_analysis` | regra-nova | HIGH | Grava as quatro chaves da árvore sugerida e injeta o emissor (opcional) |
| `src/reporting/mermaid_render.py` | `reporting.mermaid_render` | contrato-novo | HIGH | Ganha `mermaid_da_sugestao`, com `classDef` das três classes e a aresta rompida |
| `src/app.py` | `tela: borda HTTP` | contrato-alterado | MEDIUM | Passa o emissor na montagem de `Dependencias`; nenhuma regra nova |
| `src/templates/index.html` | `tela: cartão de DNA` | contrato-alterado | HIGH | Bloco colapsável da árvore sugerida, abaixo do diagrama documentado |
| `tests/fixtures/resultado_para_cartao.py` | `tests.fixtures` | regra-alterada | LOW | Ganha as quatro chaves e dois helpers de caso |
| `tests/fixtures/helpers.py` | `tests.fixtures` | regra-alterada | LOW | Monta as dependências com o emissor |
| `tests/test_resumo_da_sugestao.py` | `tests` | artefato-novo | LOW | 8 testes: derivação, fonte única e custo |
| `tests/test_mermaid_da_sugestao.py` | `tests` | artefato-novo | LOW | 10 testes: estrutura, cores, aresta, escape e determinismo |
| `tests/test_arvore_sugerida_na_tela.py` | `tests` | artefato-novo | LOW | 8 testes de tela, incluindo os dois casos negativos |

**Arquivos que NÃO mudaram:** `src/assets/app.css`, `requirements.txt`, `init.sql`, `docker/*`,
`tests/test_icone_de_atalho.py`, o JavaScript do template e as tabelas do banco.

## 2. Diff conceitual por componente

### 2.1 `core.cirurgia_do_grafo` (contrato novo)

`resumo_da_sugestao(resultado, documental)` aplica a **mesma** fórmula do hiato da `arvore_sugerida`
— `floor(gerações + 0,5) − a_up` — em O(1), sem `grafo.copy()`. Devolve `geracoes`, `resumo`,
`rotulos`, `lado`, `codigo` e `aviso`.

O aviso (a frase de ausência) só vem preenchido em **cartão em conflito**: repetir a explicação em
142 cartões, a maioria sem conflito, trocaria um silêncio ruidoso por um ruído constante.

### 2.2 `core.dna_analysis` (regra nova)

Depois do veredito, o laço calcula o resumo e — se houver geração a inserir e o emissor estiver
injetado — o texto Mermaid, gravando `sugestao_geracoes`, `sugestao_resumo`, `sugestao_mermaid` e
`sugestao_aviso`.

`_validacao_do_cartao` passou a devolver `(chaves, resultado_bruto)`: o resumo precisa do `status` e
do `mrca_estimado` do validador, e devolver o bruto evita recalcular o veredito.

### 2.3 `reporting.mermaid_render` (contrato novo)

`mermaid_da_sugestao(documental, resumo)` desenha o caminho com as gerações virtuais em `classDef` e
a aresta rompida como **última** ligação, para o índice do `linkStyle` ser previsível. Reusa
`_mermaid_sid` e `_mermaid_label` — o contrato de escape do módulo.

### 2.4 `src/app.py` (emenda de injeção)

Duas linhas: importar o emissor e passá-lo em `Dependencias`. `core/` não pode importar `reporting/`
(ADR-34), então o seam de injeção que já existia para `generate_mermaid` recebe mais uma função.

### 2.5 Tela (contrato alterado)

Um `details.arvore-sugerida` depois de `details.grafo-do-registro`, com o resumo no `<summary>` e o
Mermaid no corpo. Sem sugestão e em conflito, uma frase (`sem-sugestao`) explica a ausência. **O
JavaScript não muda**: o `toggle` já cobre qualquer `details` com `.mermaid`.

## 3. Preservadas

| Regra | Onde | Por que não foi tocada |
|-------|------|------------------------|
| O diagrama documentado | `index.html` (871-891) | O bloco novo entra depois dele, sem substituir |
| Os quatro estados e o selo da `031` | `domain.md#21`; `index.html` | Nenhuma linha alterada |
| `reporting/` não importa `core` | `ADR-34` | O emissor recebe tudo por parâmetro |
| Fallback de 25 anos e 12–70 | `documentary_relationship`; `validator` | A fórmula do hiato é a mesma |
| Nenhuma dependência nova | `requirements.txt` | Intocado; o desenho é Mermaid no navegador |
| Árvore não duplicada no banco | `architecture.md#4` | Nenhuma escrita |
| Dados reais fora do versionamento | `principles.md#i` | Fixture sintética |
| Contraste dos selos | `app.css` | A folha não mudou; as cores do desenho vão no `classDef` |

## 4. Modificadas

| Regra | Onde | O que mudou | Severidade |
|-------|------|-------------|------------|
| Vocabulário de códigos da sugestão | `_reversa_forward/032-.../requirements.md` §4.4 | A implementação usa `HIATO_NAO_POSITIVO` e `SEM_MRCA_ESTIMADO`, da `029`, em vez de criar dois nomes novos. O documento foi corrigido | LOW |

Nenhuma regra de domínio foi alterada ou removida.

## 5. Verificação de execução

| Verificação | Resultado |
|-------------|-----------|
| Suíte completa no `.venv` | **1198 passam, 11 pulados, 0 falham** |
| Baseline antes da feature | 1172 passam, 11 pulados |
| Testes novos | **26** (8 + 10 + 8) |
| `SHA_DA_TELA` | **inalterado**, verificado pelos 15 testes do ícone |
| Custo por cartão | O(1) no resumo; sem `grafo.copy()` — provado por espião que levanta |
| `git status` | apenas os arquivos de §1 e os artefatos de `_reversa_forward/032-*` |
| Tempo de suíte | 446 s nesta rodada, contra 113 s da anterior; o subconjunto equivalente subiu 38% (7,46 s vs 5,42 s), então a diferença é carga da máquina, não o código |
