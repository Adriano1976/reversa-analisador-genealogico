# Actions: humanizar a geração de diferença

> Identificador: `045-humanizar-geracao-de-diferenca`
> Data: `2026-10-22`
> Roadmap: `_reversa_forward/045-humanizar-geracao-de-diferenca/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 5 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 3 (T001 → T002 → T003 → T004) |

## Fase 1, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar `geracoes_de_diferenca` e `nome_do_primo` à folha sem import | - | `[//]` | `src/core/graus_de_parentesco.py` | 🟢 | `[X]` |
| T002 | `documentary_label` passa a usar `nome_do_primo`, sem montar rótulo próprio | T001 | - | `src/core/documentary_relationship.py` | 🟢 | `[X]` |
| T003 | As nove linhas de `SCP40_ROWS` com diferença de geração deixam de ter literal | T001 | `[//]` | `src/core/relationship_hypotheses.py` | 🟢 | `[X]` |

## Fase 2, Verificação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Atualizar os rótulos presos por teste e acrescentar a série da geração de diferença e a igualdade entre as duas superfícies | T002, T003 | - | `tests/test_rotulos_de_parentesco.py`, `tests/test_confrontacao_gedcom_dna.py`, `tests/test_tabela_do_bloco_3.py`, `tests/test_destaque_da_hipotese.py`, `tests/test_destaque_na_tela.py` | 🟢 | `[X]` |
| T005 | Rodar a suíte completa e varrer os rótulos do arquivo real | T004 | - | — | 🟢 | `[X]` |

## Notas de execução

- **T001:** `nome_do_primo` mora na folha sem import de propósito. Ela é usada por um módulo puro
  (`relationship_hypotheses`, no caminho do CSV) e por um que importa `networkx`
  (`documentary_relationship`); a folha é o único lugar que os dois alcançam sem arrastar nada.
- **T001 (as palavras por extenso):** `uma/duas/três` até dez, algarismo acima. `11 gerações de
  diferença` é mais legível que `onze gerações de diferença` em rótulo de tabela, e a série dos
  primos vai longe — o maior par do arquivo é `(11, 1)`.
- **T002:** o rótulo do documental deixou de ter `(1× removido)` **e** `com N× remoção`; agora é
  parêntese único, igual ao da tabela publicada. Nada de chave, meioses ou `degrees` mudou.
- **T003:** trocar literais por chamada de função dentro de `SCP40_ROWS` é deliberado: mantém a
  tabela como **dado** (ordem, meioses, média, faixa intactos) e elimina a segunda fonte do nome.
- **T004:** 11 casos novos na série da geração de diferença, mais o teste de igualdade entre
  `SCP40_ROWS[i][2]` e `documentary_label`. Os rótulos presos em cinco arquivos foram atualizados.
- **T004 (comentários):** cinco docstrings e comentários que citavam o rótulo antigo como exemplo
  (`profundidade_do_caminho`, `path_finding`, `janela_de_vida`, `dna_analysis`, `evidence_comparison`)
  foram atualizados — exemplo desatualizado em docstring ensina errado.
- **T005:** suíte completa em **1585 passed, 9 skipped** (antes: 1574/9, delta de +11).
  `SHA_DA_TELA` inalterado.

## Conferência no arquivo real

Varredura dos **456 kits** do `Famílias_Sergipanas.csv`: **17 rótulos distintos**, e **nenhum** com
`×` ou com a palavra `remoção`. Os nove que têm diferença de geração agora leem:

```
Primos de 1º grau (uma geração de diferença)      Primos de 3º grau (uma geração de diferença)
Primos de 1º grau (duas gerações de diferença)    Primos de 4º grau (uma geração de diferença)
Primos de 1º grau (três gerações de diferença)    Primos de 5º grau (uma geração de diferença)
Primos de 2º grau (uma geração de diferença)
Primos de 2º grau (duas gerações de diferença)
Primos de 2º grau (três gerações de diferença)
```

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-22 | Versão inicial gerada por `/reversa-code-express` | reversa |
| 2026-10-22 | Execução: 5/5 ações concluídas | reversa |
