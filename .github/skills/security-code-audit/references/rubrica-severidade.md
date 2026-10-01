# Rubrica de severidade

Use esta rubrica para que crítica/alta/média/baixa não varie de critério
entre execuções diferentes da skill. Classifique pelo **pior cenário
realista** de exploração, considerando impacto e facilidade de exploração
juntos — não só um dos dois.

## Crítica
Compromete dados ou controle de **múltiplos usuários/tenants** ou do sistema
inteiro, e é explorável por um atacante com acesso mínimo (não autenticado,
ou autenticado como usuário comum sem privilégio especial).
Exemplos: vazamento cross-tenant em massa, segredo que permite forjar
autenticação, RCE, autopromoção a admin sem nenhuma barreira.

## Alta
Compromete dados ou uma ação sensível de **outro usuário específico**
(não em massa), ou exige um passo a mais de exploração (ex: conhecer/enumerar
um ID), mas ainda assim está ao alcance de um usuário autenticado comum.
Exemplos: IDOR pontual (ler/alterar/deletar recurso de outro usuário),
checagem de papel ausente em uma ação administrativa isolada.

## Média
Exploração exige uma condição adicional não trivial (feature flag específica,
configuração fora do padrão, informação que normalmente não é pública), ou o
impacto é limitado (ex: XSS refletido que exige interação da vítima, vazamento
de metadado não sensível).

## Baixa
Risco real mas de impacto limitado ou defesa em profundidade ausente onde já
existe outra camada de proteção compensando parcialmente. Vale a pena
corrigir, mas não é urgente.

## Informativa
Não é uma vulnerabilidade por si só, mas é um ponto de atenção — prática que
pode virar risco se outra coisa mudar (ex: falta de validação de startup para
uma variável que hoje sempre é definida corretamente no deploy, mas não tem
proteção formal).

## Condições de exploração
Sempre que a severidade depender de uma condição (feature flag ligada, config
insegura, ausência de outra camada), registre essa condição explicitamente no
campo `condicoes_exploracao` do achado — isso é o que diferencia, por
exemplo, uma crítica de uma média para o mesmo tipo de falha.
