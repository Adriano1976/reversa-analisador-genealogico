# ADR-33 — O desfecho em três valores, e a projeção pura

- **Status:** Aceito e **vigente** — duas decisões que resolvem o mesmo problema por ângulos diferentes
- **Data da decisão:** 2026-10-07
- **Commit(s):** `f775045` ("escreve os casos de uso da fronteira com resultado tipado"), `6ad74a3` ("encaminha as tres rotas pelos casos de uso com traducao de erros"), dentro do ciclo `006-fronteira-aplicacao-ports`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A fronteira do `ADR-25` tirou o texto de tela da rota, mas deixou dois problemas concretos que o `RF-20` nomeia e que a decisão anterior não resolvia sozinha:

**Problema 1 — o `success` era ambíguo na busca.** `core.path_search.path_search` devolve uma tupla de **três** elementos `(path_result, msg, success)`, e os três estados que ela sinaliza têm **modos de apresentação diferentes**:

| O que o núcleo devolve | O que a tela mostra |
| --- | --- |
| payload, `success=True` | cartão de resultado |
| `None`, `success=True` | "nenhuma conexão encontrada" — **com sucesso** |
| `None`, `success=False` | alerta de erro |

Os dois últimos se distinguem apenas pelo **texto** da mensagem. Sem um campo que carregue o **fato**, o adaptador teria de inferir o modo de renderização do literal — dando ao texto de tela **autoridade semântica**, que é exatamente o que a `RF-20` existe para impedir.

**Problema 2 — o resultado do núcleo chegava inteiro ao adaptador.** A análise de DNA devolve dicionários aninhados com **nomes de campo de template** (`dna_results`, `skipped_matches`, `documentary`, `per_kit`). Enquanto isso atravessasse a fronteira, a camada de aplicação não teria contrato: qualquer mudança no formato do núcleo vazaria para o adaptador e para o banco.

## Decisão

**Um enum de desfecho para o fato, e uma projeção pura para o dado.**

1. **`Desfecho` com três valores** — `RESULTADO`, `SEM_RESULTADO`, `ERRO_DE_ENTRADA` —, derivado dos **dois insumos que o núcleo já sinaliza** (presença de payload e indicador de sucesso), e **nunca do texto**.
2. **A precedência é do payload:** payload presente é `RESULTADO` mesmo que o indicador viesse falso — e ele não vem, nos três estados que o núcleo produz hoje.
3. **A rota escolhe o modo de renderização pelo desfecho**, e não pelo texto da mensagem.
4. **A tupla de três elementos do núcleo NÃO foi alterada.** Ela é contrato de paridade: o harness compara o indicador de sucesso contra o oráculo, e nove asserções de teste a desempacotam.
5. **A projeção é pura e mora no caso de uso** (`projetar_analise`, em `application/dna_analysis.py`): ela lê o que o núcleo devolveu e **nada mais** — não chama função do núcleo, não recalcula cM, não reordena e não formata.
6. **O payload da porta é dado PLANO**, em tipos próprios, sem dicionário aninhado e sem nome de campo de template.
7. **A projeção é pública para poder ser exercitada sem banco** — ela é pura, e o teste dela não precisa de `DATABASE_URL`.

## Evidência

- `src/application/__init__.py` declara `Desfecho`; `src/application/path_search.py` traz o `_desfecho` e o comentário que declara a ordem dos testes como precedência.
- A tupla do núcleo é confrontada pelo harness: `_reversa_sdd/parity/harness.py` compara o indicador de sucesso contra o oráculo.
- `src/ports/__init__.py` declara os cinco tipos de payload (`AnaliseParaRegistrar`, `PessoaDaAnalise`, `KitDaAnalise`, `ConexaoDaAnalise`, `DescartadoDaAnalise`).
- `tests/test_projecao_da_analise.py` (254 linhas úteis) exercita a projeção **sem banco** — o achado `B003` da auditoria de 2026-10-08.
- **O pareamento entre metadados de kit e veredito é POR ÍNDICE**, e não por rótulo: `hypotheses_for_evidence` percorre `evidence["kits"]` na ordem, e `compare` monta `per_kit` com `zip(hypotheses, avaliacoes)`. Como as duas listas seguem a mesma ordem, **dois kits com o mesmo nome — ou ambos sem kit — não se confundem.**
- `DescartadoDaAnalise.reason` carrega o motivo em **texto**, e não um código: o alvo tem `reason_code` como enum fechado, e fechá-lo aqui exigiria mapear texto em código — a inferência a partir de mensagem de contrato que o projeto recusa desde a feature 006.

## Justificativa

**Um campo que carrega o fato é mais barato que um texto que o insinua.** O enum custa três linhas e elimina uma classe inteira de acoplamento: enquanto o modo de renderização depender do literal, qualquer ajuste de redação muda comportamento. E o `_desfecho` **não** inventa informação — ele deriva de dois insumos que **já existiam** na tupla, e é por isso que ele não alterou o núcleo.

**A projeção pura é o que permite a persistência ser opcional.** Um adaptador que recebe dicionário aninhado do núcleo teria de conhecê-lo; um que recebe dado plano só **escreve**. É isso que faz o `ADR-27` caber sem que o adaptador entenda de cM, de faixa publicada ou de estado de confronto.

## Consequências

- 🟢 **O literal de tela deixou de ter autoridade semântica** nos três fluxos. O `ADR-25` criou o mecanismo; esta decisão o aplica onde ele era indispensável.
- 🟢 **A projeção é testável sem infraestrutura**, e é por isso que os testes de persistência podem existir num ambiente **sem driver instalado** (`L-26`).
- 🟡 **"gravado" e "inativo" são indistinguíveis na tela** (`M-06`): os dois produzem `aviso_de_persistencia = None`. A distinção existe no código e **não** é observável pelo operador.
- 🟢 **`dono` está na assinatura dos dois casos de uso e não participa de decisão nenhuma**, pelo `ADR-26`.
- 🟡 **A projeção deriva o papel de cada nó do caminho** com corte no ancestral comum, recuando para o **penúltimo** nó quando o MRCA não está no caminho. É um recuo **declarado** no código, mas pode marcar como ascendente um nó que é descendente em um caminho indireto.
- 🟢 **`afinidade` nunca é atribuída pela projeção da análise de DNA** — quem atribui esse estado é `path_search.py`, e o domínio de `match_path_node.role` é fechado.
