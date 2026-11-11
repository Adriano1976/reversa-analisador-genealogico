<!--
Onboarding da feature 057 — Distribuição por cromossomo.
Passo a passo para um humano que vai testar a feature pela primeira vez.
-->

# Onboarding: testar a "Distribuição por cromossomo"

> Identificador: `057-distribuicao-por-cromossomo`
> Data: `2026-11-10`
> Público: quem nunca viu a feature. Nenhum dado real é necessário — e nenhum dado real deve ser
> versionado (`.reversa/principles.md#I`).

## Antes de começar

| Você precisa de | Como obter |
|-----------------|------------|
| Python 3.13 e a `.venv` do projeto | `py -3.13 -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| Um GEDCOM sintético | o passo 2 gera `exemplo.ged` a partir da fixture do projeto |
| Um CSV de matches sintético | o passo 3 gera `exemplo_segmentos.csv`, já com segmentos em três cromossomos |

Os dois arquivos ficam **fora do repositório** (ou em `uploads/`, que não é versionado). Se você
usar um arquivo real, ele não entra no git em nenhuma hipótese.

## 1. Subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

A inicialização anuncia o endereço (`Servindo com waitress em http://0.0.0.0:5000`). Abra no
navegador.

## 2. Gerar o GEDCOM sintético

```powershell
.\.venv\Scripts\python.exe -c "from tests.fixtures.sample_dna import DNA_GED; open('exemplo.ged','w',encoding='utf-8').write(DNA_GED)"
```

## 3. Gerar o CSV de segmentos

Salve o conteúdo abaixo em `exemplo_segmentos.csv`. Ele tem **três cromossomos** e um kit que
aparece em dois deles — o suficiente para ver as barras, os dois eixos e a deduplicação:

```csv
Name,cM,Kit,Chromosome,Start,End
Ana Silva Souza,45,A111111,7,21000000,39000000
Zzz Um,40,B222222,7,21500000,38500000
Zzz Dois,35,C333333,7,22000000,38000000
Zzz Tres,30,D444444,7,23000000,37000000
Bento Alves,22,E555555,1,53000000,55000000
Clara Dias,18,F666666,1,53500000,55200000
Davi Reis,15,G777777,1,54000000,54800000
Ana Silva Souza,12,A111111,1,54500000,56000000
Elisa Prado,11,H888888,16,53000000,54500000
Fabio Nunes,13,I999999,16,53500000,55000000
Gilda Rocha,14,J000000,16,54000000,54800000
```

O que esperar dessa entrada (é a conta que você vai conferir no passo 6):

| Cromossomo | Kits distintos | cM médio |
|---|---:|---:|
| 1 | 4 (`A111111`, `E555555`, `F666666`, `G777777`) | 16,75 |
| 7 | 4 | 37,5 |
| 16 | 3 | 12,667 |

## 4. Carregar a árvore

Na **fase 1**, envie `exemplo.ged` e confirme que a árvore aparece na lista de arquivos.

## 5. Rodar a análise de DNA

Na **fase 3**, escolha a árvore carregada e envie `exemplo_segmentos.csv` em "Lista de Matches
(CSV)". A primeira análise de uma árvore grande é a mais lenta (o parse domina); com este GEDCOM
sintético a resposta é imediata.

## 6. Conferir o gráfico

Abra o cartão **"Regiões compartilhadas"** (ele nasce fechado). A ordem dentro do cartão deve ser:

1. o parágrafo que explica o que é região compartilhada;
2. o **ideograma** por cromossomo e a legenda dele (convergente, dividido, parcial, sem ancestral,
   "Régua: GRCh37");
3. **"Distribuição por cromossomo"** — o gráfico novo;
4. a lista de regiões.

No gráfico, confira:

- [ ] Um par de barras por cromossomo, e só para os cromossomos que têm região (1, 7 e 16 no
      exemplo). Nenhum cromossomo vazio entra no eixo (`RN-06`).
- [ ] Eixo da esquerda rotulado **Matches**, eixo da direita rotulado **cM médio**; os dois
      começam em **zero** (`RN-08`).
- [ ] Os números do passo 3 batem: chr 1 com 4 matches, chr 7 com 4, chr 16 com 3. O kit
      `A111111` conta **uma vez** em cada cromossomo, mesmo aparecendo em dois (`RN-02`).
- [ ] cM médio do chr 1 = (22 + 18 + 15 + 12) / 4 = **16,75**; do chr 7 = (45 + 40 + 35 + 30) /
      4 = **37,5**; do chr 16 = (11 + 13 + 14) / 3 ≈ **12,67** (`RN-03`).
- [ ] Passar o mouse sobre um cromossomo destaca o par e abre o cartão com `Chr N`, o número de
      matches e o cM médio — **sem nome nem kit de match** (`RN-07`).
- [ ] `Tab` percorre os cromossomos e o cartão abre igual, com os dois números no `aria-label`
      (`RF-07`).
- [ ] A legenda nomeia as duas séries e diz de onde vem o número (regiões compartilhadas,
      segmentos de 10 cM ou mais).

## 7. Conferir o que NÃO mudou

- [ ] A tela de entrada (sem resultado) não ganhou byte nenhum: é o `SHA_DA_TELA` de
      `tests/test_icone_de_atalho.py`.
- [ ] A lista de regiões e o ideograma continuam com os mesmos números de antes.
- [ ] `POST /regioes.csv` continua exportando uma linha por região, sem coluna agregada (`D-11`).

## 8. Rodar os testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_distribuicao.py tests/test_grafico_da_distribuicao.py tests/test_contrato_das_regioes.py -q
```

Na suíte inteira, as falhas conhecidas de ambiente (4 de `test_characterization_mermaid` e o literal
`1. Lista de Matches (CSV)` em `test_tres_fases_da_tela.py`) não são causadas por esta feature.

## 9. Se algo divergir

1. Anote o cromossomo, o valor esperado e o valor exibido.
2. Compare com a conta do passo 3 — é a única fonte de verdade do exemplo.
3. Abra um bug com `/reversa-debugger` (contexto `analise-dna`) em vez de ajustar o número no
   template: o número nasce no núcleo, e o gráfico só desenha.
