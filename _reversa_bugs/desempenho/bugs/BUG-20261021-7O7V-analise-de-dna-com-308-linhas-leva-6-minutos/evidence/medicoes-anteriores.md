# Medições anteriores que tocam este defeito

Nenhuma medição nova foi feita pelo registrador. Esta página reúne o que o projeto já mediu,
com a fonte, para a triagem não recomeçar do zero.

| Medição | Valor | Fonte | O que ela diz |
|---|---|---|---|
| Carga de 15.000 pessoas (upload com parse) | 6,26 s | `_reversa_bugs/seguranca/inspections/checklist-20261013/RESULTADOS-DO-CHECKLIST.md`, item 3 | O parse de uma árvore grande custa segundos, não minutos |
| Quatro requisições simultâneas na mesma árvore | 72,16 s a 70,32 s cada; `GET /` esperou 69,67 s | idem, item 3 | O processo inteiro para: parse CPU-bound no processo único, com GIL |
| DNA com pool 608 e 24, 49 e 199 linhas | 1,22 s, 1,22 s e 3,27 s | idem, item 4 | O custo cresce com linhas x pool, sem teto |
| Parse da árvore real de 35.460 pessoas | 20,9 s | `_reversa_sdd/gaps.md` (L-20) | Ordem de grandeza do parse |
| `person_summary` | 15,4 ms por ficha; 142 fichas custam cerca de 2,2 s | idem (L-20) | As fichas não são o gargalo isolado |
| `homonym_dossier` | 1,73 s por chamada | idem (L-20) | Custo por nome distinto do CSV |
| Ganho da feature 025 | cerca de 1,5 s por carga, "não perceptível" | `_reversa_sdd/addenda/025-desempenho-carga-arvore.md` | Já se tentou otimizar o parse, e o ganho foi pequeno |

> Nenhum desses números foi medido com 19.403 pessoas e 308 linhas. Extrapolar para esse volume é
> estimativa, não medição.

## O que falta medir

1. O parse da árvore de 19.403 pessoas, isolado.
2. O matching das 308 linhas (pool de sobrenomes x razões difusas), isolado.
3. O pipeline por cartão aceito (dossiê, parentesco, endogamia, validação, Mermaid), isolado, e
   quantos cartões a execução do operador produz.
4. O tempo de renderização no navegador, depois que a página chega.

O ponto 4 é o único que exige o navegador. Os pontos 1 a 3 podem ser medidos no `.venv` com
dados sintéticos.
