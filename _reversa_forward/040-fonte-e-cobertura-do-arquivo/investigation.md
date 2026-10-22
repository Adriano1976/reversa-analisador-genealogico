# Investigation: fonte normalizada e cobertura do arquivo

> Identificador: `040-fonte-e-cobertura-do-arquivo`
> Data: `2026-10-22`
> Insumo: `_reversa_forward/040-fonte-e-cobertura-do-arquivo/requirements.md` e a medição da análise de
> 2026-10-22 descrita em `_reversa_sdd/analise-planilhas-dna-sergipe/analise.md` (seção 0).

## 1. A pergunta que a investigação tinha de responder

1. **Onde** normalizar a fonte: no parser, no núcleo, na aplicação ou no template?
2. **Como** decidir o que é laboratório sem inventar: catálogo, heurística ou dicionário externo?
3. **Onde** medir a cobertura do arquivo, sem reler o CSV nem devolver um quarto valor do núcleo?
4. **Quais** pisos usar no estado da medida, e com que estatuto (publicado ou declarado)?
5. O que **muda** para os testes que já prendem o payload e o texto da tela?

## 2. O dado real, medido antes de decidir

Arquivo `Famílias_Sergipanas.csv` (617 linhas, 456 evidências), lido com os módulos do próprio projeto:

| Medida | Valor |
| --- | --- |
| Valores distintos em `Source` | **45** (44 grafias + célula vazia) |
| Laboratórios que os valores representam | **11** |
| Células sem laboratório | **59** — 40 texto de formulário, 10 empresa não confirmada, 7 nome de projeto, 1 haplogrupo, 1 não reconhecida |
| Segmentos abaixo do piso de 10 cM | **456 de 617 (74%)** |
| Evidências sem bloco de 15 cM | **402 de 456 (88%)** |
| Evidências com SNPs < 900 | **232 de 456 (51%)** |
| Total ≥ 15 cM com maior bloco < 15 cM | **58 de 112** |
| Mediana de cM por evidência | **9,05** |

Duas leituras que mudaram o plano:

- **A variação é ortográfica, não semântica.** `GENERA`, `genera`, `gENERA`, `GEN`, `Genera Brasil` e
  `Outros (Genera)` são a mesma empresa; `Meu DNA`, `MEUDNA`, `Meudna`, `MeuDNa`, `MeuDNA-Mandelics` também.
  Isso pede tabela explícita, não distância de edição — `Genos` e `Genera` ficam a uma edição de distância e
  são empresas diferentes.
- **Parte das células não é empresa nenhuma.** `Selecione uma empresa ou fonte`, `Outro (insira o nome
  abaixo)`, `Select a Company or Source` e `Other (enter name below)` são texto de formulário que vazou para
  o dado; `L1b1a` é haplogrupo; `Migration - F2 - A` é nome de projeto. Nenhum deles pode virar laboratório.

## 3. Alternativas avaliadas

| Questão | Alternativa | Por que foi descartada |
| --- | --- | --- |
| Onde normalizar | No `parsers/csv_ingest` | Decidir o que é laboratório é domínio, não leitura de arquivo; o parser já tem responsabilidade única (encoding, separador, linha torta) |
| | No template | Regra no Jinja, contra `architecture.md#3` e contra o RF-12 do projeto |
| | Na `application` | A evidência sairia inconsistente para o histórico e para o cartão, que leem o mesmo payload |
| | **`core/fontes_de_laboratorio.py`** | Escolhida: testável sem CSV, como `motivos_do_descarte.py` |
| Como decidir | Heurística por prefixo | `Genera` casaria com `Genos`; `Meu` casaria com `Meu Patrimônio` |
| | Distância de edição | Aproximaria empresas distintas e erraria em silêncio |
| | Dicionário externo/API | Não há registro público de nomes de laboratório; cria dependência de rede (o sistema não tem nenhuma) |
| | **Tabela literal de alias** | Escolhida: auditável, sem dependência e reversível |
| Onde medir cobertura | No template | O dado não chega lá; e seria regra na apresentação |
| | Relendo o CSV na aplicação | I/O duplicado — o núcleo já tem o `df` em mãos |
| | Quarto valor no retorno de `dna_analysis` | Quebraria os chamadores e o coletor de paridade |
| | **Coletor opcional, como `observacoes_do_arquivo`** | Escolhida: padrão já existente no mesmo arquivo e no mesmo escopo |
| Pisos do estado | Reusar só o que existe (10 e 15 cM) | Deixaria SNPs sem papel, e 4 dos 50 cartões "robustos" têm menos de 900 SNPs |
| | Usar a fórmula da planilha inteira (com `BA`, o cM triangulado) | `BA` é volume de triangulação, não qualidade de medida; e a fórmula original mistura isso com parentesco |
| | **15,0 / 15,0 / 900, declarados** | Escolhida: dois pisos que o projeto já usa e um de triagem declarado |

## 4. Padrões do projeto aplicados

- **Vocabulário canônico com alias**, como `utils/name_keys.norm_name` faz com nomes: normaliza antes de
  comparar, mas preserva o original para exibir.
- **Coletor opcional no núcleo**, como `observacoes_do_arquivo` (`core/dna_analysis.py:563`): a função
  preenche uma lista/dict do chamador e mantém o retorno de três posições.
- **Contador derivado e frase composta no template**, como a contagem em três faixas da feature 033: o
  núcleo entrega números, o template compõe a frase.
- **Corte de triagem declarado**, como os 20,0 cM da feature 039: o número fica num literal nomeado, com a
  medição no docstring, e a natureza declarada aparece na tela.

## 5. O que **não** foi investigado (e por quê)

- **Nome oficial de cada laboratório**: não há fonte pública estável; o catálogo é do projeto e está
  declarado como tal (Princípio V).
- **`TestCompany` como coluna de fonte**: o export de um-para-muitos do GEDmatch usa esse nome e o detector
  não o reconhece. Ficou fora de escopo (lacuna registrada no requirements) para não ampliar a superfície de
  leitura de CSV nesta feature.
- **Reconstruir o painel a partir do histórico**: o banco não guarda evidência nem cobertura; reabrir uma
  análise antiga não reconstrói o painel (data-delta §6).
- **Cor do estado**: mediu-se que 75% das evidências são `insuficiente`; pintar três faixas transformaria a
  exceção em regra visual. Ficou como texto (D-11).
