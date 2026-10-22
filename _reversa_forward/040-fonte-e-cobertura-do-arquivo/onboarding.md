# Onboarding: conferir fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Para quem nunca viu esta feature: o roteiro leva do zero à leitura do painel e do estado de medida.

## 1. Subir a aplicação

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
.\.venv\Scripts\python.exe src\app.py
```

A aplicação anuncia o endereço no log (por padrão, `http://127.0.0.1:5000`). Se o processo já estiver
rodando de uma sessão anterior, **reinicie**: o Jinja cacheia template, e mudança de template só aparece em
processo novo. Mudança só de CSS não precisa reiniciar — basta `Ctrl+F5`.

## 2. Rodar a análise real

1. Na aba da árvore, escolha `Adriano_Santos_v3_tratado.ged` (ou envie o arquivo de
   `D:\dados-genealogicos\Arquivos  GEDCOM\`).
2. Na aba do relatório de DNA, escolha `Famílias_Sergipanas.csv` (ou envie de
   `D:\dados-genealogicos\GEDmatch Ancestor Projects\`).
3. Informe a raiz `Adriano Santos` e rode a análise.

O resultado esperado continua **8 conexões encontradas. 448 descartadas.** — a feature não mexe em
aceitação, ordem nem contagem.

## 3. O que olhar no painel "Cobertura do arquivo"

O painel fica **antes de "Resultados das Análises de Conexão"**, fora da guarda dos cartões, e nasce aberto.

| Onde | O que deve aparecer |
|------|---------------------|
| Números | `617` linhas · `456` evidências · `456` kits · `11` laboratórios (de `45` grafias) · `22` cromossomos · `9,05` cM de mediana · `74%` de segmentos abaixo de 10 cM · `88%` sem bloco de 15 cM |
| Frase do filtro | "456 de 617 segmentos estão abaixo do piso de 10 cM e são descartados pelo filtro de endogamia" |
| Frase do bloco | "58 de 112 pessoas passam de 15 cM somados, mas nenhum bloco chega a 15 cM" |
| Frase dos SNPs | "232 pessoas têm menos de 900 SNPs somados" |
| Frase do corte | "O arquivo não declara o corte usado na busca que o gerou" e "ausência aqui não é ausência de parentesco" |
| Frase das fontes | "59 células de fonte não trazem laboratório" com os motivos |
| Contagem por laboratório | `Genera 184`, `MyHeritage 117`, `meuDNA 49`, `FTDNA 22`, `23andMe 15`, `Ancestry 5`, os de uma evidência cada, e `não declarada` |

## 4. O que olhar nos cartões

1. Abra o cartão de **Clezia Santos** (154,5 cM): a linha `Fonte: Genera` aparece **sem etiqueta** — o valor
   já era canônico.
2. Abra o cartão de **Airton Passos Vasconcelos** (51,3 cM): a linha deve dizer
   `Fonte: não declarada` **com** a etiqueta `Outro (insira o nome abaixo)` ao lado, e o bloco 2 deve trazer
   `Medida parcial — menor bloco de 13,7 cM (abaixo de 15)`.
3. Confira que nenhum cartão traz `Selecione uma empresa ou fonte`, `Minha herança` ou `Meu Patrimônio` como
   **rótulo** de fonte (eles só podem aparecer dentro da etiqueta de texto original).
4. Confira que a ressalva "qualidade da medida, não do parentesco" acompanha todo estado.

## 5. Conferir os casos negativos (teste sintético)

| Caso | O que deve acontecer |
|------|----------------------|
| CSV sem coluna de fonte | O painel aparece e o item de laboratórios diz "nenhuma fonte declarada"; nenhum cartão inventa laboratório |
| Kit com `-` na primeira linha e `Genera` na terceira | O cartão exibe `Fonte: Genera` |
| Kit com `Genera` e `MyHeritage` em linhas diferentes | O cartão exibe o primeiro e traz o aviso `fontes_divergentes` com os dois |
| Arquivo sem nenhuma evidência utilizável | O painel **não** é renderizado; o aviso de falta de evidência continua no cartão |
| Evidência de 14,99 cM | Estado `insuficiente` |
| Evidência de 15,00 cM com bloco de 15,00 cM e 899 SNPs | Estado `parcial` |

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_fontes_de_laboratorio.py tests/test_qualidade_da_medida.py tests/test_cobertura_do_arquivo.py -v
```

## 6. Rodar a suíte e a paridade

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests\rodar_paridade.py
```

O esperado é suíte verde e `PARIDADE 100 %` (ou divergência **declarada** nas chaves aditivas do payload da
evidência, nunca tolerância ampliada).

## 7. Conferir a tela de entrada

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_icone_de_atalho.py -q
```

`SHA_DA_TELA` **não** pode mudar: o painel depende de `cobertura`, que é `None` na tela de entrada.

## 8. Limpeza

Nada a limpar: a feature não grava arquivo, tabela nem histórico. Os uploads usados no roteiro são os mesmos
de sempre, em `src/uploads/`.
