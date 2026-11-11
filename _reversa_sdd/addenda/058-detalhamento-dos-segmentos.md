# Adendo 058 — Detalhamento dos segmentos compartilhados

> Identificador: `058-detalhamento-dos-segmentos`
> Data: `2026-11-11`
> Cenário: `legado` (extração em `_reversa_sdd/`, com `architecture.md` e `domain.md`)
> Feature: `_reversa_forward/058-detalhamento-dos-segmentos/`

## Vigência

Vigente desde 2026-11-11.

## Resumo da entrega

O bloco "Regiões compartilhadas" ganhou a **tabela de segmentos**: uma linha por par (região, kit),
com cromossomo, posição inicial e final, tamanho em Mb, cM, kit, nome do match e o desfecho
documental da região. A seção entra **depois da distribuição por cromossomo e antes da lista de
regiões**, e traz título com contador ("N de M"), busca por texto (kit, nome ou cromossomo), filtro
por cromossomo, paginação de **10/20/30** (20 como padrão) e, em cada linha, o botão de copiar.

O clique na linha destaca a **faixa correspondente no ideograma**: a faixa carrega `id="regiao-N"`
e o destaque é `:target` — sem JavaScript. Filtro, paginação e cópia são **camada de apresentação**:
o documento é servido inteiro e o script só marca `hidden`. Sem JavaScript, a tabela continua
inteira e legível e o link do emblema do cromossomo continua levando à faixa.

Foram executadas **18 de 18** ações (Preparação 3, Testes 4, Núcleo 3, Integração 5, Polimento 3),
sem falha. `SHA_DA_TELA` continua `0b926895…` (52.497 bytes).

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3. Componentes e estrutura de pacotes | `componente-novo` | Dois módulos novos: `src/core/segmentos.py` (achata as regiões em linhas, com ordem fixa e o índice da região) e `src/application/segmentos.py` (projeta a linha e lista os cromossomos do filtro). `src/app.py` projeta uma vez e passa `segmentos` ao template |
| `_reversa_sdd/c4-components.md` | Fichas de componente (nível 3) | `componente-novo` | Fichas dos dois módulos, com o detalhe de que a tabela é leitura derivada e que o `regiao_indice` é o vínculo com a faixa do ideograma (`id="regiao-N"`) |
| `_reversa_sdd/inventory.md` | Superfície do código | `componente-novo` | Dois arquivos de `src/` e dois de `tests/`; a projeção de regiões ganhou a chave `indice`, e `core/distribuicao.ordem_do_cromossomo` passou a ser pública |
| `_reversa_sdd/domain.md` | §1. Glossário de Domínio | `regra-nova` | "Detalhamento dos segmentos": uma linha por **par (região, kit)** — o segmento que aquele match contribuiu para a região —, ordenada por cromossomo natural, posição inicial e kit |

Nenhuma regra 🟢 de `domain.md` foi alterada ou removida: a regra central (`#2`), a evidência
genética (`#3.2`) e a ordem de apresentação (`#3.9`) continuam valendo sem emenda. O cM da linha é o
do segmento; nada é somado, e o `/regioes.csv` continua com uma linha por região.

## Regras sob vigilância

`W058-01` a `W058-09` — ver `_reversa_forward/058-detalhamento-dos-segmentos/regression-watch.md`.

## Fontes

- `_reversa_forward/058-detalhamento-dos-segmentos/requirements.md`
- `_reversa_forward/058-detalhamento-dos-segmentos/roadmap.md`
- `_reversa_forward/058-detalhamento-dos-segmentos/legacy-impact.md`
- `_reversa_forward/058-detalhamento-dos-segmentos/regression-watch.md`
- `_reversa_forward/058-detalhamento-dos-segmentos/progress.jsonl`
- `_reversa_forward/058-detalhamento-dos-segmentos/evidence/` (SHA da tela, medições, captura da tabela)
