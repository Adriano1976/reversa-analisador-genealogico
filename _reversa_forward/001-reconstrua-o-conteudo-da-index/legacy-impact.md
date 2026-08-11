# Legacy Impact — 001-reconstrua-o-conteudo-da-index

> Data: 2026-08-11
> Feature: `001-reconstrua-o-conteudo-da-index`
> Âncora: `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`
> Escopo: reconstrução fiel da interface (`templates/index.html`) com ajuste de segurança no Mermaid.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `analisador-genealogico/templates/index.html` | Frontend UI (arquitetura.md#2) | regra-alterada | LOW | Reconstrução fiel da index: estrutura Bootstrap 5, form GEDCOM, abas Path Search/DNA Analysis, blocos Jinja2 de resultados e spinner de loading foram mantidos em essência; a única alteração funcional foi a inicialização do Mermaid, de `securityLevel: 'loose'` para `securityLevel: 'strict'`. |

## Diff conceitual por componente

### Frontend UI — `templates/index.html`

O template já existia com a quase totalidade do comportamento esperado pelas ações (estrutura base, formulário de upload, abas, condicionais Jinja2 e feedback de loading). Durante a execução, nenhuma reescrita estrutural foi necessária — o arquivo foi verificado contra as ações T001–T004 e apenas a configuração do Mermaid foi alterada (`securityLevel: 'loose'` → `'strict'`), conforme D-02 do roadmap e esclarecimento registrado no requirements.md (seção 9, sessão 2026-08-11).

O `strict` impede a renderização de tags HTML não seguras nos rótulos dos grafos, fechando vetor de XSS quando o conteúdo vem dos arquivos do usuário (GEDCOM/CSV). Não há mudança de contrato com o backend: todas as variáveis Jinja2 consumidas (`gedcom_filename`, `message`, `success`, `all_names`, `path_result`, `dna_results`, `skipped_matches`) continuam idênticas às expostas por `app.py`.

## Preservadas

Regras 🟢 do `domain.md` que continuam intactas (nenhuma foi alterada por esta feature):

- **2.1** Relação prevista por faixa de cM (`SHARED_CM_DATA`) — intacta.
- **2.3** Regras de namespace de nome / matching viral — intactas.
- **2.4** Limites de busca (ancestral 20, indireta 40 hops) — intactos.
- **3** Regras de decisão e fluxo (DNA Analysis, Path Search, descartados) — intactas.

## Modificadas

Nenhuma regra 🟢 do `domain.md` foi alterada ou removida por esta feature. A mudança de `securityLevel` do Mermaid é uma decisão de frontend/segurança (D-02), não uma regra de negócio do domínio.
