# Regression Watch: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Fonte dos itens: seção "Modificadas" de `legacy-impact.md`

## Itens de vigilância

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-------------------------------|---------------------|-------------------|
| W001 | `tests/test_icone_de_atalho.py` (214, 307); `_reversa_forward/031-veredito-no-cartao/legacy-impact.md#4-modificadas` | `SHA_DA_TELA` prende o HTML de `GET /` **sem resultados**; o bloco do cartão não é renderizado nesse caminho, então o hash não muda quando só o cartão muda | `presença` | O hash passar a falhar por causa de mudança no cartão (alguém tornou o bloco incondicional), ou alguém "consertar" a diferença atualizando o hash sem mudar a tela |

## Observações (sem peso de regressão)

- **O-01 — o cartão é protegido por teste de tela, não por hash.** Nove testes renderizam o
  template real e olham o bloco do cartão. Se alguém mover o selo de lugar ou trocar a classe,
  eles falham; o hash não veria nada.
- **O-02 — o literal de máquina vive no `title`.** O texto visível é `Validado` /
  `Linha em conflito`; `ERRO CRONICO / QUEBRA DE LINHA` continua existindo no `title`, junto do
  motivo e do código. Quem procurar o literal no corpo da página não vai achar.
- **O-03 — `INCONCLUSIVO` não tem selo.** A ausência é a mensagem, e a linha da lista declara
  isso. Se uma extração futura encontrar um selo de inconclusivo, é regressão de decisão.
- **O-04 — as cores do selo são variáveis próprias.** `--validacao-*` existe nos dois temas
  porque `--st-*` não são redefinidas no escuro. Se alguém "simplificar" para `--st-*`, o
  contorno cai para ~2,3:1 no tema noturno — e o teste de contraste acusa.
- **O-05 — o `G` tem uma implementação só.** `application.validacao` delega para
  `core.documentary_relationship`. Duas implementações dariam dois vereditos para o mesmo kit.

## Histórico de re-extrações

> Preenchido pelo agente reverso quando `/reversa` rodar novamente.

| Data | Item | Resultado | Observação |
|------|------|-----------|------------|
| — | — | — | Nenhuma re-extração executada desde a criação deste arquivo |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | Nenhum item arquivado | — |
