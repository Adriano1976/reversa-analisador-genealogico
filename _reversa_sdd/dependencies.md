# Mapeamento de Dependências — analisador-genealogico

> Re-extração de 2026-09-30. Substitui o mapeamento de 2026-08-03, que listava `pyvis` e `matplotlib` — ambas **removidas** do projeto.
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## 1. Gerenciador de Pacotes

* **Ecossistema:** Python
* **Gerenciador:** `pip` (`analisador-genealogico/requirements.txt`) 🟢
* **Ambiente verificado:** Python **3.14.6** global. **Não existe `.venv` no projeto** — não há ambiente virtual versionado. 🟢
* **Versões fixadas:** **nenhuma**. O arquivo lista nomes sem operador de versão. 🔴

---

## 2. Dependências Diretas (`requirements.txt`)

Arquivo completo — 6 linhas, todas verificadas contra a instalação real:

| Pacote | Versão declarada | Versão instalada (verificada) | Categoria | Finalidade no Projeto |
| --- | --- | --- | --- | --- |
| **Flask** | *não fixada* | **3.1.3** 🟢 | Framework Web | Roteamento HTTP, renderização Jinja2, servidor de desenvolvimento. |
| **ged4py** | *não fixada* | **0.5.2** 🟢 | Parser | Leitura e navegação estruturada de arquivos GEDCOM (`.ged`). |
| **networkx** | *não fixada* | **3.6.1** 🟢 | Grafos | Construção do grafo familiar e cálculo de caminhos. |
| **pandas** | *não fixada* | **3.0.3** 🟢 | Análise de dados | Leitura, limpeza e agregação dos segmentos cM do CSV de DNA. |
| **thefuzz** | *não fixada* | **0.22.1** 🟢 | Matching de texto | Similaridade difusa (`ratio`, `token_sort_ratio`) entre nomes. |
| **gunicorn** | *não fixada* | **26.0.0** 🟢 | Servidor de produção | Servidor WSGI para deploy. |

> Nota: `gunicorn` aparece no `requirements.txt` com espaço final na linha ("`gunicorn `"), detalhe inofensivo para o `pip`.

---

## 3. Dependências Transitivas Relevantes

Não estão no `requirements.txt`, mas são instaladas e **alteram o comportamento** dos cálculos:

| Pacote | Versão instalada | Papel |
| --- | --- | --- |
| **RapidFuzz** | 3.14.5 🟢 | Backend real do `thefuzz`. É ele quem calcula a similaridade. |
| **python-Levenshtein** | 0.27.3 🟢 | Aceleração C. Aumenta a velocidade e pode alterar desempates em casos-limite. |
| **numpy** | 2.5.0 🟢 | Base do pandas. |

> ⚠️ **Ponto de atenção para paridade:** `thefuzz` delega a `RapidFuzz`/`Levenshtein`. Trocar a versão de qualquer uma dessas três **altera o resultado do matching sem alterar uma linha de código do projeto**. Isso já está registrado como risco no `migration/risk_register.md` (RISK-006).

---

## 4. Dependências Removidas Desde a Extração Anterior

| Pacote | Situação atual | Evidência |
| --- | --- | --- |
| **pyvis** | **removido** 🟢 | Ausente do `requirements.txt`. Varredura do código não encontra nenhum import. A visualização de grafo passou a ser Mermaid renderizado no cliente. |
| **matplotlib** | **removido** 🟢 | Ausente do `requirements.txt`. Nenhum import no código. |

> Consequência documental: `analisador-genealogico/README.md` ainda anuncia **Pyvis** como biblioteca de visualização. O README está **desatualizado** em relação ao código. 🟡

---

## 5. Avaliação de Riscos de Dependências

> [!WARNING]
> **Versões não fixadas.** Nenhuma das 6 dependências declara versão. Uma instalação nova em outro ambiente pode trazer versões incompatíveis — e, no caso de `thefuzz`/`RapidFuzz`/`Levenshtein`, **mudar silenciosamente o resultado do matching**. 🔴

> [!WARNING]
> **Python 3.14 sem pin.** O projeto roda em Python 3.14.6, versão recente. As bibliotecas instaladas são compatíveis hoje, mas não há registro do que era compatível antes. 🟡

> [!NOTE]
> **`python-Levenshtein` exige toolchain C** quando não há wheel binário para a plataforma. Não é problema aqui, mas é um ponto de fricção para reprodução em outro ambiente. 🟡

> [!NOTE]
> **`gunicorn` não tem uso interno.** Nenhum arquivo do projeto o importa ou o configura. É dependência exclusivamente de deploy, o que é esperado. 🟢

---

*Gerado pelo Reversa-Scout em 2026-09-30 (re-extração).*
