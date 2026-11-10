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
- `W056-06`: `SHA_DA_TELA` de volta a `3487986a…`.

## Fontes

- `_reversa_forward/056-regioes-compartilhadas/requirements.md`
- `_reversa_forward/056-regioes-compartilhadas/evidence/SHA_DA_TELA.md`
- `_reversa_forward/056-regioes-compartilhadas/evidence/medicoes.md`
- `_reversa_sdd/addenda/055-grupos-de-triangulacao.md` (insumo substituído)
