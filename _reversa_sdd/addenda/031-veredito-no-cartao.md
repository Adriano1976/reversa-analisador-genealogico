# Adendo: veredito de validação no cartão de DNA

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md` e
> `_reversa_sdd/data-dictionary.md`)

## Vigência

Vigente desde 2026-10-18.

## Resumo da entrega

O veredito de viabilidade temporal da `028` — `VALIDADO`, `INCONCLUSIVO` ou `ERRO CRONICO /
QUEBRA DE LINHA` — existe desde então e **nunca chegou à tela**. Esta feature o leva ao cartão de
cada match, como um selo de contorno: `Validado` (verde) e `Linha em conflito` (vermelho), com o
literal de máquina, o motivo e o código da anomalia no `title`. `INCONCLUSIVO` **não** ganha selo —
numa análise de 142 cartões ele é o caso mais comum, e marcar quase todos não marcaria nenhum; a
lista declara que a ausência significa "não concluído".

A entrega foi concluída em **15 de 15 ações**, com 18 testes novos (suíte em 1172 passam, 11
pulados, 0 falham). O veredito é calculado **uma vez** por resultado, dentro do laço que já tinha
`documentary` e `comparison`, e o `G` (intervalo de geração) passou a ter **fonte única** no
núcleo — antes ele só existia na fachada da `028`, e o cartão e a fachada poderiam dar vereditos
diferentes para o mesmo kit.

**Achado registrado:** o `SHA_DA_TELA` **não** cobre o cartão. O invariante prende o HTML de
`GET /` sem resultados, e o bloco do cartão só é renderizado quando há análise. A verificação de
2026-10-18 mostrou que o hash não muda e que a proteção do cartão fica com os testes de tela
novos. Os documentos da feature foram corrigidos antes de a afirmação errada virar registro.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | regra-nova | `core.dna_analysis` passa a chamar `validar_comparacao` por resultado e grava quatro chaves de veredito no dicionário que a tela consome |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `core.documentary_relationship` ganha `intervalo_de_geracao_mediano(arvore)` — o `G` deixa de morar só na fachada |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | regra-alterada | `application.validacao.intervalo_de_geracao_mediano` delega ao núcleo; nome, assinatura e comportamento públicos idênticos |
| `_reversa_sdd/data-dictionary.md` | §8 Payload do núcleo → tela | delta-de-dados | Cada item de `resultados` ganha `validacao_status`, `validacao_rotulo`, `validacao_classe` e `validacao_aviso`; nenhuma coluna, nenhuma migração |
| `_reversa_sdd/domain.md` | §5 Contrato de Mensagens ao Usuário | regra-nova | Entram os rótulos `Validado` e `Linha em conflito`; o literal `ERRO CRONICO / QUEBRA DE LINHA` fica no `title`; ausência de selo significa "não concluído" |
| `_reversa_sdd/domain.md` | §21 Os quatro estados do confronto | regra-nova | O veredito temporal é um **campo novo**, não um quinto estado: `COMPATIVEL`, `POSSIVEL`, `CONFLITANTE` e `INCONCLUSIVO` continuam com texto, classe e cor |
| `_reversa_sdd/code-analysis.md` | §4 Unidade `analise-dna` | regra-nova | A unidade passa a compor o validador da `028`, como já compunha confronto, janela de vida e profundidade |

## Regras sob vigilância

- **W001** — o `SHA_DA_TELA` prende o HTML de `GET /` **sem resultados**; mudança só no cartão não
  deve mexer nele. Ver
  `_reversa_forward/031-veredito-no-cartao/regression-watch.md#itens-de-vigilância`.
- As observações **O-01 a O-05** do mesmo arquivo registram a proteção por teste de tela, o
  literal no `title`, a ausência de selo em `INCONCLUSIVO`, as variáveis de cor próprias e a fonte
  única do `G`, sem peso de regressão.

## Fontes

- `_reversa_forward/031-veredito-no-cartao/requirements.md`
- `_reversa_forward/031-veredito-no-cartao/roadmap.md`
- `_reversa_forward/031-veredito-no-cartao/investigation.md`
- `_reversa_forward/031-veredito-no-cartao/data-delta.md`
- `_reversa_forward/031-veredito-no-cartao/actions.md`
- `_reversa_forward/031-veredito-no-cartao/legacy-impact.md`
- `_reversa_forward/031-veredito-no-cartao/regression-watch.md`
