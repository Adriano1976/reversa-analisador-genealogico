# Legacy Impact: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/data-dictionary.md`)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/core/dna_analysis.py` | `core.dna_analysis` | regra-nova | HIGH | Passa a chamar o validador por resultado e grava quatro chaves de veredito no dicionário que a tela consome |
| `src/core/documentary_relationship.py` | `core.documentary_relationship` | contrato-novo | HIGH | Ganha `intervalo_de_geracao_mediano(arvore)` — fonte única do `G`, antes só na fachada |
| `src/application/validacao.py` | `application.validacao` | regra-alterada | MEDIUM | `intervalo_de_geracao_mediano` passa a delegar ao núcleo; nome e comportamento públicos idênticos |
| `src/templates/index.html` | `tela: cartão de DNA` | contrato-alterado | HIGH | Cabeçalho do cartão ganha o selo de validação; a lista ganha a linha que declara a ausência |
| `src/assets/app.css` | `tela: folha de estilo` | regra-nova | MEDIUM | Duas variáveis por tema e duas classes de contorno `validacao-*` |
| `tests/fixtures/resultado_para_cartao.py` | `tests.fixtures` | artefato-novo | LOW | Resultado sintético para renderizar o cartão |
| `tests/test_veredito_no_nucleo.py` | `tests` | artefato-novo | LOW | Seis testes: quatro campos, três status, custo e fonte única do `G` |
| `tests/test_validacao_no_cartao.py` | `tests` | artefato-novo | LOW | Nove testes de tela, pelo template real |
| `tests/test_contraste_do_selo.py` | `tests` | artefato-novo | LOW | Três testes que calculam o contraste a partir da folha |

**Arquivos que NÃO mudaram:** `src/app.py`, `requirements.txt`, `init.sql`, `docker/*`,
`src/reporting/mermaid_render.py`, `tests/test_icone_de_atalho.py` (o hash continua válido) e as
tabelas do banco.

## 2. Diff conceitual por componente

### 2.1 `core.dna_analysis` (regra nova)

O laço que monta o cartão passa a chamar `validar_comparacao` com o que já produziu. O veredito
viaja em **quatro chaves** no dicionário do resultado — `validacao_status`, `validacao_rotulo`,
`validacao_classe` e `validacao_aviso` — porque é esse dicionário que o template itera. O
mapeamento status → rótulo/classe mora aqui, junto do `confrontacao_rotulo` que já existia.

O veredito olha o **documental original**: quando a janela de vida é impossível, a tela troca o
parentesco pelo "não encontrado", mas a linha existe — e é sobre ela que o veredito fala. Nesse
caso a comparação é recalculada sobre o original, para o cartão e a fachada nunca divergirem.

### 2.2 `core.documentary_relationship` (contrato novo)

`intervalo_de_geracao_mediano(arvore)` muda de casa: nasceu em `application/validacao` (feature
`028`) e agora é do núcleo, porque o fluxo de DNA também precisa dela. Duas implementações de `G`
divergiriam em silêncio, e o mesmo kit teria dois vereditos.

### 2.3 `application.validacao` (emenda)

A função delegada mantém nome, assinatura e comportamento. O `_ref` e os imports que só ela usava
saíram junto.

### 2.4 Tela (contrato alterado)

O selo entra no cabeçalho, ao lado dos outros, e só aparece quando o veredito **conclui**:
`Validado` (contorno verde) e `Linha em conflito` (contorno vermelho). `INCONCLUSIVO` não ganha
selo, e a lista ganha uma linha declarando que a ausência significa "não concluído".

## 3. Preservadas

| Regra | Onde | Por que não foi tocada |
|-------|------|------------------------|
| Os quatro estados do confronto | `domain.md#21`; `app.css` (207-226) | Texto, classe e cor intactos; o veredito é campo novo |
| `reporting/` não importa `core` | `ADR-34` | Nenhum import novo nasce em `reporting/` |
| Projeção pura (ADR-33) | `application/dna_analysis` | Não foi tocada: o template consome os dicionários |
| Nenhuma dependência nova | `requirements.txt` | Intocado |
| Árvore não duplicada no banco | `architecture.md#4` | Nenhuma escrita; o veredito é derivável e não é persistido |
| Dados reais fora do versionamento | `principles.md#i` | Fixture sintética em todos os testes |
| Ordem de apresentação dos resultados | `domain.md#39` | A ordenação por caminho e cM não mudou |
| Contraste dos selos existentes | `app.css` (207-219) | As `--st-*` não foram redefinidas |

## 4. Modificadas

| Regra | Onde | O que mudou | Severidade |
|-------|------|-------------|------------|
| Alcance do invariante `SHA_DA_TELA` | `tests/test_icone_de_atalho.py`; `architecture.md#5` | **Nada no arquivo**: verificado que `GET /` não renderiza o bloco de resultados, então o hash não cobre o cartão. A proteção do cartão passou a ser dos testes de tela novos | MEDIUM |

Nenhuma regra de domínio foi alterada ou removida. A "modificação" aqui é de **entendimento**: o
invariante sempre cobriu só a casca da tela, e os documentos da feature passaram a dizer isso.

## 5. Verificação de execução

| Verificação | Resultado |
|-------------|-----------|
| Suíte completa no `.venv` | **1172 passam, 11 pulados, 0 falham** (112,94 s) |
| Baseline antes da feature | 1154 passam, 11 pulados |
| Testes novos | **18** (6 de núcleo, 9 de tela, 3 de contraste) |
| `git status` | apenas os arquivos de §1 e os artefatos de `_reversa_forward/031-*` |
| `app.py`, `requirements.txt`, Docker, `init.sql` | intocados |
| Contraste medido | 5,66:1 e 5,92:1 no claro; 8,30:1 e 8,42:1 no escuro |
| Hash da tela | inalterado, e a razão está medida |
