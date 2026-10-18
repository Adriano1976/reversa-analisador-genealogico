# Onboarding: gerar a primeira imagem da árvore sugerida

> Identificador: `030-renderizador-graphviz`
> Data: `2026-10-18`
> Público: quem vai rodar a feature pela primeira vez.
> Tempo estimado: 15 minutos, dos quais 10 são a instalação do Graphviz.

## 1. O que você precisa ter

| Item | Como conferir |
|------|----------------|
| Python oficial do projeto | `.venv\Scripts\python --version` → `3.14.6` |
| **Graphviz de sistema** (binário `dot`) | `dot -V` → `dot - graphviz version ...` |
| Pacote `graphviz` no `.venv` | `.venv\Scripts\python -c "import graphviz; print(graphviz.__version__)"` |
| Diretório correto | o terminal está na raiz do projeto (a pasta com `src/` e `tests/`) |

> ⚠️ **Nesta máquina, o binário `dot` não existe** (medido em 2026-10-18). O pacote Python
> **já está instalado** (0.21). Sem o `dot` a feature **falha de propósito**, com mensagem clara. Não
> há degradação para `.dot`.

## 2. Instalar o Graphviz (uma vez)

### Windows

```powershell
winget install --id Graphviz.Graphviz -e
# alternativa, se você usa Chocolatey:
# choco install graphviz -y
```

Depois de instalar, **feche e reabra o terminal**: o `PATH` do Windows não se atualiza sozinho.
Confirme com `dot -V`. Se o comando continuar não encontrado, adicione à mão a pasta `bin` da
instalação (por padrão `C:\Program Files\Graphviz\bin`) ao `PATH`.

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y graphviz
dot -V
```

## 3. Instalar o pacote Python

```powershell
.venv\Scripts\python -m pip install graphviz
.venv\Scripts\python -c "import graphviz; print(graphviz.__version__)"
```

Anote a versão impressa: ela é o pin que vai para o `requirements.txt` (ADR-13 exige versão fixa).

## 4. Rodar os testes

```powershell
.venv\Scripts\python -m pytest tests/test_visualizer.py tests/test_fronteira_do_visualizer.py -q
```

Esses rodam **sempre** — não precisam de Graphviz. Depois:

```powershell
.venv\Scripts\python -m pytest tests/test_visualizer_render.py -q
```

Se aparecer `1 skipped`, o `dot` não está no `PATH`; volte ao passo 2. Se passar, a imagem foi gerada
de verdade em diretório temporário.

## 5. Gerar a primeira imagem, passo a passo

```python
import sys, tempfile
sys.path.insert(0, ".")
sys.path.insert(0, "src")

from application.validacao import validar_arquivos
from core.cirurgia_do_grafo import arvore_sugerida
from reporting.visualizer import renderizar_arvore_sugerida, texto_dot
from tests.fixtures.arvore_para_cirurgia import (CSV_SALTO, GED_SALTO_IMPOSSIVEL)

# 1. O GEDCOM e o CSV sintéticos viram arquivos temporários.
with tempfile.NamedTemporaryFile("w", suffix=".ged", delete=False, encoding="utf-8") as fh:
    fh.write(GED_SALTO_IMPOSSIVEL); ged = fh.name
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as fh:
    fh.write(CSV_SALTO); csv = fh.name

# 2. A validação da 028, pedindo o material da correção (documental + árvore).
validacao = validar_arquivos(ged, csv, "Doador Sintetico", ano_referencia=2026,
                             incluir_documental=True)
arvore = validacao["arvore"]
comparacao = validacao["comparacoes"][0]      # cm, mrca_estimado, status, documental
documental = comparacao["documental"]         # path.ids, common_ancestor, person_b

# 3. A sugestão da 029.
sugestao = arvore_sugerida(arvore, documental, comparacao, validacao["doador"]["id"])
print("status:", sugestao["status_origem"], "| hiato:", sugestao["hiato"])

# 4. O texto DOT, sem Graphviz nenhum.
print(texto_dot(sugestao, comparacao, documental)[:400])

# 5. A imagem (precisa do dot).
destino = tempfile.gettempdir() + r"\arvore-sugerida.png"
caminho = renderizar_arvore_sugerida(sugestao, comparacao, documental, destino)
print("gerado:", caminho)
```

> **Por que a cadeia é explícita e não `sugerir_correcao`.** A fachada da `029` devolve as sugestões
> prontas, mas **sem** o `resultado` e o `documental` que o desenho precisa (o cM e as gerações
> vivem no resultado; o caminho, no parentesco documental). Quem quiser os dois juntos usa
> `sugerir_correcao` **e** guarda a validação, ou segue o passo a passo acima. Unificar isso é
> candidato a uma feature de ergonomia, não a um ajuste escondido aqui.

### O que olhar na imagem

1. **O doador está verde** (`#a8e6cf`) e tem o rótulo do nome dele.
2. **As gerações sugeridas estão em pêssego** (`#ffd3b6`) e se chamam `Geração 1`, `Geração 2`, … —
   não são pessoas.
3. **Existe uma aresta tracejada vermelha** entre o ancestral e o filho documental, com o rótulo
   `DESVIO DE CONEXÃO / QUEBRA DE LINHA`. Ela representa o vínculo que a `029` cortou; a cadeia
   pêssego ao lado é o caminho sugerido.
4. **A caixa de evidência** traz `"<cM> cM, <gerações> gerações - <veredito>"`. Se faltar cM ou
   geração, o campo aparece como `—` — a caixa não inventa número.
5. **Nenhum nó de família** (`@F1@`) aparece: as famílias são comprimidas em arestas genitor→filho.

## 6. Testar com a sua árvore (opcional)

1. Copie o GEDCOM para uma pasta **fora do repositório** (nunca em `uploads/`).
2. Rode `sugerir_correcao` com o seu arquivo e o seu CSV.
3. **Gere a imagem em uma pasta fora do repositório.** O PNG contém nomes de pessoas vivas: é dado
   pessoal, e o projeto não versiona dado pessoal (princípio I).
4. Se `sugestao["grafo"]` vier `None`, o status não foi de erro — veja `avisos[0]["codigo"]`.

## 7. O que **não** fazer

| Não faça | Por quê |
|----------|---------|
| Commitar o PNG/SVG gerado | A imagem tem nome de pessoa viva; é dado pessoal (princípio I) |
| Gravar a imagem em `src/uploads/` | A pasta é imutável por conteúdo e some da lista por posição (ADR-30) |
| Passar `destino` sem querer sobrescrever | A função grava no caminho informado; se o arquivo existir, ele é substituído |
| Ler `Geração 2` como pessoa | É posição estimada, não indivíduo |

## 8. Problemas comuns

| Sintoma | Causa provável | Saída |
|---------|----------------|-------|
| `ErroDeRenderizacao: DOT_AUSENTE` | `dot` não está no `PATH` | Passo 2; reabra o terminal |
| `ErroDeRenderizacao: GRAPHVIZ_AUSENTE` | pacote não instalado no `.venv` | Passo 3 |
| `ErroDeRenderizacao: FORMATO_NAO_SUPORTADO` | extensão diferente de `.png`/`.svg` | Use `.png` ou `.svg`, ou passe `formato=` coerente |
| `ErroDeRenderizacao: DESTINO_OBRIGATORIO` | destino vazio ou pasta inexistente | Crie a pasta e informe o caminho completo |
| `ErroDeRenderizacao: SEM_SUGESTAO_PARA_DESENHAR` | a `029` não gerou árvore (status não é erro, hiato ≤ 0 ou afinidade) | Leia `avisos` da sugestão |
| `1 skipped` no teste de renderização | `dot` ausente | É o esperado em máquina sem Graphviz; instale para rodar |
| Nome sai cortado ou com `\` estranho | rótulo com aspas/barra | O escape é automático; se ainda quebrar, reporte com o nome exato |

## 9. Onde ler mais

- Regras e contrato: `_reversa_forward/030-renderizador-graphviz/requirements.md`
- Decisões técnicas: `_reversa_forward/030-renderizador-graphviz/roadmap.md` (§3)
- Por que DOT à mão e como o recorte é montado:
  `_reversa_forward/030-renderizador-graphviz/investigation.md`
- Atributos e classes: `_reversa_forward/030-renderizador-graphviz/data-delta.md`
- O que a imagem desenha: `_reversa_sdd/addenda/029-desacoplamento-de-nos.md`
