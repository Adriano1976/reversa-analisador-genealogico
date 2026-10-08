# T020 — Persistência ponta a ponta

> Feature: `008-persistencia-postgres-docker` · Data: `2026-10-08`
> Ações cobertas: `T020`, e a substância do `T014` executada **dentro do contêiner**
> (`RF-03` a `RF-09`, `RF-10`, `RF-14`, `RN-05`, `RN-11`, `RN-13`)

## 1. O stack, depois de recriar o volume

`docker compose down -v` e `up -d --build`. O volume foi recriado porque o `init.sql` mudou
depois da primeira inicialização, e `CREATE TABLE IF NOT EXISTS` **não altera tabela
existente** — o `OBS-18` já registrava isso. Não havia dado a perder.

| Medição | Resultado |
|---|---|
| Banco pronto | **6 s** |
| Aplicação respondendo `200` | **4 s** |
| Colunas `detail` / `comparison_detail` | **1** — só `comparison_detail`, o desvio 3 do `actions.md` conferido no banco |
| Restrições de FK com `CASCADE` | **7** |

## 2. Os três fluxos da rota, com **dois kits do mesmo nome**

GEDCOM e CSV sintéticos (`evidence/_tmp_e2e/`), com a coluna de kit presente e valores no
padrão que o núcleo reconhece.

| Medição | Resultado |
|---|---|
| Conexões na tela | **2** |
| Aviso de persistência | **ausente** — com o banco no ar, nada a avisar |
| `accepted_count` / `skipped_count` | **2** / **0** |
| `match_result` | **2** linhas, `result_ordinal` **0 e 1** |
| `match_kit` | **2** linhas |
| `analysis_person` | **3** pessoas |

As duas conexões ficaram gravadas com o cM do **seu** kit, e nenhum total somado:

```
 ord | total_cm | comparison_status | comparison_method | expected_low | expected_high
   0 | 200.0000 | CONFLITANTE       | scp40:Sibling     |    1613.0000 |     3488.0000
   1 |  60.0000 | CONFLITANTE       | scp40:Sibling     |    1613.0000 |     3488.0000

 ord |    kit    | total_cm |   status
   0 | AA1234567 | 200.0000 | CONFLITANTE
   1 | BB7654321 |  60.0000 | CONFLITANTE
```

E as pessoas, com `completa` distinguindo ficha de identificação (`D-15`):

```
 xref  |        nome        | completa
 @I12@ | Carlos Silva Souza | t      <- a raiz
 @I13@ | Ana Silva Souza    | t      <- o match
 @I10@ | Joaquim Silva      | f      <- o nó do caminho
```

O caminho saiu com os papéis derivados do ancestral comum, nas duas conexões:

```
 ordinal | person_xref |    role
       0 | @I12@       | ascendente
       1 | @I10@       | ascendente
       2 | @I13@       | descendente
```

## 3. O adaptador verificado **dentro** do contêiner

O `T014` não roda no host: sem `psycopg2` no `.venv/`, ele é pulado. Dentro do contêiner o
driver existe, e `evidence/_t020_verificar_adapter.py` executou os mesmos caminhos:

```
RESULTADO: 0 falha(s)          <- 24 verificações, todas PASS
```

As que mais importam:

| Verificação | Resultado |
|---|---|
| Dois kits do mesmo nome → **duas conexões**, um kit cada | PASS — `[(0, 200.0, COMPATIVEL), (1, 60.0, CONFLITANTE)]` |
| Ordem preservada | PASS — `result_ordinal` 0 e 1, sem reordenação |
| Estados individuais preservados | PASS |
| cM por kit, sem soma — e a soma **não existe em lugar nenhum** | PASS |
| Papéis do caminho derivados | PASS |
| Raiz e match com ficha completa; nó do caminho só identificado | PASS |
| Descarte com o motivo **em texto** | PASS — `('Zzz Ninguem', 'não encontrado')` |
| **cM de fronteira sobrevive à ida e volta** | PASS nos **seis** valores: 46, 200, 553, 1317, 2200, 3300 |
| Ausente é `NULL`, e não zero — cM, método, faixa e `causes` | PASS |
| Falha devolve aviso em vez de exceção | PASS — `OperationalError: Connection refused` |
| O `CHECK` recusa estado fora dos quatro | PASS — `CheckViolation: ck_comparison_status` |
| **Transação única: a análise recusada não deixou NENHUMA linha** | PASS — contagem `(1, 1)` |

## 4. Dois achados, e os dois são de instrumento ou de esquema — não do produto

### 4.1 Defeito de **esquema**, encontrado por acidente e corrigido

O script de verificação chama `limpar()` para não poluir o histórico do operador, e ele
**falhou**:

```
psycopg2.errors.ForeignKeyViolation: update or delete on table "analysis_person" violates
foreign key constraint "fk_path_person" on table "match_path_node"
DETAIL: Key (analysis_id, xref)=(..., I12) is still referenced from table "match_path_node".
```

As duas FKs de pessoa estavam com `ON DELETE RESTRICT`, e `analysis_person` cascateia de
`dna_analysis`. O resultado é que **apagar uma análise era impossível**: a cascata removia as
pessoas enquanto os filhos ainda as referenciavam. O `RESTRICT` não protegia nada — a garantia
que interessa (não gravar referência a pessoa inexistente) o próprio FK já dá no `INSERT`.

**Corrigido** para `ON DELETE CASCADE` nos dois casos, com a razão escrita no `init.sql`, e
provado depois da correção:

```
DELETE FROM dna_analysis;   -> DELETE 1
SELECT count(*) FROM match_result;  -> 0
```

Expurgo e limpeza de teste são operações legítimas, e não podem ser impossíveis por desenho.

### 4.2 Defeito de **instrumento**: o CSV sintético não exercitava o caso

A primeira execução do `T020` gravou **uma** conexão, com `total_cm = 260.0000` e `kit` vazio.
Não era defeito da persistência: era o **meu CSV**. O núcleo só reconhece a coluna de kit
quando o **valor** casa `[A-Z]{1,3}\d{4,8}` (`core/genetic_evidence.py:42-44`), e `KIT-A` não
casa. Sem kit detectado, as duas linhas viram o **mesmo** match `SEM-KIT` e o cM é **somado** —
que é o comportamento documentado do núcleo para segmentos de um mesmo match.

Medido no host, com três CSVs:

| CSV | Resultado |
|---|---|
| `KIT-A` / `KIT-B` (como eu escrevi) | **um** dossiê `SEM-KIT`, cM **260.0**, 2 segmentos |
| `AA1234567` / `BB7654321` | **dois** dossiês, cM **200.0** e **60.0** |
| sem coluna de kit | **idêntico ao primeiro** — e é isso que prova que a coluna não era detectada |

⚠️ **A lição está registrada porque o sintoma era convincente:** "duas linhas de kits
diferentes somadas em 260" parece defeito de agregação da persistência, e não é. É o núcleo
fazendo o que sempre fez. Um instrumento que não exercita o caso produz um resultado que
parece achado.

## 5. O que este passo **não** prova

- **A sobrevivência ao `down`/`up`** (`RF-02`) é do `T021`, e a contagem de análises antes e
  depois vai ter de ser comparada.
- **O estado de falha pela ROTA** com o banco fora — o `T019` cobre isso no host exercitando a
  ausência do driver; com o banco no ar e depois derrubado, é o §9 do onboarding, também no
  `T021`.
- **O custo da gravação** (`T026`) e a **varredura de credencial** (`T025`) continuam pendentes.
