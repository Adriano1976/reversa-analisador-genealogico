# dsh-markdownlint

Plugin **host** do DeepSeek Harness que expõe, para o agente, uma ferramenta de
lint de Markdown apoiada no [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2).

Ferramenta registrada: **`markdown_lint`**.

## O que a ferramenta faz

- Roda o `markdownlint-cli2` **em processo** (sem shell nem subprocesso)
  sobre o diretório do workspace da sessão.
- Descobre a configuração como o CLI descobre: `.markdownlint-cli2.jsonc|yaml|cjs|mjs`
  e `.markdownlint.jsonc|json|yaml|yml|cjs|mjs`, com herança por diretório,
  `overrides` e `customRules`. Não é preciso passar regras.
- Devolve os problemas **estruturados** (arquivo, linha, coluna, regras, severidade,
  descrição e se há correção automática), não o texto de console do CLI.
- Linta `**/*.md` por padrão e **sempre** exclui `**/node_modules/**`,
  `**/.git/**`, `**/.venv/**` e `**/venv/**`, mesmo com `globs` próprios.

| Parâmetro | Tipo | Para que serve |
| --- | --- | --- |
| `globs` | `string[]` | Padrões a lintar (globby). `!padrão` exclui mais. |
| `fix` | `boolean` | Aplica as correções (`--fix`) nos próprios arquivos. |
| `config` | `string` | Arquivo de configuração base (`--config`). Opcional. |
| `workdir` | `string` | Diretório-base do lint. Padrão: o workspace. |

`fix: true` escreve direto nos arquivos, sem backup e **fora do sandbox de escrita
do harness** — use só quando a correção for o pedido.

## Estrutura

```text
plugins/dsh-markdownlint/
├── lib/index.js          # plugin Cordis: registra a ferramenta markdown_lint
├── lib/lint.js           # núcleo do lint (markdownlint-cli2), importável sozinho
├── cli.mjs               # atalho de linha de comando sobre o mesmo núcleo
├── smoke.mjs             # teste de fumaça: acha, corrige e define a ferramenta
├── link-host.mjs         # cria o junction de @deepseek-ai/dsh-tools neste pacote
├── fixtures/quebrado.md  # Markdown com violações conhecidas
└── package.json
```

## Instalação

```powershell
cd plugins/dsh-markdownlint
npm install          # traz o markdownlint-cli2
npm run link-host    # junction local para @deepseek-ai/dsh-tools
npm run smoke        # confere lint, fix e definição da ferramenta
```

`link-host` existe porque o Node resolve as importações pelo caminho real do
módulo: como este pacote é ligado ao profile por um junction, o `import` de
`@deepseek-ai/dsh-tools` não enxergaria o `node_modules` do harness sem o
junction local. O script é idempotente.

## Ativação no profile

O plugin é carregado pelo Cordis a partir de uma entrada em
`$DSH_HOME/profiles/<profile>/cordis.patch.yml`, com o pacote presente no
`node_modules` do profile. No profile `web` desta máquina já está assim:

```yaml
- insert:
    - id: markdownlint
      name: 'dsh-markdownlint'
```

```powershell
# junction do pacote para o profile (uma vez)
New-Item -ItemType Junction `
  -Path "$env:DSH_HOME\profiles\web\node_modules\dsh-markdownlint" `
  -Target "D:\Projetos\reversa_analisador_gelealogico\plugins\dsh-markdownlint"
```

O profile `web` usa `patchReload: live`, então a entrada é aplicada sem
reiniciar; se a ferramenta não aparecer ao agente, reinicie o `dsh web`.

Para **desativar**: apague o bloco do `cordis.patch.yml` (o junction pode ficar).

## Uso

```text
markdown_lint {}
markdown_lint { "globs": ["README.md", "docs/**/*.md"] }
markdown_lint { "globs": ["**/*.md", "!_reversa_docs/**"] }
markdown_lint { "fix": true, "globs": ["README.md"] }
```

Sem harness:

```powershell
npm run lint -- .. README.md
```

## Regras do projeto

Este plugin não traz configuração própria: o que vale é a configuração que o
`markdownlint-cli2` encontrar no projeto — hoje, nenhuma, portanto as regras
padrão valem (a `MD013`, comprimento de linha 80, é a mais ruidosa em prosa
longa). Para ajustar, crie na raiz do repositório um `.markdownlint-cli2.jsonc`:

```jsonc
{
  "config": {
    "MD013": { "line_length": 200, "tables": false, "code_blocks": false }
  },
  "ignores": ["_reversa_docs/**", "_reversa_sdd/**"]
}
```

A criação desse arquivo é ato seu: a raiz do projeto não está em `allowedPaths`
do `.reversa/reversa-config.json`.

> Nota de política do projeto: `plugins/**` **não** está nos `allowedPaths` de
> `.reversa/reversa-config.json`. Enquanto não estiver, os agentes do Reversa
> recusam escrever nesta pasta. A inclusão do glob é edição exclusiva do usuário.

## Licença

MIT, como o próprio `markdownlint-cli2`.
