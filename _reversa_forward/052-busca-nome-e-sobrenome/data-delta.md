# Data Delta: busca por nome e sobrenome

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> Modelo extraído: `_reversa_sdd/erd-complete.md` · `_reversa_sdd/data-dictionary.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo

**Nenhuma mudança persistente.** Não há campo, tabela, coluna, índice, constraint, migração ou
backfill. O Diagrama E do `erd-complete.md` — o esquema físico PostgreSQL de 6 tabelas — fica
byte a byte igual, e o `init.sql` não é tocado.

O que esta feature acrescenta são **estruturas em memória**: duas visões de índice presas ao grafo da
árvore e quatro payloads congelados que atravessam uma requisição. Nada sobrevive ao processo, com uma
exceção já conhecida: quando o cache de árvore da feature 047 está ligado, o índice novo vive enquanto
a árvore viver — que é o comportamento pretendido, não um efeito colateral.

## 2. Estruturas novas

| Estrutura | Onde vive | Persiste? | Tipo de mudança | Observação |
|-----------|-----------|-----------|-----------------|------------|
| **Visão por nome** (`nome normalizado → [xref]`) | Atributo `_analisador_indice_de_nomes` no `networkx.Graph` da árvore | Não — vida da árvore | **presença** (já existia) | Criada pela 048; a busca apenas a consome |
| **Visão por token** (`token → [xref]`) | Atributo `_analisador_indice_de_tokens` no mesmo grafo | Não — vida da árvore | **nova** | Nasce na **mesma varredura** que constrói a visão por nome |
| `TermoDeBusca` | Payload da requisição | Não | nova | Congelado: texto cru, forma normalizada, tokens e o escopo derivado |
| `NomeDaFonte` | Payload da porta `FonteDeNomes` | Não | nova | O que uma fonte entrega: origem, identificador, nome e os dados de exibição |
| `AcertoDeBusca` | Payload do caso de uso | Não | nova | Identificador, nome, pontuação, origem e a ficha quando existe |
| `ResultadoDaBusca` | Payload do caso de uso | Não | nova | Termo, acertos ordenados, total por seção e o sinal de truncamento |

## 3. O índice, em detalhe

- **Nome do atributo:** prefixo `_` para não colidir com atributo de `networkx`, e sufixo que diz o que
  ele é (mesma convenção de `_analisador_indice_de_nomes`, da 048).
- **Chave:** não existe. A vida do mapa é a vida do grafo, e é exatamente o que a 048 fixou ao enterrar
  a chave `(len, primeiro xref, último xref)` que colidia (`L-24`).
- **Construção:** uma varredura de `arvore[0]` que, para cada pessoa, normaliza o nome, registra a
  visão por nome e decompõe o nome em tokens para a visão por token. O custo medido da varredura de
  35 mil pessoas é ~0,9 s (uma vez por árvore); o acréscimo da segunda visão é medido na execução.
- **Idempotência:** a gravação é `setattr` do mesmo objeto; concorrente ou repetida, o valor é o mesmo.
  É a propriedade que a `architecture.md#2` declara como segura entre as 4 threads.
- **Árvore sem grafo** (sonda, teste unitário): o mapa é construído e devolvido **sem** ser pendurado —
  não há onde prender. Comportamento igual ao da 048.

## 4. O que **não** muda

| Artefato | Situação |
|----------|----------|
| `_reversa_sdd/erd-complete.md` (Diagrama E) | Intocado — 6 tabelas, nenhuma coluna nova |
| `_reversa_sdd/data-dictionary.md` | Intocado — nenhum campo, padrão ou sentinela novo |
| `init.sql` | Intocado — a feature não lê nem escreve o banco |
| Layout de `src/uploads/` | Intocado — a busca não move arquivo |
| `analysis_person`, `match_*` | Intocados — nenhum retrato novo é gravado (`RN-01`) |
| `owner_id` | Intocado — a busca **filtra** pelo dono da sessão, sem gravar nada |

## 5. Migração

n/a. Não há dado a converter: o índice é derivado e efêmero, e nenhuma estrutura persistida muda de
forma. Uma instalação existente ganha a busca sem passo de atualização.

## 6. Retenção e privacidade

- **Nada novo é persistido.** Nenhum acerto, termo ou contagem é gravado — e a busca não entra na
  trilha de auditoria (§9 do `requirements.md`).
- **O índice não aumenta a retenção.** Ele é derivado da árvore que já estava em memória e morre com
  ela; desligado o cache da 047, morre no fim da requisição. É a mesma direção da nota de retenção do
  `addenda/048`.
- **O termo não entra em URL.** A rota é `POST`, o que mantém o texto digitado fora do log de acesso e
  do histórico do navegador — e é o que permite, no futuro, logar a busca sem o termo.

## 7. Impacto em fixtures e testes

- Nenhuma fixture nova de dado real: as árvores e relatórios de teste são sintéticos
  (`tests/fixtures/sample_gedcom.py`, `sample_dna.py`), conforme o princípio I.
- A fixture precisa de **duas árvores do mesmo tamanho, com os mesmos xrefs extremos**, para o teste
  que prova a ausência da colisão da `L-24`.
- A fixture precisa de um relatório sintético com nome que **existe** e nome que **não existe** na
  árvore, para o teste de referência cruzada (`RF-07`).
