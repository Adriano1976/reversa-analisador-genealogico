# Contrato: cobertura do arquivo e estado da medida

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Rota: `POST /` com `action=dna_analysis`
> Formato: resposta `200 text/html` (a mesma página de resultados da análise de DNA)

## 1. Request

Nenhum campo novo. O contrato da análise continua o mesmo:

| Campo | Tipo | Obrigatório | Conteúdo |
|-------|------|-------------|----------|
| `action` | `str` | sim | `dna_analysis` |
| `gedcom_filename` | `str` | sim | Referência da árvore armazenada |
| `matches_csv_filename` | `str` | não | Referência do CSV armazenado; tem precedência sobre o upload |
| `matches_csv` | arquivo | não | CSV enviado no próprio formulário |
| `root_name` | `str` | sim | Nome da raiz, como o operador digitou |
| `promover` | `str` | não | Promoções já feitas, no formato `nome\|pid\|motivo` |

## 2. Response

- `200` com a página de resultados, quando a análise conclui.
- O painel é um fragmento HTML **dentro** dessa página; não há rota, JSON, download ou cabeçalho novo.
- A linha da medida é um fragmento **dentro** do bloco 2 de cada cartão já existente.
- As respostas de erro (`404` raiz inexistente, `422` CSV/arquivo inválido) não mudam e não contêm painel.

## 3. Regra de presença

O painel existe quando a análise produziu **pelo menos uma evidência** — isto é, `cobertura` não é `None` e
`cobertura.evidencias > 0`. Ele **não** depende de haver cartão: um arquivo com 456 evidências e zero cartões
tem painel.

A linha da medida existe em **todo** cartão que tenha evidência genética disponível (`kits` não vazio); ela
não aparece no cartão "Sem evidência genética disponível para esta pessoa".

## 4. Contrato do HTML — painel

| Elemento | Contrato |
|----------|----------|
| Container | `<details class="card cobertura-do-arquivo mb-4" id="cobertura" open>` |
| Posição | **Fora** de `{% if dna_results %}`, depois do bloco "Observações do arquivo" e antes de "Resultados das Análises de Conexão" |
| Título | `Cobertura do arquivo`, em `<summary class="sumario-do-cartao">` com `<div class="card-header"><h5 class="mb-0">` |
| Subtítulo | Texto que informe que os números valem para o CSV inteiro e não para uma conexão |
| Números | Oito itens, cada um com valor e rótulo: linhas, evidências, kits, laboratórios (com o número de grafias), cromossomos, mediana de cM, percentual de segmentos abaixo de 10 cM, percentual sem bloco de 15 cM |
| Contagem por laboratório | Lista de rótulos com contagem, em ordem decrescente de contagem e alfabética no empate; inclui `não declarada` quando houver célula sem laboratório || Frases | (a) filtro de 10 cM; (b) total ≥ 15 cM sem bloco ≥ 15 cM; (c) SNPs < 900; (d) corte não declarado + "ausência no arquivo não é ausência de parentesco"; (e) células sem laboratório com motivos |
| Proibido | Qualquer afirmação de parentesco, diagrama, confronto, hipótese, promoção, botão ou formulário |

## 5. Contrato do HTML — fonte no bloco 2

| Situação | O que renderiza |
|----------|-----------------|
| Laboratório reconhecido igual ao texto original | `Fonte: Genera` |
| Laboratório reconhecido com grafia diferente | `Fonte: Genera` **e** etiqueta com o texto original (`GENERA`, `Meu DNA`, …) |
| Texto de formulário | `Fonte: não declarada` **e** etiqueta com o texto original |
| Empresa não confirmada (`Minha herança`, `Meu Patrimônio`) | `Fonte: não declarada` **e** etiqueta com o texto original |
| Valor não reconhecido | `Fonte: outro` **e** etiqueta com o texto original |
| CSV sem coluna de fonte | `Fonte: não identificada no CSV` (texto que já existe) |

## 6. Contrato do HTML — linha da medida

| Elemento | Contrato |
|----------|----------|
| Posição | Dentro do bloco 2, **depois** da grade de números do kit |
| Marcação | `<p class="medida-da-evidencia">` com o rótulo em negrito |
| Rótulos | `Medida robusta`, `Medida parcial`, `Medida insuficiente` |
| Conteúdo | Os três números que produziram o estado: total, maior bloco e SNPs |
| Motivo | `parcial` e `insuficiente` nomeiam o motivo: bloco menor que 15,0 cM, SNPs abaixo de 900, total abaixo de 15,0 cM |
| Ressalva | Frase fixa: "qualidade da medida, não do parentesco" |
| Proibido | Cor de fundo por estado, selo no cabeçalho do cartão, alteração do selo de cM ou do confronto |

Exemplo mínimo (dados sintéticos):

```html
<p class="medida-da-evidencia">
  <strong>Medida parcial</strong> — total 51,3 cM, maior bloco 13,7 cM e 7.349 SNPs.
  Menor bloco abaixo de 15,0 cM. Qualidade da medida, não do parentesco.
</p>
```

## 7. Estados vazios e de borda

| Situação | Comportamento |
|----------|---------------|
| Sem evidência nenhuma | Painel não renderizado; o aviso de falta de evidência continua no cartão |
| Arquivo sem coluna de fonte | Painel renderiza; item de laboratórios diz "nenhuma fonte declarada" |
| Todas as evidências sem laboratório | Lista por laboratório só com `não declarada` |
| Evidência sem SNPs | Estado não penaliza por SNPs ausentes; o número aparece como "não informado" |
| Evidência sem maior bloco (nenhum segmento com cM) | Conta como abaixo do piso: `insuficiente` |
| Um único cromossomo | Painel mostra `1`; mediana de uma evidência é o próprio valor |
| Arquivo com 0 linhas ou erro de leitura | O erro atual; painel não renderizado |

## 8. Determinismo e idempotência

- A mesma análise produz o mesmo painel e os mesmos estados, byte a byte, independentemente da ordem do CSV,
  do processo ou do `PYTHONHASHSEED` (a ordenação dos laboratórios é explícita).
- O painel é leitura pura: não grava, não lê arquivo e não altera cartão, descarte ou histórico.

## 9. Erros

| Situação | O que acontece |
|----------|----------------|
| Raiz inexistente / CSV sem colunas / CSV ilegível | Exceções atuais; `404`/`422` com a tela de entrada, sem painel |
| Falha de persistência | A análise conclui; `cobertura` e `medida` não dependem do banco |
| Erro inesperado | Tela de erro atual; nenhum painel parcial |

Nenhum timeout novo: o painel não faz I/O e é renderizado junto com a página.

## 10. Compatibilidade

| Elemento | Garantia |
|----------|----------|
| `SHA_DA_TELA` (tela de entrada) | Não muda: `cobertura` é `None` fora do ramo `dna_analysis` |
| Contagem "N conexões analisadas" | Mesma frase, mesmos números |
| Confronto, viabilidade, caminho, sugestão | Nenhum campo lido muda |
| Lista "Matches descartados" e CSV | Mesmas nove colunas, mesmos itens e ordem |
| Histórico (`analysis`, `match_result`, `skipped_match`) | Sem campo, coluna ou migração; `cobertura` e `medida` não são projetados |
| Request | Sem campo novo |

## 11. Testes que prendem este contrato

- `tests/test_cobertura_do_arquivo.py` — os oito números, percentuais, mediana, ordenação dos laboratórios,
  casos vazios e arquivo sem coluna de fonte.
- `tests/test_qualidade_da_medida.py` — 14,99/15,00, 899/900, SNPs ausentes, bloco ausente.
- `tests/test_fontes_de_laboratorio.py` — catálogo, placeholders, empresa não confirmada, desconhecido,
  escolha dentro do kit e divergência.
- `tests/test_dna_analysis.py` / `tests/test_characterization_matching.py` — chaves aditivas declaradas.
- `tests/test_estilo_da_tela.py` — a classe `cobertura-do-arquivo` e a linha `medida-da-evidencia` existem;
  o painel não é cartão de resultado nem rodapé de descartes.
- `tests/test_icone_de_atalho.py` — hash da tela de entrada.
