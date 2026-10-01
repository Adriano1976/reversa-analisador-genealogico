---
name: security-code-audit
description: Audita um projeto de código quanto a 5 categorias de vulnerabilidade — isolamento de inquilino/dono ausente (RLS ou equivalente), permissão validada só no frontend, IDOR, chaves/segredos expostos e inputs sem tratamento (XSS) — e gera um relatório completo (PDF e/ou Markdown, à escolha do usuário) com gráficos, tabela de achados e issues do GitHub prontas para copiar. Use esta skill sempre que o usuário pedir uma "auditoria de segurança", "revisão de segurança do código", "pentest de código", "checar vulnerabilidades", "checar IDOR/RLS/segredos expostos/XSS", ou pedir para revisar um repositório/projeto atrás de falhas de segurança — mesmo que ele não cite as 5 categorias pelo nome.
---

# Auditoria de Segurança de Código

Esta skill audita um projeto real (não hipotético) quanto a 5 categorias de
vulnerabilidade que, juntas, cobrem a maior parte dos incidentes de
autorização e exposição de dados vistos em produtos SaaS: isolamento de
dados ausente, autorização só na UI, IDOR, segredos expostos e XSS.

O produto final é sempre em duas partes: (1) o relatório para humanos (PDF
e/ou Markdown) e (2) issues de GitHub já redigidas, prontas para copiar e
colar — a ideia é que a auditoria vire trabalho rastreável, não só um
documento lido uma vez e esquecido.

## Fluxo de trabalho

1. **Detectar a stack** do projeto.
2. **Auditar** as 5 categorias, arquivo por arquivo, adaptando cada uma à
   stack detectada.
3. **Montar `achados.json`** com tudo que foi encontrado (e o que está
   correto).
4. **Perguntar ao usuário o formato do relatório** (PDF, Markdown, ou ambos)
   — nunca assuma um formato por padrão, mesmo que o usuário já tenha
   escolhido em uma execução anterior desta conversa.
5. **Gerar o relatório** rodando `scripts/gerar_relatorio.py`.
6. **Verificar o output** antes de entregar.
7. **Entregar**: relatório(s), lista de achados no chat (arquivo por arquivo,
   linha por linha) e o caminho de todos os arquivos gerados.

Não pule etapas nem troque a ordem — o relatório depende do `achados.json`
estar completo, e o `achados.json` depende da stack já ter sido identificada
(a nota metodológica do relatório documenta exatamente essa cadeia).

---

## Passo 1 — Detectar a stack

Antes de abrir qualquer arquivo em busca de vulnerabilidade, identifique:

- Linguagem e framework principal (`package.json`, `requirements.txt`,
  `Gemfile`, `composer.json`, `pom.xml`, `*.csproj`, etc.)
- ORM ou query builder (Prisma, TypeORM, Sequelize, SQLAlchemy, ActiveRecord,
  Eloquent, Entity Framework, ou SQL cru)
- Mecanismo de autenticação (JWT próprio, sessão, OAuth, Supabase Auth,
  Auth0, Devise, etc.)
- Frontend, se houver (React, Vue, Angular, Svelte, ou nenhum — API pura)
- Arquivos de deploy: Docker/`docker-compose.yml`, CI (`.github/workflows/`,
  `.gitlab-ci.yml`), Helm, Terraform

Isso vira o campo `projeto.stack_detectada` do `achados.json` e a base da
`nota_metodologica` — a explicação de como cada categoria abaixo foi mapeada
para o que existe *neste* projeto. Sem essa etapa, a auditoria vira genérica
e perde precisão.

---

## Passo 2 — Auditar as 5 categorias

Leia **`references/categorias-por-stack.md`** antes de auditar — ele traz,
por stack, onde procurar e qual é o sinal de furo para cada categoria. Não
pule essa leitura mesmo em stacks familiares: o objetivo é manter a
adaptação consistente entre execuções, não depender só do que vier à cabeça
na hora.

As 5 categorias:

1. **Banco sem tranca** (isolamento de inquilino/dono) — em Supabase é RLS
   ausente; em APIs próprias, são queries de listagem/busca/agregação/
   relatório/exportação que não filtram pelo usuário autenticado ou pela
   organização/workspace/tenant dele. Primeiro identifique qual é o
   mecanismo de isolamento do projeto, depois aponte onde ele está ausente
   ou furado.
2. **Permissão definida no navegador** — operações privilegiadas (admin,
   configurações, gestão de usuários, ações de escrita) em que o frontend
   esconde a UI por papel, mas o servidor não repete a verificação. Cruze
   cada gate do frontend com o endpoint correspondente.
3. **IDOR** — rotas que buscam, alteram ou deletam um objeto por ID sem
   verificar posse. Percorra **todos** os handlers, não uma amostra.
4. **Chaves expostas** — segredos hardcoded em código, configs,
   docker-compose, charts, CI e documentação. Atenção especial a defaults
   públicos que viram segredo real (`${VAR:-valor-default}`) sem validação
   de startup que os rejeite. Cheque também histórico do git e bundle do
   frontend, quando acessíveis.
5. **Inputs sem tratamento (XSS)** — sinks de HTML/markdown sem sanitização
   no frontend; escape desativado em templates ou e-mails no backend.

### Regras da auditoria

- **Só reporte achados verificados no código real.** Nada de especulação. Se
  não tiver certeza, não inclua — um falso positivo custa mais confiança do
  que um achado a menos.
- Para cada achado: arquivo, linha(s) exata(s), trecho de código, por que é
  explorável, condições de exploração (se houver) e severidade.
- Classifique a severidade usando **`references/rubrica-severidade.md`** —
  não invente o critério a cada achado.
- Registre também o que foi verificado e **está correto** (ex: "router X
  valida posse em todos os handlers"). Isso vira a seção de pontos fortes e
  é a prova de que a categoria foi de fato coberta, não pulada.
- Quando uma categoria não se aplicar à stack (ex: projeto sem frontend →
  sem XSS de frontend), diga isso explicitamente em `categorias_nao_aplicaveis`
  em vez de forçar um achado ou simplesmente omitir a categoria.
- Vá arquivo por arquivo, linha por linha — isso é o que separa uma
  auditoria de uma leitura superficial.

---

## Passo 3 — Montar `achados.json`

Estruture tudo que foi encontrado (e o que está correto) seguindo
**`assets/achados.schema.json`**. Use **`assets/achados.exemplo.json`** como
referência de formato preenchido — inclusive para o texto das issues do
GitHub, que já devem sair redigidas neste momento (título, labels, descrição,
evidência, impacto, sugestão de correção e critérios de aceite), não deixadas
para depois.

Agrupe achados triviais relacionados numa única issue quando fizer sentido
(ex: vários defaults de segredo no mesmo tema) para não gerar spam de
issues — veja o exemplo de `achados.exemplo.json` para o formato de
agrupamento via `achados_relacionados`.

Salve este arquivo em `docs/security-audit/achados.json` dentro do projeto
auditado (crie o diretório se não existir). Ele é o que permite regerar o
relatório depois, em outro formato, sem refazer a auditoria inteira.

---

## Passo 4 — Perguntar o formato do relatório

Pergunte ao usuário se o relatório final deve ser **PDF**, **Markdown**, ou
**ambos**, antes de gerar qualquer coisa. Isso vale toda vez que a skill
rodar, mesmo que o usuário já tenha escolhido um formato antes nesta mesma
conversa — a escolha certa pode mudar conforme o destino do relatório (ex:
PDF para enviar a um stakeholder, Markdown para commitar direto no repositório
ou colar num PR).

Vale mencionar rapidamente a diferença se o usuário parecer indeciso: o PDF
tem capa, gráficos (rosca por severidade, barras por categoria) e é melhor
para leitura fora do editor; o Markdown é mais leve, sem gráficos de imagem
(usa tabelas e um gráfico de pizza em Mermaid, que o GitHub renderiza
nativamente), e é melhor para versionar junto do código.

---

## Passo 5 — Gerar o relatório

Rode o script bundlado, que lê o `achados.json` e monta o(s) arquivo(s)
final(is):

```bash
python3 scripts/gerar_relatorio.py \
  --achados docs/security-audit/achados.json \
  --formato pdf   # ou: md | ambos
```

O script já aplica a paleta de cores fixa (crítica `#B91C1C`, alta
`#EA580C`, média `#D97706`, baixa `#2563EB`, ponto forte `#059669`), gera os
dois gráficos do resumo executivo, monta a tabela de achados por categoria
com chip de severidade colorido, e monta a seção final de issues do GitHub
usando os blocos `--- ISSUE n ---` / `--- FIM ISSUE n ---`.

Antes de rodar, garanta que as dependências existem (isolado, sem instalar
nada globalmente):

```bash
python3 -m venv /tmp/venv-auditoria
source /tmp/venv-auditoria/bin/activate
pip install reportlab matplotlib pypdf
```

(`pypdf` é opcional — só é usado para a verificação automática de número de
páginas no Passo 6; `reportlab`/`matplotlib` só são necessários se o formato
incluir PDF. Gerar só em Markdown não exige nenhuma dependência externa.)

O relatório sai em `docs/security-audit/relatorio-auditoria-seguranca.pdf`
e/ou `.md`, conforme o formato escolhido. Use `--saida-dir` e `--nome-base`
se o usuário pedir um caminho ou nome diferente.

---

## Passo 6 — Verificar antes de entregar

Não entregue o relatório sem checar:

- **PDF**: o script já imprime o número de páginas gerado — confirme que
  bate com o esperado (capa + resumo + achados + recomendações + issues).
  Se possível, rasterize a primeira página e a página de gráficos para
  conferir visualmente que os dois gráficos renderizaram e que as tabelas
  não estão cortando texto:
  ```bash
  pdftoppm -png -r 100 -f 1 -l 3 docs/security-audit/relatorio-auditoria-seguranca.pdf /tmp/preview
  ```
  e olhe as imagens resultantes. Corrija qualquer defeito visual antes de
  entregar (tabela cortando linha, gráfico sem legenda visível, etc.) — o
  ajuste normalmente é no próprio `scripts/gerar_relatorio.py` (larguras de
  coluna, tamanho de fonte, tamanho da figura).
- **Markdown**: abra o arquivo gerado e confirme que as tabelas estão bem
  formadas (colunas alinhadas, sem `|` quebrado por descrição com quebra de
  linha) e que o bloco `mermaid` está sintaticamente válido.

---

## Passo 7 — Entregar

Ao final, entregue três coisas:

1. O(s) arquivo(s) de relatório gerado(s).
2. A lista de achados **no chat**, arquivo por arquivo, linha por linha —
   isso não substitui o relatório, é um resumo rápido para quem não vai abrir
   o PDF/Markdown na hora.
3. O caminho de todos os arquivos gerados (`achados.json`, relatório(s),
   `scripts/gerar_relatorio.py` já fica salvo dentro do projeto para permitir
   regerar o relatório depois).

---

## Referências

- `references/categorias-por-stack.md` — onde procurar cada categoria por
  stack, e qual é o sinal de furo.
- `references/rubrica-severidade.md` — critério fixo de crítica/alta/média/
  baixa/informativa.
- `assets/achados.schema.json` — estrutura exata esperada pelo script.
- `assets/achados.exemplo.json` — exemplo completo preenchido, incluindo
  issues do GitHub já redigidas.
- `scripts/gerar_relatorio.py` — gerador do relatório (PDF e/ou Markdown).
