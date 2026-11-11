# Adendo: regiões compartilhadas, sem o arquivo de triangulação

> Identificador: `056-regioes-compartilhadas`
> Data: `2026-11-09`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`,
> `_reversa_sdd/data-dictionary.md` e `_reversa_sdd/c4-components.md`)

## Vigência

Vigente desde 2026-11-09.

## Resumo da entrega

A 055 agrupava matches por cromossomo, mas exigia um **segundo arquivo** — o CSV de
triangulação do GEDmatch — porque só ele dizia quais matches compartilham faixa **entre si**. A
056 removeu esse insumo: a região passa a nascer do próprio **CSV de matches do Ancestor
Projects**, que já traz `Chromosome`, `Start`, `End` e `cM` por segmento. O bloco mudou de nome
para **"Regiões compartilhadas"** porque afirma menos: são matches que compartilham a mesma faixa
**com o kit do arquivo**, não necessariamente entre si.

O **piso de 10 cM virou filtro**. Medido no `DNA_Nordestino.csv`: sem piso, 158 regiões e **553
dos 606 kits**; com piso, **32 regiões e 108 kits**. Sem a confirmação entre os matches, o
segmento pequeno é a maior fonte de falso grupo.

O que continuou: agrupamento por cromossomo e interseção, alerta de **acúmulo**, os quatro
desfechos documentais (convergente, dividido, parcial, sem ancestral documentado), o bloco aberto
antes dos cartões e o CSV das regiões. O que saiu: o formulário, o campo opcional, a ação isolada,
o adaptador de pares e o teste de fechamento.

**21 testes novos.** Suíte: **2.035 passam / 9 pulados / 5 falham**, as cinco pré-existentes. O
`SHA_DA_TELA` voltou a `3487986a…` (51.218 bytes) — **idêntico ao valor anterior à 055**, o que
prova que a remoção não deixou resíduo.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3. Componentes e estrutura de pacotes | `componente-extinto` | Saem `parsers.triangulacao_gedmatch`, `core.triangulacao` e `core.triangulacao_no_cartao`; entram `core.regioes` e `core.regiao_no_cartao` |
| `_reversa_sdd/architecture.md` | §5. O Fluxo que Define o Sistema | `regra-alterada` | As regiões nascem dentro da análise de DNA, dos segmentos que a evidência já montou; não há mais passo com arquivo auxiliar |
| `_reversa_sdd/domain.md` | §1. Glossário de Domínio | `regra-alterada` | "Grupo de triangulação" dá lugar a **região compartilhada**: matches que compartilham faixa com o kit do arquivo, sem confirmação entre si |
| `_reversa_sdd/domain.md` | §3.2. Evidência genética | `regra-alterada` | O piso de 10 cM passa a ser **filtro do agrupamento**, além de regra de evidência por match; o cM continua nunca somado |
| `_reversa_sdd/data-dictionary.md` | §8. Payload do núcleo → tela | `delta-de-dados` | `ResultadoDeAnalise.grupos` dá lugar a `regioes`; o contexto da tela passa a `regioes` e `regioes_dados` |
| `_reversa_sdd/c4-components.md` | Componentes por unidade | `delta-de-contrato-externo` | A ação `triangulacao_analysis` **não existe mais**; a rota `POST /grupos.csv` vira `POST /regioes.csv` |

Nenhuma regra de matching, cM, travessia de grafo ou persistência mudou. O banco continua com as
6 tabelas: a região é leitura derivada e não é persistida.

## Regras sob vigilância

- `W056-01`: só segmento de 10 cM ou mais entra na região.
- `W056-02`: a faixa da região é a interseção, e está contida em cada segmento membro.
- `W056-03`: o desfecho vem dos cartões, sem segundo matching.
- `W056-04`: o bloco não afirma triângulo fechado.
- `W056-05`: nenhum cM é somado entre segmentos.
- `W056-06`: `SHA_DA_TELA` de volta a `0b926895…`.
- `W056-08`: o cartão do hover do ideograma não é recortado pelo raio do card.

## Atualização 2026-11-10 — mapa por cromossomo

O bloco ganhou um **ideograma**: uma linha por cromossomo, uma faixa por região
posicionada pela coordenada, cor por desfecho e um cartão de detalhe ao passar o mouse —
e também ao focar a faixa pelo teclado, para o dado não existir só no hover. O cartão
mostra a posição em pares de bases, o tamanho em Mb, o cM mínimo e máximo, o desfecho e
até cinco membros.

A régua é o **GRCh37**, declarado na legenda: o CSV de matches não traz build nem RSID,
e um número de escala sem procedência seria invenção. A faixa mínima de 0,6 % impede que
uma região de 1 Mb desapareça no trilho; posição além do comprimento é presa na borda.

O detalhe textual das regiões continua abaixo, agora recolhido por padrão, como o bloco
inteiro. Nenhum dado novo nasce do mapa: ele lê as mesmas regiões que a lista.

## Atualização 2026-11-10 — o cartão do hover não é mais cortado

O cartão do hover abria cortado nas duas primeiras linhas do mapa (cromossomos 1 e 2): via-se
"Tamanho:" e o resto, sem o título e sem a posição exata. Não era dado faltando — o elemento
estava lá —, era o `overflow:hidden` de `details.card` recortando no raio da borda tudo o que o
cartão desenhava **acima** da faixa, e o topo do cartão caía fora do card.

O conserto é de folha, no escopo deste bloco: `details.card.regioes-compartilhadas` passa a
`overflow:visible` e o raio migra para o cabeçalho, que é quem de fato precisa dele (fechado, o
cabeçalho é o cartão inteiro e leva o raio nos quatro cantos; aberto, só nos dois de cima).
Nenhuma classe, marcação, texto ou número mudou, e o `SHA_DA_TELA` continua `0b926895…`.

Medido no harness estático (Chrome headless, 1114 px): o cartão do hover tem 219 px de altura
com cinco membros e a linha 1 do mapa fica a 133 px do topo do card — faltavam 86 px, quatro
linhas. Inverter o cartão para baixo nas primeiras linhas exigiria inverter **quatro das nove**
linhas, e a conta muda com o zoom: por isso a correção foi liberar o recorte, e não mexer na
direção.

Na mesma passada, a dica ganhou o lado esquerdo: uma faixa colada no início do cromossomo abria
centrada e saía do trilho pela esquerda (`lado` = `direita`, `left:0`).

## Fontes

- `_reversa_forward/056-regioes-compartilhadas/requirements.md`
- `_reversa_forward/056-regioes-compartilhadas/evidence/SHA_DA_TELA.md`
- `_reversa_forward/056-regioes-compartilhadas/evidence/medicoes.md`
- `_reversa_sdd/addenda/055-grupos-de-triangulacao.md` (insumo substituído)
