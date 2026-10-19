# Onboarding: ver a árvore sugerida no cartão

> Identificador: `032-arvore-sugerida-na-tela`
> Data: `2026-10-19`
> Público: quem vai conferir a mudança na tela.
> Tempo estimado: 8 minutos.

## 1. Antes de começar

| Item | Como conferir |
|------|----------------|
| Python oficial | `.venv\Scripts\python --version` → `3.14.6` |
| Diretório | a raiz do projeto |
| Graphviz | **não é necessário** — o desenho é Mermaid, no navegador |
| Nada a instalar | a feature não tem dependência nova |

> ⚠️ **Reinicie o servidor.** O `waitress` não recarrega template: processo no ar desde antes da
> mudança continua servindo o HTML velho.

## 2. Rodar os testes da feature

```powershell
.venv\Scripts\python -m pytest tests/test_resumo_da_sugestao.py tests/test_mermaid_da_sugestao.py tests/test_arvore_sugerida_na_tela.py -q
```

| Teste que falha | O que significa |
|-----------------|-----------------|
| `test_sem_copia_de_grafo` | Alguém passou a chamar a cirurgia (e a copiar o grafo) por cartão |
| `test_cores_das_tres_classes` | Um `classDef` saiu da paleta da `030` |
| `test_aresta_rompida_e_a_ultima` | O `linkStyle` ficou com índice errado |
| `test_cartao_sem_conflito_nao_mostra_nada` | A frase de ausência está vazando para cartões validados |
| `test_bloco_vem_depois_do_diagrama_documentado` | O bloco foi colocado no lugar errado |

## 3. Ver o resumo sem subir o servidor

```python
import sys, tempfile
sys.path.insert(0, "."); sys.path.insert(0, "src")

from application.validacao import validar_arquivos
from core.cirurgia_do_grafo import resumo_da_sugestao
from core.dna_analysis import dna_analysis, Dependencias
from reporting.mermaid_render import mermaid_da_sugestao
from tests.fixtures.arvore_para_cirurgia import GED_SALTO_IMPOSSIVEL, CSV_SALTO

def tmp(txt, suf):
    f = tempfile.NamedTemporaryFile("w", suffix=suf, delete=False, encoding="utf-8")
    f.write(txt); f.close(); return f.name

ged, csv = tmp(GED_SALTO_IMPOSSIVEL, ".ged"), tmp(CSV_SALTO, ".csv")
v = validar_arquivos(ged, csv, "Doador Sintetico", incluir_documental=True)
c = v["comparacoes"][0]

resumo = resumo_da_sugestao(c, c["documental"])
print("gerações:", resumo["geracoes"], "| resumo:", resumo["resumo"], "| aviso:", resumo["aviso"])
print(mermaid_da_sugestao(c, c["documental"]))
```

O esperado: `gerações: 3 | resumo: 3 gerações sugeridas | aviso: None`, e um `graph TD` com
`:::base`, `:::doc`, `:::virt`, a aresta `-.->` rotulada e o `linkStyle` no fim.

## 4. Ver na tela

1. Suba o servidor: `.venv\Scripts\python src/app.py`.
2. Abra `http://127.0.0.1:5000/` e rode uma análise de DNA com um par que gere conflito.
3. No cartão em conflito, procure o bloco **"Árvore sugerida — N gerações"** logo abaixo do
   diagrama de parentesco.

| Sinal | Onde | Como deve ser |
|-------|------|---------------|
| Resumo `N gerações sugeridas` | título do bloco | visível sem clique |
| Diagrama | corpo do bloco, ao abrir | doador verde, documentais cinza, gerações em pêssego |
| Aresta vermelha tracejada | entre ancestral e descendente | com o rótulo do desvio |
| Sem bloco | cartão validado/inconclusivo | nada aparece |
| Frase de ausência | cartão em conflito sem hiato | "as duas medidas concordam" |
| Diagrama documentado | acima do bloco novo | continua igual, aberto como antes |

## 5. O que **não** fazer

| Não faça | Por quê |
|----------|---------|
| Chamar `arvore_sugerida` por cartão | Copia o grafo (O(V+E)); 142 cartões inviabilizam a requisição |
| Trocar Mermaid por Graphviz na tela | O container não tem `dot`; a tela passaria a depender de instalação |
| Mudar as cores do `classDef` | A paleta é o contrato comum com a imagem da `030` |
| Mostrar a frase de ausência em todos os cartões | Troca um silêncio ruidoso por um ruído constante |
| Abrir o bloco por padrão | Soma um segundo diagrama aberto a um cartão com cinco seções |

## 6. Problemas comuns

| Sintoma | Causa provável | Saída |
|---------|----------------|-------|
| O bloco não aparece | servidor antigo no ar | reinicie o `src/app.py` |
| O diagrama sai vazio ao abrir | Mermaid não rodou no `toggle` | confira se o `div` tem a classe `mermaid` |
| A aresta vermelha não está tracejada | `linkStyle` com índice errado | a aresta rompida tem de ser emitida por último |
| Nenhum cartão mostra o bloco | hiato ≤ 0 em todos (cM alto) | é o comportamento correto; veja a frase de ausência |
| A frase aparece em cartão validado | `sugestao_aviso` preenchido fora de conflito | o núcleo decide; veja `core/dna_analysis` |

## 7. Onde ler mais

- Regras: `_reversa_forward/032-arvore-sugerida-na-tela/requirements.md`
- Decisões: `_reversa_forward/032-arvore-sugerida-na-tela/roadmap.md` (§3)
- Custo e sintaxe Mermaid: `_reversa_forward/032-arvore-sugerida-na-tela/investigation.md`
- Chaves e contrato do desenho: `_reversa_forward/032-arvore-sugerida-na-tela/data-delta.md`
- A sugestão em si: `_reversa_sdd/addenda/029-desacoplamento-de-nos.md`
