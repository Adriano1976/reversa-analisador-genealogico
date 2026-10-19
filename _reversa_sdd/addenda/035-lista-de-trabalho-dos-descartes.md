# Adendo: lista de trabalho dos descartes

> Identificador: `035-lista-de-trabalho-dos-descartes`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `020`, `024`, `034`)

## Vigência

Vigente desde 2026-10-19.

## Resumo da entrega

Os descartes se resolvem no cadastro da árvore, que acontece **fora** da aplicação. Faltava
levar a lista para lá. O bloco "Matches descartados" ganhou **"Baixar lista de trabalho
(CSV)"**: uma planilha com uma linha por descarte, o motivo e o candidato compatível.

A decisão de arquitetura vem da ausência de sessão: o bloco carrega, num campo oculto, o
JSON que ele mesmo renderizou, e a rota `POST /descartes.csv` só formata. **Nenhuma análise
roda de novo** — 90 segundos de espera para baixar um arquivo seriam inaceitáveis.

Formato: `;` como separador, decimal com vírgula, BOM UTF-8 e prefixo `'` em célula que
começa com `=`, `+`, `-` ou `@`. O Excel em português abre sem ajuste, e nome de pessoa não
vira fórmula.

**Só o candidato compatível entra na planilha.** O "melhor avaliado" aparece na tela para
explicar a recusa, mas na lista de trabalho seria enganoso: medido, *Luzia Martins dos
Santos* (n. 1798) saía como candidata de *Clezia Santos* — homônimo de outro século não é
endereço de ninguém.

Medido no GEDCOM real: **367 linhas** (cabeçalho + 366 descartes), **58 KB**, e **76 linhas**
com candidato compatível. As outras 290 saem com `Motivo` e sem candidato.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `reporting.csv_de_descartes.csv_de_descartes(itens) -> str`, função pura, sem `core/` (`ADR-34`) |
| `_reversa_sdd/architecture.md` | §Rotas | contrato-novo | `POST /descartes.csv` devolve `text/csv` com `Content-Disposition: attachment`; não lê arquivo nem analisa |
| `_reversa_sdd/domain.md` | §5 Contrato de Mensagens ao Usuário | regra-nova | Entra a ação "Baixar lista de trabalho (CSV)" no bloco dos descartados |
| `_reversa_sdd/data-dictionary.md` | §Exportações | delta-de-dados | Oito colunas: `Nome no CSV`, `Kit`, `cM`, `Motivo`, `Candidato na árvore`, `Nascimento`, `Prenome`, `Nota` |

## Regras sob vigilância

- **W001** — a rota recebe corpo do navegador e **não** confia nele: corpo inválido ou que
  não é lista devolve só o cabeçalho, sem estourar (`tests/test_csv_de_descartes.py`).
- **W002** — célula que começa com `=`, `+`, `-` ou `@` sai com prefixo `'`; sem isso o
  Excel avaliaria nome de pessoa como fórmula.
- **W003** — o formato mora em `reporting/`; o template não formata CSV.

## Fontes

- `_reversa_forward/035-lista-de-trabalho-dos-descartes/requirements.md`
- `_reversa_forward/035-lista-de-trabalho-dos-descartes/actions.md`
- `_reversa_sdd/addenda/034-revisao-dos-descartes.md`
