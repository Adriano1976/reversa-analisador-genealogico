# Mapeamento de Dependências — analisador-genealogico

> Re-extração de 2026-10-10. Substitui o mapeamento de 2026-10-05, que descrevia 8 dependências diretas e uma divergência de ambiente que **deixou de existir**.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-10-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA
> Medições desta fase: `pip list --format=freeze` **dentro do `.venv/`** e no interpretador **global**, ambos executados em 2026-10-10.

---

## 1. Gerenciador de Pacotes

* **Ecossistema:** Python 🟢
* **Gerenciador:** `pip`, com `requirements.txt` na **raiz** do repositório. 🟢
* **Versões fixadas:** **todas as nove** dependências diretas usam `==` com versão exata. 🟢
* **Interpretador oficial:** o **`.venv/`** (Python 3.14.6), por decisão registrada em `_reversa_sdd/questions.md#pergunta-11` (2026-10-05). O `.venv/` não é versionado (`.gitignore`, linha 3). 🟢
* **Docker:** a imagem instala exatamente o mesmo arquivo (`COPY requirements.txt` + `pip install -r`), então o container e o `.venv` partem do mesmo pin. 🟢

---

## 2. Dependências Diretas (`requirements.txt`)

Nove linhas efetivas. A coluna "instalada" foi medida, não presumida:

| Pacote | Declarada | `.venv` (oficial) | Global | Categoria | Finalidade no projeto |
| --- | --- | --- | --- | --- | --- |
| **Flask** | `3.1.3` | **3.1.3** 🟢 | 3.1.3 | Framework web | Rotas, Jinja2, filtros de template |
| **ged4py** | `0.5.5` | **0.5.5** 🟢 | 0.5.2 ⚠️ | Parser | Leitura e navegação de GEDCOM |
| **networkx** | `3.7` | **3.7** 🟢 | 3.6.1 ⚠️ | Grafos | Grafo familiar, ancestral comum, caminhos |
| **pandas** | `3.0.6` | **3.0.6** 🟢 | 3.0.3 ⚠️ | Análise de dados | Leitura do CSV de matches e agregação de cM |
| **thefuzz** | `0.22.1` | **0.22.1** 🟢 | 0.22.1 | Matching de texto | Similaridade difusa entre nomes |
| **waitress** | `3.0.2` | **3.0.2** 🟢 | 3.0.2 | Servidor de produção | Servidor WSGI do bloco de entrada |
| **rapidfuzz** | `3.14.6` | **3.14.6** 🟢 | 3.14.5 ⚠️ | Backend de matching | Backend **real** do `thefuzz` |
| **python-Levenshtein** | `0.27.5` | **0.27.5** 🟢 | 0.27.3 ⚠️ | Aceleração em C | Backend alternativo do `thefuzz` |
| **psycopg2-binary** | `2.9.13` | ❌ **ausente** 🔴 | ❌ ausente | Driver de banco | Único consumidor: `ports/adaptadores.py` (`import psycopg2` preguiçoso, linha 281) |

**Onde cada dependência é importada** (varredura de `src/`): `flask` e `werkzeug` em `app.py`; `waitress` dentro do `if __name__`; `thefuzz` em `core/matching.py`; `networkx` em `core/path_finding.py` e `parsers/gedcom_parser.py`; `pandas` em `parsers/csv_ingest.py`; `ged4py` em `parsers/gedcom_parser.py`; `psycopg2` em `ports/adaptadores.py`. **`rapidfuzz` e `Levenshtein` não são importados por nenhum arquivo do projeto** — existem declarados porque são eles que decidem o matching por baixo do `thefuzz`. 🟢

---

## 3. Dependências Transitivas Relevantes

Instaladas no `.venv/`, ausentes do pin, e listadas porque **alteram comportamento** ou sustentam o runtime:

| Pacote | Versão no `.venv` | Vem de | Papel |
| --- | --- | --- | --- |
| **RapidFuzz** | 3.14.6 | `thefuzz` (declarado no pin) | Calcula a similaridade de fato |
| **Levenshtein** (`python-Levenshtein`) | 0.27.5 | `thefuzz` (declarado no pin) | Aceleração em C; pode alterar desempate em caso-limite |
| **numpy** | 2.5.3 | `pandas` | Base numérica do pandas |
| **Werkzeug** | 3.1.9 | `Flask` | `RequestEntityTooLarge` (handler de 413), `send_file` |
| **Jinja2** · **MarkupSafe** | 3.1.6 · 3.0.4 | `Flask` | Renderização do template |
| **click** · **itsdangerous** · **blinker** | 8.5.0 · 2.2.0 · 1.9.0 | `Flask` | Suporte do framework |
| **python-dateutil** · **tzdata** | 2.9.0.post0 · 2026.5 | `pandas` | Datas e fusos |
| **ansel** · **convertdate** | 1.0.0 · 2.5.1 | `ged4py` | Conversão de calendários e de charset ANSEL do GEDCOM |

> ⚠️ **Ponto de atenção para paridade (herdado):** o `thefuzz` delega a `RapidFuzz`/`Levenshtein`. Trocar a versão de qualquer um dos dois **altera o resultado do matching sem uma linha de código mudar**. É o `RISK-006` de `migration/risk_register.md`, e é a razão pela qual os dois foram promovidos a dependência declarada em 2026-10-05. 🟢

---

## 4. Estado dos Ambientes (medido)

### 4.1 `.venv/` contra o pin: **9 de 9 conferem — exceto o driver do banco**

Oito das nove dependências diretas estão instaladas na versão exata do pin. A exceção é
**`psycopg2-binary`, que não está instalada**. 🔴

**Consequência prática:** com `DATABASE_URL` no ambiente, o registro histórico **não grava** e o operador vê o
aviso não bloqueante de "histórico não registrado" no resultado da análise. Sem `DATABASE_URL`, o registrador é
nulo e nada aparece. O sistema **não quebra** em nenhum dos casos — o import é preguiçoso e a falha é tratada
(`RN-13`) —, mas o único caminho que liga a persistência fica desligado no ambiente oficial.

**Efeito colateral medido na suíte:** duas asserções de `tests/test_persistencia_desabilitada.py` pressupõem
que a variável **não** existe no ambiente. Com ela presente e o driver ausente, a suíte vai a **525 passam /
9 pulados / 2 falham** em vez de 527/9/0. Ver `inventory.md` §9.2.

### 4.2 Global contra o pin: divergente, e agora sem consequência

| Pacote | Pin | Global | Situação |
| --- | --- | --- | --- |
| ged4py | 0.5.5 | 0.5.2 | ⚠️ divergente |
| networkx | 3.7 | 3.6.1 | ⚠️ divergente |
| pandas | 3.0.6 | 3.0.3 | ⚠️ divergente |
| RapidFuzz | 3.14.6 | 3.14.5 | ⚠️ divergente |
| python-Levenshtein | 0.27.5 | 0.27.3 | ⚠️ divergente |
| Flask · thefuzz · waitress | 3.1.3 · 0.22.1 · 3.0.2 | iguais | ✅ |

O interpretador global segue com as versões antigas e **não tem `rapidfuzz` nem `python-Levenshtein`
declarados** — o que significa que ele **não reproduz o pin**. A diferença que importava em 2026-10-05 (a
suíte rodar em dois interpretadores com resultados potencialmente distintos) **deixou de existir como
problema aberto**: o `.venv/` é o oficial, e o `README.md` passou a documentá-lo (§6). 🟢

---

## 5. Pacotes Instalados sem Uso pelo Projeto

### 5.1 No `.venv/` (o interpretador oficial)

| Pacote | Versão | Situação |
| --- | --- | --- |
| **gunicorn** | 26.2.0 🟢 | Servidor da extração anterior; saiu do pin na feature 004 (não roda no Windows). Zero imports. |
| **matplotlib** | 3.11.2 🟢 | Visualização passou a ser Mermaid no cliente. Zero imports. |
| **pyvis** | 0.3.2 🟢 | Idem. Zero imports. |
| **ipython** · **jedi** · **parso** · **asttokens** · **pure_eval** · **stack-data** · **prompt_toolkit** · **traitlets** · **Pygments** | — 🟡 | Ferramental de depuração interativa; não é dependência do projeto. |
| **pypdf** · **reportlab** · **pillow** | — 🟡 | Ferramental de manipulação de PDF/imagem; não é dependência do projeto. |
| **psutil** · **jsonpickle** · **six** · **colorama** · **packaging** | — 🟡 | Suporte/resíduo de outras ferramentas. |

### 5.2 No global

`gunicorn 26.0.0`, `matplotlib 3.11.1`, `pyvis 0.3.2` — os três já registrados em 2026-09-30 e 2026-10-05.

> Nenhum deles é dívida do código: nenhum arquivo de `src/` os importa. São resíduo de ambiente, e o `.venv/`
> agora concentra o mesmo tipo de resíduo. 🟢

---

## 6. Mudanças Desde a Extração de 2026-10-05

| Item | Antes (2026-10-05) | Agora (2026-10-10) |
| --- | --- | --- |
| Dependências diretas | 8 | **9** — entrou `psycopg2-binary==2.9.13` (feature 008) |
| `.venv` × pin | 8 de 8 conferiam | **8 de 9** conferem; `psycopg2-binary` declarado e não instalado 🔴 |
| README × pin | README documentava o interpretador **global** e contradizia o pin 🟡 | **alinhado**: documenta `.venv/` como oficial (linhas 45, 251-263, 602) 🟢 |
| Divergência de ambiente | aberta como lacuna para o humano | **encerrada por decisão** (`questions.md#pergunta-11`) 🟢 |
| Docker | ausente | imagem instala o mesmo pin (`docker/Dockerfile`) 🟢 |

> **Dívida fechada:** a pendência de documentação "o `README.md` contradiz o pin" **deixou de existir** — o
> README foi reescrito em 2026-10-08 e atualizado em 2026-10-09/10, e hoje declara o `.venv/` como
> interpretador oficial, com os comandos de criação, instalação e execução. 🟢

---

## 7. Avaliação de Riscos de Dependências

> [!IMPORTANT]
> **A divergência que motivava o alerta anterior está ENCERRADA — mas surgiu uma no sentido oposto.** O
> `.venv/` deixou de contrariar o pin em 2026-10-05, e o pin foi realinhado a ele. Em 2026-10-10, o que não
> confere é a **presença** do `psycopg2-binary`: ele está declarado e não está instalado. Não é regressão de
> comportamento (o código degrada por desenho), é **capacidade desligada no ambiente oficial**. 🔴

> [!WARNING]
> **O resultado da suíte depende de uma variável de ambiente.** Com `DATABASE_URL` presente e sem o driver,
> dois testes de contrato de tela falham. O pin manda instalar o driver; o `.venv` não o tem; e o teste assume
> que a variável não existe. As três coisas juntas produzem um resultado de suíte que muda com o ambiente, e
> isso é uma lacuna de reprodutibilidade, não um defeito de código. 🟡

> [!WARNING]
> **Python 3.14 sem pin no `requirements.txt`.** O projeto exige 3.14 pela imagem (`python:3.14-slim`) e pelo
> `.venv` (3.14.6), mas o arquivo de dependências não declara a versão do interpretador. 🟡

> [!NOTE]
> **`rapidfuzz` e `python-Levenshtein` são declarados e nunca importados** — de propósito. Eles são o backend
> real do matching difuso; deixá-los livres permitiria que uma instalação nova trouxesse outra versão e
> mudasse o resultado da análise sem uma linha de código mudar. 🟢

> [!NOTE]
> **`psycopg2-binary` tem wheel `cp314`** para Windows e Linux, então a ausência não se explica por falta de
> binário — não há compilação local em nenhuma das duas plataformas, e o `Dockerfile` conta com isso. 🟢

> [!NOTE]
> **Os módulos de borda fazem import preguiçoso de propósito.** `waitress` é importado dentro do
> `if __name__` (a suíte e o harness importam `app` sem precisar do servidor) e `psycopg2` é importado dentro
> do método de gravação (sem ele, `import app` quebraria a suíte **por ambiente**). 🟢

---

*Gerado pelo Reversa-Scout em 2026-10-10 (re-extração).*
