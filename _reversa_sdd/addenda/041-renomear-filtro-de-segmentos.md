# Adendo: renomear o filtro de segmentos

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md` e `_reversa_sdd/domain.md`)
> Modo: **express** — a spec fina vive em `_reversa_forward/041-renomear-filtro-de-segmentos/`

## Vigência

Vigente desde 2026-10-22.

## Resumo da entrega

O bloco da seção 2 que mostra a aritmética do cM depois do piso de 10 cM chamava-se **"Filtro de
endogamia"** — um nome que sugere um diagnóstico de endogamia que ele não faz: ele descarta segmentos
abaixo de 10 cM e recalcula o total. O título de queda passou a ser **"Filtro de segmentos (10 cM)"**,
com o limite lido de `result.endogamia.limiares.segmento` (o template não guarda um segundo `10`).

**Nada mais mudou.** O ramo estrutural do mesmo bloco continua exibindo o rótulo decidido pelo núcleo —
`Sinal estrutural na árvore` sem caminho documental, `Endogamia estrutural` com ele —, assim como os
selos `Filtro: N seg. abaixo de 10 cM` e `Evidência fraca`. Nenhum número, cM, veredito, caminho,
confronto, ordem ou exportação foi tocado.

**3 ações concluídas** (`T001`–`T003`). `tests/test_endogamia.py` em **46 passed**; suíte completa em
**1492 passed, 9 skipped** (mesma contagem: as asserções novas entraram dentro de um teste existente).
A varredura confirma **zero** ocorrências de "Filtro de endogamia" em `src/`; a única restante no
repositório é a assertiva negativa do teste e a maquete da análise, que é retrato do estado anterior.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|---|---|---|---|
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | §3 Componentes e estrutura de pacotes | delta-de-contrato-externo | O título de queda do bloco `endogamia-bloco` na resposta HTML de `POST /` (`action=dna_analysis`) passa a ser `Filtro de segmentos (<limite> cM)`, com o limite vindo do payload; o ramo estrutural do mesmo título e todos os selos ficam iguais |

> **Observação para a próxima extração:** a leitura de `_reversa_sdd/domain.md#32-evidência-genética`
> continua válida sem ressalva — o filtro de 10 cM e o "avisar, não corrigir" não mudaram; mudou o
> **nome visível** do bloco. `_reversa_sdd/code-analysis.md#46` continua verdadeiro: `CM_MINIMO_SEGMENTO`
> segue `10.0` e agora é ainda mais citado do dado, porque o título o lê do payload.

## Regras sob vigilância

- `W001` — ver `_reversa_forward/041-renomear-filtro-de-segmentos/regression-watch.md`.
- As três observações sem peso (rótulos estruturais preservados, selos do filtro preservados e a
  maquete com o rótulo antigo) estão no mesmo arquivo.

## Fontes

- `_reversa_forward/041-renomear-filtro-de-segmentos/requirements.md`
- `_reversa_forward/041-renomear-filtro-de-segmentos/roadmap.md`
- `_reversa_forward/041-renomear-filtro-de-segmentos/actions.md`
- `_reversa_forward/041-renomear-filtro-de-segmentos/legacy-impact.md`
- `_reversa_forward/041-renomear-filtro-de-segmentos/regression-watch.md`
- `_reversa_forward/041-renomear-filtro-de-segmentos/progress.jsonl`
