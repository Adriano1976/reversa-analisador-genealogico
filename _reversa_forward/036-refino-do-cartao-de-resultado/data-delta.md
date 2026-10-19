# Data delta: refino visual do cartão de resultado

> Identificador: `036-refino-do-cartao-de-resultado`
> Data: `2026-10-19`
> Modelo extraído em: `_reversa_sdd/erd-complete.md`, `_reversa_sdd/data-dictionary.md`

## 1. Veredito

**Nenhuma mudança de dados.** A feature é de apresentação: o cabeçalho do cartão lê os mesmos campos do
payload de resultado que já lia, na mesma ordem, e não grava, não calcula e não persiste nada.

| Operação | Quantidade |
|----------|------------|
| Campos novos | 0 |
| Campos removidos | 0 |
| Campos renomeados | 0 |
| Estruturas novas | 0 |
| Tabelas ou colunas | 0 |
| Migrações | 0 |
| Scripts de dados | 0 |

## 2. Campos consumidos pelo cabeçalho (leitura, sem alteração)

| Campo do payload | Origem no legado | Uso no cartão | Mudou? |
|------------------|------------------|---------------|--------|
| `match_name` | `_reversa_sdd/data-dictionary.md`; `core/dna_analysis.py` | Título da conexão | não |
| `cm` | idem | Selo `bg-secondary` (`DNA: N cM`) | não |
| `comparison` / `confrontacao_efetiva` / `confrontacao_rotulo` | idem | Selo `estado-*` | não |
| `identidade` / `identidade_aviso` | idem | Selo e aviso de identidade | não |
| `validacao_rotulo` / `validacao_classe` / `validacao_aviso` | adendo `031` | Selo de validação temporal | não |
| `documentary` / `janela_de_vida` / `profundidade_*` | idem | Faixa de sinais | não |

A projeção para a porta (`application/dna_analysis.py`, `ADR-33`) não é tocada: o template só lê o
dicionário que o caso de uso entrega.

## 3. Persistência

Nenhuma escrita. O registro histórico (`RegistroDeAnalises`, `ADR-27`) continua recebendo exatamente o
mesmo payload, e as tabelas do `init.sql` não são alcançadas por esta feature.

## 4. Migração

n/a — não há dado a converter, reprocessar ou reindexar. Nenhum arquivo em `uploads/` é lido pela
feature.

## 5. Como conferir que nada mudou

- `tests/test_identidade_do_match.py`, `tests/test_janela_de_vida.py`,
  `tests/test_validacao_no_cartao.py` e `tests/test_contador_em_tres_faixas.py` leem o cartão pelo
  conteúdo e continuam verdes.
- Nenhum teste novo de dados é necessário: não há dado novo.
