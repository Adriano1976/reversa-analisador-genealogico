# Regression Watch: polimento visual da tela de entrada

> Identificador: `026-polimento-visual-da-tela`
> Data: `2026-10-17`

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após a mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-------------------------------|---------------------|-------------------|
| W001 | `src/assets/app.css`, `:root`; `requirements.md` `RF-11` | Os quatro tokens `--ok`, `--poss`, `--conf` e `--inc` **não existem**; a família `--st-*` é a única declaração das cores de estado | `ausência` | Qualquer um dos quatro nomes reaparece na folha, no template ou numa regra |
| W002 | `src/assets/app.css`, token `--st-inconclusivo`; `requirements.md` `RF-04` | O token vale `#6A6150` e **nunca** é `var(--muted)`; o comentário ao lado registra 6,11:1 e 2,62:1 | `presença` | O valor vira alias de `--muted`, clareia ou o comentário some |
| W003 | `src/assets/app.css`, comentário dos estados; `requirements.md` `RF-05` | O comentário traz os quatro contrastes medidos (6,39 / 7,13 / 6,69 / 6,11:1) e preserva o caso do laranja (2,57:1) | `redação` | Os números somem, mudam ou o caso do laranja é apagado |
| W004 | `src/assets/app.css`, bloco do banner; `requirements.md` `RF-06` | Os dois comentários descrevem a arte atual: sem título, com a placa clara justificada pelo fundo claro da ilustração | `redação` | O comentário volta a dizer que o banner mostra o nome ou que o texto da arte é marrom |
| W005 | `tests/test_icone_de_atalho.py`, `SHA_DA_TELA`; `requirements.md` `RF-10` | `GET /` continua com `sha256` `c4a34f7b…` e 30.781 bytes; o template não declara `apple-touch-icon` | `presença` | O hash muda sem uma mudança de tela declarada, ou o `<link>` do ícone de atalho aparece |
| W006 | `tests/test_banner_do_topo.py`; `requirements.md` `RF-07` | O `<h1>` continua com o texto do produto e **sem** `visually-hidden` | `ausência` | A classe do `h1` ganha `visually-hidden` |
| W007 | `tests/test_estilo_da_tela.py`, `TestOContrasteDosSelos`; `requirements.md` `RF-05` | Os quatro selos mantêm ≥ 4,5:1 nos temas claro e escuro, resolvidos pela cascata | `presença` | O teste de contraste falha em qualquer estado ou tema |

## Observações

Itens sem peso de regressão (não são 🟢 de código):

- **OBS-01** 🟡 A conferência visual humana não foi executada nesta rodada (sem navegador). A
  verificação foi por medição dos valores efetivos (`evidence/depois/tela.md`); o roteiro humano está
  no `onboarding.md` passos 2 a 5 e continua recomendado.
- **OBS-02** 🟡 `_reversa_sdd/design-system/tokens-derived.md` é de 2026-09-28, anterior à folha
  servida por rota, e não descreve os tokens atuais. Não foi regenerado por esta feature; é dívida
  documental da extração, não regressão desta entrega.
- **OBS-03** 🟡 Existe uma modificação em `.gitignore` anterior à linha de base (HEAD `f49bc47`),
  alheia a esta feature e não revertida. Registrada em `evidence/RELATORIO.md` §4.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|------|-------------|-----------|
| — | — | Aguardando a próxima execução de `/reversa` |

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
| — | — | — |
