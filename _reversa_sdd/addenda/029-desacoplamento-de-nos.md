# Adendo: desacoplamento de nós e gerações virtuais no grafo

> Identificador: `029-desacoplamento-de-nos`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/data-dictionary.md`)

## Vigência

Vigente desde 2026-10-18.

## Resumo da entrega

A feature transforma o veredito de quebra de linha da `028` em uma **árvore sugerida**: quando
`core.validator` devolve `ERRO CRONICO / QUEBRA DE LINHA`, uma cópia do grafo pessoa↔família é
desacoplada na junção provada errada e as gerações que faltam aparecem como nós virtuais numerados.
É a primeira vez que o sistema **produz uma variante da árvore** — até aqui tudo só lia o grafo.
Nada é gravado: nem `.ged`, nem banco, nem tela.

A entrega foi concluída em **22 de 22 ações**, com 39 testes novos (suíte em 1122 passam, 9 pulados,
0 falham). Ela é composta por:

- `core.cirurgia_do_grafo` — as seis funções puras da cirurgia: ramo base, junção, desacoplamento,
  injeção, verificação do ramo e orquestração;
- `application.correcao` — fachada que lê GEDCOM + CSV uma vez e monta uma sugestão por comparação;
- `application.validacao` — emenda **aditiva**: `incluir_documental`, desligado por padrão.

**Desvios declarados** (ver `_reversa_forward/029-desacoplamento-de-nos/actions.md#notas-de-execução`):
o contrato ganhou `juncoes` (plural) para os dois lados acusados; duas junções podem compartilhar a
mesma aresta e são deduplicadas; `incluir_documental` também devolve a árvore parseada; e a afinidade
não pode ser produzida por `documentary_relationship`, então é exercitada com um `documental` montado
à mão.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | componente-novo | `core.cirurgia_do_grafo` concentra a decisão estrutural sobre o grafo (quais nós são protegidos, onde cortar, quantas gerações injetar); é puro e recebe a árvore por parâmetro |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | componente-novo | `application.correcao` é a fachada que lê os dois arquivos e delega validação e cirurgia; reutiliza `validar_arquivos`, sem parser nem matching próprios |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | regra-nova | `application.validacao.validar_arquivos` ganha `incluir_documental: bool = False`; com `True`, cada comparação traz `documental` e o retorno traz `arvore`. Sem o parâmetro, o retorno é idêntico ao anterior |
| `_reversa_sdd/architecture.md` | §4 Modelo de dados | delta-de-dados | Nenhuma estrutura persistente nova. Entra uma **cópia do grafo em memória** (`grafo.copy()`) com dois tipos de nó sintético; o banco segue com as 6 tabelas e não recebe linha alguma |
| `_reversa_sdd/domain.md` | §3.1 Parentesco documental | regra-nova | A cirurgia só corta aresta de **filiação** (`CHIL`/`FAMC` + `HUSB`/`WIFE`), só na cópia, e só a aresta da junção: casamento nunca é cortado nem usado como linhagem, e o vínculo declarado pelo GEDCOM não é reescrito |
| `_reversa_sdd/data-dictionary.md` | §2 A árvore do GEDCOM em memória | delta-de-dados | Entram os tipos de nó `virtual` e `virtual-family`, com `label`, `origem="estimado"`, `justificativa` e `nascimento_estimado` como faixa. Nó virtual **não** tem `name`, `sex` nem data exata: é posição, não pessoa |
| `_reversa_sdd/code-analysis.md` | §5 Unidade `busca-caminho` | componente-novo | A unidade que navega o grafo ganha o vizinho que o transforma: a primeira função do projeto que devolve uma variante da árvore, com verificação de que o ramo do doador não mudou |

## Regras sob vigilância

- **W001** — `validar_arquivos` sem `incluir_documental` mantém exatamente as mesmas chaves; ver
  `_reversa_forward/029-desacoplamento-de-nos/regression-watch.md#itens-de-vigilância`.
- As observações **O-01 a O-05** do mesmo arquivo registram o campo `juncoes`, a deduplicação da
  junção compartilhada, a heurística de `SUGESTAO_INSUFICIENTE`, a limitação de o grafo sugerido não
  servir aos leitores existentes e a chave `arvore`, sem peso de regressão.

## Fontes

- `_reversa_forward/029-desacoplamento-de-nos/requirements.md`
- `_reversa_forward/029-desacoplamento-de-nos/roadmap.md`
- `_reversa_forward/029-desacoplamento-de-nos/data-delta.md`
- `_reversa_forward/029-desacoplamento-de-nos/actions.md`
- `_reversa_forward/029-desacoplamento-de-nos/legacy-impact.md`
- `_reversa_forward/029-desacoplamento-de-nos/regression-watch.md`
- `_reversa_forward/029-desacoplamento-de-nos/progress.jsonl`
