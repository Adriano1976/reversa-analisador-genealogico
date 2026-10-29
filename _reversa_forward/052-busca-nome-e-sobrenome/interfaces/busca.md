# Interface: `POST /busca`

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Tipo: HTTP, formulário de página (`application/x-www-form-urlencoded`), resposta HTML
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Por que uma rota própria

O projeto despacha `POST /` por `action`, mas a rota `/` já tem **23** `render_template`, **12** deles
passando `gedcom_filename` (`_reversa_sdd/domain.md#3.6`). A busca entra como **Blueprint próprio**
(`src/web/rotas_busca.py`), no mesmo desenho de `rotas_auth.py` e `rotas_assets.py` — um ponto de render,
um ponto de guarda.

O método é `POST`, e não `GET`, por um motivo de privacidade: o termo pode conter nome de pessoa, e em
`GET` ele iria para o log de acesso e para o histórico do navegador.

## 2. Requisição

| Campo | Obrigatório | Tipo | Regra |
|-------|-------------|------|-------|
| `termo` | sim | texto | Preservado como escrito; aparado nas pontas; teto de **120** caracteres; vazio é recusado |
| `gedcom_filename` | sim | texto | Referência da árvore aberta, no formato já usado pelo formulário de análise |
| `matches_csv_ref` | não | texto | Referência do relatório selecionado; ausente significa "sem relatório nesta sessão" |

Nenhum outro campo. Nenhum upload: a busca **não** aceita arquivo — ela lê o que já está aberto.

## 3. Resposta

Toda resposta é **HTML de página inteira**, com o mesmo template da tela e a área de resultado
preenchida. O projeto não expõe JSON e esta rota não inaugura isso (`_reversa_sdd/architecture.md#1`).

| Situação | Status | Corpo |
|----------|--------|-------|
| Busca com acertos | `200` | Tela com a área de resultado; seções rotuladas **árvore** e **relatório** |
| Busca sem acerto | `200` | Tela com o aviso de não encontrado e **o termo preservado no campo** |
| `termo` vazio | `200` | Tela com o aviso de que é preciso digitar um nome ou sobrenome; nenhuma seção é produzida |
| Relatório ilegível | `200` | Seção do relatório **omitida**, linha de aviso com o texto acionável já existente, seção da árvore respondendo |
| `gedcom_filename` que não resolve | `404` | **O mesmo** literal de referência inexistente — inclusive quando a referência existe e é de outro dono |

O `404` é decisão herdada da 051 (`RN-06`): recurso de outro dono é indistinguível de inexistente, e
nunca `403`. A busca não inventa uma exceção a essa regra.

## 4. Erros e mensagens

- **Sem sessão:** `POST` sem sessão responde `303 /login`, pela guarda única da feature 051. A rota não
  implementa guarda própria.
- **Texto novo de tela:** entram poucos literais (rótulo do campo, dica, aviso de termo vazio e título
  das duas seções). Eles passam a fazer parte do contrato de mensagens (`_reversa_sdd/domain.md#5`) e
  precisam ser catalogados no mesmo commit — os 29 existentes não mudam.
- **Falha do relatório:** reaproveita o texto acionável de `core.erros` já usado pela análise; não nasce
  uma segunda redação para o mesmo problema.

## 5. Idempotência e efeitos

- **Idempotente e sem efeito:** repetir a mesma requisição devolve a mesma resposta e não altera
  arquivo, árvore, histórico nem trilha (`RN-01`).
- **Não grava nada.** Não há escrita em disco, banco ou log de auditoria.
- **Não toca análise:** nenhuma chamada a `matching`, `dna_analysis` ou `path_search`.

## 6. Tempo limite e concorrência

- **Sem timeout de rede:** a rota não chama serviço externo; ela lê a árvore já aberta.
- **Custo por requisição:** proporcional à varredura do índice de tokens, não ao número de buscas
  anteriores. A construção do índice acontece uma vez por árvore, no primeiro uso.
- **Concorrência:** o índice é atributo do grafo e a gravação é idempotente; as 4 threads do processo
  não compartilham estado mutável de busca (`_reversa_sdd/architecture.md#2`).

## 7. Fora de escopo desta interface

- Paginação de resultado além do teto de 50 por seção.
- Busca assíncrona, autocomplete servido por esta rota e resposta em JSON.
- Busca global entre árvores armazenadas: a rota só alcança o que está aberto na sessão.
- Auditoria da consulta — foi decidida para a entrega que retirar o `all_names` (§9 do requirements).
