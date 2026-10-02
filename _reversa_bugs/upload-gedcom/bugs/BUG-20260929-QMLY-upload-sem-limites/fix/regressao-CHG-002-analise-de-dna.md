# Regressão do CHG-002: a análise de DNA quebrou

Registrado em 2026-10-02, relatado pelo usuário ao usar a aba "Analisador de DNA" no app em execução.

```text
Ocorreu um erro: [Errno 2] No such file or directory:
'94e2402671702cac__Famílias_Sergipanas.csv.ged'
```

## Veredito

**Regressão introduzida pela correção deste mesmo bug.** O `CHG-002` fechou os cinco critérios de
aceite e quebrou um fluxo que funcionava. O reparo é `CHG-004`, e entra como `code` no mesmo change
set porque corrige o que o `CHG-002` quebrou.

## Como eu quebrei

**Erro 1: extensão fixa em `.ged`.** O `CHG-001` escreveu `nome_visivel_seguro` para o GEDCOM, e ele
acrescentava `.ged` sempre. O `CHG-002` passou a usar a mesma função nos **dois** uploads, e o CSV de
DNA era gravado como `<...>.csv.ged`. O nome no erro do usuário mostra isso literalmente.

**Erro 2, mais grave: nome e caminho tratados como intercambiáveis.** O `_guardar_upload` devolvia o
**nome** do arquivo, e as duas rotas o consumiam de formas diferentes:

| Rota | O que fazia | Resultado |
|---|---|---|
| GEDCOM | `os.path.join(_pasta_uploads(), nome)` antes de carregar | funcionava |
| DNA | passava o nome direto ao parser | procurava o CSV **no diretório corrente** e falhava |

Foi por isso que o upload de GEDCOM continuou funcionando enquanto a análise de DNA quebrava. A
assimetria entre as duas rotas era o defeito, e ela passou despercebida porque o Gate 2 testou o
upload do GEDCOM e o fluxo de `path_search`, mas **nunca o fluxo de DNA**.

## O que eu deixei de verificar

O critério de aceite do bug fala de "extensão e conteúdo" e de "chave de armazenamento", e eu cobri
tudo isso **no caminho do GEDCOM**. A aba de DNA faz um segundo upload, de CSV, e eu apliquei a
mesma função sem exercitar o fluxo que a consome. A lição: quando uma correção passa a ser usada por
um segundo chamador, o teste tem de cobrir o segundo chamador, não só o primeiro.

## O reparo

**1. Extensão preservada, não fixada.** `nome_visivel_seguro` preserva a extensão original e só
acrescenta `.ged` quando não há extensão nenhuma. `Famílias_Sergipanas.csv` continua `.csv`.

**2. Um só caminho para gravar e ler.** O `_guardar_upload` passa a devolver o **caminho completo**,
e não o nome. Quem lê usa exatamente o que foi escrito. A rota de DNA recebe o caminho e não precisa
remontá-lo; a de GEDCOM usa `os.path.basename` apenas para o valor do formulário.

**3. A pasta de upload deixou de depender do diretório corrente.** Era `"uploads"` relativo, o que
dava dois nomes para o mesmo arquivo quando o CWD mudava. Passa a ser ancorada no arquivo do app,
com `ANALISADOR_UPLOAD_FOLDER` para apontá-la em teste. Foi essa ambiguidade que tornou o erro
possível.

## Testes de regressão acrescentados

Em `tests/test_upload_seguranca.py`, classe `TestExtensaoPreservada`:

| Teste | O que prova |
|---|---|
| `test_csv_de_dna_nao_vira_ged` | o nome do CSV preserva a extensão |
| `test_extensao_do_gedcom_e_preservada` | o GEDCOM continua `.ged` |
| `test_nome_sem_extensao_recebe_ged` | o caso sem extensão tem destino definido |
| `test_extensao_em_maiuscula_e_preservada` | `.GED` não é reescrito |
| `test_fluxo_completo_de_analise_de_dna` | **o fluxo inteiro**: sobe a árvore, envia o CSV, e a análise não falha |
| `test_csv_fica_gravado_com_a_extensao_original` | em disco, o CSV termina em `__matches.csv` e não em `.csv.ged` |

Os dois últimos são os que pegam o defeito relatado. Os quatro primeiros isolam a causa.

## Prova

```text
134 passed in 3.72s
PARIDADE 100% (zero divergencia)
```

Antes do reparo: `1 failed, 32 passed`, com a falha sendo exatamente
`test_fluxo_completo_de_analise_de_dna`.

## Verificação pelo usuário

**Confirmada em 2026-10-02.** Com o reparo aplicado e o app rodando, o usuário repetiu o fluxo que
havia falhado, na aba "Analisador de DNA", e respondeu: **"Funcionou. Sem falha."**

Isto é a verificação que o Gate 2 não tinha: o fluxo real, na tela, com o CSV real
(`Famílias_Sergipanas.csv`) e a árvore real. O defeito era de fumaça, e a confirmação também é.

## O que isto ensina sobre o fechamento anterior

O `DONE.md` foi gravado com os cinco critérios de aceite marcados e a suíte em 27 testes. Nenhum
teste exercitava o segundo upload. Um bug pode ser fechado com todos os critérios atendidos e ainda
assim deixar regressão, quando o critério não cobre todos os consumidores da mudança.

A consequência prática é que a classe `TestExtensaoPreservada` passou a cobrir o fluxo de DNA de
ponta a ponta, o que o Gate 2 deveria ter feito na primeira passagem.
