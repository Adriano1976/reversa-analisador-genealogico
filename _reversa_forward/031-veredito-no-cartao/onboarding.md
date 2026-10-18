# Onboarding: ver o veredito no cartão pela primeira vez

> Identificador: `031-veredito-no-cartao`
> Data: `2026-10-18`
> Público: quem vai conferir a mudança na tela.
> Tempo estimado: 10 minutos.

## 1. Antes de começar

| Item | Como conferir |
|------|----------------|
| Python oficial | `.venv\Scripts\python --version` → `3.14.6` |
| Diretório | a raiz do projeto (a pasta com `src/` e `tests/`) |
| Nada instalado a mais | esta feature **não** tem dependência nova |
| Graphviz | **não é necessário** — o selo é HTML/CSS |

> ⚠️ **O servidor precisa ser reiniciado.** O `waitress` não recarrega template: se o processo estava
> no ar antes da mudança, ele continua servindo o HTML antigo. Feche e suba de novo.

## 2. Rodar os testes da feature

```powershell
.venv\Scripts\python -m pytest tests/test_veredito_no_nucleo.py tests/test_validacao_no_cartao.py tests/test_contraste_do_selo.py -q
```

Esperado: todos passam, sem `skip`.

Depois, a suíte inteira — o teste do hash da tela **precisa** passar com o valor novo:

```powershell
.venv\Scripts\python -m pytest -q
```

| Teste que falha | O que significa |
|-----------------|-----------------|
| `test_icone_de_atalho::test_html_servido_...` | O `SHA_DA_TELA` não foi atualizado depois da mudança |
| `test_validacao_no_cartao::test_inconclusivo_nao_ganha_selo` | O template está renderizando mais do que devia |
| `test_contraste_do_selo::*` | Uma das variáveis saiu da faixa AA, ou falta no tema escuro |
| `test_veredito_no_nucleo::test_uma_chamada_por_resultado` | O validador está sendo chamado duas vezes (ou nenhuma) |

## 3. Ver o selo sem subir o servidor

O caminho mais rápido é olhar os quatro campos que o núcleo produz:

```python
import os, sys, tempfile
sys.path.insert(0, "."); sys.path.insert(0, "src")

from core.dna_analysis import Dependencias, dna_analysis
from core.genetic_evidence import build_genetic_evidence
from parsers.csv_ingest import read_csv_with_fallback
from parsers.gedcom_parser import carregar_arvore
from tests.fixtures.arvore_para_cirurgia import GED_SALTO_IMPOSSIVEL, CSV_SALTO

with tempfile.NamedTemporaryFile("w", suffix=".ged", delete=False, encoding="utf-8") as fh:
    fh.write(GED_SALTO_IMPOSSIVEL); ged = fh.name
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as fh:
    fh.write(CSV_SALTO); csv = fh.name

deps = Dependencias(ler_csv=read_csv_with_fallback, construir_evidencia=build_genetic_evidence)
arvore = carregar_arvore(ged)
resultados, _descartados, _msg = dna_analysis(csv, "Doador Sintetico", deps, arvore)

for item in resultados:
    print(item["match_name"] if "match_name" in item else "?",
          "|", item["validacao_status"], "|", item["validacao_rotulo"], "|", item["validacao_classe"])
    print("   title:", item["validacao_aviso"])
```

O esperado no cenário da fixture: `ERRO CRONICO / QUEBRA DE LINHA`, rótulo `Linha em conflito`,
classe `validacao-conflito`, e o `title` citando `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` (ou o primeiro
código crítico daquele par).

> **Se `Dependencias` pedir outros campos**, confira a assinatura em `src/core/dna_analysis.py` — ela
> é dataclass e muda com o tempo; o que importa aqui são as quatro chaves no dicionário.

## 4. Ver o selo na tela

1. Suba o servidor: `.venv\Scripts\python src/app.py` (ou o job que você já usa).
2. Abra `http://127.0.0.1:5000/`.
3. Na aba de arquivos, escolha um GEDCOM e envie um CSV de matches; depois rode a análise de DNA.
   Para um teste seguro, use os arquivos sintéticos da fixture (`tests/fixtures/arvore_para_cirurgia.py`)
   salvos como `.ged` e `.csv` — eles não contêm dado real.
4. **O que olhar no cartão:**

| Sinal | Onde | Como deve ser |
|-------|------|---------------|
| Selo `Linha em conflito` | cabeçalho do cartão, ao lado de cM/confronto | contorno vermelho, texto escuro |
| Selo `Validado` | idem | contorno verde, texto escuro |
| Ausência de selo | idem | cartão inconclusivo **não** tem selo |
| `title` do selo | passe o mouse | motivo + código da anomalia |
| Linha explicativa | topo da lista de resultados | diz que sem selo = não concluído |

5. Alterne o tema (claro/escuro) e confira que o contorno continua legível nos dois.

## 5. O que **não** fazer

| Não faça | Por quê |
|----------|---------|
| Atualizar o `SHA_DA_TELA` sem registrar data e motivo | O invariante perde o sentido: ele existe para a mudança ser declarada |
| Reusar a classe `estado-*` para o selo novo | O texto vira branco sobre fundo claro — foi o defeito de 1,11:1 |
| Mostrar o selo de `INCONCLUSIVO` | Marca quase todos os cartões e deixa de marcar qualquer um |
| Achar que o selo `Validado` prova parentesco | Ele diz que não há contradição **com os dados disponíveis**, não que a linha está certa |

## 6. Problemas comuns

| Sintoma | Causa provável | Saída |
|---------|----------------|-------|
| O selo não aparece na tela, mas os testes passam | servidor antigo no ar | reinicie o `src/app.py` |
| `SHA_DA_TELA` falhando | hash desatualizado | recalcule com o HTML servido e registre a data |
| Selo ilegível no tema escuro | variável `--validacao-*` ausente no bloco escuro | confira `:root[data-bs-theme="dark"]` |
| `validacao_rotulo` é `None` num cartão que deveria concluir | o resultado não tem caminho/`status` | veja `comparison` e `documentary` daquele item |
| Todos os cartões sem selo | o validador não foi chamado no laço | confira D-01 no `roadmap.md` |

## 7. Onde ler mais

- Regras e contrato: `_reversa_forward/031-veredito-no-cartao/requirements.md`
- Decisões técnicas: `_reversa_forward/031-veredito-no-cartao/roadmap.md` (§3)
- Por que contorno, e o contraste medido:
  `_reversa_forward/031-veredito-no-cartao/investigation.md`
- Chaves e classes: `_reversa_forward/031-veredito-no-cartao/data-delta.md`
- O veredito em si: `_reversa_sdd/addenda/028-validador-de-dados-dna.md`
