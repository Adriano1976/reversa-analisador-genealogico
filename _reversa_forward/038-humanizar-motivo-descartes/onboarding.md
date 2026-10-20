# Onboarding: conferir os motivos humanizados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Para quem nunca viu esta feature: o roteiro abaixo leva do zero à leitura da coluna Motivo.

## 1. Subir a aplicação

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
.\.venv\Scripts\python.exe -m src.app
```

A aplicação abre em `http://127.0.0.1:5000` (ou na porta que o log anunciar). Se o processo já
estiver rodando de uma sessão anterior, **reinicie**: o Jinja cacheia template, e mudança de
template só aparece em processo novo. Mudança só de CSS não precisa reiniciar — basta `Ctrl+F5`.

## 2. Carregar uma árvore e rodar uma análise

1. Na fase 1, envie um GEDCOM (o sintético de `tests/fixtures/sample_gedcom.py` serve).
2. Abra a árvore pela lista.
3. Na fase 2 ou 3, envie um CSV de matches que produza **descartes** — nomes que não casam com
   ninguém da árvore.

Se não tiver o par à mão, o caminho mais rápido é rodar a análise pelos testes:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_motivo_humanizado.py -v
```

## 3. O que olhar no bloco "Matches descartados"

| Onde | O que deve aparecer |
|------|---------------------|
| Coluna **Motivo** | Uma frase em português comum, sem `given`, `final`, `inter`, `jacc`, sem parênteses de fórmula |
| Motivo de recusa por semelhança | Uma das cinco: "o nome tem uma parte a mais que não aparece na árvore", "há sobrenomes em comum, mas de menos para este prenome", "o sobrenome é parecido, mas não o suficiente", "o prenome é diferente do que está na árvore", "o nome é parecido, mas não o suficiente para ser a mesma pessoa" |
| Texto sob o botão de download | Diz que o detalhe técnico vai na planilha |
| Cartão promovido | Repete o motivo **humano**, não a fórmula |

## 4. Baixar a planilha e conferir

1. Clique em **Baixar lista de trabalho (CSV)**.
2. Abra no Excel (duplo clique; não use "importar").
3. Confira:
   - continua abrindo com acento correto (BOM);
   - a separação é por `;` e o cM usa vírgula decimal;
   - a **nona** coluna chama-se `Detalhe técnico` e traz, por exemplo,
     `prenome 100 · nota 88,25 · sobrenomes em comum 1 de 1 · grafia do sobrenome 0,50`;
   - as oito colunas anteriores estão na mesma ordem de antes.

## 5. Conferir que a decisão não mudou

Esta é a parte que importa mais que a redação. Rode:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_characterization_matching.py tests/test_dna_analysis.py -v
```

Os cartões aceitos, os descartes, o cM e os caminhos precisam ser os mesmos de antes da feature. Se
algum nome mudou de lado, a mudança saiu do escopo de texto e deve ser tratada como defeito.

## 6. Sinais de que algo deu errado

| Sintoma | Causa provável |
|---------|----------------|
| A tela ainda mostra a fórmula | O processo não foi reiniciado (template cacheado) |
| A frase aparece, mas a planilha não tem a nona coluna | A rota usada é a antiga; conferir `reporting/csv_de_descartes.py` |
| `SHA_DA_TELA` mudou | A edição do template vazou para fora do `{% if skipped_matches %}` |
| Uma frase diz "sobrenome" quando o nome não tem sobrenome | O diagnóstico está sendo aplicado fora do bloco de semelhança |
