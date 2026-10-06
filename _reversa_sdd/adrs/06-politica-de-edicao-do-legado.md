# ADR-06 — Governança de edição do legado por lista de caminhos permitidos

- **Status:** Aceito e vigente
- **Data da decisão:** 2026-09-29 (e ampliações em 2026-10-04 e 2026-10-05)
- **Commit(s):** `80afe02` (política), `6cef54d` (libera `requirements.txt`), `4188946` (libera a config do markdownlint)
- **Confiança:** 🟢 CONFIRMADO

## Contexto

O Reversa escreve, por padrão, **apenas em suas próprias pastas**. Mas o trabalho real — corrigir um bug, renomear a raiz, trocar o servidor — exige tocar **código de produção**. Sem regra, cada escrita fora das pastas do framework seria discricionária e não auditável.

## Decisão

Editar arquivos fora das pastas do Reversa **somente** quando `.reversa/reversa-config.json` declarar `allowLegacyEdits: true` **e** o caminho casar com um glob da lista `allowedPaths`. **Ausência de arquivo, JSON inválido ou campo com tipo errado = falha segura (`false`)**: nenhuma escrita.

Estado atual do arquivo, verbatim:

```json
{ "version": 1,
"allowLegacyEdits": true,
  "allowedPaths": ["analisador-genealogico/**", "tests/**", "README.md", "pyrefly.toml",
                 "src/**", ".vscode/**", "requirements.txt", ".markdownlint-cli2.jsonc"]
}
```

## Evidência

- `.reversa/reversa-config.json` — a lista acima.
- `.reversa/hooks/check-legacy-policy.mjs` — o hook que aplica a política.
- `migration/.state.json` → `correctionsApplied` — cada escrita fora de `_reversa_sdd/` registrada **com sha256 antes e depois**.
- `analisador-genealogico/**` continua na lista **mesmo com a pasta renomeada para `src/`** (ADR-10): é caminho histórico, mantido para não alargar nem estreitar a autorização sem decisão explícita.

## Justificativa

Editar código de produção é **ato explícito e auditável do usuário**, não consequência colateral de rodar um agente. A falha segura é a escolha certa porque o modo padrão do risco é "escrita não autorizada", e não "escrita não realizada".

## Consequências

- 🟢 **A política já foi exercida nos dois sentidos.** A remoção das entidades decorativas (ADR-09) só foi possível porque `src/**` está autorizado; e a própria `reversa-config.json` **nunca** é editada por iniciativa de agente — é ato exclusivo do usuário.
- ⚠️ **A lista cresceu por necessidade, uma vez por commit** (`requirements.txt`, depois `.markdownlint-cli2.jsonc`). É o comportamento desejado: cada ampliação é um commit visível.
- ⚠️ **A governança protege o repositório, não o dado do usuário.** Ela nada diz sobre a pasta `uploads/`, onde vivem GEDCOMs reais. O incidente `INC-001` no `migration/.state.json` — em que um `git checkout --` destruiu trabalho não commitado de 335 linhas, depois recuperado byte a byte de um blob *dangling* — nasceu exatamente dessa assimetria.
- 🔴 **Lição registrada no próprio incidente e que vale como contrato:** `git status` mostrando `M` **não** significa corrupção. Neste repositório há atividade concorrente; alterações em `uploads/` são **esperadas**.

## Alternativas consideradas

- **Autorizar tudo (`allowLegacyEdits: true` com lista vazia).** Descartada: a diretiva não-destrutiva perderia o mecanismo de auditoria.
- **Nunca editar o legado.** Descartada: impediria todo o ciclo forward (`_reversa_forward/`), que é o propósito do framework.
