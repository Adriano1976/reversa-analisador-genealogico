# Adendo: contagem em três faixas

> Identificador: `033-contador-em-tres-faixas`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `016` e `031`)

## Vigência

Vigente desde 2026-10-19.

## Resumo da entrega

A frase do topo de "Resultados das Análises de Conexão" tinha duas faixas — "com caminho
genealógico no GEDCOM" e "apenas com evidência genética" — e chamava de **sem caminho** o que a
árvore tem. Quando a janela de vida torna o parentesco impossível, a regra do adendo `016`
troca o texto apresentado por "não encontrado" e guarda o original em
`documentary_do_registro`; a frase contava pelo apresentado.

Medido no GEDCOM real em 2026-10-19 (`..._V1_2_Tratado.ged` + `Famílias_Sergipanas.csv`): a
árvore tem **9** caminhos, **6** são apresentados e **3** são recusados pela idade do match. A
frase antiga mandava o operador procurar registro faltando onde o trabalho é procurar homônimo
— exatamente o custo que o adendo `016` já descrevia.

A entrega tem três faixas mutuamente exclusivas que fecham a conta
(`com caminho + recusados + sem caminho` = total), e a árvore sugerida passa a ser contada em
frase própria, com a **mesma condição do bloco do cartão** (`sugestao_resumo` **e**
`sugestao_mermaid`). A sugestão **não** entra como faixa: ela não cria nó documental, e somá-la
ao "com caminho" inflaria o número sem que exista parentesco novo.

**Decisão de escopo registrada:** a árvore sugerida não é caminho para aumentar a contagem. A
cirurgia *consome* um caminho (exige `ERRO_CRONICO` + `path.ids` + ancestral comum + estimativa
de gerações); nos 90 cartões medidos, `hiato` é negativo nos seis caminhos existentes — a árvore
documenta mais gerações do que o cM paga. O reservatório real são os **366 nomes descartados**
antes de qualquer trabalho de grafo (274 por score de sobrenome), que é motor de identidade,
não tela.

A entrega foi concluída em **10 de 10 ações**, com 10 testes novos
(`tests/test_contador_em_tres_faixas.py`).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/domain.md` | §5 Contrato de Mensagens ao Usuário | regra-alterada | A frase de contagem passa a ter três faixas e uma frase condicional de árvore sugerida; a faixa dos recusados só aparece com contagem positiva |
| `_reversa_sdd/domain.md` | §Regras de apresentação do parentesco | regra-nova | "Caminho documental recusado pela idade do match" é o nome do que antes caía em "sem caminho no GEDCOM" |
| `_reversa_sdd/data-dictionary.md` | §8 Payload do núcleo → tela | uso-novo | O template passa a ler `documentary_do_registro` (já existia no payload desde o adendo `016`, sem consumidor de tela) |
| `_reversa_sdd/architecture.md` | §Camada `reporting`/templates | regra-nova | A contagem é derivada no template a partir do payload; nenhum cálculo novo no núcleo |

## Regras sob vigilância

- **W001** — o `SHA_DA_TELA` prende o HTML de `GET /` **sem resultados**; a frase da contagem
  vive sob `{% if dna_results %}` e não o altera. Verificado: os testes de ícone passam.
- **W002** — a frase da sugestão deve continuar dizendo que as gerações **não estão no GEDCOM**.
  Sem a ressalva, hipótese é lida como parentesco documentado.

## Fontes

- `_reversa_forward/033-contador-em-tres-faixas/requirements.md`
- `_reversa_forward/033-contador-em-tres-faixas/actions.md`
- `_reversa_forward/033-contador-em-tres-faixas/evidence/medicoes.md`
- `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`
