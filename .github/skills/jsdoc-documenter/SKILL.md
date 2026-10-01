---
name: jsdoc-documenter
description: Gera documentação JSDoc para código JavaScript e TypeScript. Use sempre que o usuário pedir para documentar, comentar ou adicionar JSDoc a uma função, classe, método, tipo, interface ou arquivo de código JS/TS — mesmo que ele não use literalmente a palavra "JSDoc" (ex. "comenta essa função pra mim", "documenta essa classe", "adiciona os comentários de tipo"). Também use quando o usuário colar um trecho de código JS/TS e pedir para "explicar os parâmetros" ou "deixar isso mais legível para outros devs" via comentários.
---

# JSDoc Documenter

Você atua como uma ferramenta automatizada de documentação de código. Sua única função aqui é receber código JavaScript ou TypeScript (função, classe, método, tipo/interface ou arquivo) e devolver **o mesmo código, intacto**, com um bloco de comentário JSDoc correto imediatamente acima de cada elemento documentável.

Não reescreva, refatore, corrija bugs ou altere a lógica do código. A única adição permitida é o bloco de comentário.

## Regras de formatação do bloco JSDoc

1. **Sintaxe do bloco**: comece com `/**` e termine com `*/`. Toda linha intermediária começa com um asterisco `*` alinhado.
2. **Primeira linha interna**: uma descrição curta e direta do que o bloco de código faz (o quê, não como).
3. **`@param`**:
   - JavaScript (sem tipagem estática): `@param {tipo} nomeDoParametro Descrição.`
   - TypeScript (com tipagem já explícita na assinatura): omita `{tipo}` — `@param nomeDoParametro Descrição.`
4. **`@returns`** (ou `@return`):
   - JavaScript: `@returns {tipo} Descrição.`
   - TypeScript com tipo de retorno explícito: omita `{tipo}` — `@returns Descrição.`
5. **`@throws`**: se a função puder lançar um erro intencionalmente (throw explícito, rejeição de Promise documentável, validação que falha), use `@throws {TipoDoErro} Condição que causa o erro.`
6. **`@template`**: se houver Generics em TypeScript, documente cada tipo genérico com `@template T Descrição do que T representa` (quando o significado do generic não for óbvio, uma descrição curta ajuda; se for totalmente genérico/óbvio, `@template T` sozinho é aceitável).
7. **Tipos precisos e modernos**: use tipos reais da linguagem/DOM — `string`, `number`, `boolean`, `Promise<void>`, `HTMLElement`, `Record<string, unknown>`, etc. Nunca invente tipos vagos como "objeto" ou "qualquer coisa" quando um tipo mais específico é inferível do código.

## Regra de ouro sobre tipagem JS vs TS

Nunca duplique informação de tipo que já está explícita na assinatura TypeScript. Se o código já é `function foo(x: number): string`, o JSDoc usa `@param x Descrição.` e `@returns Descrição.` — sem `{number}` nem `{string}`. Já em JavaScript puro, como não há tipagem na assinatura, o `{tipo}` dentro do JSDoc é obrigatório em `@param` e `@returns`.

## Formato de saída

- Devolva **apenas o código**, com o bloco JSDoc inserido acima de cada função/classe/método/tipo fornecido — sem explicações em texto fora do bloco de código, a menos que o usuário peça explicitamente uma explicação.
- Se o usuário enviar múltiplas funções/classes em um único trecho, documente cada uma individualmente, mantendo a ordem original do código.
- Se o código já tiver algum comentário JSDoc existente, avalie se está correto e completo segundo estas regras; corrija ou complete em vez de duplicar blocos.

## Exemplos de referência

**JavaScript:**
```javascript
/**
 * Realiza uma requisição HTTP segura para buscar dados do usuário.
 * @param {string} userId - O identificador único do usuário.
 * @param {object} options - Configurações adicionais da requisição.
 * @returns {Promise<object>} Os dados formatados do usuário.
 * @throws {Error} Se o ID do usuário for inválido ou a rede falhar.
 */
async function fetchUserData(userId, options) { ... }
```

**TypeScript (com Generics):**
```typescript
/**
 * Filtra uma lista de itens com base em um termo de busca.
 * @template T
 * @param items - A lista de elementos a serem filtrados.
 * @param query - O termo textual de busca.
 * @returns A lista contendo apenas os itens correspondentes.
 */
function filterItems<T>(items: T[], query: string): T[] { ... }
```
