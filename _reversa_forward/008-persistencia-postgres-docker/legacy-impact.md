# Legacy impact: persistência histórica das análises em banco relacional

> Identificador: `008-persistencia-postgres-docker`
> Data: `2026-10-08`
> Âncora: **legado** — `_reversa_sdd/architecture.md` + `_reversa_sdd/domain.md`
> Rodada: **completa, com uma ação aberta.** `25` de `26` ações concluídas; `T026` **falhou o
> critério**, e a falha é do critério de desempenho, não da implementação — ver
> `evidence/T026-custo-da-gravacao.md`. Os repositórios de evidência estão em `evidence/`.

## Resumo

Esta feature tocou **cinco** arquivos do legado em `src/`, **um** em `tests/`, mais o
`requirements.txt` — e a natureza dos cinco primeiros é o que importa: **nenhum deles é do
núcleo**. `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` seguem **sem uma linha
alterada**, e é isso que sustenta a `RN-01` e a `RN-02`.

A persistência entrou como **porta na fronteira** e como **projeção no caso de uso**, com a
borda montando o registrador. Nenhuma regra de domínio foi reescrita; nenhuma constante
numérica mudou.

## Tabela de impacto

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|---|---|---|---|---|
| `src/ports/__init__.py` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | `contrato-novo` | **MEDIUM** | A **quarta** porta, `RegistroDeAnalises`, mais cinco tipos de payload. O payload é **dado plano**, para que o adaptador não precise conhecer o formato do resultado do núcleo (`D-01`, `D-15`). A tabela de portas do docstring passou de três para quatro entradas |
| `src/ports/adaptadores.py` | `_reversa_sdd/architecture.md#3` | `componente-novo` | **MEDIUM** | `RegistroDeAnalisesPostgres`. O `import psycopg2` é **preguiçoso**, e a razão é medida: o driver não está no `.venv/` do host, que é o interpretador da suíte e da paridade |
| `src/application/dna_analysis.py` | `_reversa_sdd/addenda/006-fronteira-aplicacao-ports.md` | `contrato-alterado` | **MEDIUM** | Recebe a porta e a referência da árvore; monta o payload por **projeção pura**; `ResultadoDeAnalise` ganha `aviso_de_persistencia` **com valor padrão**. As chamadas existentes continuam válidas sem alteração — que é o `RF-13` |
| `index()` em `src/app.py` | `_reversa_sdd/architecture.md#1` | `regra-alterada` | **MEDIUM** | Monta o registrador uma única vez, pela **regra dos três estados**, e repassa o aviso ao template. **Nenhum passo de domínio voltou para a rota**: persistir é I/O de borda, e a `RF-01` da feature 006 continua verdadeira |
| `src/templates/index.html` | `_reversa_sdd/architecture.md#1` | `regra-alterada` | **LOW** | Um bloco sob `{% if aviso_de_persistencia %}`, reusando a classe `.alerta-aviso` que já existia. **Não renderiza nada** quando o aviso é nulo, e é isso que preserva o contrato congelado de tela |
| `tests/test_porta_de_armazenamento.py` | *(infraestrutura de teste)* | `regra-alterada` | **MEDIUM** | ⚠️ **Um arame de tropeço da feature 007 disparou, e estava fazendo o trabalho dele.** O teste prende `adaptadores.__all__` numa lista literal e manda reabrir a decisão se um adaptador novo aparecer. A decisão foi reaberta: o `D-01` desta feature a declara. A lista ganhou o terceiro nome, a docstring registra por quê, e a **outra metade do teste segue intacta** — nenhuma classe implementa o par `guardar`/`obter` do `RepositorioDeArvores` |
| `requirements.txt` | `_reversa_sdd/dependencies.md#2` | `regra-alterada` | **LOW** | As diretas passam de **oito** para **nove** (`psycopg2-binary==2.9.13`). Nenhuma versão existente muda |
| `init.sql` (novo, raiz) | `_reversa_sdd/erd-complete.md#6` e `#7` | `delta-de-dados` | **MEDIUM** | **Seis tabelas** onde o modelo extraído tinha **27 estruturas e nenhuma**. Herda nomes e colunas do DDL do alvo e **nomeia** duas extensões que o alvo congelado não alcança (o veredito e os metadados de kit). Na execução, a coluna `detail` foi **removida**: ela era redundante com `comparison_detail` |
| `.dockerignore` (novo, raiz) | *(infraestrutura, fora da extração)* | `componente-novo` | LOW | Lista de **permissão**. Existe em parte para impedir que `src/uploads/` — o GEDCOM real de 5,3 MB — vá ao contexto de build (Princípio I), e em parte porque os 10 diretórios ilegíveis da raiz derrubariam o `docker build` (`D-18`) |
| `docker/Dockerfile` (novo) | `_reversa_sdd/architecture.md#2` | `componente-novo` | LOW | O contêiner de aplicação que a extração registrava como inexistente |
| `docker-compose.yml` (novo, raiz) | `_reversa_sdd/architecture.md#2` e `#6` | `componente-novo` | **MEDIUM** | Sobe banco e aplicação. Cria a **primeira integração de rede** do sistema, que a extração descrevia como "zero integrações de rede" |
| `tests/test_projecao_da_analise.py` (novo) | *(infraestrutura de teste)* | `componente-novo` | LOW | Prova a projeção **sem banco** — ela é pura. Fecha o achado `B003` da auditoria, que registrou que a projeção era a única parte central da feature sem teste independente de ambiente |
| `tests/test_persistencia_desabilitada.py` (novo) | *(infraestrutura de teste)* | `componente-novo` | LOW | Prende o estado desabilitado (`D-02`, `RF-13`) |
| `tests/test_persistencia_indisponivel.py` (novo) | *(infraestrutura de teste)* | `componente-novo` | LOW | Prende o estado de falha (`RN-13`, `RF-17`), na rota e no adaptador |
| `tests/test_registro_de_analises.py` (novo) | *(infraestrutura de teste)* | `componente-novo` | LOW | O teste do adaptador (`T014`). **Escrito e nunca executado** — ver "Lacunas declaradas" |

> `src/core/`, `src/parsers/`, `src/reporting/` e `src/utils/` **não aparecem nesta tabela
> porque não foram tocados.** A ausência é a informação: é ela que faz a `RN-01` ser
> verificável por `diff` em vez de por afirmação.

## Diff conceitual por componente

**A fronteira (`src/ports/`).** Ganhou a quarta porta e o adaptador dela. O que **não** mudou:
`ArmazenamentoDeArquivos`, `CarregadorDeArvores` e `RepositorioDeArvores` seguem com as
assinaturas que a feature 007 fixou, e o `RepositorioDeArvores` continua **declarado, sem
implementação e sem consumidor**. A porta nova é de outra coisa — ela guarda o **resultado**
da análise, não a árvore.

**O caso de uso (`src/application/dna_analysis.py`).** Passou a montar o payload da porta. A
projeção é **pura** e vive aqui, e não no adaptador: o adaptador recebe dado plano e só
escreve. Três decisões de projeção merecem registro, e nenhuma é recálculo de regra do
núcleo: os papéis do caminho são **derivados** do ancestral comum (o núcleo não os entrega);
o pareamento kit↔veredito é **por índice** e não por rótulo (dois kits de mesmo nome não se
confundem); e o estado por kit, quando o confronto termina antes de avaliá-lo, **herda o
estado final** em vez de inventar um por kit.

**A borda (`src/app.py`).** Ganhou a regra dos três estados e mais nada. A leitura de
`DATABASE_URL` acontece no import; a **conexão**, nunca.

## Preservadas

Todas as regras 🟢 do `_reversa_sdd/domain.md` seguem intactas, e agora isso é **verificável
por diff**: nenhum arquivo de `src/core/` foi tocado. As regras que a feature declara
preservar, e que a execução manteve:

| Regra | Onde vive | Como a execução a manteve |
|---|---|---|
| Os três eixos que não se contaminam | `core/dna_analysis.py`, `core/evidence_comparison.py` | `src/core/` sem uma linha alterada (`RN-01`) |
| O cM nunca é usado sozinho para afirmar parentesco | `core/evidence_comparison.py` | A projeção transporta `comparison_status`; não recalcula nada |
| O veredito em quatro estados, por kit, com junção conservadora | `core/evidence_comparison.py` | O estado da conexão vem do confronto; o por-kit vem do `per_kit` |
| A ordem de apresentação `(tem_caminho, −cM)` | `core/dna_analysis.py` | `result_ordinal` é a posição recebida, sem reordenação — há teste |
| `None` significa "não sei / não existe", nunca zero | todo o núcleo | Há teste: cM, meioses, MRCA, método e faixa ausentes ficam `None` |
| A chave de evidência é `(nome, kit)`, e kits nunca se somam | `core/genetic_evidence.py` | Há teste com dois kits de mesmo nome e cMs diferentes |
| O contrato de mensagens ao caractere | `core/` e `application/traducao.py` | A `message` é transportada; há teste de que ela não foi reescrita |
| A árvore é arquivo imutável sob chave de conteúdo | `src/uploads/`, `utils/validate.py` | O banco guarda a **referência**, não o arquivo (`RN-04`) |
| Single-tenant por aceite de risco, sem isolamento | `src/app.py` (`DONO_DO_PROCESSO`) | `owner_id` é coluna, e nenhuma consulta filtra por ele (`RN-10`) |
| A análise sob demanda, sem cache entre requisições | `src/app.py` | Nada lê o banco para decidir (`RN-12`) |
| A assinatura de retorno do núcleo | `core/dna_analysis.py` | ⚠️ **`W016` preservado**: o núcleo continua devolvendo a tupla de três, e o `Tree` continua com quatro elementos |

## Modificadas

**Nenhuma regra 🟢 foi alterada, removida ou enfraquecida.** O que mudou foi a **expectativa
de um teste**, e ela está registrada na tabela acima: o `T028` da feature 007 prendia a
superfície pública de `adaptadores.py` numa lista literal, e a lista mudou por decisão
declarada. A segunda metade daquele teste — a que prova que nenhum adaptador implementa o
`RepositorioDeArvores` — continua intacta e passando.

## Lacunas declaradas

1. **O `T014` nunca executou.** Ele está escrito e marcado com `skipif`, e é pulado porque o
   host não tem o driver e a suíte roda sem `DATABASE_URL`. **Um teste pulado não é um teste
   que passou**, e o `T022` tem de registrar os dois números da suíte lado a lado. A prova
   dos mesmos caminhos com o banco no ar é do `T020`.
2. **A coluna `detail` foi removida do `init.sql` depois de o banco já ter sido criado.**
   `CREATE TABLE IF NOT EXISTS` não altera tabela existente, então o volume do banco precisa
   ser **recriado** (`docker compose down -v`) antes do `T020` — não há dado a perder, porque
   nenhuma análise foi gravada ainda.
3. **O RNF de Desempenho continua sem medição.** O `T026` é quem mede, e ele depende do
   `T021`.

---

*Rodada de `/reversa-coding` de 2026-10-08: `T001`–`T025` concluídas, `T026` aberta por
critério não atendido. Suíte em **`282 passed, 8 skipped`**, contra `261 passed` da linha de
base — os 21 aprovados novos são os testes desta feature, e os 8 pulos são o `T014` e as seis
parametrizações dele. A persistência foi verificada ponta a ponta (`T020`) e na verificação
manual (`T021`).*
