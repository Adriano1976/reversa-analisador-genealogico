# Engines e flags

## Sumário
- lite · agent · ollama · llmlingua
- Flags principais
- Verificação (o que é checado)
- Problemas comuns

## lite (padrão)
Biblioteca padrão apenas. Pipeline: protege trechos críticos → aplica níveis 1..N → restaura.
`--level N` fixa o nível; `--rate R` sobe até atingir R. `--lang auto|pt|en|es` controla listas de
enchimento/artigos (auto detecta por palavras frequentes; em texto misto, force o idioma dominante).
Ganho típico em texto já enxuto: 15–35%. Em markdown cheio de tabelas/decoração: mais.
Ele **não resume**: se o texto é denso, a meta 0.4 não será atingida e o script avisa.

## agent
Não comprime; imprime um prompt de reescrita com inventário do que deve sobreviver. Quem reescreve é o
modelo do harness (zero dependência, zero download). Depois: `verify.py original comprimido`.
É o caminho certo quando se quer cortar 50–70% sem instalar nada.

## ollama
Reescrita generativa local via REST (`/api/chat`), só `urllib`. Pré-requisitos: Ollama instalado e rodando
(`ollama serve`) e modelo baixado (`ollama pull qwen3:8b`, ~5 GB; ou `--pull`).
- `--ollama-model`, `--ollama-host` (padrão `http://localhost:11434`), `--num-ctx` (padrão 8192), `--timeout`.
- Host não-local exige `--allow-remote` (o texto sairia da máquina).
- Textos longos são divididos em blocos de ~6000 caracteres por parágrafos.
- A taxa é aproximada (LLM nem sempre obedece). Se a verificação falhar → fallback para `lite`.

## llmlingua (opcional)
Extrativo token a token (LLMLingua-2, Microsoft). Mantém palavras originais, texto fica "telegráfico".
- Instalação: `python -m pip install llmlingua` (puxa torch/transformers; modelo ~1 GB do HuggingFace na 1ª vez),
  **ou** `--auto-install` (venv isolado em `~/.cache/token-reduce-universal/venv`; o script se reexecuta nele).
- `--llmlingua-model` troca o modelo (há variantes menores; confira o catálogo do projeto LLMLingua).
- Blocos de ~1200 caracteres (janela de 512 tokens do modelo). GPU CUDA é detectada sozinha.
- Negações e obrigações pt/en/es entram em `force_tokens`; números são protegidos (`force_reserve_digit`).

## Flags principais
| Flag | Efeito |
|---|---|
| `--text` / `--file` / stdin | entrada (`--file x.pdf` extrai o PDF) |
| `--rate R` | fração de tokens a manter (0.05–1.0) |
| `--level 1-4` | lite: nível fixo |
| `-o FILE` | grava o resultado (senão vai para stdout) |
| `--json` | JSON completo (texto, métricas, verificação, fallback) |
| `--quiet` | sem relatório no stderr |
| `--no-verify` / `--no-fallback` | pula verificação / não troca por lite |
| `--ignore a,b` | categorias ignoradas na verificação |
| `--save-extracted` | PDF: salva o texto extraído ao lado do PDF (por padrão NÃO grava nada extra) |

## Verificação (verify.py / automática)
Categorias **críticas** (FAIL se faltar): `numbers` (qualquer token com dígito), `urls`, `emails`, `paths`, `code`
(blocos, inline, front matter), `negations` (contagem total pt/en/es não pode cair).
Categorias de **aviso** (WARN): `idents`, `quoted`, `modals`.
Limites: a checagem de negações é por contagem (troca "não" por "nunca" passa); não detecta paráfrase que
muda sentido sem tocar nesses itens; é uma rede de segurança, não substitui leitura do resultado quando o
risco é alto. Reformulação legítima ("não pode" → "proibido") dispara FAIL de negations: confira e use `--ignore negations`.

## Problemas comuns
- `ERRO: ... nao e local` → Ollama remoto; use `--allow-remote` só se for intencional.
- Saída 4 (`exit 4`) → dependência/serviço ausente; a mensagem lista as opções.
- Windows: o script já força UTF-8 no stdout/stderr; use `python` em vez de `python3`.
- Contagem "estimado": instale `tiktoken` (`pip install tiktoken`) se quiser números mais próximos de modelos OpenAI;
  para Claude/Gemini a contagem exata exige a API/tokenizer do provedor.
