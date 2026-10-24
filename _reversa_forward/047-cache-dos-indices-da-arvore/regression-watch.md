# Regression Watch: cache dos índices derivados da árvore

> Feature: `047-cache-dos-indices-da-arvore`
> Data: `2026-10-24`

## Itens sob vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| `W001` | `_reversa_sdd/architecture.md#1` | A afirmação sobre cache entre requisições passa a ser **condicional**: existe com `ANALISADOR_CACHE_DE_ARVORE`, não existe sem ela | `redação` | Documento afirmar cache incondicional, ou o código cachear sem a variável |
| `W002` | `src/core/matching.py` (`build_ged_indexes`) | Duas chamadas na mesma árvore devolvem o **mesmo objeto** e a segunda não percorre as pessoas | `presença` | Objetos diferentes, ou contagem de `get_name` subindo na segunda chamada |
| `W003` | `_reversa_sdd/analise-dna/design.md#fluxo-principal` | O resultado da análise é idêntico com o cache ligado e desligado | `presença` | `sha256` do HTML diferente entre os dois estados |
| `W004` | `_reversa_sdd/architecture.md#4` | Com teto 1, o processo estabiliza em ~412 MB e não cresce entre requisições da mesma árvore | `presença` | RSS subindo a cada `POST` |
| `W005` | `_reversa_sdd/domain.md#7-lacunas` (`L-24`) | Duas árvores de mesmo tamanho e mesmos `xref` extremos **não** compartilham índices | `presença` | Um nome exclusivo de uma árvore aparecer no índice da outra |

## Histórico de re-extrações

## Arquivadas

## Observações

- O `L-24` do cache de nomes (`documentary_relationship._INDICE_DE_NOMES`) continua **aberto** e
  fora desta feature, conforme a decisão de 2026-10-24. Não confundir com `W005`, que vigia o memo
  novo, esse sim imune à colisão por construção.
- **Privacidade:** a árvore, que antes vivia só durante a requisição, passa a ficar residente
  enquanto o cache estiver ligado. O `/reversa-sync` deve registrar esse prolongamento de retenção
  em memória no adendo da feature.
- A medição de tempo **não** é item de vigilância: o parse variou de 41 s a 92 s na mesma máquina.
  Vigie contagem de chamadas, não relógio.
