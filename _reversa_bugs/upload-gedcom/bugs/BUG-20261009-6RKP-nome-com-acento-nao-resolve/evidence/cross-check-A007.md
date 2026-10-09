# Recorte da auditoria que mediu este defeito

Origem: `_reversa_forward/011-escolher-arquivo-da-lista/audit/cross-check.md`, finding `A007` (`CRITICAL`).
O documento original é a fonte; este recorte existe para que a evidência do bug não dependa de o leitor
sair do registro de bugs.

## Como o achado apareceu

A auditoria da feature 011 concluiu, na primeira passagem, que a `D-08` do roadmap ("o arquivo que não
serve ao uso **não** é filtrado na lista; a recusa continua no uso") estava correta, com a justificativa de
que "o caso já é pego pela validação de uso".

Ao corrigir outro achado, foi preciso **medir** o desfecho real do caso negativo em vez de supor. A
medição mostrou que a justificativa era **falsa**: a validação de conteúdo só roda no **envio**
(`ArmazenamentoEmDisco.guardar`), e um arquivo escolhido por referência não passa por ela. O que existe é a
recusa do **resolvedor**, com a mensagem falsa `Erro: Arquivo '...' não existe mais.`.

A partir daí, a pergunta virou mais ampla: quantos arquivos da pasta são inalcançáveis por referência? A
varredura respondeu **7 dos 19**, e o recorte por aba respondeu **6 dos 17 itens** que a lista desenha.

## Texto do finding, como está na auditoria

> **A007, CRITICAL, Coerência com o legado e Cobertura.** 6 dos 17 itens que a lista vai renderizar não
> podem ser usados. `ArmazenamentoEmDisco.resolver` recusa a referência por `chave_recebida_e_valida`
> (forma `^[0-9a-f]{16}__[A-Za-z0-9._-]+$`), mas `nome_visivel_seguro` preserva acentos e espaços. Das 19
> entradas da pasta, 7 são recusadas: 3 por acento no nome visível, 3 por não terem chave e 1 por espaço.
> Escolher qualquer uma delas responde `Erro: Arquivo '...' não existe mais.`, que é falso. Nenhum dos
> cinco artefatos menciona isso.
>
> Onde está: `src/ports/adaptadores.py:93`; `src/utils/validate.py:32` e `:40-65`; medido em
> `evidence/_sonda_forma_do_nome.py` e `evidence/_sonda_caso_negativo_real.py`.

## O que a auditoria deixou explícito sobre o próprio erro

A auditoria registra, na seção 0, que **esta é uma auditoria do autor sobre a própria obra** e que a
primeira passagem errou por omissão neste ponto, porque comparou os documentos entre si em vez de
confrontar a afirmação central deles com a pasta real.

## O segundo defeito, medido na mesma sonda

`A008`, `MEDIUM`: um arquivo cujo nome passa na forma fechada e cujo conteúdo o `ged4py` não lê derruba a
requisição com `500` e traceback, porque `_arvore_do_formulario` chama `carregar_arvore` fora de qualquer
`try` (`src/app.py:186` e `:263`, contra os ramos que capturam exceção em `:299` e `:322`). Está registrado
nas Agent Notes do `bug.md` para decisão humana: entra neste bug ou vira um segundo.
