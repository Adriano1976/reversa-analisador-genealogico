# Interface: `POST /` com `action=triangulacao_analysis`

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Tipo: HTTP (formulário HTML → render de página)
> Confidência: 🟢 CONFIRMADO

## 1. Quando existe

Caminho **sem árvore**: o operador envia só o CSV de triangulação e recebe o bloco de grupos. É o `RF-18`.
A ação é despachada **antes** da resolução da árvore (`_ACOES_PRE_ARVORE`), porque o formulário de DNA exige
árvore e raiz e este não exige nenhuma das duas.

## 2. Requisição

```http
POST / HTTP/1.1
Content-Type: multipart/form-data; boundary=...
Cookie: session=...
```

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| `action` | texto | sim | Literal `triangulacao_analysis` |
| `triangulacao_csv` | arquivo | sim | CSV no formato consolidado de pares; gravado pela mesma porta do CSV de matches, com a mesma regra de reenvio |
| `gedcom_filename` | texto | não | Ignorado nesta ação; presente ou não, o resultado é o mesmo |

**Sem listagem nesta ação.** Na v1 o campo é só de arquivo: a lista da tela é particionada por extensão
(`.csv` → aba de DNA), e um seletor ofereceria o arquivo de triangulação como se fosse lista de matches.
Decisão `D-06` no `roadmap.md`.

**Limite de corpo:** 16 MB, com `413` e mensagem em português (regra vigente da borda).

**Sessão:** obrigatória. Sem sessão, a resposta é o redirecionamento de entrada, como em qualquer rota da tela
(feature 051).

## 3. Resposta de sucesso

`200 OK`, HTML da tela com:

| Contexto | Conteúdo |
|----------|----------|
| `grupos` | Lista de grupos classificados, **sem desfecho**: cada um com cromossomo, faixa de interseção em pb, cM mínimo e máximo dos pares, e membros com nome e kit |
| `triangulacao_sem_arvore` | `True` — o template usa para declarar que o desfecho depende da árvore |
| `message` | `"N grupos de triangulação encontrados."` ou o texto de nenhum grupo |

O bloco nasce **aberto** e **antes** dos cartões. Não há cartão, cM de match, caminho nem veredito nesta
resposta.

## 4. Erros

| Situação | Resposta | Corpo |
|----------|----------|-------|
| Arquivo ausente ou vazio | `200` com `success=False` | `"Nenhum arquivo de triangulação enviado."` |
| Colunas de par ausentes (é um CSV de matches) | `200` com `success=False` | Recusa **nomeando o campo correto** ("este arquivo é de matches; use o campo 1 da análise de DNA") |
| Build não declarado no cabeçalho | `200` com `success=False` | Texto que diz qual declaração falta (`RN-10`) |
| Nenhum grupo fechado | `200` com `success=True` | `"Nenhum grupo de triangulação: as sobreposições não fecham."` |
| Arquivo ilegível em todas as tentativas | `200` com `success=False` | Mensagem de `CsvIlegivel`, listando as tentativas |
| Corpo acima de 16 MB | `413` | Mensagem de corpo grande vigente |

**Não há `404`** nesta ação: não há referência de arquivo a resolver.

## 5. Idempotência

Reenviar **o mesmo conteúdo** produz o mesmo resultado e não duplica arquivo: a chave é o sha256 do conteúdo
(`ADR-17`), e o desfecho do armazenamento é `identico`. Reenviar conteúdo **diferente** com o mesmo nome
visível substitui a versão anterior (`RN-17`), que vai para `_aposentados/`.

## 6. Timeouts e limites

| Item | Valor |
|------|-------|
| Timeout do servidor | o vigente do waitress; a ação não define timeout próprio |
| Limite de grupos | 200, com truncamento declarado na tela (`D-08`) |
| Tamanho de arquivo | 16 MB (limite de borda) |
| Chamadas externas | nenhuma |
