# Regression watch: explicar a fonte não declarada

> Identificador: `042-explicar-fonte-nao-declarada`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/core/genetic_evidence.py` (`evidence_for`) | Todo cartão com fonte não declarada expõe `source_motivo` **e** `source_explicacao`, e a linha `Fonte:` exibe a explicação | presença | a etiqueta volta a aparecer sozinha, sem dizer o que é |
| W002 | `src/core/fontes_de_laboratorio.py` (`explicacao`) | Célula vazia ou `-` devolve `SEM_VALOR_UTIL` e o cartão **não** renderiza a etiqueta | presença | a etiqueta `-` volta ao cartão, ou a frase passa a dizer "texto de formulário" para célula vazia |
| W003 | `src/core/fontes_de_laboratorio.py` | `EXPLICACOES` (frase do cartão) e `MOTIVOS_TEXTO` (contagem do painel) continuam separados | redação | os dois viram um dicionário só, e o painel passa a exibir frase longa ao lado do número |

## Observações (sem peso de regressão)

- 🟢 **Laboratório reconhecido não ganha texto extra:** `Fonte: Genera` continua sem explicação; a etiqueta
  só aparece quando a grafia difere (`GENERA`). Preso por `test_laboratorio_reconhecido_nao_ganha_etiqueta_redundante`.
- 🟢 **O texto original nunca é escondido:** a etiqueta continua no cartão para todo valor não-laboratório
  com conteúdo; a supressão vale só para `-` e vazio, que não têm o que mostrar.
- 🟡 **A frase é do projeto, não de fonte externa:** "nome de projeto de pesquisa", "empresa não confirmada
  pelo projeto" — nenhuma delas é terminologia publicada, e a redação pode mudar sem alterar regra.

## Histórico de re-extrações

*(vazio — preenchido pelo agente reverso quando `/reversa` rodar de novo)*

## Arquivadas

*(vazio)*
