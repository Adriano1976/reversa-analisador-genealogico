# Recuperação do oráculo congelado

> Escrito em 2026-09-29.
> Assunto: o arquivo `_reversa_sdd/oracle/app_legacy_e43ca22.py` desapareceu da árvore local e foi
> recuperado byte a byte.
> Este documento existe para que a perda não volte a acontecer sem procedimento conhecido.

## O que aconteceu

O oráculo congelado, que é a base da métrica primária de paridade do projeto, **não estava presente**
na árvore de trabalho. Estava ausente de três lugares ao mesmo tempo:

| Onde se procurou | Resultado |
|------------------|-----------|
| Disco, em `_reversa_sdd/oracle/` | só `ORACLE_MANIFEST.md` e `run_oracle.py` |
| Refs do git (`git log --all`) | nenhum ref aponta para o commit `e43ca22` |
| Banco de objetos (`git cat-file --batch-all-objects`) | **zero** blobs de 41950 bytes |

O commit de origem, `e43ca22`, foi reescrito para fora do histórico local na limpeza de histórico do
repositório. E `git fetch origin e43ca22` **não funciona**, porque o GitHub só serve objetos
alcançáveis por algum ref anunciado:

```
fatal: couldn't find remote ref e43ca22
```

## Por que isso importava

O `handoff.md` da migração chama o harness diferencial de **"o ato mais importante de todo o
projeto"**, e a regra de sequenciamento é **"nenhuma onda avança com paridade pendente"**. Sem o
oráculo, o `parity/harness.py` morre na largada, a Onda 0 não fecha, e **todas as ondas seguintes
ficam bloqueadas**, porque a paridade é medida contra ele.

## Como foi recuperado

O que tornou a recuperação possível e **verificável** foi o `.state.json` ter gravado a procedência
completa do artefato: o blob de origem, o `sha256` do conteúdo, o tamanho em bytes e a contagem de
linhas. Sem o `sha256`, o conteúdo recuperado seria indistinguível de uma versão parecida e errada.

### Procedimento

1. **Confirmar que o commit ainda existe no servidor.** A API REST do GitHub lê commits que o
   protocolo git recusa, porque eles continuam no armazenamento de objetos mesmo órfãos:

   ```
   https://api.github.com/repos/Adriano1976/reversa-analisador-genealogico/commits/e43ca22
   ```

   Resposta obtida: HTTP 200, `"sha": "e43ca22f04fa2f20b9421a624934e6678e94a619"`,
   `"parents": []`, mensagem `chore: inicializa projeto reversa do app analisador genealogico`.

2. **Buscar o conteúdo em base64, com tamanho e sha256 do blob.** A API de conteúdo devolve tudo:

   ```
   https://api.github.com/repos/Adriano1976/reversa-analisador-genealogico/contents/analisador-genealogico/app.py?ref=e43ca22f04fa2f20b9421a624934e6678e94a619
   ```

   Campos relevantes da resposta:

   | Campo | Valor |
   |-------|-------|
   | `size` | **41950** |
   | `sha` (blob git) | `2490e0509c76351b8fefce65c6df1092ab243aa2` |
   | `encoding` | `base64` |

3. **Decodificar e conferir o `sha256`** contra o registrado no `.state.json`. O base64 do JSON vem
   com quebras de linha escapadas como `\n`; como o alfabeto base64 é `A-Za-z0-9+/=`, removê-las é
   suficiente para reconstituir o bloco.

4. **Só gravar se o `sha256` bater.** Se divergir, não gravar: um oráculo errado é pior que nenhum,
   porque produziria divergência silenciosa e contaminaria toda medição de paridade.

### Resultado da verificação

| Conferência | Esperado | Obtido |
|-------------|----------|--------|
| Tamanho | 41950 bytes | **41950 bytes** |
| `sha256` | `44370b2339a645c4d9ce732ac3962811b16b35f587ece3507dad4fc3d87646bb` | **idêntico** |
| Linhas | 888 no registro | 887 no `splitlines`, porque o arquivo termina em quebra de linha |
| Referências a `reconstructed` | 0, para não haver validação circular (`RISK-002`) | **0** |
| `from flask import` | presente, é o monólito legado | presente |

Com o arquivo restaurado, o harness voltou a rodar:

```
FIXTURE: _reversa_sdd\parity\fixtures\gedcom\affinity.ged (450 bytes)
  ORACLE coletado: 6 pessoas, 3 familias
  CANDIDATO coletado: 6 pessoas, 3 familias
  PARIDADE OK — zero divergencia
RESULTADO: PARIDADE 100%% (zero divergencia)
```

## Como reverificar a qualquer momento

Conferir que o oráculo em disco é o congelado:

```
py -3.14 -c "import hashlib;print(hashlib.sha256(open(r'_reversa_sdd/oracle/app_legacy_e43ca22.py','rb').read()).hexdigest())"
```

O resultado tem de ser `44370b2339a645c4d9ce732ac3962811b16b35f587ece3507dad4fc3d87646bb`.

Conferir que os hashes do pipeline continuam íntegros:

```
py -3.14 _reversa_sdd/parity/_verify_hashes.py
```

Rodar o harness com escopo mínimo, sem tocar em dados reais:

```
py -3.14 _reversa_sdd/parity/harness.py --gedcom _reversa_sdd/parity/fixtures/gedcom/affinity.ged --pares 4
```

## Duas armadilhas operacionais

**O import do oráculo cria `uploads/` e `static/` no diretório de trabalho**, porque o monólito faz
`os.makedirs` relativo. Rodar o harness a partir da raiz do repositório suja a árvore com uma pasta
`static/`, que **não** está no `.gitignore`. Execute a partir de um diretório contido, como
`.pytest-tmp/`, ou confira o `git status` depois.

**O harness deixa resíduo de coletores** (`_collect_*`, `_obs_*`, `.parity-run-*`). Existe limpador
próprio, e ele reporta o que o sandbox nega remover em vez de fingir sucesso:

```
py -3.14 _reversa_sdd/parity/_clean_residue.py
```

## A lição

O `sha256` do `.state.json` não é burocracia de auditoria: foi **a única razão** pela qual esta
recuperação pôde ser provada em vez de presumida. Enquanto o hash existir, o oráculo é reconstruível
a partir de qualquer cópia do conteúdo, inclusive uma servida por API depois de o commit sair do
histórico.

O que se perdeu de fato foi a **alcançabilidade por git**, não o conteúdo. Este documento registra o
caminho alternativo antes que ele também se perca.
