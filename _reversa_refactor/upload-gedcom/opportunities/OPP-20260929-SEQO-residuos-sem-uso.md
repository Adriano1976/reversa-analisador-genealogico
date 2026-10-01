---
schema_version: 1
id: OPP-20260929-SEQO
display_number: 9
context: upload-gedcom
verb: prune
title: STATIC_FOLDER, matplotlib e pyvis são resíduos sem uso
target:
  files: [analisador-genealogico/app.py, analisador-genealogico/requirements.txt]
  symbol: STATIC_FOLDER, matplotlib, pyvis
smell: recurso criado ou declarado sem nenhum consumidor, resíduo da remoção do pyvis
roi:
  confidence: green
  impact: superfície de instalação e efeito colateral em disco no start da aplicação
  cost: low
  est_return: menos dependência instalada e nenhuma pasta criada sem motivo
state: applied
traceability:
  soul: [.reversa/soul.md#decisões-fundadoras]
  specs: [_reversa_sdd/architecture.md#5-dívidas-técnicas-identificadas, _reversa_sdd/migration/topology_decision.md#168]
---

## Roteamento

- Destino: `/reversa-prune OPP-20260929-SEQO`
- Ordem de encadeamento: **4 de 4**.
- Aprovada pelo usuário em 2026-09-29 para roteamento, com execução parando no gate.
- Motivo da posição: independente das outras três, sem conflito de arquivo. Fica por último apenas
  porque o retorno é menor, não porque dependa de algo.

## Estado do gate

Especialista acionado em 2026-09-29 em `control_mode: gated`. Plano, prova de morte e confirmação
estão em `../transformations/OPP-20260929-SEQO-podar-residuos/`.

| Rede | Resultado |
|------|-----------|
| Suíte completa | 50 passed |
| Equivalência de rotas do app (`url_map`, `static_folder`, `static_url_path`, views) | idênticos |
| Prova de morte, 406 arquivos varridos no repositório | anexada |

**Esta transformação não empilha.** `app.py` e `requirements.txt` não são tocados pela AU76 nem pela
32Q7, então o patch se aplica ao estado atual do projeto, e não ao estado pós-AU76.

Achado da prova que vale registrar: `app = Flask(__name__)` usa o padrão do framework e portanto
**continua registrando a rota `/static/<path:filename>`** mesmo depois de remover `STATIC_FOLDER` e o
`makedirs`. A prova de equivalência confirma: as 2 rotas seguem idênticas. Remover a variável não
remove a rota, apenas deixa de criar a pasta vazia no start.

A aplicação está **bloqueada** por `.reversa/reversa-config.json` em `allowLegacyEdits: false`.

## Antes observado

1. `app.py:14` declara `STATIC_FOLDER = "static"` e `app.py:16` faz
   `os.makedirs(STATIC_FOLDER, exist_ok=True)` no import do módulo. **Nenhum** outro ponto do projeto
   lê ou escreve nessa variável. Era a pasta do artefato `static/graph_path_search.html`, gerado pelo
   pyvis, que não existe mais na árvore atual.

2. `requirements.txt` declara `matplotlib` (linha 4) e `pyvis` (linha 8). Busca por
   `import matplotlib`, `from matplotlib`, `import pyvis` e `from pyvis` em todo o `*.py` do projeto
   devolve **zero** ocorrências. As duas dependências são pesadas: `matplotlib` arrasta numpy e
   Pillow, `pyvis` arrasta jinja2 e ipython em alguns ambientes.

O contexto histórico está documentado: `_reversa_sdd/migration/topology_decision.md` registra que
`static/graph_path_search.html` (pyvis) e `templates/index.html` (Mermaid) eram duas tecnologias de
visualização coexistindo, e que a decisão foi colapsar em uma só. O código colapsou; as dependências e
a criação da pasta ficaram para trás.

## Transformação proposta

1. Remover `STATIC_FOLDER` e o `os.makedirs` correspondente de `app.py`.
2. Remover `matplotlib` e `pyvis` de `requirements.txt`.

## Rede de segurança exigida

`prune` exige `preservation.method: death-proof` com a prova anexada. A prova aqui é busca estática por
referência, já executada e registrada acima. Nenhum teste referencia qualquer dos três itens, então a
suíte permanece em 50.

A conferência que faltava foi feita e o resultado é favorável: a varredura de **todo** o repositório,
incluindo `_reversa_sdd/parity/` e os demais scripts de diagnóstico, encontra **zero** imports de
`matplotlib` ou `pyvis`. Nenhum consumidor vivo existe em nenhum lugar.

Também foi verificado que `import os` continua necessário em `app.py` depois da remoção, com 5 usos
de `os.path.join` e `os.path.exists` nas rotas. Nenhum import órfão é criado.

## Risco

Baixo. O risco real é de ambiente: remover dependência de `requirements.txt` não a desinstala de
ambientes já montados, e um script de diagnóstico pode passar a falhar em ambiente novo. Vale conferir
`_reversa_sdd/parity/` antes.

## Órfão suspeito registrado (não removido)

A varredura de morte trouxe um candidato a mais, que **não** entra nesta poda:

| Item | Classificação | Motivo |
|------|---------------|--------|
| `ensure_dirs` (`reconstructed/upload.py:24`) | **órfão suspeito**, `promoted_to: null` | Sem chamador de produção: o único uso é `tests/test_upload.py:129`. É API pública do módulo e aparece em `_reversa_sdd/reconstruction-report.md:22` como parte da Tarefa 02. Pode ser religada, então nunca é removida automaticamente |

Fica registrado aqui em vez de removido, conforme a regra do verbo: na dúvida, sinaliza.

## Observação de escopo

`requirements.txt` também não tem nenhuma versão fixada, o que `_reversa_sdd/architecture.md#5` já
registra como dívida de severidade alta. Fixar versões é `standardize` e mexe em risco de ambiente,
não em qualidade de código. Fica fora deste registro de propósito.

---
*Gerado pelo Reversa-Refactor em 2026-09-29.*
