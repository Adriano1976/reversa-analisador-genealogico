<!--
Onboarding da feature 058 — Detalhamento dos segmentos compartilhados.
Passo a passo para um humano que vai testar a feature pela primeira vez.
-->

# Onboarding: testar o "Detalhamento dos segmentos compartilhados"

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Público: quem nunca viu a feature. Usa a fixture sintética da 057 — nenhum dado real é necessário,
> e nenhum dado real deve ser versionado (`.reversa/principles.md#I`).

## Antes de começar

| Você precisa de | Como obter |
|-----------------|------------|
| Python 3.13 e a `.venv` | `py -3.13 -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| GEDCOM sintético | `exemplo.ged`, gerado no passo 1 |
| CSV de segmentos sintético | `exemplo_segmentos.csv`, com 11 segmentos em 3 cromossomos (passo 2) |

## 1. Subir a aplicação e gerar o GEDCOM

```powershell
.\.venv\Scripts\python.exe -c "from tests.fixtures.sample_dna import DNA_GED; open('exemplo.ged','w',encoding='utf-8').write(DNA_GED)"
.\.venv\Scripts\python.exe src\app.py
```

A inicialização anuncia o endereço (`Servindo com waitress em http://0.0.0.0:5000`).

## 2. Gerar o CSV de segmentos

```powershell
.\.venv\Scripts\python.exe -c "from tests.fixtures.sample_dna import DNA_CSV_SEGMENTOS_DISTRIBUICAO as c; open('exemplo_segmentos.csv','w',encoding='utf-8').write(c)"
```

Ele tem 11 segmentos: 4 no cromossomo 1, 4 no 7 e 3 no 16, todos de 10 cM ou mais.

## 3. Carregar e analisar

1. **Fase 1**: envie `exemplo.ged`.
2. **Fase 3**: escolha a árvore e envie `exemplo_segmentos.csv` em "Lista de Matches (CSV)".

## 4. Conferir a tabela

Abra o cartão **"Regiões compartilhadas"** (nasce fechado). A ordem dentro do cartão deve ser:

1. o parágrafo de abertura;
2. o **ideograma** e a legenda dele;
3. a **distribuição por cromossomo** (barras) e a legenda;
4. **"Detalhamento dos segmentos compartilhados"** — a tabela nova;
5. a lista de regiões.

Na tabela, confira:

- [ ] O contador mostra **11** linhas (sem filtro, o texto é só o total).
- [ ] Uma linha por par (região, kit): o kit `A111111` aparece **duas vezes** — no cromossomo 7
      (45 cM) e no cromossomo 1 (12 cM) —, porque são dois segmentos diferentes, em regiões
      diferentes.
- [ ] As colunas trazem: cromossomo em **badge**, posição `início – fim` em pares de bases, tamanho em
      **Mb**, **cM**, **kit**, **nome** e o **selo de desfecho** igual ao da lista.
- [ ] A ordem é cromossomo 1 → 7 → 16, e dentro do cromossomo por posição inicial.
- [ ] A paginação oferece **10, 20 e 30** por página. Com 11 linhas o seletor aparece com **20**
      selecionado (cabem as 11, então não há anterior/próxima); escolha **10** e os controles passam a
      mostrar "Página 1 de 2".

## 5. Conferir os filtros

- [ ] No filtro de cromossomo, escolha **7**: sobram **4 linhas** e o contador passa a mostrar
      "4 de 11".
- [ ] Volte para **Todos** e digite `ana` na busca: sobram **2 linhas** (a Ana do cromossomo 7 e a do
      cromossomo 1).
- [ ] Digite algo inexistente (`zzz`): nenhuma linha visível, a tabela mostra a frase de estado vazio
      e os controles continuam na tela.

## 6. Conferir o clique

- [ ] Clique em qualquer linha do cromossomo 7: o navegador rola até o **ideograma** e a faixa do
      cromossomo 7 fica destacada com um contorno.
- [ ] O mesmo clique funciona pelo **teclado**: `Tab` até o badge do cromossomo e `Enter`.
- [ ] Com o JavaScript desligado, a tabela mostra as 11 linhas e o badge continua levando à faixa
      (o que se perde é filtrar e paginar).

## 7. Conferir a cópia

- [ ] O botão "Copiar" da linha coloca no clipboard um texto com cromossomo, posição, tamanho, cM,
      kit e nome, e o rótulo vira "copiado" por alguns segundos.

## 8. Rodar os testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_segmentos.py tests/test_contrato_dos_segmentos.py -q
```

Na suíte inteira, as falhas conhecidas de ambiente (4 de `test_characterization_mermaid` e o literal
`1. Lista de Matches (CSV)`) não são desta feature.

## 9. Se algo divergir

1. Anote a linha, o valor esperado e o exibido — a conta de referência é a seção 4.
2. Confira se a divergência é de **número** (nasce no núcleo) ou de **formatação** (nasce no template).
3. Abra um bug com `/reversa-debugger` (contexto `analise-dna`) em vez de ajustar o valor na mão.
