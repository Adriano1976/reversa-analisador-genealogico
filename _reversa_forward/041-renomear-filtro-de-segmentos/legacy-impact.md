# Legacy impact: renomear o filtro de segmentos

> Identificador: `041-renomear-filtro-de-segmentos`
> Data: `2026-10-22`
> Modo: **express**
> Política de edição do legado: `allowLegacyEdits: true`, com `allowedPaths` liberando `src/**` e
> `tests/**`. Os dois arquivos tocados estão dentro desses globs.

## 1. Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/templates/index.html` | apresentação | contrato-alterado | LOW | O título de queda do bloco `endogamia-bloco` passa de `Filtro de endogamia` para `Filtro de segmentos (<limite> cM)`; o limite vem do payload |
| `tests/test_endogamia.py` | — | contrato-alterado | LOW | O literal preso no teste de "sem fato nenhum" foi atualizado e o teste do bloco ganhou asserção positiva do título novo |

## 2. Diff conceitual

**Template.** Na seção 2, o bloco que mostra total bruto, total após filtro, segmentos descartados e
maior bloco tinha dois títulos possíveis: o rótulo do selo quando havia sinal estrutural, e o literal
`Filtro de endogamia` quando não havia. A queda passou a ser
`Filtro de segmentos ({{ result.endogamia.limiares.segmento | cm_br }} cM)`.

O ramo estrutural **não foi tocado**: continua `{{ result.endogamia.selo.rotulo }}`, que vale
`Sinal estrutural na árvore` sem caminho documental e `Endogamia estrutural` com ele — decisão do
núcleo em `_selo_da_endogamia`, não do template.

**Teste.** O teste de "sem fato nenhum" prendia a ausência do título antigo; passou a prender a
ausência do novo. E o teste que renderiza o bloco de verdade ganhou:

- `assert "Filtro de segmentos (10 cM)" in html` — positiva, com o limite formatado;
- `assert "Filtro de endogamia" not in html` — negativa, para o rótulo velho não voltar.

## 3. Regras do `domain.md` **preservadas**

| Regra | Verificação |
|---|---|
| §3.2 — o filtro de 10 cM **avisa, não corrige**; total bruto ao lado do recalculado | o bloco continua com `Total bruto (arquivo)` e `Total após filtro`; nenhum número mudou |
| `CM_MINIMO_SEGMENTO = 10.0` como critério do projeto | o título lê o valor do payload; o teste prende `(10 cM)` |
| `ADR-21` — endogamia avisa, não corrige | nenhum veredito, cM, caminho ou confronto foi tocado |
| Rótulos estruturais (`Sinal estrutural na árvore` / `Endogamia estrutural`) e `Evidência fraca` | testes existentes continuam passando, sem edição |

## 4. Regras **modificadas**

| Regra | O que mudou | Onde |
|---|---|---|
| Texto do título do bloco de filtro | era `Filtro de endogamia`; passa a nomear o objeto e o limiar | `src/templates/index.html`, seção 2 |

> **Para o `/reversa-sync`:** nenhum artefato de `_reversa_sdd/` cita o título antigo (varredura: zero
> ocorrências em `_reversa_sdd/*.md`). A única ocorrência restante no repositório é a maquete
> `_reversa_sdd/analise-planilhas-dna-sergipe/simulacao-sem-familysearch.html`, que é **retrato do
> estado anterior** e fica como está, de propósito.
