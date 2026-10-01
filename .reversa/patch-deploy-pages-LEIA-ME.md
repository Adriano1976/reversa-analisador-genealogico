# Patch — workflow de deploy do GitHub Pages

> Preparado em 2026-10-01. **Não aplicado**: `.github/` está fora das pastas onde o Reversa
> pode escrever (`.reversa/`, `_reversa_sdd/`, `_reversa_docs/`, `_reversa_forward/`) e o
> `reversa-config.json` não inclui `.github/**` em `allowedPaths`. Aplicação é ato seu.

## Arquivos

| Arquivo | O que é |
|---|---|
| `patch-deploy-pages.yml` | O workflow corrigido, completo, pronto para substituir o atual |
| `patch-deploy-pages.diff` | O mesmo, em diff unificado, para conferência |

## Como aplicar

**Opção A, substituir o arquivo (mais simples):**

```powershell
Copy-Item .reversa\patch-deploy-pages.yml .github\workflows\deploy-pages.yml -Force
```

**Opção B, revisar antes:** abra `.reversa/patch-deploy-pages.diff` e aplique com
`git apply` ou pela interface do editor.

## As três correções

### 1. O gatilho apontava para uma branch inexistente (crítico)

```diff
-    branches: ["main"] # Altere para 'master' se sua branch principal for master
+    branches: ["master"] # Branch principal deste repositorio.
```

O repositório usa `master`. As branches existentes são `master` e `melhorias-reversa`, e o
`refs/remotes/origin/HEAD` aponta para `origin/master`. **Não existe branch `main`**, então o
gatilho nunca casava e o deploy nunca disparava. O próprio comentário do arquivo original
avisava disso.

### 2. O artefato publicava 3,02 MB, metade disso lixo (moderado)

`path: '_reversa_docs'` sobe a pasta inteira. Entravam no site público:

- `.backup-20261001-003512/` — 31 arquivos, 1,5 MB, backup de regeneração
- `.state.json` — telemetria interna da execução
- `.config.json` — respostas da entrevista e o seed
- `assets/data/*.json` — os 6 JSONs intermediários, que sobem **em duplicidade**: o site lê
  tudo de `assets/js/data.js`, que já os embute

O novo passo de limpeza remove esses quatro grupos e cria `.nojekyll`, que impede o
processamento Jekyll do GitHub Pages.

**Medido:** 62 → **24 arquivos**, 3,02 → **1,49 MB** (−51%).

### 3. Verificação de segurança da limpeza

Antes de propor a remoção, confirmei por simulação que ela não quebra nada:

- **0** referências diretas a `assets/data/` nas páginas: as 10 leem `window.RV_DATA`
- **57** links e assets relativos conferidos, **0 quebrados** após a limpeza
- `data.js` (36.870 bytes) e as 9 bibliotecas de `assets/vendor/` (1,4 MB) preservados
- Todos os caminhos do site são relativos, então funciona publicado em subpasta
  (`https://<user>.github.io/<repo>/`); nenhum caminho absoluto encontrado

## Validação já feita

| Verificação | Resultado |
|---|---|
| Gatilho contém `master` e não contém mais `main` | ok |
| Mantém `workflow_dispatch`, `permissions`, `concurrency` | ok |
| Mantém os 4 passos originais (`checkout`, `configure-pages`, `upload`, `deploy`) | ok |
| Adiciona 1 passo de limpeza | ok |
| Indentação do bloco `run: \|` consistente | ok |
| YAML estruturalmente válido | ok (sem PyYAML, por inspeção direta) |

> Não foi possível rodar o workflow localmente: não há `act` nem Docker neste ambiente. A
> validação é estrutural e por simulação do artefato, não por execução real do Actions.

## Depois de aplicar

1. Confirme em **Settings → Pages** que a fonte é **GitHub Actions** (e não "Deploy from a branch")
2. Faça o push para `master`
3. O deploy deve aparecer em **Actions → Deploy GitHub Pages**
4. Se quiser testar sem push, use **workflow_dispatch** na aba Actions

## Lembrete

A cada regeneração do mini-site, um `.backup-<timestamp>/` novo é criado dentro de
`_reversa_docs/`. O passo de limpeza usa `rm -rf _reversa_docs/.backup-*`, então todos são
removidos do artefato. Os backups continuam existindo no repositório local.
