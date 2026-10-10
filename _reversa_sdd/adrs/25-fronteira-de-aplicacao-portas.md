# ADR-25 — Fronteira de aplicação: quatro portas e resultado tipado

- **Status:** Aceito e **vigente**
- **Data da decisão:** 2026-10-07
- **Commit(s):** `ea3a0c3` (abre o ciclo `006-fronteira-aplicacao-ports`), `cb7232e`, `cc875c1`, `f775045`, `1c108dc`, `6ad74a3`, `7676b99`, `ffa835e`, `3758f46`
- **Confiança:** 🟢 CONFIRMADO

## Contexto

Depois do `ADR-24`, o núcleo estava puro — e a **rota** tinha herdado tudo o que o núcleo deixou de fazer: resolver caminho, parsear, escolher entre candidatos, montar mensagem. Os dois defeitos concretos que a decisão ataca:

1. **A rota montava o texto de erro.** Um `except Exception` genérico produzia `"Ocorreu um erro: {e}"`, o que impedia distinguir, sem ler o texto, uma entrada inválida de uma falha inesperada. O `RF-20` proíbe que o **literal de tela** tenha autoridade semântica.
2. **O núcleo importava a borda.** `core/dna_analysis.py` importava `parsers/csv_ingest` e `reporting/mermaid_render`, e `reporting/mermaid_render.py` importava `core` — dois ciclos de pacote.

## Decisão

Criar a **camada de aplicação** (`src/application/`) e a **fronteira de portas** (`src/ports/`):

1. **Um caso de uso por fluxo** — `upload_gedcom`, `path_search` e `dna_analysis` —, que **orquestra e não decide** regra: limiar, peso, ordem de avaliação e critério de matching continuam no núcleo.
2. **Quatro portas como `Protocol`**: `ArmazenamentoDeArquivos` (4 métodos), `CarregadorDeArvores` (1), `RepositorioDeArvores` (2, **declarado sem implementação e sem consumidor**) e, depois, `RegistroDeAnalises` (1, do `ADR-27`).
3. **Resultado tipado** na travessia: campos nomeados, sem nome de campo de template, sem o parâmetro `success=` e sem dicionário de contexto.
4. **Erros de domínio tipados** (`core/erros.py`) com raiz `ErroDeDominio`, e uma **tabela de tradução** (`application/traducao.py`) que converte tipo em mensagem e status.
5. **A casca `load_gedcom_and_build_graph` é removida** (`1c108dc`): `carregar_arvore` passa a ser o único ponto que parseia.

## Evidência

- `src/application/` existe com `__init__.py` (59), `dna_analysis.py` (294), `path_search.py` (79), `reenvio.py` (74), `traducao.py` (135) e `upload_gedcom.py` (104 linhas cruas).
- `src/ports/__init__.py` declara os quatro `Protocol` e os cinco tipos de payload; `src/ports/adaptadores.py` traz as três implementações concretas.
- **A guarda de dependências tem teste:** `tests/test_dependencias_nucleo.py` (254 linhas úteis) cobra que o núcleo não importe `parsers/` nem `reporting/`.
- `traducao.py` mapeia os cinco tipos para `(mensagem, status)`; a **coluna de status não tem consumidor** nesta onda (`RN-05`) e isso está declarado no próprio módulo.
- Os **literais foram medidos**, não deduzidos: a sonda `evidence/probe_mensagens_antes.py` registrou que três das condições nascem **dentro** do fluxo de DNA e por isso levam o prefixo `"Ocorreu um erro: "`, enquanto a recusa de conteúdo do GEDCOM nasce no caminho de gravação e **sai sem prefixo**.

## Justificativa

Uma fronteira explícita é o que permite a Onda 3 existir sem reescrever o núcleo: o `RepositorioDeArvores` está **declarado e vazio** exatamente para dar lugar tipado onde a persistência vai encaixar. E o `ErroDeDominio` herdando de `ValueError` é deliberado: sem a herança, quatro asserções que a suíte já escrevia quebrariam — a feature que existe para **preservar** comportamento seria a que o quebraria.

## Consequências

- 🟢 **O literal de tela deixou de ter autoridade semântica.** O `ADR-33` é a consequência direta para a busca.
- 🟡 **A tradução carrega uma assimetria de prefixo que veio do legado e foi preservada:** a recusa de conteúdo do GEDCOM sai sem `"Ocorreu um erro: "` e as demais com ele. Reproduzir o prefixo onde ele existia foi a escolha que manteve a paridade de tela.
- 🟢 **`CarregadorDeArvores` é uma quarta porta não prevista** no `requirements.md` da feature — declarada como desvio, e a razão é objetiva: sem ela, ou o caso de uso importaria o parser, ou cada ramo da rota repetiria a resolução de caminho. Ela tem **um único método**, e a `D-02` declara que **um segundo método significa que a decisão estava errada** e o auditor deve reabri-la.
- 🟡 **O status HTTP da tradução é superfície sem gatilho hoje.** Ele existe e está testado para que a regra de conversão exista em um lugar só quando a API nova chegar, em vez de ser redescoberta lá.
- 🟢 **A casca removida era um oráculo de comportamento duplicado** — a mesma classe de defeito que o `ADR-02` combateu.
