# Adendo: revisão dos descartes

> Identificador: `034-revisao-dos-descartes`
> Data: `2026-10-19`
> Cenário: **legado** (âncora em `_reversa_sdd/`, adendos `016`, `024` e `033`)

## Vigência

Vigente desde 2026-10-19.

## Resumo da entrega

O bloco "Matches descartados" era uma lista de motivos técnicos: o operador via
`score insuficiente ou conflito de sobrenome (given=46, final=81.5, …)` e não tinha como
saber se o descarte foi acerto ou perda. Esta feature mostra **a quem a árvore oferecia** —
até três candidatos, com ano de nascimento, semelhança de prenome e nota — e permite
**promover** um deles a cartão.

Medido no GEDCOM real (`..._V1_2_Tratado.ged` + `Famílias_Sergipanas.csv`, raiz `adriano`):
**366** descartes, **281** com algum candidato avaliado, **76** com candidato compatível
(prenome parecido **e** sobrenome em comum) e **7** em que o candidato tem caminho documental
que sobrevive à janela de vida.

**Três decisões, todas nascidas de medição:**

- **Compatível não é "melhor avaliado".** Mostrar candidato nas 281 linhas era ruído com cara
  de resposta (`"Clezia Santos"` → *"Luzia Martins dos Santos"*, prenome 73). Só o compatível
  entra como lista; o resto aparece como "melhor avaliado", em texto fraco.
- **A ordem é a do operador, não a da decisão.** A decisão desempata por interseção de
  sobrenomes primeiro; para a tela isso enterrava o parente certo atrás de homônimos de
  sobrenome. Pela ordem da decisão, **50** descartes mostravam um compatível; pela ordem do
  operador, **76**. A aceitação não mudou uma vírgula.
- **A promoção é do operador, nunca automática.** Caso real que a proíbe: `*Maria de Fátima
  Oliveira de Jesus` teve como melhor colocado *Angelica Maria De Jesus De Oliveira*
  (`given` 55) — pessoa errada.

## O que a promoção faz

O nó escolhido **substitui** a decisão do casamento para aquele nome e o cartão passa por todo
o fluxo normal (parentesco, veredito, janela de vida, árvore sugerida). O cartão registra a
promoção e o motivo original como observação. As promoções viajam no próprio formulário: a
aplicação não tem sessão, então a tela reenvia as anteriores para que promover a segunda não
apague a primeira.

Validado de ponta a ponta:

| Promoção | Cartões | Descartados | Com caminho |
|---|---:|---:|---:|
| `Maria José de Souza Santos` → *Mariza Souza Santos* | 90 → 91 | 366 → 365 | 6 → 6 |
| `Sheila Costa Bonates` → *Sheila Moreira Costa* (caminho de 10 pessoas) | 90 → 91 | 366 → 365 | 6 → **7** |

A promoção **não garante** caminho — o primeiro caso não tem, o segundo tem.

## Achado de ambiente (corrigido na mesma entrega)

A suíte inteira não rodava neste ambiente: `tests/conftest.py` criava o diretório temporário
sob `tests/.tmp/`, e o sandbox de escrita do harness recusa **criar subdiretório** dentro do
workspace — 408 testes morriam no preparo. A raiz passou para
`%TEMP%/reversa-analisador-testes`, e os testes de política do ambiente foram atualizados.

**Regressão pré-existente encontrada ao rodar a suíte pela primeira vez:** o bloco
`observacoes-do-arquivo` estava sem o atributo `open`, contrariando o adendo `017` e o próprio
comentário do template. Corrigido. Sem o conserto do ambiente, esse defeito continuaria
invisível.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `core.matching.avaliar_candidatos` devolve `(pids, motivo, proximos)`; `match_candidates` mantém o contrato de dois valores |
| `_reversa_sdd/architecture.md` | §3 Componentes e estrutura de pacotes | contrato-novo | `core.dna_analysis.dna_analysis` aceita `candidatos_fixos` (nome do CSV → pid e motivo) |
| `_reversa_sdd/data-dictionary.md` | §8 Payload do núcleo → tela | delta-de-dados | Cada descarte ganha `candidatos` (até três: nome, prenome, nota, interseção, nascimento, `compativel`); cada cartão ganha `promovido` |
| `_reversa_sdd/domain.md` | §5 Contrato de Mensagens ao Usuário | regra-nova | Entram "Candidatos na árvore", "sem candidato compatível — melhor avaliado" e a ação "usar este candidato" |
| `_reversa_sdd/domain.md` | §Regras de apresentação do parentesco | regra-nova | Promover não é parentesco inferido: é decisão do operador, registrada no cartão com o motivo original |
| `_reversa_sdd/code-analysis.md` | §Ambiente de testes | regra-alterada | A raiz temporária da suíte passa para `%TEMP%/reversa-analisador-testes` |

## Regras sob vigilância

- **W001** — o casamento **não** pode voltar a aceitar por nota: a promoção é ato do operador.
  O caso `Adelina da Silva Vieira` (sobrenome idêntico, pessoa errada) é a prova.
- **W002** — `match_candidates` deve continuar devolvendo dois valores: três consumidores
  dependem disso, e o contrato está preso em `tests/test_characterization_matching.py`.
- **W003** — o formulário de promoção deve reenviar as promoções anteriores
  (`tests/test_promocao_de_descarte.py::test_o_formulario_carrega_as_promocoes_anteriores`).
- **W004** — o bloco `observacoes-do-arquivo` nasce **aberto** (adendo `017`).

## Fontes

- `_reversa_forward/034-revisao-dos-descartes/requirements.md`
- `_reversa_forward/034-revisao-dos-descartes/roadmap.md`
- `_reversa_forward/034-revisao-dos-descartes/actions.md`
- `_reversa_forward/034-revisao-dos-descartes/evidence/medicoes.md`
- `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md`
- `_reversa_sdd/addenda/024-motivo-de-recusa-por-sobrenome.md`
