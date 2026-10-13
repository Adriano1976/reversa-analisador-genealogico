# Checklist de Validação — Auditoria de Segurança
**Projeto:** reversa_analisador_genealogico
**Repositório:** https://github.com/Adriano1976/reversa-analisador-genealogico
**Origem:** run-1 da auditoria de código (architecture.md, NEEDS-VALIDATION.md, FINDINGS-DETAIL.md)
**Ref. de origem:** branch `master`, commit `0620bcd2690259c17066295aafc8c4f90c30be39`

## Leia antes de começar

- Nenhum dos 9 itens abaixo é uma falha **confirmada**. São leads (`needs_validation`) levantados só pela leitura do código — ninguém executou o app nesse run.
- Use **sempre dados fictícios/sintéticos** nos testes (GEDCOM e CSV de teste, nunca os reais do operador).
- Rode os testes num ambiente isolado (cópia scratch, sem rede externa quando possível).
- Marque o `Status` de cada item conforme for validado ou corrigido.

## Visão geral e prioridade sugerida

| # | Item | Prioridade | Esforço de correção | Só é crítico se... |
|---|------|-----------|---------------------|---------------------|
| 5 | Scripts de terceiros sem integridade (SRI/CSP) | **Alta** | Baixo | sempre |
| 6 | Sem proteção contra clickjacking | **Alta** | Baixo | sempre |
| 8 | Mensagens de erro vazam detalhes internos | **Alta** | Baixo/Médio | sempre |
| 9 | Erro do banco vaza detalhes internos | Média | Baixo | usa Postgres |
| 7 | Nome de arquivo malicioso (reservado/Windows) | Média | Médio | sempre, mais grave no Windows |
| 3 | Parse da árvore sem cache/limite | Média | Médio/Alto | árvores grandes |
| 4 | Análise de DNA sem limite | Média | Médio/Alto | CSVs grandes |
| 1 | Sem proteção CSRF | Baixa* | Médio | app exposto além de localhost |
| 2 | Sem autenticação/autorização | Baixa* | Alto | app exposto na rede |

\* Itens 1 e 2 são baixa prioridade **enquanto** o app rodar só em `127.0.0.1`. Se o app for exposto em rede (`ANALISADOR_HOST=0.0.0.0` ou LAN), reclassificar ambos como **Alta** antes de expor.

---

## Detalhamento por item

### 1. `POST /` sem verificação de origem (CSRF)
**Status:** [ ] não verificado

- **Fingerprint da auditoria:** `src/app.py:POST-/-no-origin-or-token-binding-on-state-changing-form`
- **Localização:** `src/app.py:506-509`, `:517-519`; `src/ports/adaptadores.py:85`, `:215`; `src/templates/index.html:68`
- **Problema:** a única rota que muda estado (`GET|POST /`) não lê `Origin`, `Referer` nem token algum antes de aplicar upload ou "aposentar arquivo".
- **Teste seguro:** com app rodando sobre dados fictícios, servir uma página HTML local que dispara um POST cross-site (form e fetch multipart) para o endereço loopback com um arquivo de teste começando com `0 HEAD`. Observar se é aceito e se o "aposentar" funciona sem interação no app.
- **Correção sugerida:** validar `Origin`/`Referer` e/ou adicionar token CSRF (ex.: Flask-WTF) nas duas ações de estado.

### 2. Sem autenticação ou autorização
**Status:** [ ] não verificado

- **Fingerprint:** `src/app.py:route-GET-POST-/-absent-identity-and-authorization-seam`
- **Localização:** `src/app.py:506`, `:498`, `:307`, `:553`; `src/ports/adaptadores.py:106`
- **Problema:** não existe identidade, sessão ou cookie. `DONO_DO_PROCESSO = "unico"` é ignorado por todos os adaptadores e o próprio código comenta que **não é mecanismo de segurança** (`src/app.py:76`, `:62`).
- **Teste seguro:** tentar acessar o app a partir de outro dispositivo/conta na mesma rede enquanto ele roda e registrar se o Host allowlist (`TRUSTED_HOSTS`) bloqueia ou não.
- **Correção sugerida:** só relevante se o app deixar de ser uso estritamente local. Antes de expor em rede, adicionar autenticação mínima (ex.: usuário/senha básica).

### 3. Árvore GEDCOM reprocessada do zero a cada requisição
**Status:** [ ] não verificado

- **Fingerprint:** `src/app.py:stored-tree-parse-per-request-no-deadline`
- **Localização:** `src/app.py:565`, `:307`; `src/ports/adaptadores.py:257`; `src/parsers/gedcom_parser.py:72`
- **Problema:** toda seleção de árvore, análise de DNA e busca de caminho reprocessa o `.ged` inteiro, sem cache e sem limite de tempo. Medição interna do próprio projeto registrou ~20,9s para a árvore real do operador (`_reversa_sdd/gaps.md:65`).
- **Teste seguro:** com árvore de teste grande, clicar a mesma árvore em 4 abas simultâneas e observar se o processo trava (o servidor só tem 4 threads por padrão).
- **Correção sugerida:** cachear a árvore já parseada em memória (invalidando no reupload) e/ou aplicar timeout no parse.

### 4. Análise de DNA sem limite de linhas/pool
**Status:** [ ] não verificado

- **Fingerprint:** `src/core/dna_analysis.py:per-row-surname-pool-fanout`
- **Localização:** `src/app.py:636`, `:651`; `src/core/dna_analysis.py:131`, `:210`, `:230`; `src/core/matching.py:92`, `:104`
- **Problema:** o custo cresce com (linhas do CSV) × (tamanho do grupo de sobrenomes parecidos), sem teto de linhas nem de pool de candidatos.
- **Teste seguro:** comparar tempo e memória entre o CSV real completo e uma versão cortada (poucas centenas de linhas) do mesmo CSV.
- **Correção sugerida:** definir um limite máximo de linhas aceitas por CSV e/ou um teto para o tamanho do pool fuzzy por correspondência.

### 5. Scripts de terceiros sem integridade (SRI) nem CSP
**Status:** [ ] não verificado

- **Fingerprint:** `templates.index.third_party_scripts_loaded_without_sri_or_csp`
- **Localização:** `src/templates/index.html:120`, `:823`
- **Problema:** bibliotecas JS carregadas de CDN sem atributo `integrity`/`crossorigin`; nenhum cabeçalho `Content-Security-Policy` é emitido.
- **Teste seguro:** abrir a página, inspecionar a aba Network do navegador (F12) e confirmar a ausência de `integrity=` nas tags `<script>` e do header CSP na resposta.
- **Correção sugerida:** adicionar `integrity="sha384-..."` + `crossorigin="anonymous"` em cada `<script src="https://cdn...">`, ou hospedar os arquivos localmente.

### 6. Página sem proteção contra clickjacking
**Status:** [ ] não verificado

- **Fingerprint:** `templates.index.state_changing_form_page_framable_without_frame_ancestors`
- **Localização:** `src/templates/index.html:58`, `:68`; `src/app.py:506`, `:553`
- **Problema:** nenhum header `X-Frame-Options` nem `frame-ancestors`; a página com o formulário destrutivo pode ser embutida num `<iframe>`.
- **Teste seguro:** criar uma página HTML local com `<iframe src="http://127.0.0.1:5000">` e ver se a aplicação carrega dentro dela.
- **Correção sugerida:** adicionar `X-Frame-Options: DENY` (ou `Content-Security-Policy: frame-ancestors 'none'`) nas respostas do Flask.

### 7. Nome de arquivo do cliente sem checagem de "arquivo regular"
**Status:** [ ] não verificado

- **Fingerprint:** `src/ports/adaptadores.py:guardar:destino-nao-verificado-como-arquivo-regular`
- **Localização:** `src/application/upload_gedcom.py:80`; `src/application/reenvio.py:70`; `src/utils/validate.py:101`; `src/ports/adaptadores.py:85`
- **Problema:** o nome enviado pelo navegador é concatenado ao nome final salvo. A sanitização cobre separadores, acentos e espaços, mas não nomes reservados do Windows (`CON`, `NUL`, `PRN`) nem `:` (alternate data streams em NTFS).
- **Teste seguro:** no Windows, enviar um `.ged` de teste nomeado `con.ged` ou `teste:1.ged` e confirmar que o arquivo salvo é um arquivo regular legível de volta (não um "sucesso" fantasma).
- **Correção sugerida:** adicionar testes automatizados (pytest) cobrindo nomes reservados e nomes com `:`; reforçar a sanitização conforme o resultado.

### 8. Mensagens de erro expõem texto de exceção cru
**Status:** [ ] não verificado

- **Fingerprint:** `app.exception_text_interpolated_into_rendered_page`
- **Localização:** `src/app.py:538` (upload), `:680` (DNA), `:710` (busca de caminho); `src/parsers/csv_ingest.py:167`
- **Problema:** três blocos "catch-all" colocam o texto da exceção direto na página, sem filtrar.
- **Teste seguro:** provocar um erro de propósito (GEDCOM truncado, CSV ilegível, pasta de upload sem permissão de escrita) e ler a mensagem exata exibida.
- **Correção sugerida:** trocar o texto da exceção por uma mensagem genérica na tela; logar o detalhe técnico só em arquivo de log local.

### 9. Erro do driver do banco de dados exposto na página
**Status:** [ ] não verificado

- **Fingerprint:** `app.persistence_failure_driver_text_rendered_in_page`
- **Localização:** `src/ports/adaptadores.py:311`; `src/application/dna_analysis.py:278`, `:283`; `src/app.py:666`; `src/templates/index.html:402`
- **Problema:** se a gravação no Postgres falhar, o nome do tipo de exceção e a mensagem do driver (psycopg2) aparecem no aviso exibido na página de sucesso.
- **Teste seguro:** parar o container/serviço do Postgres e rodar uma análise; ler o aviso de persistência retornado e ver se nomeia host, usuário ou outro detalhe interno.
- **Correção sugerida:** capturar a exceção e mostrar apenas "falha ao salvar histórico", guardando o detalhe técnico em log, não na resposta HTTP.

---

## Candidatos já descartados (não revalidar sem evidência nova)

Estes 5 pontos foram analisados e rejeitados no próprio run-1 — não são achados e não precisam de novo teste a menos que o código mude:

- Dois defeitos de resolução de unidade com nome vazio (bugs de correção, não falha de segurança, em ferramenta de operador único).
- Substituição automática no reenvio de arquivo (comportamento documentado e intencional).
- Esgotamento da cadeia de "aposentar arquivo" (design assumido de desistência; todos os bytes permanecem íntegros).
- Espelho de documentação publicado (não expõe credencial, dado pessoal nem caminho local da máquina).
