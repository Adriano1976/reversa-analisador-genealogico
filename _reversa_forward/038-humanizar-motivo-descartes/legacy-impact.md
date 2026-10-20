# Legacy Impact: humanizar o motivo dos matches descartados

> Identificador: `038-humanizar-motivo-descartes`
> Data: `2026-10-20`
> Âncora: `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md` (cenário **legado**)

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/core/motivos_do_descarte.py` | `core` (novo) | componente-novo | MEDIUM | Catálogo `código → frase`, `Motivo`, diagnóstico por precedência e detalhe técnico. Isola o texto de apresentação do motor de decisão |
| `src/core/matching.py` | `core.matching` | contrato-alterado | **HIGH** | O segundo elemento de `avaliar_candidatos` deixou de ser `str` e passou a ser `Motivo`. Os dez motivos de recusa nascem do catálogo. `match_candidates` preserva o contrato de texto |
| `src/core/dna_analysis.py` | `core.dna_analysis` | delta-de-contrato-externo | **HIGH** | O dicionário do descarte ganhou `motivo_codigo` e `motivo_detalhe`; `motivo` passou a ser o texto humano. É o contrato que a tela e a planilha consomem |
| `src/ports/__init__.py` | `ports` | contrato-alterado | MEDIUM | `DescartadoDaAnalise` ganhou `reason_code` e `detail`, ambos com default — o adaptador de persistência não muda |
| `src/application/dna_analysis.py` | `application.dna_analysis` | contrato-alterado | LOW | Projeta os dois campos novos; nenhuma regra de negócio mora aqui |
| `src/reporting/csv_de_descartes.py` | `reporting.csv_de_descartes` | delta-de-contrato-externo | MEDIUM | Nona coluna `Detalhe técnico`. As oito primeiras mantêm nome e posição |
| `src/templates/index.html` | `templates` | regra-alterada | LOW | Uma frase sob o botão de download; a célula Motivo já renderiza o texto que receber |

## 2. Diff conceitual, por componente

**`core.matching`.** A decisão não mudou — nenhum limiar, peso, ramo ou ordem de avaliação foi
tocado. O que mudou é o **relato** da recusa: onde antes uma f-string montava
`score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)`, agora um
diagnóstico escolhe **uma** causa entre seis e devolve `Motivo(codigo, texto, detalhe)`. Para que
o diagnóstico pudesse citar o sétimo portão, o cálculo do token do meio
(`csv_tokens`/`csv_middle`/`isdisjoint`) subiu para antes do veredito — mesma expressão, mesmo
resultado, apenas disponível antes. O veto continua exatamente onde estava e com os mesmos
números: `nota >= 96`, `prenome >= 92`, `interseção >= exigida`, `grafia ok`.

**`core.motivos_do_descarte` (novo).** Onze códigos estáveis, um por causa: seis do bloco de
semelhança (cinco recusas + o filtro anti-falso-positivo) e cinco do adendo `024`. A precedência é
explícita e documentada: token do meio → sobrenomes de menos → grafia → prenome → semelhança
geral. Quem consome o motivo pode usar o texto (humano) ou o código (estável).

**`core.dna_analysis`.** O descarte que sai do motor passou a levar três campos em vez de um, e o
texto é o humano. O caminho da promoção continua com `motivo` = `"não encontrado"` quando não há
recusa; nesse caso o código é `nao_encontrado` e o detalhe é vazio.

**`ports` / `application`.** `DescartadoDaAnalise` ganhou dois campos com default vazio, então o
adaptador Postgres não precisou de uma linha: ele continua gravando `reason` (o texto). O histórico
guarda o texto humano; o código e o detalhe existem só no payload da análise.

**`reporting.csv_de_descartes`.** Uma coluna ao fim, `Detalhe técnico`, com os quatro números
rotulados e vírgula decimal. As regras de formato da `035` continuam valendo inteiras: BOM,
separador `;`, decimal com vírgula, guarda contra fórmula e uma linha por descarte.

**`templates/index.html`.** Só o texto sob o botão de download mudou, para dizer onde estão os
números. A alteração fica dentro do `{% if skipped_matches %}`, e é por isso que `SHA_DA_TELA`
não se move.

## 3. Preservadas

Regras 🟢 de `_reversa_sdd/domain.md` que continuam verdadeiras, palavra por palavra:

- **§3.4 — matching difuso de nomes: o cM não decide aceitação.** Todos os portões, limiares e
  pesos intactos; o `cm` só entra no limiar adaptativo de Jaccard, como antes.
- **§3.4 — filtro anti-falso-positivo.** Continua recusando quem não tem sobrenome em comum nem
  acerto de sufixo. Só perdeu o parêntese técnico no texto.
- **`RN-07` — o match descartado é exibido com motivo, nunca omitido.** A regra é sobre existir
  motivo; ele continua existindo para todo descarte.
- **Adendo `024` — a decisão não mudou, só o texto.** Os quatro motivos por sobrenome mantêm a
  redação, agora vinda do catálogo.
- **Adendo `034` — o descarte leva os candidatos avaliados e o ano de nascimento.** Intocado.
- **Adendo `035` — formato da planilha.** BOM, `;`, decimal com vírgula, guarda contra fórmula,
  uma linha por descarte, ` | ` entre candidatos.
- **`ADR-34` — `reporting/` não importa `core/`.** A `reporting` continua pura; o texto chega
  pronto no dicionário.
- **`RN-18`** (mensagem fixa de GEDCOM recusado) e **`RN-17`** (reenvio): fora do caminho tocado.

## 4. Modificadas

| Regra | Antes | Depois | Motivo |
|---|---|---|---|
| Contrato de mensagem do motivo de score (`_reversa_sdd/analise-dna/contracts.md#6`) | `"score insuficiente ou conflito de sobrenome (given=…, final=…, inter=…/…, jacc=…)"` | uma das cinco frases do catálogo, com código estável | O texto antigo não dizia a causa e omitia o sétimo portão (adendo `024`, resíduo 3) |
| Contrato do motivo do filtro anti-falso-positivo | `"sem sobrenome em comum (filtro anti-falso-positivo)"` | `"nenhum sobrenome em comum entre o nome e o da árvore"` | `RF-07`: tirar o jargão do catálogo inteiro |
| Payload do descarte (`034`) | `{csv_name, kit, cm, motivo, candidatos}` | `+ motivo_codigo, motivo_detalhe` | `RN-27` (causa estável) e `RN-28` (números preservados) |
| Planilha de trabalho (`035`) | 8 colunas | 9 colunas, a nona `Detalhe técnico` | `RN-28` — os números saem da coluna Motivo sem se perder |

## 5. Sem impacto

Nenhuma tabela, coluna, índice, migração ou consulta foi criada ou alterada. Nenhuma dependência
nova. Nenhum arquivo pré-existente foi apagado.
