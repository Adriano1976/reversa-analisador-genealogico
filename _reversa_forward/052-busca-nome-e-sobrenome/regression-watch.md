# Regression Watch: busca por nome e sobrenome

> Identificador: `052-busca-nome-e-sobrenome`
> Data: `2026-10-28`
> O que precisa continuar verdadeiro nas próximas extrações. Itens marcados 🟢 nasceram
> de regra confirmada; o que era 🟡 ou 🔴 não entra no watch principal — vai para
> "Observações".

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/code-analysis.md#5.7` · `src/core/homonimos.py` | O dossiê de homônimos continua devolvendo o **mesmo conjunto** de ids, na mesma ordem, com o mesmo `exact_count`, para a mesma árvore | `presença` | `exact_count`, lista de ids ou ordem diferentes das de antes da 052 |
| W002 | `_reversa_sdd/addenda/048-indice-de-nomes-sem-colisao.md` | O índice continua **preso ao grafo**, sem chave de conteúdo e sem estado de módulo — agora nas duas visões | `presença` | Surgir atributo de módulo com chave derivada do conteúdo, ou o dossiê da segunda árvore citar xref da primeira |
| W003 | `_reversa_sdd/architecture.md#3` · `src/ports/__init__.py` | A fonte de nomes declara **a sua** normalização; não existe normalizador único na busca | `redação` | `FonteDeNomes` perder `normalizar`, ou a busca passar a usar `norm_name`/`normalizar` para as duas fontes |
| W004 | `_reversa_sdd/architecture.md#1` · `src/app.py` | A borda registra o Blueprint da busca e monta o serviço; **não** decide casamento nem ranking | `presença` | Regra de casamento, pontuação ou limite aparecendo em `app.py` ou em `rotas_busca.py` |
| W005 | `tests/test_icone_de_atalho.py` | O bloco de busca continua **fora** da tela vazia; `SHA_DA_TELA` só muda com declaração | `presença` | Hash diferente sem adendo que o declare |
| W006 | `requirements.md` `RN-01` | A busca **não grava**: sem disco, sem histórico, sem trilha de auditoria | `ausência` | Arquivo criado na pasta de upload, linha em `dna_analysis` ou linha em `access_audit` com origem em `/busca` |
| W007 | `requirements.md` `RN-06`, `RF-11` | A busca não altera veredito, número de conexões nem descartados da análise | `presença` | Mesma entrada GEDCOM+CSV produzindo veredito diferente depois de uma busca |
| W008 | `requirements.md` `RN-03` · `addenda/051` | Referência de outro dono responde `404` com o literal de inexistência, nunca `403` | `presença` | Resposta `403`, ou corpo citando nome de outro dono |
| W009 | `requirements.md` `RN-04` | A ordem dos acertos é total e estável: duas buscas iguais devolvem a mesma sequência | `presença` | Ordem variando com `PYTHONHASHSEED` |

## Observações

Nada aqui tem peso de regressão: são fatos de contexto que a próxima extração deve apenas
registrar, e não vigiar.

- O **casamento aproximado** ficou de fora (`requirements.md#8`, "Could"). Se entrar, deve
  entrar atrás de `EstrategiaDeCasamento` e com medição — o `rapidfuzz` já pinado é o
  candidato, e reusá-lo acopla a ordenação da busca ao pin que existe para não mudar o
  resultado da análise (`RISK-006`).
- O **`all_names` continua no HTML**. A remoção é a entrega seguinte; quando ela acontecer,
  a auditoria da busca passa a ser devida (sessão de esclarecimentos de 2026-10-28).
- O **marco da suíte** no `HEAD` é 5 falhas, e não 4: a quinta
  (`test_tres_fases_da_tela.py`, literal `1. Lista de Matches (CSV)`) é anterior a esta
  entrega. Ver `legacy-impact.md#5`.

## Histórico de re-extrações

| Data | Re-extração | Resultado |
|------|-------------|-----------|
| — | — | Nenhuma re-extração desde a criação deste arquivo |

## Arquivadas

| ID | Motivo do arquivamento | Data |
|----|------------------------|------|
| — | — | — |
