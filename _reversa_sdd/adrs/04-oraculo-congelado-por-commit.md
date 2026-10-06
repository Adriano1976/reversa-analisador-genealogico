# ADR-04 — Oráculo congelado por commit, e não a reconstrução

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-09-28
- **Confiança:** 🟢 CONFIRMADO

## Contexto

A migração precisava provar que o alvo reproduz o legado. As duas referências disponíveis eram **inutilizáveis**:

1. O `app.py` **atual** importava o próprio candidato (`reconstructed/`) — comparar contra ele seria **validação circular** (`RISK-002`).
2. Os **47 testes** da época testavam a **reconstrução**, não o legado — mesma circularidade, com uma camada a mais de distância.

## Decisão

Congelar o commit **`e43ca22`** — o último estado do **monolito original**, com **888 linhas** e **zero referências** a `reconstructed/` — como **oráculo de comportamento, somente leitura**.

## Evidência

- `_reversa_sdd/oracle/app_legacy_e43ca22.py` — `gitBlob e43ca22:analisador-genealogico/app.py`, 888 linhas, 41.950 bytes, sha256 `44370b23…`.
- `_reversa_sdd/oracle/ORACLE_MANIFEST.md` — proveniência, 14 funções verificadas, dependências travadas.
- `_reversa_sdd/oracle/run_oracle.py` — runner que **isola** a execução (`.oracle-run/`, `chdir` antes do import, UTF-8 forçado), porque o import do oráculo cria `uploads/` e `static/` no diretório de trabalho.
- `_reversa_sdd/parity/harness.py` — harness diferencial; **dois subprocessos obrigatórios**, porque o oráculo mantém estado global mutável e importar ambos no mesmo processo contaminaria o candidato.

## Justificativa

O comportamento observável do código é a única especificação não interpretável. Uma spec é uma **leitura** do sistema; o código é o sistema — e a diferença entre os dois já havia produzido um erro factual (`AMB-023`, sobre `cM ≤ 0`) que sobreviveu a seis agentes e sete portões humanos.

## Resultado medido

- **Paridade 100%** em **6/6 fixtures** sintéticas e **5/5 árvores reais**, incluindo uma de **35.460 pessoas**.
- Descoberta de **`DIV-001`** (`get_name`): a **única** divergência de comportamento real entre legado e reconstrução.
- **Contraprova:** substituindo *apenas* `get_name` pela versão do oráculo, a paridade volta a 100% — o que isola a divergência àquela função.

## Consequências

- 🟢 **A lição está escrita no próprio manifesto:** *"a spec do legado não era oráculo; o código era."*
- ⚠️ **Falsos positivos são caros.** O harness produziu **três**, todos defeito do **probe** e não do sistema — o mais perigoso sendo uma divergência **intermitente** dependente de `PYTHONHASHSEED`, causada por materializar um `set` em lista antes de canonicalizar. A defesa adotada foi **canonicalizar na fronteira de coleta**.
- ⚠️ **O oráculo depende de ambiente travado.** Se `thefuzz`/`pandas`/`ged4py` divergirem entre o ambiente do oráculo e o do alvo, a divergência **não é erro do port** (`RISK-009`) — e é exatamente o que o `L-19` de `domain.md` registra hoje sobre o `.venv`.
- O oráculo é **cópia congelada**: continua válido mesmo com a raiz de código renomeada para `src/` (ADR-10), porque não lê o repositório vivo.
