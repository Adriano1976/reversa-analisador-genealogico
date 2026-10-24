# Notas de design

Base de análise: skills `sandeco-token-reduce` (LLMLingua-2) e `sandeco-token-reduce-ollama` (reescrita com
Ollama) do repositório `sandeco/prompts` (pasta `sandeco-token`), lidas por clonagem (SKILL.md, `setup.py`,
`compress.py`). Esta skill é uma obra nova inspirada nelas; nenhum código foi copiado.

## O que foi aproveitado
- Duas famílias de compressão (extrativa vs generativa) e o guia de taxas (0.5 leve · 0.4 padrão · 0.2 agressivo).
- Pré-processamento de markdown (decoração, tabelas, separadores) antes de comprimir.
- Proteção de números/IDs, negações e termos técnicos; relatório de métricas; saída JSON.
- Chunking para a janela de 512 tokens do LLMLingua-2; `/no_think` e remoção de `<think>` no Qwen3.
- Idempotência do setup e mensagens de erro acionáveis.

## O que foi mudado, e por quê
| Original | Aqui | Motivo |
|---|---|---|
| Exige venv dentro da pasta da skill + modelo de ~1 GB | Engine padrão só stdlib; extras opcionais, venv em `~/.cache` | pasta de skill pode ser somente-leitura/efêmera (sandboxes); funciona em qualquer harness |
| `setup.py` instala pacotes e `ollama pull` (5 GB) sem perguntar | Nada é instalado/baixado sem `--auto-install` / `--pull` | consentimento explícito, custo previsível |
| `--ask` chama a API Anthropic com modelo fixo | Removido; o agente do harness consome o texto | acoplamento a um provedor; cada harness já tem seu modelo |
| `force_tokens` e IDs específicos de um projeto (`npm`, `WAL`, `RF-01`, `G05`…) e só negações em PT | Proteção genérica por padrão (dígitos, URLs, código, identificadores) + negações/obrigações pt/en/es | generalizar para outros textos e idiomas |
| Tabela → `cabeçalho: valor` por célula (repete o cabeçalho em toda linha) | Tabela compacta `a|b|c` com cabeçalho uma vez | a forma antiga pode **aumentar** tokens em tabelas largas |
| Remove checkbox `- [x]` | Mantém o marcador | perdia o estado feito/pendente |
| Hifens de IDs removidos (`RF-01`→`RF01`) | IDs mantidos como estão | alterar o texto do usuário é mudança de conteúdo |
| Sem checagem da saída | `verify.py` + verificação automática + fallback para `lite` | LLM/BERT podem descartar número ou negação sem aviso |
| PDF: grava `.md` ao lado do PDF sempre | Só com `--save-extracted` | evitar efeito colateral inesperado |
| Métricas e texto misturados no stdout | texto em stdout, relatório em stderr | facilita pipes e leitura por agentes |
| Texto comprimido enviado a LLM sem proteção | Prompts tratam o texto como dado (anti prompt-injection) | documentos de terceiros podem conter instruções |
| Ollama via pacote `ollama` | REST com `urllib` + recusa de host remoto sem `--allow-remote` | zero dependência; privacidade |

## Referências do repositório (como foram usadas)
Os PDFs em `reference/` foram identificados pelo título; só o primeiro tem relação direta com esta skill.
| arXiv | Título | Relação |
|---|---|---|
| 2403.12968 | LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression | base do engine `llmlingua` |
| 2409.10994 | Less is More: ... Token Reduction Method for Efficient Multi-modal LLMs (TRIM) | tokens **visuais** de MLLMs; não se aplica a texto |
| 2502.11501 | Token Pruning in Multimodal LLMs: Are We Solving the Right Problem? | multimodal; fora de escopo |
| 2502.14477 | Unshackling Context Length: ... Query-Key Compression | técnica interna do modelo (atenção), não pré-processamento |
| 2510.26585 | Stop Wasting Your Tokens: Towards Efficient Runtime Multi-Agent Systems | relevante a sistemas multiagente (mensagens redundantes entre agentes); só o título foi considerado |
Nota: apenas o resumo/introdução do TRIM foi lido; os demais PDFs não foram analisados em profundidade.

## Limites conhecidos
- Estimativa de tokens (sem tiktoken) é aproximada; o tokenizer real do modelo de destino pode divergir.
- `lite` não resume: em texto denso o ganho é pequeno (15–35%). Para cortes maiores use `agent`/`ollama`/`llmlingua`.
- Detecção de idioma por palavras frequentes; texto misto pode usar listas do idioma errado (use `--lang`).
- Removidos artigos pt "a" (ambíguo com preposição); nível 4 é deliberadamente conservador mesmo sendo "com perda".
- Engines `ollama` e `llmlingua` foram testados aqui apenas contra simulações (servidor HTTP falso e módulo falso),
  não com modelos reais: valide no seu ambiente com um texto pequeno antes de usar em volume.
