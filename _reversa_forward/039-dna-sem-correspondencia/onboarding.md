# Onboarding: conferir os cartões "DNA sem correspondência na árvore"

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Para quem nunca viu esta feature: o roteiro abaixo leva do zero à leitura dos cartões.
>
> **Vigente:** o roteiro atual é o da seção "Atualização 2026-10-22 (E003)"; as seções 2–8
> descrevem a primeira entrega, quando o item era um bloco separado de 40,0 cM.

## 1. Subir a aplicação

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
.\.venv\Scripts\python.exe src\app.py
```

A aplicação anuncia o endereço no log (por padrão, `http://127.0.0.1:5000`). Se o processo já
estiver rodando de uma sessão anterior, **reinicie**: o Jinja cacheia template, e mudança de
template só aparece em processo novo. Mudança só de CSS não precisa reiniciar — basta `Ctrl+F5`.

## 2. Rodar a análise real

1. Na aba da árvore, escolha `Adriano_Santos_v3_tratado.ged` (ou envie o arquivo de
   `D:\dados-genealogicos\Arquivos  GEDCOM\`).
2. Na aba do relatório de DNA, escolha `Famílias_Sergipanas.csv` (ou envie de
   `D:\dados-genealogicos\GEDmatch Ancestor Projects\`).
3. Informe a raiz `Adriano Santos` e rode a análise.

O resultado esperado é **8 conexões encontradas. 448 descartadas.** (456 grupos nome+kit).

## 3. O que olhar no bloco

O bloco fica **depois dos cartões e antes de "Matches descartados"**, e nasce **aberto**.

| Onde | O que deve aparecer |
|------|---------------------|
| Título | `DNA sem correspondência na árvore (9)` |
| Aviso | "Estes matches têm cM alto, mas a árvore não tem ninguém com nome compatível. Isto **não é parentesco documentado**: é um sinal de DNA a investigar. O cM sozinho não define a relação." |
| Primeiro item | `Clezia Santos` · `AZ4078391` · `154,5` cM · `MRCA estimado: 3,27 gerações` |
| Terceiro item | `Airton Passos Vasconcelos` · `SD5093704` · `51,3` cM · `MRCA estimado: 4,06 gerações` |
| Ordem | 154,5; 52,5; 51,3; 50,5; 45,8; 43,7; 43,3; 42,6; 41,2 |
| O que **não** pode haver | "Parentesco documental", "conexão com", diagrama, confronto, "usar este candidato" |

O bloco é um recorte: os mesmos nove nomes continuam em "Matches descartados", com o motivo e os
candidatos de cada um. O texto do bloco diz isso.

## 4. Conferir a lista completa e a planilha

1. Abra "Matches descartados (448)".
2. Confira que os 9 nomes do bloco estão lá, com o motivo de cada recusa.
3. Clique em **Baixar lista de trabalho (CSV)** e abra no Excel.
4. Confira que a planilha continua com **nove colunas**, com `Detalhe técnico` na última, e que a
   Clezia aparece nela (sem candidato compatível, portanto sem candidato preenchido).

## 5. Conferir o caso de zero cartões

O bloco não depende de haver cartão: ele é um aviso sobre o que **não** virou cartão. O teste
sintético cobre o cenário em que a análise tem zero cartões e um descarte de 150,0 cM sem candidato
compatível — o bloco precisa renderizar mesmo assim.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sem_correspondencia.py -v
```

## 6. Rodar os testes

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sem_correspondencia.py tests/test_dna_analysis.py tests/test_characterization_matching.py -v
```

Depois, a suíte completa:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

O que importa mais que o bloco: **cartões, descartes, cM e caminhos continuam os mesmos**. Se algum
nome mudou de lado, a mudança saiu do escopo de leitura e deve ser tratada como defeito.

## 7. Sinais de que algo deu errado

| Sintoma | Causa provável |
|---------|----------------|
| O bloco não aparece na análise real | `sem_correspondencia` não chegou ao contexto; verifique o seletor, o `app.py` e o `{% if skipped_matches %}` |
| O bloco aparece com menos de 9 itens | Limiar, filtro de candidato compatível ou exclusão por nome com cartão mais rígidos que o esperado |
| Um nome que tem cartão aparece no bloco | A exclusão por `norm_name(csv_name)` não está sendo aplicada |
| O bloco mostra candidato, motivo ou botão de promoção | O template copiou a lista completa em vez de usar a lista enxuta |
| O bloco mostra "Parentesco documental" ou diagrama | A feature invadiu o eixo documental; o bloco é só sinal de DNA |
| A tela ainda mostra o layout antigo | O processo não foi reiniciado (template cacheado) |
| `SHA_DA_TELA` mudou | A edição vazou para fora do `{% if skipped_matches %}` |
| O CSV mudou de colunas | O formatador foi tocado; ele não deveria mudar nesta feature |
| A lista completa perdeu itens | O seletor filtrou a lista original em vez de devolver uma lista nova |

## 8. O que não fazer

- **Não promover** ninguém a partir do bloco. Ele não tem botão de propósito; os candidatos fracos
  (por exemplo, um Vasconcelos de 1394) não são a pessoa do match.
- **Não mudar o limiar** de 40,0 cM sem remedir e atualizar o docstring da constante e o
  `requirements.md`.
- **Não somar kits** do mesmo nome. O item é por (nome, kit); dois kits sem cartão são duas linhas.
- **Não usar** o bloco como lista de trabalho. A lista completa e o CSV continuam sendo a via de
  trabalho; o bloco é uma priorização de leitura.

## Atualização 2026-10-22 (E001/E002)

O bloco separado **não existe mais**. O roteiro acima descreve a primeira entrega; o que vale
agora é:

- o corte de triagem é **20,0 cM** (medido: 40 → 9 itens; 30 → 20; 20 → **60**);
- os itens sem correspondência são **cartões na lista de resultados**, com o rótulo
  "Parentesco documental não encontrado", o mesmo cabeçalho e as cinco seções dos demais
  cartões, **sem diagrama e sem promoção**; o **MRCA estimado** aparece na seção 2
  (Evidência genética);
- a análise real mostra **68 cartões** (8 aceitos + 60 sem correspondência) e **448
  descartes**; Clezia Santos (154,5 cM) e Airton Passos Vasconcelos (51,3 cM) estão entre os
  cartões sem correspondência;
- a lista completa de descartes e o CSV de nove colunas continuam intactos; o mesmo item
  aparece nos dois lugares, e o resumo diz isso;
- `tests/test_sem_correspondencia.py` cobre 20,0/19,9, o cartão com o rótulo de não
  encontrado e a lista completa intacta. `SHA_DA_TELA` continua `7375696d…` (16.504 bytes).

## Atualização 2026-10-22 (E003)

O seletor `core.sem_correspondencia.selecionar` **não existe mais**. O módulo guarda só a
regra (`CM_MINIMO_SEM_CORRESPONDENCIA`, `nomes_com_cartao_aceito` e `elegivel`), e a
contagem do resumo é derivada dos próprios cartões marcados em `resultados`:

- `ResultadoDeAnalise.sem_correspondencia` é a **tupla dos cartões** sem correspondência,
  na ordem da tela; o template usa apenas `|length`;
- não há segunda varredura de descartes nem projeção de quatro campos;
- nada muda na tela: **68 cartões** (8 aceitos + 60 sem correspondência), **448
  descartes**, CSV de **9 colunas / 449 linhas**, a mesma mensagem e a mesma promoção;
- `tests/test_sem_correspondencia.py` tem **15 testes** (6 da regra, 8 do cartão e 1 da
  ordem); a suíte completa fica em **1409 passed, 9 skipped**;
- se o resumo mostrar um número diferente do de cartões marcados, o problema está na
  derivação em `application/dna_analysis.py` (a regra do núcleo não mudou).
