---
name: git-naming-conventions
description: "Use when standardizing branch names, commit messages, and pull request titles in software development. Applies consistent naming conventions using conventional prefixes such as feat/, fix/, refactor/, and chore/ to improve clarity, automation, and team collaboration."
---

# Convenções de Nomenclatura Git

## Introdução

Esta skill padroniza a criação de nomes para branches, commits e Pull Requests (PRs) em projetos de software. O objetivo é manter a base de trabalho legível, consistente e fácil de rastrear, além de facilitar a automação em pipelines, releases e revisão de código.

A regra geral é usar um prefixo semântico seguido de uma descrição curta e objetiva em kebab-case.

## Nomenclaturas Principais (Core)

### feat/
- Uso: novas funcionalidades ou melhorias significativas para o produto.
- Exemplo: `feat/login-social`

### fix/
- Uso: correções de bugs, defeitos e problemas em comportamento já existente.
- Exemplo: `fix/validation-email`

### refactor/
- Uso: refatoração de código sem alterar o comportamento externo da funcionalidade.
- Exemplo: `refactor/user-service-cleanup`

### chore/
- Uso: manutenção geral, infraestrutura, configuração, dependências e tarefas operacionais.
- Exemplo: `chore/update-eslint-config`

## Nomenclaturas Secundárias e Especializadas

### docs/
- Uso: documentação, READMEs, guias, comentários e materiais de apoio.
- Exemplo: `docs/api-authentication`

### style/
- Uso: ajustes de formatação, layout, CSS, aparência visual e padronização estética.
- Exemplo: `style/button-primary-theme`

### test/
- Uso: testes automatizados, validações, cenários de cobertura e ajustes de QA.
- Exemplo: `test/user-login-flow`

### perf/
- Uso: melhorias de desempenho, otimização de algoritmos, redução de custo computacional e ganho de velocidade.
- Exemplo: `perf/cache-query-results`

### build/
- Uso: alterações no sistema de build, empacotamento, bundlers e configurações de geração.
- Exemplo: `build/vite-config-update`

### ci/
- Uso: alterações em pipelines de integração contínua, deploy contínuo e automações de qualidade.
- Exemplo: `ci/github-actions-lint`

### revert/
- Uso: reversão de commits anteriores para desfazer alterações específicas.
- Exemplo: `revert/remove-legacy-login`

### hotfix/
- Uso: correções urgentes em produção que exigem resposta rápida e imediata.
- Exemplo: `hotfix/payment-timeout-error`

## Regras de Formatação

- Use kebab-case para separar palavras.
- Escreva tudo em letras minúsculas.
- Evite acentos, caracteres especiais e espaços.
- Separe a ideia principal por hífens, por exemplo: `feat/user-profile-edition`.
- Mantenha o nome curto e descritivo, sem frases longas ou excessivamente genéricas.
- Prefira um padrão consistente entre branches, commits e PRs do mesmo projeto.
- Use o prefixo adequado ao tipo de mudança, não apenas um nome genérico.
- Quando possível, inclua o contexto do módulo, funcionalidade ou problema em uma descrição objetiva.

## Boas Práticas para Branches, Commits e PRs

- Branch: `prefix/descricao-curta`
- Commit: `prefix: descricao curta em presente` ou `prefix: descricao-curta`
- PR: usar o mesmo prefixo da mudança, com título claro e objetivo, por exemplo: `feat: adicionar login social`

## Checklist de Validação

Antes de finalizar qualquer branch, commit ou PR, confirme:

- O prefixo está correto para o tipo de alteração.
- O nome está em kebab-case.
- Todas as letras estão em minúsculas.
- Não há acentos, espaços ou underscores.
- A descrição reflete a intenção real da mudança.
- O nome é claro para qualquer pessoa do time entender rapidamente o contexto.
