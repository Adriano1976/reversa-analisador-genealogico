# Mapeamento de Dependências — analisador-genealogico

> Re-extração de 2026-10-05. Substitui o mapeamento de 2026-09-30, que descrevia um `requirements.txt` dentro do módulo, **sem nenhuma versão fixada** e com `gunicorn` no lugar de `waitress`.
> Snapshot da versão substituída: `.reversa/snapshots/2026-10-05-pre-reextracao/`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Gerenciador de Pacotes

* **Ecossistema:** Python 🟢
* **Gerenciador:** `pip` (`requirements.txt` **na raiz do repositório** — o arquivo deixou de ficar dentro da pasta do módulo junto com a renomeação para `src/`). 🟢
* **Versões fixadas:** **todas as seis** usam `==` com versão exata. A lacuna anterior ("nenhuma versão declarada", 🔴) está **fechada**. 🟢
* **Ambiente virtual:** **existe `.venv/`** (não versionado, coberto pelo `.gitignore`) com Python 3.14.6. ⚠️ **O `.venv` não reproduz o pin** — ver §4.
* **Interpretador que a documentação manda usar:** o **global** — o `README.md` documenta `pip install -r requirements.txt` e `python src/app.py`, sem ativar ambiente virtual. 🟢

---

## 2. Dependências Diretas (`requirements.txt`)

Arquivo completo — 6 linhas, conferidas contra a instalação real do interpretador global:

| Pacote | Versão declarada | Instalada (global, verificada) | Categoria | Finalidade no Projeto |
| --- | --- | --- | --- | --- |
| **Flask** | `3.1.3` | **3.1.3** 🟢 | Framework Web | Roteamento HTTP, renderização Jinja2, filtros de template. |
| **ged4py** | `0.5.2` | **0.5.2** 🟢 | Parser | Leitura e navegação estruturada de arquivos GEDCOM (`.ged`). |
| **networkx** | `3.6.1` | **3.6.1** 🟢 | Grafos | Grafo familiar, ancestral comum e busca de caminhos. |
| **pandas** | `3.0.3` | **3.0.3** 🟢 | Análise de dados | Leitura do CSV de matches e agregação dos segmentos cM. |
| **thefuzz** | `0.22.1` | **0.22.1** 🟢 | Matching de texto | Similaridade difusa entre nomes. |
| **waitress** | `3.0.2` | **3.0.2** 🟢 | Servidor de produção | Servidor WSGI do bloco de entrada (`src/app.py`), importado dentro do `if __name__`. |

---

## 3. Dependências Transitivas Relevantes

Não estão no `requirements.txt`, mas são instaladas e **alteram o comportamento** dos cálculos:

| Pacote | Versão instalada (global) | Papel |
| --- | --- | --- |
| **RapidFuzz** | 3.14.5 🟢 | Backend real do `thefuzz`. É ele quem calcula a similaridade. |
| **python-Levenshtein** | 0.27.3 🟢 | Aceleração em C. Pode alterar desempates em casos-limite. |
| **numpy** | 2.5.0 🟢 | Base do pandas. |

> ⚠️ **Ponto de atenção para paridade (herdado):** o `thefuzz` delega a `RapidFuzz`/`Levenshtein`. Trocar a versão de qualquer uma dessas três **altera o resultado do matching sem alterar uma linha de código do projeto**. Continua registrado como `RISK-006` em `migration/risk_register.md`, e é justamente por isso que a divergência de §4 importa.

---

## 4. ⚠️ Divergência entre o `.venv` e o `requirements.txt`

O `.venv/` do projeto **não é uma cópia do pin**. Medido por `pip list` nos dois interpretadores:

| Pacote | `requirements.txt` | Global | `.venv/` | Situação |
| --- | --- | --- | --- | --- |
| Flask | 3.1.3 | 3.1.3 | 3.1.3 | ✅ igual |
| thefuzz | 0.22.1 | 0.22.1 | 0.22.1 | ✅ igual |
| waitress | 3.0.2 | 3.0.2 | 3.0.2 | ✅ igual |
| **ged4py** | 0.5.2 | 0.5.2 | **0.5.5** | ⚠️ divergente |
| **networkx** | 3.6.1 | 3.6.1 | **3.7** | ⚠️ divergente |
| **pandas** | 3.0.3 | 3.0.3 | **3.0.6** | ⚠️ divergente |
| **RapidFuzz** (transitiva) | — | 3.14.5 | **3.14.6** | ⚠️ divergente |
| **python-Levenshtein** (transitiva) | — | 0.27.3 | **0.27.5** | ⚠️ divergente |

**Consequência prática:** o comportamento do sistema depende de qual interpretador o executa. O `.venv` traz `ged4py`, `networkx` e `pandas` mais novos e, sobretudo, **outro `RapidFuzz`** — exatamente o pacote que decide o matching difuso. Duas execuções da mesma árvore e do mesmo CSV, uma em cada interpretador, **podem** produzir resultados diferentes em casos-limite de nome. 🟡

Nenhum arquivo do projeto declara qual dos dois é o oficial; o `README.md` documenta o fluxo global. A divergência está registrada aqui como **lacuna para validação humana** — não foi "corrigida" por nenhum agente, porque reconciliar ambiente é decisão do dono do repositório. 🔴

---

## 5. Instalados no Global sem Uso pelo Projeto

Pacotes presentes no interpretador global, **ausentes do `requirements.txt`** e **sem nenhum import** em `src/` ou `tests/` (varredura: 0 ocorrências):

| Pacote | Versão instalada | Situação |
| --- | --- | --- |
| **gunicorn** | 26.0.0 🟢 | Era a dependência de servidor da extração anterior. **Deixou de ser declarada** quando o `waitress` entrou. Permanece instalado, sem uso. |
| **matplotlib** | 3.11.1 🟢 | Removido do projeto antes da extração anterior (visualização passou a ser Mermaid no cliente). Permanece instalado, sem uso. |
| **pyvis** | 0.3.2 🟢 | Idem: removido do projeto, permanece instalado, sem uso. |

> Estes três **não** são dívida do código: nenhum arquivo os importa. São resíduo do ambiente. A dívida que existia sobre o README do módulo anunciar `pyvis` **deixou de existir** — o arquivo foi removido na feature 003, e o `README.md` da raiz descreve a stack real.

---

## 6. Dependências Removidas Desde a Extração Anterior

| Pacote | Situação atual | Evidência |
| --- | --- | --- |
| **gunicorn** | **removido** do `requirements.txt` 🟢 | Substituído por `waitress==3.0.2` na feature `004-servidor-waitress`: o `gunicorn` não roda no Windows, que é a plataforma alvo. Zero imports no código. |
| **pyvis** | já removido 🟢 | Ausente do arquivo e do código; a visualização é Mermaid renderizado no cliente. |
| **matplotlib** | já removido 🟢 | Ausente do arquivo e do código. |

---

## 7. Avaliação de Riscos de Dependências

> [!NOTE]
> **Versões fixadas — e agora OITO, não seis.** As seis dependências diretas declaram versão exata, e em 2026-10-05 o `rapidfuzz` e o `python-Levenshtein` foram **promovidos a dependência declarada**. Eram transitivas do `thefuzz`, e o `RapidFuzz` é o **backend real do matching difuso**: deixá-lo livre permitiria que uma instalação nova trouxesse outra versão e mudasse o resultado da análise sem uma linha de código mudar. 🟢

> [!IMPORTANT]
> **O `.venv` deixou de contrariar o pin — a divergência foi ENCERRADA em 2026-10-05.** Correção do Revisor: este aviso dizia que o `.venv` contrariava o `requirements.txt` e recomendava rodar pelo interpretador global. Por decisão do usuário (`questions.md#pergunta-11`), o **`.venv` passou a ser o interpretador OFICIAL**, e o `requirements.txt` foi realinhado a ele (`ged4py==0.5.5`, `networkx==3.7`, `pandas==3.0.6`). A suíte foi verificada **nos dois interpretadores**, com resultado idêntico. 🟢

> [!WARNING]
> **O `README.md` da raiz contradiz o pin.** Ele documenta o fluxo pelo interpretador **global** (`pip install -r requirements.txt`, `python src/app.py`, sem ativar o venv), e o oficial passou a ser o `.venv/`. **Pendência de documentação declarada, não corrigida** — o README é documento do usuário. 🟡

> [!WARNING]
> **Python 3.14 sem pin.** O projeto roda em Python 3.14.6, versão recente, e o `requirements.txt` não declara a versão do interpretador. Não há registro de qual combinação era compatível antes. 🟡

> [!NOTE]
> **`python-Levenshtein` exige toolchain C** quando não há wheel binário para a plataforma. Não é problema aqui (há wheel instalado), mas é ponto de fricção para reprodução em outro ambiente — e é uma razão a mais para ele estar **declarado**, e não apenas resolvido por transitividade. 🟡

> [!NOTE]
> **`waitress` é importado dentro do bloco de entrada**, de propósito: o módulo é importado pela suíte de testes e pela instrumentação de paridade, e um import no topo obrigaria o servidor de produção instalado em quem só quer a aplicação como objeto. A ausência do pacote produz mensagem que nomeia o pacote e o interpretador exato, e aponta para o arquivo de dependências. 🟢

---

*Gerado pelo Reversa-Scout em 2026-10-05 (re-extração).*
