# Data delta: DNA sem correspondência na árvore

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Requirements: `_reversa_forward/039-dna-sem-correspondencia/requirements.md`
> Modelo extraído: `_reversa_sdd/data-dictionary.md#8-payload-do-núcleo--tela`
>
> **Vigente:** o estado atual é o da seção "Atualização 2026-10-22 (E003)"; as seções 2–5
> descrevem a primeira entrega e ficam como histórico.

## 1. Resumo

A feature **não cria tabela, coluna, porta nem migração**. Ela acrescenta:

1. uma chave aditiva no dicionário de descarte do núcleo (`mrca_generations`);
2. uma lista derivada no resultado da aplicação (`sem_correspondencia`);
3. uma constante de domínio (`CM_MINIMO_SEM_CORRESPONDENCIA = 40.0`).

Tudo vive no payload da análise, entre o núcleo e a tela. O histórico (`skipped_match`) e a lista de
trabalho em CSV continuam exatamente como estão.

## 2. Delta no dicionário de descarte do núcleo

O item de `skipped_matches`, hoje:

| Campo | Tipo | Origem |
|-------|------|--------|
| `csv_name` | `str` | `kit["person_name_csv"]` |
| `kit` | `str \| None` | `kit["kit"]` |
| `cm` | `float` | `kit["total_cm"]` |
| `motivo` | `str` | `Motivo.texto` ou `"não encontrado"` |
| `motivo_codigo` | `str` | `Motivo.codigo` ou `NAO_ENCONTRADO` |
| `motivo_detalhe` | `str` | `Motivo.detalhe` |
| `candidatos` | `list[dict]` | até três candidatos avaliados, com `id`, `nome`, `nota`, `prenome`, `intersecao`, `compativel`, `nascimento` |

Ganha **uma** chave:

| Campo | Tipo | Origem | Observação |
|-------|------|--------|------------|
| `mrca_generations` | `float \| None` | `kit["mrca_generations"]` | Média das linhas do CSV para o kit, já calculada por `core/genetic_evidence.py:286-290`; `None` quando o CSV não traz a coluna |

Nenhum campo existente muda de nome, tipo ou ordem. A chave é **aditiva** e não participa de
nenhuma decisão de aceitação.

## 3. Delta no resultado da aplicação

`ResultadoDeAnalise` (`src/application/dna_analysis.py`) ganha um campo por último, com default:

| Campo | Tipo | Padrão | Conteúdo |
|-------|------|--------|----------|
| `sem_correspondencia` | `tuple[dict, ...]` | `()` | Itens do bloco, já filtrados e ordenados |

O item da lista é **deliberadamente menor** que o descarte; o bloco não deve carregar motivo nem
candidatos:

| Campo | Tipo | Observação |
|-------|------|------------|
| `csv_name` | `str` | Nome como veio do CSV |
| `kit` | `str \| None` | Kit do item |
| `cm` | `float` | cM **do kit**, nunca soma |
| `mrca_generations` | `float \| None` | Estimativa do relatório para o kit; `None` vira "não informado" na tela |

A lista é produzida pela função pura `core.sem_correspondencia.selecionar(resultados, descartados,
limite_cm=CM_MINIMO_SEM_CORRESPONDENCIA)`, chamada pelo caso de uso depois de `fluxo_dna`. Ela não
recalcula cM, não relê CSV/GEDCOM e não altera as listas originais.

## 4. A constante

| Constante | Valor | Onde | Papel |
|-----------|-------|------|-------|
| `CM_MINIMO_SEM_CORRESPONDENCIA` | `40.0` | `core/sem_correspondencia.py` | Corte de triagem do bloco; não é faixa de parentesco publicada |

É o **único** lugar do código com o número 40,0 para esta regra. O template não contém o literal; o
docstring da constante registra a medição de 2026-10-22 (9 casos: 154,5; 52,5; 51,3; 50,5; 45,8;
43,7; 43,3; 42,6; 41,2 cM).

## 5. Regra de seleção (contrato do seletor)

Um item entra quando **todas** as condições valem:

1. `cm >= 40.0` (o limite é inclusivo; nenhum dos 9 casos medidos está exatamente em 40,0);
2. **nenhum** candidato do descarte tem `compativel == True`;
3. `norm_name(csv_name)` **não** aparece entre os `csv_name` normalizados dos cartões aceitos —
   qualquer kit do mesmo nome exclui o item.

Ordem: `(-cm, norm_name(csv_name), csv_name, kit or "")`.

Invariantes:

- o item é por **(nome, kit)**; dois kits descartados do mesmo nome, sem cartão, aparecem em duas
  linhas, cada uma com seu cM e MRCA; **nunca** há soma entre kits;
- a lista completa de descartes **não** é filtrada; o bloco é um recorte;
- o bloco não é persistido e não entra no payload da porta `RegistroDeAnalises`.

## 6. O que **não** muda

| Estrutura | Situação |
|-----------|----------|
| `ports.DescartadoDaAnalise` | Sem campo novo; o MRCA não é persistido |
| `AnaliseParaRegistrar` | Sem campo novo |
| Tabela `skipped_match` | Sem coluna nova; nenhuma migração |
| `reporting/csv_de_descartes.py` | Mesmas nove colunas e mesmos cabeçalhos |
| Lista "Matches descartados" | Mesmos itens, mesma ordem, mesmos motivos e candidatos |
| `ResultadoDeAnalise` existente | Os campos atuais mantêm nome, tipo e posição; o novo é o último, com default |
| `core.dna_analysis` retorno | Continua `(resultados, descartados, mensagem)`; a lista nova é uma função separada |

## 7. Fluxo do dado

```
CSV (MRCA por linha)
  → core.genetic_evidence: kit["mrca_generations"] (média por kit)
  → core.dna_analysis: skipped_matches[i]["mrca_generations"]
  → core.sem_correspondencia.selecionar(resultados, descartados)
  → application.ResultadoDeAnalise.sem_correspondencia
  → app.py: render_template(..., sem_correspondencia=...)
  → templates/index.html: bloco "DNA sem correspondência na árvore"
```

## 8. Migração

**n/a.** Nenhum dado existente é lido, reescrito ou apagado. As linhas de `skipped_match` já
gravadas continuam com o texto e os campos que tinham. Não há backfill: o MRCA do bloco é derivado
da análise atual, não do histórico.

## 9. Fixtures e testes

- **Seletor (unidade)**: `tests/test_sem_correspondencia.py` com dicionários sintéticos —
  limite 39,9 / 40,0, candidato compatível, nome com cartão em outro kit, ordem e empate, MRCA
  ausente, dois kits do mesmo nome sem cartão.
- **Tela (ponta a ponta)**: renderização de `index.html` com um contexto sintético — bloco presente,
  campos, aviso, ausência de parentesco/promoção, lista completa intacta, zero itens e zero cartões.
- **Fixtures**: `tests/fixtures/sample_dna.py` e `sample_gedcom.py`, estendidos com um caso de
  150,0 cM sem candidato compatível e com a coluna `MRCA`; nenhum arquivo real é copiado
  (Princípio I).
- **Caracterização**: `tests/test_characterization_matching.py` continua prendendo os mesmos
  aceitos/descartes; a chave nova é tratada explicitamente, sem afrouxar a comparação das decisões.

## 10. Compatibilidade

| Consumidor | Efeito |
|------------|--------|
| Template da lista completa | Ignora a chave nova; nenhum campo lido muda |
| `tojson` do formulário de descartes | O JSON cresce com a chave; o receptor do CSV ignora chaves desconhecidas |
| `projetar_analise` | Ignora a chave; o histórico não muda |
| Testes que comparam o dict inteiro | Precisam ser atualizados de forma declarada (D-11); as decisões não mudam |
| Consumidores do CSV | Nenhuma coluna nova; as nove posições continuam iguais |

## Atualização 2026-10-22 (E001/E002)

- `CM_MINIMO_SEM_CORRESPONDENCIA` passa de `40.0` para **`20.0`**.
- Os itens do recorte agora são **cartões em `resultados`**, com `sem_correspondencia: True`
  no dicionário do cartão. O `documentary` é `status: "not_found"`, `label: "Parentesco
  documental não encontrado"` e `path: None`; o cartão tem as cinco seções, sem diagrama.
- O seletor `core.sem_correspondencia.selecionar` continua devolvendo a lista
  `ResultadoDeAnalise.sem_correspondencia` para o resumo, mas **ignora o cartão marcado** ao
  montar `nomes_com_cartao` — o cartão sem correspondência não pode excluir o próprio item.
- A projeção histórica (`projetar_analise`) **filtra os cartões sem correspondência**: não há
  pessoa para `match_result.matched_person_xref` (NOT NULL/FK). Eles continuam em
  `skipped_match`, como descartes.
- A lista completa de descartes, o CSV de nove colunas, `DescartadoDaAnalise`,
  `AnaliseParaRegistrar`, `skipped_match` e o schema **não mudam**.
- O item aparece nos dois lugares (cartão e lista completa) por decisão do operador; o texto
  do resumo diz que os N cartões sem correspondência também estão na lista completa.

## Atualização 2026-10-22 (E003)

A limpeza da E003 **não muda dado, contrato externo nem comportamento**. Muda quem calcula o
recorte:

- `core.sem_correspondencia.selecionar` **sai**. O módulo fica só com a regra:
  `CM_MINIMO_SEM_CORRESPONDENCIA`, `nomes_com_cartao_aceito(resultados)` e
  `elegivel(descarte, nomes_com_cartao)`. Não ordena, não projeta e não varre os descartes
  outra vez.
- `core.dna_analysis` usa `elegivel` no laço que acrescenta os cartões; a lista completa
  (`skipped_matches`) continua intacta com os **448**.
- `ResultadoDeAnalise.sem_correspondencia` passa a ser a tupla dos **próprios cartões**
  marcados com `sem_correspondencia: True`, na ordem da tela — não mais a projeção de quatro
  campos. O template usa apenas `|length`; a contagem não pode divergir da lista.
- O fluxo fica:

  ```
  core.dna_analysis: elegivel(...) decide o cartão
    → results_list (8 aceitos + 60 sem correspondência)
    → application: sem_correspondencia = tuple(cartões marcados)
    → app.py: render_template(..., sem_correspondencia=...)
    → templates/index.html: "Desses, 60 cartões sem correspondência..."
  ```

- `mrca_generations` **permanece** no dicionário de descarte (o B+ não foi aplicado); ele
  deixou de ter consumidor na tela, porque o MRCA do cartão vem de `genetic_evidence`. É um
  resíduo declarado, não uma decisão nova.
- A lista "Matches descartados", o CSV de nove colunas, `DescartadoDaAnalise`,
  `AnaliseParaRegistrar`, `skipped_match`, a projeção histórica e a promoção **não mudam**.
- `tests/test_sem_correspondencia.py` passa de 18 para **15 testes**: 6 da regra, 8 do cartão
  na lista e 1 da ordem dos cartões. A suíte completa fica em **1409 passed, 9 skipped**
  (antes: 1412/9; −3 testes do seletor).
