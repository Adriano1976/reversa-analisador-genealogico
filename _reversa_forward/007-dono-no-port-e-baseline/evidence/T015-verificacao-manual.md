# T015 — verificação manual de ponta a ponta

> Rodada de `/reversa-coding`, 2026-10-07.
> Executada pelo roteiro do `../onboarding.md`, com dado **sintético** (Princípio I).
> Servidor de produção (`waitress`) em `127.0.0.1:5057`.

## 1. Os três fluxos, contra o servidor real

| Passo | Requisição | HTTP | Classe do alerta | Mensagem |
|---|---|---|---|---|
| 1. upload do GEDCOM | `POST /` `action=upload_gedcom`, `gedcom=@arvore.ged` | `200` | `success` | `Arquivo 'arvore.ged' carregado!` |
| 2. busca de caminho | `POST /` `action=path_search`, `Carlos Silva` × `Ana Silva` | `200` | `success` | `Conexão direta encontrada (ancestral comum).` |
| 3. análise de DNA | `POST /` `action=dna_analysis`, `root_name=Carlos Silva`, `matches_csv=@matches.csv` | `200` | `success` | `1 conexões encontradas. 0 descartadas.` |

Chave devolvida pelo upload, no campo oculto `gedcom_filename`:
`8b667f911a986069__arvore.ged` — a forma `<16 hex>__<nome visível>`, inalterada.

Saídas cruas: `_tmp_e2e/1_upload.html`, `_tmp_e2e/2_busca.html`, `_tmp_e2e/3_dna.html`.

⚠️ **O console desta sessão é cp1252** e imprime `ConexÃ£o` onde o arquivo tem
`Conexão`. Os três HTML estão em UTF-8 correto; o defeito é de exibição do terminal,
e não do produto. O mesmo já estava registrado nas features 005 e 006.

## 2. A pasta de upload não recebeu resíduo

O servidor foi subido com `ANALISADOR_UPLOAD_FOLDER` apontando para
`evidence/_tmp_e2e/uploads` — o mesmo mecanismo que a feature 006 usou. Resultado:

```text
evidence/_tmp_e2e/uploads:  2 entradas
  8b667f911a986069__arvore.ged
  d584bc625434e356__matches.csv
src/uploads/:              33 entradas
```

**Nenhuma das 33 entradas de `src/uploads/` foi escrita nesta rodada.** A mais nova
é de `11:09:19`, horas antes desta verificação, e é um GEDCOM real do operador
(`Arvore_Unificada_Oficial_V1_2.ged`), que é justamente o que a pasta existe para
receber — ela é coberta por `uploads/` no `.gitignore` (Princípio I).

⚠️ **A contagem `33` não contradiz o `32` que a feature 006 registrou.** A entrada a
mais é `src/uploads/_pytest`, um **diretório preso** criado pela própria rodada da
006 na tentativa de `--basetemp` — ele está no inventário de 13 de
`_reversa_forward/006-fronteira-aplicacao-ports/evidence/README-evidencias.md` §2.2.
O `32` foi medido antes de essa tentativa acontecer.

## 3. O servidor foi encerrado, e o encerramento foi verificado

Uma instância de pé faria a próxima execução falhar na guarda de exclusividade, com
um sintoma que não parece com a causa. Por isso o encerramento foi **medido**, e não
presumido:

```text
GET http://127.0.0.1:5057/  ->  recusou conexão (servidor encerrado)
```

## 4. O que esta verificação NÃO prova

Ela exercita a superfície HTTP de ponta a ponta, e **não** prova isolamento entre
donos — nada nesta feature implementa isolamento. A prova de que o dono não altera
o armazenamento é o `T010`, e a de que ele não altera comportamento nenhum é o
`T012` (19 casos) mais a paridade do `T014`.
