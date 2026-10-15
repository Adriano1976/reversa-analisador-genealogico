---
name: gedcom-desambiguacao
description: Processa arquivos GEDCOM (.ged) de genealogia para desambiguar homônimos (padrão FamilySearch), expandir locais (PLAC) para "Cidade, Estado, País", validar a lógica biológica entre pais e filhos e injetar metadados de status de vida (_ALIV, RESN PRIVACY) para uso em aplicativo pessoal. Use sempre que o usuário enviar ou mencionar um arquivo .ged/GEDCOM, árvore genealógica, FamilySearch, homônimos, perfis sem sobrenome, indivíduos vivos/falecidos, privacidade de pessoas vivas, tags _ALIV/RESN/NOTE/PLAC ou pedir para "limpar", "corrigir" ou "preparar" uma árvore genealógica, mesmo que não cite a palavra GEDCOM.
---

# Desambiguação e Saneamento de Arquivos GEDCOM

Atue como Engenheiro de Dados Genealógicos: o objetivo é devolver um `.ged` válido, com homônimos separados, locais padronizados, grafo familiar biologicamente coerente e status de vida explícito para o backend de um app pessoal.

O arquivo é o único registro da família do usuário, então a regra de ouro é **nunca perder dados nem quebrar ponteiros** (`@Ixx@`, `@Fxx@`). Por isso, as partes mecânicas ficam em um script determinístico (`scripts/gedcom_process.py`) e o julgamento fica com você.

## Fluxo de trabalho

1. **Localizar o arquivo** em `/mnt/user-data/uploads/` (se o conteúdo não estiver no contexto, leia pelo disco). Nunca edite o original; trabalhe em cópia.
2. **Diagnóstico (dry-run)**, sem gravar nada:
   ```bash
   python /mnt/skills/user/gedcom-desambiguacao/scripts/gedcom_process.py ARQUIVO.ged --dry-run
   ```
   (ajuste o caminho para onde a skill estiver instalada). Leia o relatório: perfis sem sobrenome, homônimos, locais não resolvidos, incoerências biológicas, vivos presumidos.
3. **Definir os parâmetros que o arquivo não responde.** Infira a partir da árvore quando possível; se não der, pergunte em uma única mensagem:
   - `--lineage`: rótulo da linhagem usado no sobrenome provisório (ex.: "Linhagem de Sergipe"). Não invente; deve vir do usuário ou do contexto óbvio da árvore.
   - `--ref-person`: pessoa de referência citada nas NOTEs (ex.: "Celso Gomes Gama"). Opcional; omita se não souber.
4. **Executar o processamento:**
   ```bash
   python .../gedcom_process.py ARQUIVO.ged -o /mnt/user-data/outputs/ARQUIVO_tratado.ged \
       --lineage "Linhagem de Sergipe" --ref-person "Celso Gomes Gama" --fix-ages
   ```
   Opções úteis: `--places-map extra.json` (municípios não cobertos), `--escape-at`, `--no-notes`, `--events BIRT,DEAT,MARR,BURI`, `--current-year`, `--cutoff-age`.
5. **Revisar o relatório e resolver o que o script não decide** (ver "Julgamento humano" abaixo), editando o `.ged` de saída com `str_replace`.
6. **Entregar** o `.ged` tratado e o `.relatorio.md` com `present_files`, e resumir ao usuário em poucas linhas: o que mudou e o que precisa de decisão dele.

## Regras de transformação

### 1. Homônimos (diretrizes FamilySearch)
- **Sem sobrenome:** indivíduo cujo `NAME` tem apenas prenome (`Maria //`). Vira `Maria /[<linhagem> - @I11@]/`, com `2 SURN <linhagem> - @I11@` (sem colchetes no SURN). O ID dentro do nome quebra a ambiguidade nos algoritmos de busca.
- **Defesa biográfica (`1 NOTE`):** todo perfil sem sobrenome e todo homônimo na mesma base (mesmo prenome + sobrenome, pai/filho de mesmo nome, cônjuges sucessivos de mesmo prenome) recebe uma NOTE iniciada por `ALERTA DE HOMÔNIMO:` com linhas `2 CONT`, deixando claro que são pessoas distintas e que não devem ser fundidas, listando os IDs dos outros homônimos. O script gera o texto base; refine manualmente casos como pai/filho (ex.: "pai de @I9@").
- **Locais (`2 PLAC`)** sob `BIRT`, `DEAT`, `MARR`: expandir para "Cidade, Estado, País" (`Aracaju` → `Aracaju, Sergipe, Brasil`; `Açôres` → `Açores, Portugal`). O script cobre siglas de estados, municípios sergipanos e capitais comuns. Locais que ele não resolve vão para o relatório: complete-os só quando tiver certeza; do contrário, pergunte. Nunca chute um estado.

### 2. Consistência biológica
- Mãe: diferença para o filho deve estar entre **12 e 60 anos**. Pai: mínimo de 12 (acima de 80 gera só aviso).
- Se a conta for impossível, rompa o vínculo incorreto e isole em nova `FAM`, mantendo o grafo consistente (o script faz isso com `--fix-ages`):
  - se o genitor é incompatível com **todos** os filhos da família, ele é o intruso (típico de mãe homônima ligada à família errada): sai a linha `FAMS` dele e o `WIFE`/`HUSB` correspondente na `FAM`;
  - se só **alguns** filhos são incompatíveis, o intruso é o filho: saem `FAMC` dele e o `CHIL` correspondente.
  - Em ambos os casos cria-se uma nova `FAM` e os ponteiros são reapontados, sem apagar pessoas.
- Datas aproximadas (`ABT`, `BEF`, `BET`) usam o primeiro ano encontrado. Quando o resultado estiver perto do limite, trate como suspeito e avise o usuário em vez de afirmar.
- Esse rompimento é a única situação em que `FAMC`/`FAMS` podem ser removidos. O exemplo do prompt original omitia o `1 FAMC @F3@` por abreviação; **não** o remova sem violação biológica.

### 3. Status de vida e privacidade
Ano corrente 2026, corte = 2026 − 116 = **1910**.

| Situação | Classe | Ação |
|---|---|---|
| Tem `1 DEAT` | MORTO | garantir que não há `_ALIV Y` (vira `_ALIV N`) |
| Sem `DEAT` e nascimento < 1910 | MORTO | idem |
| Sem `DEAT` e nascimento ≥ 1910 | VIVO | injetar `1 RESN PRIVACY` e `1 _ALIV Y` |
| Sem `DEAT` e sem data de nascimento | VIVO presumido | injetar sob `1 SEX` e listar no relatório |

- Posição: logo abaixo do bloco `1 BIRT` (incluindo seus `2 ...`); sem `BIRT`, abaixo de `1 SEX`.
- Intervalos (`BET 1900 AND 1920`) usam o maior ano, a escolha mais protetora para privacidade.
- Execução idempotente: nunca duplique `_ALIV`/`RESN`. `RESN` pré-existente com outro valor (ex.: `CONFIDENTIAL`) é mantido e reportado.
- Não presuma morte por idade avançada sem `DEAT` quando a data for ≥ 1910; o critério é o do usuário.

## Julgamento humano (o que o script não decide)
- Perfis sem sobrenome que, pelo contexto, claramente pertencem a uma linhagem diferente da informada.
- Locais não resolvidos e países fora de Brasil/Portugal.
- Violações biológicas limítrofes ou baseadas só em datas aproximadas.
- Texto final das NOTEs de pai/filho e casamentos sucessivos.
- Vivos presumidos por falta de data: confirmar se o volume é razoável.

## Pontos de atenção do formato
- `@` dentro de valores (ex.: `/[Linhagem - @I11@]/`) é tecnicamente `@@` no GEDCOM 5.5.1 estrito. O modelo do usuário usa `@` simples; mantenha assim por padrão e ofereça `--escape-at` se a importação falhar.
- O script preserva codificação (UTF-8/BOM/UTF-16/ANSI), finais de linha, indentação e linhas não alteradas. A ordem entre `RESN` e `_ALIV` é irrelevante para os parsers.
- A validação final do script verifica ponteiros quebrados e vínculos sem reciprocidade; se aparecerem problemas **novos**, corrija antes de entregar. Os já existentes no arquivo original apenas reporte.

## Exemplo

**Antes**
```gedcom
0 @I11@ INDI
1 NAME Maria //
2 GIVN Maria
1 SEX F
1 BIRT
2 DATE ABT 1928
2 PLAC Aracaju
1 FAMC @F3@
```
**Depois**
```gedcom
0 @I11@ INDI
1 NAME Maria /[Linhagem de Sergipe - @I11@]/
2 GIVN Maria
2 SURN Linhagem de Sergipe - @I11@
1 SEX F
1 BIRT
2 DATE ABT 1928
2 PLAC Aracaju, Sergipe, Brasil
1 RESN PRIVACY
1 _ALIV Y
1 NOTE ALERTA DE HOMÔNIMO: Perfil tratado para isolar esta Maria de outras homônimas. Não fundir.
2 CONT Dados vitais estimados com base na linha de Celso Gomes Gama.
2 CONT Status de vida injetado para leitura direta do aplicativo local.
1 FAMC @F3@
```

## Saída ao usuário
Arquivo `.ged` tratado + relatório `.md`. Na resposta: contagens (perfis desambiguados, locais expandidos, vivos/mortos, vínculos rompidos) e uma lista curta dos itens que dependem de decisão dele. Sem repetir o GEDCOM inteiro no chat.
