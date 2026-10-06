# ADR-10 — Mover a raiz de código de `analisador-genealogico/` para `src/`

- **Status:** Aceito e executado
- **Data da decisão:** 2026-10-03
- **Commit(s):** `f0cde9e` (abre o ciclo `003-renomear-pasta-app-para-src`), `3ed7e1a` — "refactor: move app root to src"
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A raiz de código era uma pasta com **o mesmo nome do projeto** (`analisador-genealogico/`), dentro do repositório que também se chama `analisador-genealogico`. O efeito era duplo: navegação ambígua (o nome da pasta não diz o que ela é) e **nenhum caminho canônico para a fonte**, o que obrigava cada ferramenta a ser configurada à mão.

## Decisão

Renomear a pasta para **`src/`**, tornando-a o caminho canônico da fonte, e atualizar **todas** as referências de caminho do repositório.

## Evidência

- `_reversa_sdd/addenda/003-renomear-pasta-app-para-src.md` e `_reversa_forward/003-renomear-pasta-app-para-src/` (com `evidence/` de cada portão).
- `ad10216` — "registra transformações `GUE7`, `LMAY`, `FLAT` e `RAIZ` do pacote": são exatamente as classes de referência que precisaram migrar.
- `pyrefly.toml` → `search-path = ["src"]`; `.vscode/settings.json` → `python.analysis.extraPaths = ["./src"]`; `pytest.ini` → `testpaths = tests`.
- **Portões registrados em evidência:** paridade e suíte **antes** e **depois**, varredura de resíduo de referência e smoke do `src/app.py`.

## Justificativa

Um projeto Python precisa de **um** caminho canônico de fonte para que lint, análise estática, testes e imports funcionem sem configuração ad hoc. `src/` é a convenção que o próprio README documenta.

## Consequências

- ✅ O `README.md` da raiz passa a documentar `pip install -r requirements.txt` + `python src/app.py`, e é hoje a **única superfície de documentação do repositório sem defasagem**.
- ✅ **A governança de edição do legado (ADR-06) absorveu a mudança sem afrouxamento:** a lista de caminhos permitidos ganhou `src/**` **e manteve** `analisador-genealogico/**` como caminho histórico, em vez de trocar um pelo outro.
- ⚠️ **A renomeação invalidou referências por caminho em artefatos anteriores.** Os registros de bug anteriores a 2026-10-03 citam `analisador-genealogico/app.py` e `reconstructed/upload.py`, que **não existem mais**. Isso está declarado, não corrigido, em cada registro afetado — e é a origem de parte dos links quebrados apontados em `documentation_debt` do `surface.json`.
- ⚠️ **O `oráculo congelado` (ADR-04) não foi afetado** — o que valida a decisão de congelar uma **cópia**, e não uma referência a caminho vivo.
- 🔴 **Pendência herdada por esta renomeação (fora do escopo do Detetive):** o mini-site `_reversa_docs/`, gerado em 2026-10-01, ainda descreve `analisador-genealogico/` e `reconstructed/`. Ele é o alvo do `/reversa-docs` após esta re-extração.

## Alternativas consideradas

- **Manter `analisador-genealogico/` e configurar ferramentas por caminho.** Descartada: perpetua a ambiguidade e exige configuração por ferramenta.
- **Renomear para `app/`.** Descartada: colide com o `app.py` e com o nome da rota, e não é a convenção de pacote Python.
