# Investigation

## Pesquisa de Fundo

A reconstrução (`/reversa-reconstructor`) gerou 4 módulos em `reconstructed/` (`domain.py`, `upload.py`, `path_search.py`, `dna_analysis.py`) com comportamento idêntico ao legado, validados por 47 testes (`tests/`). O `app.py` (887 linhas) ainda carrega a lógica inline duplicada (matching difuso, geração de Mermaid, tabela cM, helpers de nome), enquanto a rota `index()` é a única que expõe esses fluxos via HTTP.

O objetivo é fechar a lacuna da "camada de apresentação": mover os módulos para dentro de `analisador-genealogico/` e fazer o `app.py` delegar a eles, eliminando a duplicação (dívida técnica nº 5 de `_reversa_sdd/architecture.md`).

## Alternativas avaliadas

1. **Import direto mantendo `reconstructed/` na raiz** — menor esforço de movimentação, mas mantém a lógica fora do pacote da aplicação. Foi a alternativa rejeitada pelo usuário.
2. **Mover módulos para dentro de `analisador-genealogico/`** — escolhida (decisão do usuário em 2026-08-11). Integra a lógica ao pacote principal; os imports relativos dos módulos entre si já são relativos (`from .upload import ...`), então a movimentação preserva os imports internos se o subpacote for mantido.
3. **Reescrever a rota do zero (sem reaproveitar `reconstructed/`)** — descartada: descartaria os 47 testes existentes.

## Padrões e fontes

- O `upload.py` reconstruído já usa mutação in-place (`clear` + `update`) das globals para manter referências importadas válidas — comportamento necessário ao re-parse a cada `POST` (RF-06).
- Os módulos usam `from __future__ import annotations` e imports relativos (`from .upload import ...`), o que facilita a movimentação como subpacote.
- Suíte de testes: `tests/test_upload.py`, `tests/test_path_search.py`, `tests/test_dna_analysis.py`, `tests/test_domain.py` (47 passed) — rede de segurança para a movimentação.
