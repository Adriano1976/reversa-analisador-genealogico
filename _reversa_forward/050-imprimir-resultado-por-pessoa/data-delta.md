# Data delta: impressão do resultado por pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Modelo extraído: `_reversa_sdd/erd-complete.md` e `_reversa_sdd/data-dictionary.md`

## 1. Resumo

**Nenhum dado de domínio muda.** Não há campo novo, tabela nova, payload novo, índice, migração ou
retenção. A feature é de apresentação: o delta é de **DOM** (nós que o navegador recebe) e de
**folha de estilo** (regras de impressão). O modelo extraído continua válido byte a byte.

## 2. O que entra no DOM

| Nó | Onde | Atributos | Conteúdo | Visível na tela? |
|----|------|-----------|----------|------------------|
| `#area-de-impressao` | fim do `<body>`, antes dos scripts | `id`, `aria-hidden="true"` | vazio (recebe o clone em tempo de impressão) | não |
| `.imprimir-conexao` | cabeçalho de cada cartão, depois do "Voltar" | `type="button"`, `data-imprimir="resultado-N"`, `aria-label` com o nome da pessoa | texto "Imprimir" | sim |
| `.identificacao-da-impressao` | início do corpo de cada cartão | — | árvore, CSV, raiz e o lugar do momento da impressão | não |
| `.quando-da-impressao` | dentro da identificação | `class` | `<time>` vazio, preenchido no clique | não (oculto com o pai) |
| `.cartao-em-impressao` | raiz do clone | `class` | o cartão inteiro, com todos os `details` abertos | só na impressão |
| `.folha-do-diagrama` | fim do contêiner de impressão | `class` | título + o bloco de diagrama movido do clone | só na impressão |
| `.origem-da-impressao` | dentro do clone | `class` | origem repetida em toda folha | só na impressão |

**Campos de identificação e origem:**

| Campo | Valor | Fonte no contexto |
|-------|-------|-------------------|
| Árvore | referência armazenada (`chave__rótulo.ext`) | `gedcom_filename` (`src/app.py#L566`) |
| CSV | referência armazenada do CSV usado | `csv_filename_usado` (`src/app.py#L576`) |
| Raiz | o nome que o operador digitou | `root_name_usado` (`src/app.py#L575`) |
| Momento | data e hora do clique em "Imprimir" | `new Date()` no script |

## 3. Variáveis de template

**Nenhuma variável nova.** As três usadas já estão no render do resultado desde antes desta feature.
Consequência deliberada: o contexto não muda, a paridade não pode divergir por causa desta feature e
o `_reversa_sdd/` não ganha estrutura nova.

## 4. Classes e tokens de folha de estilo

| Classe / token | Papel | Onde nasce |
|----------------|-------|------------|
| `.imprimir-conexao` | comando no cabeçalho | `index.html`, dentro de cada cartão |
| `.identificacao-da-impressao` | bloco de identificação (oculto na tela) | idem |
| `.quando-da-impressao` | lugar do momento da impressão | idem |
| `#area-de-impressao` | contêiner do clone | idem |
| `.cartao-em-impressao` | raiz do clone | script |
| `.folha-do-diagrama` | página própria do desenho | script |
| `.origem-da-impressao` | rodapé repetido | script (no clone) |
| `body.imprimindo` | marca a impressão em curso | script |
| `--bg`, `--surface`, `--surface-2`, `--ink`, `--head`, `--muted`, `--line`, `--primary` | tokens redeclarados no tema claro dentro do contêiner | `app.css`, `@media print` |

## 5. Persistência e banco

**n/a.** Nenhuma tabela, coluna, índice, `INSERT`, consulta ou migração. O PostgreSQL opcional
(`init.sql`) não é tocado; nenhuma estrutura entra no `erd-complete.md`.

## 6. Impacto na projeção e no núcleo

**n/a.** `projetar_analise`, `AnaliseParaRegistrar` e o adaptador `RegistroDeAnalises` não mudam. O
cartão impresso mostra exatamente o retorno que a análise já produzia (`RN-05`).

## 7. Impacto na paridade

**Nenhum.** O harness substitui o render por captura de **contexto** (`parity/harness.py#L191`), e o
contexto não ganha nem perde chave. A comparação de domínio deve continuar idêntica.

## 8. Migração

**n/a.** Não há dado a migrar. O que muda de tamanho é o documento renderizado — o `SHA_DA_TELA`
passa por uma nova medição declarada, o que é registro de mudança, não migração.

## 9. Checklist de dados

- [ ] Nenhuma estrutura nova em `_reversa_sdd/erd-complete.md` ou `data-dictionary.md`
- [ ] Nenhuma mudança em `init.sql`
- [ ] Contexto de render idêntico (só template e folha mudam)
- [ ] Nenhum dado pessoal novo exposto no documento (`RN-06`)
- [ ] Nenhum artefato de impressão gravado no repositório (Princípio I)
