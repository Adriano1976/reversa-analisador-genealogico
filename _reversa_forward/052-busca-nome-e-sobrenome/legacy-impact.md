# Legacy Impact: busca por nome e sobrenome

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` cobrindo
> `src/**` e `tests/**` — os dois únicos caminhos tocados. Nenhuma escrita fora deles.
> Âncora: `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`,
> `_reversa_sdd/code-analysis.md#5.7` e os adendos 037, 048 e 051.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/busca_de_nome.py` | Núcleo (`architecture.md#3`) | `componente-novo` | LOW | Termo, estratégias, acerto e resultado; puro, sem HTTP, disco ou `pandas` |
| `src/core/homonimos.py` | Núcleo (`architecture.md#3`) | `regra-alterada` | **MEDIUM** | A varredura que alimenta o dossiê de homônimos passa a produzir também `token → xrefs`; o mapa por nome e a API do dossiê continuam idênticos |
| `src/ports/__init__.py` | Portas (`architecture.md#3`) | `contrato-novo` | LOW | Entra o `Protocol FonteDeNomes` com `normalizar`, `nomes` e `fichas`; nenhuma porta existente muda |
| `src/ports/fontes_de_nomes.py` | Portas (`architecture.md#3`) | `componente-novo` | LOW | Os dois adaptadores novos. **Desvio declarado:** ficam em módulo próprio, e não em `adaptadores.py`, que já acumula quatro responsabilidades |
| `src/application/busca_de_nome.py` | Aplicação (`architecture.md#1`) | `componente-novo` | LOW | O caso de uso; orquestra e não decide |
| `src/reporting/resultado_da_busca.py` | Apresentação (`architecture.md#3`) | `componente-novo` | LOW | Função pura do resultado ao view-model |
| `src/web/rotas_busca.py` | Borda HTTP (`architecture.md#1`) | `contrato-novo` | LOW | `POST /busca`, sob a guarda da feature 051 |
| `src/app.py` | Borda HTTP (`architecture.md#1`) | `contrato-novo` | MEDIUM | Registra o Blueprint, monta o caso de uso com as duas fontes e publica `DONO_LEGADO` na config. Nenhuma rota existente muda de comportamento |
| `src/templates/_busca.html` | Apresentação (`architecture.md#3`) | `componente-novo` | LOW | O partial do campo e do resultado |
| `src/templates/index.html` | Apresentação (`architecture.md#3`) | `regra-alterada` | LOW | Inclui o partial sob `{% if gedcom_filename %}`. `SHA_DA_TELA` **não** mudou (verificado) |
| `src/assets/app.css` | Apresentação (`architecture.md#3`) | `regra-alterada` | LOW | Bloco de estilos novo, aditivo |
| `tests/…` (9 arquivos) | — | `presença` | LOW | Nenhum arquivo de teste existente foi alterado |

**Contagem por tipo:** `componente-novo` 6 · `regra-alterada` 3 · `contrato-novo` 3 · `presença` 1.

## 2. Diff conceitual por componente

**Núcleo — `core/homonimos.py`.** A varredura de nomes deixou de ser uma função que monta
um mapa e passou a ser uma que monta dois, no mesmo laço. A consequência pretendida é que a
busca não pague uma segunda varredura de 35 mil pessoas; a consequência a vigiar é que o
dossiê de homônimos continue devolvendo exatamente o mesmo conjunto, na mesma ordem. O
`_indice_por_nome` virou acessor de uma das visões e ganhou um irmão público,
`indice_por_nome`, para que a busca não dependa de nome privado.

**Núcleo — `core/busca_de_nome.py`.** Módulo novo. Não importa `parsers`, `pandas`, `flask`
nem `os`. Recebe `NomeParaBuscar` já normalizado pela fonte e devolve acertos em ordem total.

**Portas.** A fonte declara `normalizar` — a autoridade de normalização **dela**. É o que
mantém a busca concordando com o dossiê (árvore) e com o `matching` (relatório), e o que
impede que "unificar normalizadores" entre pela porta dos fundos.

**Borda.** `app.py` monta `ServicoDeBusca` com as duas fontes sobre os adaptadores que já
existiam (`CarregadorDeArvoresGedcom` e `ArmazenamentoEmDisco`) e registra o Blueprint. A
borda continua sem decidir casamento.

## 3. Preservadas

Regras 🟢 de `domain.md` que continuam intactas e foram verificadas por execução:

- **§3.4 — matching difuso:** o `matching` continua com o mesmo normalizador (`norm_name`),
  os mesmos limiares e o mesmo desempate por xref. Teste: `test_busca_nao_muda_analise.py`.
- **§3.6 — as duas listas em toda renderização:** intocado; o processador de contexto não
  foi tocado.
- **§3.9 — ordem de apresentação dos resultados da análise:** intocada.
- **§5 — contrato de mensagens:** os 29 literais catalogados continuam na tela; a varredura
  da suíte aponta **uma** divergência de literal, e ela é anterior a esta entrega
  (§5 desta página).
- **Adendo 048 — índice preso ao grafo, sem chave de conteúdo:** preservado e estendido;
  o teste das duas árvores de mesmo tamanho continua verde.
- **Feature 051 — escopo por dono e `404` no lugar de `403`:** preservado; a busca recusa
  com o mesmo literal.
- **`SHA_DA_TELA`:** a primeira versão da entrega não mudava o hash; **a correção de
  2026-10-29 mudou** — `386f2fef…` (51.601 bytes) → `577a17fd…` (51.612, **+11 bytes**),
  o ` action="/"` do formulário de envio. A medição está declarada em
  `tests/test_icone_de_atalho.py` (décima segunda) e no adendo da feature.
- **Combobox dos três campos de nome:** inalterado; `test_combobox_de_nomes.py` passou sem
  uma linha trocada.

## 4. Modificadas

- **`core/homonimos.py` — índice de nomes.** Passa a manter a segunda visão. Não é mudança
  de regra de domínio: o dossiê responde o mesmo, com o mesmo conteúdo e a mesma ordem.
- **`app.py` — montagem da borda.** Ganha a montagem do serviço de busca e a publicação de
  `DONO_LEGADO` em `app.config`, para que a rota não importe a borda de volta.
- **`templates/index.html` — inclusão do partial.** A inclusão abre com o `{% if %}` na
  mesma linha do `</section>` de propósito: com o bloco falso, os bytes da tela vazia são
  exatamente os de antes.

## 5. Achados da execução

1. **A 5ª falha da suíte é anterior a esta entrega.** `test_tres_fases_da_tela.py::TestLiteraisPreservados::test_os_rotulos_congelados_continuam`
   espera o literal `1. Lista de Matches (CSV)`, e o template no `HEAD` (`115d6a6`) diz
   `1. Lista de Matches do Ancestor Projects (CSV)`. O `git diff` da entrega não toca essa
   linha. **Não foi corrigido:** ajustar teste alheio está fora do escopo do `/reversa-coding`.
   O marco real do `HEAD` é **5 falhas** (4 de `test_characterization_mermaid` + esta), e não
   4 como o adendo 051 registrou.
2. **Desvio do plano, declarado:** o payload da porta é o `NomeParaBuscar` do núcleo, e não
   um `NomeDaFonte` gêmeo em `ports/`. Duas estruturas idênticas seriam pior que uma; o
   domínio continua sem conhecer a porta.
3. **Desvio do plano, declarado:** os adaptadores moram em `ports/fontes_de_nomes.py`, e não
   em `adaptadores.py`.
4. **Medição registrada (T025), com 5.000 pessoas sintéticas:** parse 1.372 ms, índice com as
   duas visões 95 ms (uma vez por árvore), segunda consulta 0,00 ms, busca sobre 5.000
   candidatos 21,6 ms. Extrapolando para 35 mil: ~665 ms de índice e ~150 ms por busca.
5. **Defeito de formulário, medido em uso depois da convergência.** Seis formulários da tela
   não declaravam `action` e postavam para a URL corrente; com `POST /busca` no ar, o
   formulário da análise de DNA caía na rota da busca e a tela respondia "Digite um nome ou
   sobrenome para buscar.". Corrigido com `action="/"` nos seis, com `GET /busca`
   redirecionando para `/` e com o teste `test_todo_formulario_declara_action`, que reprova
   formulário sem `action`. Consequência declarada: `SHA_DA_TELA` mudou (+11 bytes), contra o
   que a §3 deste arquivo afirmava antes. Registrado como `corrected` em `progress.jsonl`.
