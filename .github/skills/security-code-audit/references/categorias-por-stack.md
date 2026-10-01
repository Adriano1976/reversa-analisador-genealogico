# Guia de adaptação das 5 categorias por stack

Este guia existe para que a adaptação de cada categoria à stack detectada não
dependa só de raciocínio ad hoc a cada execução. Leia a seção da stack
detectada (ou as mais próximas, se for uma combinação) antes de auditar.

Se o projeto usa uma combinação não listada aqui, use o princípio geral de
cada categoria (descrito no SKILL.md) e explique no relatório qual foi o
mecanismo equivalente encontrado.

---

## 1. Banco sem tranca (isolamento de inquilino/dono)

| Stack | Onde procurar | Sinal de furo |
|---|---|---|
| Supabase / Postgres com RLS | Migrações SQL (`CREATE POLICY`, `ENABLE ROW LEVEL SECURITY`) | Tabela sem RLS habilitado, ou policy com `USING (true)` / sem cláusula de `auth.uid()` / `workspace_id` |
| Node/Express + Prisma, TypeORM, Sequelize, Knex | Toda query `findMany`, `find`, `aggregate`, `groupBy`, rotas de exportação/relatório/busca | `where` sem `workspaceId`/`tenantId`/`userId` correspondente ao usuário autenticado |
| Django / DRF | `views.py`, `serializers.py`, managers customizados, `get_queryset()` | `Model.objects.all()` ou `get_queryset()` não filtrado por `request.user` ou `organization` |
| Ruby on Rails | Controllers, `ActiveRecord` scopes | Uso de `Model.all` / `Model.find(params[:id])` em vez de `current_user.models` ou scope do tenant (ex: gem `acts_as_tenant`) |
| Laravel | Controllers, Eloquent | Ausência de Global Scope de tenant, ou query `Model::all()` sem `where('team_id', ...)` |
| Spring Boot | `@Repository`, JPQL/Criteria | Query sem `WHERE tenant_id = :tenantId`, ou `@PreAuthorize` ausente em endpoint de listagem |
| .NET / EF Core | Controllers, DbContext | Falta de Global Query Filter (`HasQueryFilter`) por tenant, ou LINQ sem `.Where(x => x.TenantId == ...)` |

Em qualquer stack: identifique primeiro **qual é o mecanismo de isolamento do
projeto** (RLS, middleware de tenant, filtro manual, Global Scope, Global
Query Filter) antes de procurar onde ele falha — isso vira a nota
metodológica do relatório.

---

## 2. Permissão definida no navegador

Independente do frontend (React, Vue, Angular, Svelte), o padrão de falha é o
mesmo: a UI esconde um botão/rota com uma flag (`isAdmin`, `canEdit`,
`role === 'owner'`, `v-if="isAdmin"`, `*ngIf="canEdit"`), mas o endpoint
correspondente no backend não repete essa checagem.

Processo:
1. Liste todos os gates de papel/permissão no frontend (busque por `isAdmin`,
   `role`, `permission`, `can[A-Z]`, `hasAccess`, etc.).
2. Para cada gate, identifique o endpoint/ação que ele protege.
3. Abra o handler correspondente no backend e confirme se há uma checagem
   equivalente antes de executar a ação — não apenas `auth`/autenticação, mas
   **autorização** (papel, permissão, propriedade do recurso).

Frameworks comuns de autorização no backend a procurar (se existirem, é sinal
de que o projeto tem um padrão — verifique se ele foi aplicado em TODAS as
rotas sensíveis, não só nas óbvias): `requireRole()`, `@PreAuthorize`,
`can()` (Laravel Gates/Policies), `Pundit`/`CanCanCan` (Rails),
`permission_classes` (DRF), `[Authorize(Roles = ...)]` (.NET).

---

## 3. IDOR

Aplica-se a qualquer backend com rotas que recebem um ID (path, query ou
body). Percorra sistematicamente **todos** os handlers, não uma amostra —
IDOR costuma existir de forma inconsistente (algumas rotas corrigidas, outras
não).

Padrão seguro (o que procurar como "ponto forte"):
```
buscar o registro filtrando por (id AND workspaceId/userId do requisitante)
→ 404 se não encontrado
```

Padrão furado (o que procurar como achado):
```
buscar/alterar/deletar por id isolado, sem cláusula adicional de posse
```

Isso vale para REST, GraphQL (resolvers que recebem um `id` como argumento) e
RPC/gRPC.

---

## 4. Chaves expostas (hardcode)

Procurar em:
- Código-fonte (`.env.example` não é problema; `.env` commitado é)
- `docker-compose.yml`, `Dockerfile`, Helm charts (`values.yaml`), Terraform (`.tf`, `.tfvars`)
- CI (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`)
- Scripts de seed/migração e documentação (READMEs com exemplos "reais")
- Bundle do frontend (build de produção) — chaves que deveriam ser só de
  backend às vezes vazam para variáveis `VITE_`/`NEXT_PUBLIC_`/`REACT_APP_`
- Histórico do git (`git log -p` / `git log --all -- '*.env'`, busca por
  padrões de chave em commits antigos), quando o acesso ao histórico estiver
  disponível

Atenção especial a **defaults públicos que viram segredo real**:
```
${JWT_SECRET:-alguma-string-fixa}
SECRET_KEY = "django-insecure-..."  # padrão gerado pelo `startproject`, comum ficar em produção
```
E à ausência de validação de startup que rejeite esses defaults em produção.

---

## 5. Inputs sem tratamento (XSS)

**Frontend** — sinks por framework:

| Framework | Sink a procurar |
|---|---|
| React | `dangerouslySetInnerHTML`, `href`/`src` com URL controlada pelo usuário, `eval`/`new Function` |
| Vue | `v-html`, binding dinâmico de `href`/`src` |
| Angular | `[innerHTML]`, `bypassSecurityTrustHtml` |
| Svelte | `{@html ...}` |
| Qualquer um | renderização de Markdown sem sanitização (`marked`, `markdown-it` sem `rehype-sanitize`/DOMPurify) |

Verifique se existe uma lib de sanitização no projeto (DOMPurify, `sanitize-html`,
`rehype-sanitize`, `bleach` no Python, `Rails::Html::Sanitizer`) e se ela é
efetivamente aplicada nos sinks encontrados — não basta estar no
`package.json`/`requirements.txt`, precisa estar no caminho do dado do
usuário até o sink.

**Backend** — input do usuário entrando em HTML de e-mails, templates
server-side (Jinja2, ERB, Blade, Thymeleaf, Razor) ou respostas sem escape.
A maioria desses engines faz auto-escape por padrão — procure especificamente
onde esse auto-escape foi desativado (`{{ variavel|safe }}` no Django/Jinja2,
`<%= raw ... %>` no Rails, `{!! !!}` no Blade, `Html.Raw()` no Razor).

---

## Quando a categoria não se aplica

Diga isso explicitamente no relatório em vez de forçar um achado. Exemplos
legítimos de "não aplicável":
- Projeto sem frontend (API pura) → sem XSS de frontend (ainda assim, avalie
  o backend quanto a XSS em templates/e-mails)
- Projeto single-tenant sem conceito de organização/workspace → categoria 1
  não se aplica no sentido multi-tenant (mas ainda vale checar isolamento por
  dono do recurso, se houver múltiplos usuários)
