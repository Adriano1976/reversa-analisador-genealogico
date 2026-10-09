# Roadmap: Uploads fora do repositório

> Identificador: `010-uploads-fora-do-repositorio`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/010-uploads-fora-do-repositorio/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Esta é uma feature de **operação e de instrumento**, não de código de aplicação. **Nenhum arquivo de
`src/` é tocado:** a pasta continua resolvida por `_pasta_uploads()` (`src/app.py:103-118`), com o
padrão `<diretório do app>/uploads` e a sobreposição por `ANALISADOR_UPLOAD_FOLDER` que já existem, e
o adaptador continua congelando o caminho no import (`src/app.py:129`). O delta tem quatro frentes:
(a) o operador aponta a pasta canônica nos dois modos de execução, e ela vive fora do repositório;
(b) a composição de contêineres passa a montar essa pasta do host no alvo interno que o app já deriva;
(c) o harness de paridade passa a ser executado por um **invólucro** que define a pasta de upload antes
de lançar o instrumento — hoje o coletor candidato escreve na pasta real do operador, e é essa a origem
medida do resíduo; o `harness.py` **não** é editado, para que o instrumento de medição continue byte a
byte o mesmo; (d) entra uma ferramenta de manutenção com dois verbos, `migrar` (cópia verificada por
`sha256`, idempotente) e `expurgo` (manifesto, simulação e aplicação com relatório). A migração é
**cópia, nunca movimento**: as 36 entradas e 27.932.474 bytes permanecem na origem, e é essa garantia
que dá ao operador o direito de apagar a pasta do repositório depois, por decisão própria.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Dados reais de DNA/GEDCOM nunca entram no versionamento | A feature **serve** o princípio: com a migração verificada, o dado sai da árvore do repositório, e os testes da ferramenta usam arquivos sintéticos em pasta temporária. **Conflito declarado, não escondido:** sob a resposta 1a o *padrão do código* continua apontando para dentro do repositório; o que protege o princípio é a regra de ignore (`.gitignore` cobre `uploads/` em qualquer profundidade) e o procedimento documentado, não o código | respeita |
| II. Comportamento observável é preservado em refatoração | A troca de raiz e a correção do instrumento são **organizacionais**: a paridade tem de continuar 100 % e as análises têm de produzir os mesmos resultados. O único comportamento novo é a ferramenta de manutenção, acionada à mão | respeita |
| III. Nenhuma mudança sem teste que a cubra | Cada peça nova chega com teste: a ferramenta (simulação, manifesto, aplicação, relatório), o redirecionamento do coletor e a presença da variável na tabela do `README.md` | respeita |
| IV. Arestas do grafo são tipadas | Não se aplica: nenhum arquivo de `src/core/` é tocado | não se aplica |
| V. Toda suposição de genealogia genética cita a fonte | Não se aplica: nenhum número de cM, faixa ou heurística é alterado | não se aplica |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Existe **um** destino canônico, fora do repositório, declarado uma vez e usado pelos dois modos (`RF-08`) | Com 1a e 3b há dois pontos de configuração; sem caminho único, alternar entre modos invalida a referência de uma página aberta | (a) `%TEMP%`; (b) manter a pasta dentro do repositório; (c) dois destinos distintos por modo | 🟢 |
| D-02 | No contêiner, a pasta canônica do host é montada no alvo que o app **já deriva** (`/app/src/uploads`), sem variável de ambiente adicional dentro do contêiner | Menos pontos de configuração, que é o que `RF-08` pede; o comentário do `docker/Dockerfile` continua verdadeiro ao afirmar que escrita e leitura usam o caminho derivado de `__file__` | (a) montar em `/app/uploads` e declarar `ANALISADOR_UPLOAD_FOLDER` no serviço — cria o segundo ponto de configuração; (b) volume nomeado — perde o acesso direto recusado em 3b | 🟢 |
| D-03 | A ferramenta de manutenção mora em `tests/`, com um teste que a exercita, seguindo o padrão de `tests/icone_de_atalho.py` (feature 009) | `.reversa/reversa-config.json` libera `tests/**` e **não** libera pasta nova como `scripts/**`. Compromisso declarado: um utilitário de operador em `tests/` é semanticamente estranho, e o docstring precisa dizer por que ele está ali | (a) `src/tools/**` — `docker/Dockerfile` copia `src/` inteiro, então a ferramenta viajaria na imagem; (b) pedir ao operador que acrescente `scripts/**` ao `reversa-config.json` — adiável, e é ato exclusivo dele | 🟡 |
| D-04 | `migrar` **copia** com conferência de `sha256` arquivo a arquivo, é idempotente e nunca remove a origem (`RF-07`, 2a) | É o que torna seguro apagar a pasta antiga depois; e a origem só sai por decisão manual do operador | (a) mover; (b) copiar sem verificar; (c) cópia manual documentada apenas | 🟢 |
| D-05 | `expurgo` opera por **manifesto** gerado por comando, com nome, `sha256` e motivo por arquivo; a aplicação remove só o que está nele (`RN-06`, 4a) | Um critério por padrão de nome ou por data não distingue resíduo de dado real — e a pasta contém nomes de fixture de instrumento porque recebeu uploads feitos por instrumentos | (a) padrão de nome; (b) janela de data; (c) remoção direta sem manifesto | 🟢 |
| D-06 | Cópias byte a byte idênticas são **relatadas e preservadas** (5a) | Três arquivos com o mesmo `sha256` convivem com um quarto de mesmo tamanho e conteúdo distinto; qualquer heurística barata (tamanho) erraria, e a cara (hash) ainda exige decisão humana sobre qual cópia fica | (a) deduplicar automaticamente mantendo uma | 🟢 |
| D-07 | O isolamento do instrumento é obtido por um **invólucro** em `tests/` (`rodar_paridade.py`) que define `ANALISADOR_UPLOAD_FOLDER` para uma pasta descartável e só então invoca o harness; o `harness.py` **não** é editado | **Medido:** o harness lança os coletores com `env = dict(os.environ, …)` (`_reversa_sdd/parity/harness.py:465`), então a variável definida antes da chamada chega ao coletor candidato, que importa o app (`:356`) e tem a pasta resolvida no import. Manter o instrumento byte a byte igual preserva o valor metodológico da medição e evita a questão de política sobre editar `_reversa_sdd/**` | (a) editar o `harness.py` para se auto-isolar — o precedente `_reversa_refactor/analise-dna/opportunities/OPP-20261008-JXQN-legado-de-cm-fora-do-fluxo.md:158` registra esse caminho como "**exige editar `_reversa_sdd/**`, que não está liberado**"; e o instrumento congelado é o que dá sentido à paridade; (b) confiar apenas na disciplina de definir a variável à mão antes de cada execução | 🟢 |
| D-08 | A prova de que `src/` não mudou é um `diff` vazio, registrado como evidência | É o que separa esta feature de um refactor de código e o que sustenta `RF-03` sem depender de afirmação | (a) declarar sem medir | 🟢 |

## 4. Premissas

| Premissa | Origem (`requirements.md`) | Risco se errada |
|----------|----------------------------|-----------------|
| O Docker Desktop consegue montar uma pasta do host **fora** do projeto | §9, resposta 3b | O modo contêiner cai para volume nomeado, e o operador perde o acesso direto pelo sistema de arquivos. A verificação é ação do `onboarding.md` §7, com recuo declarado 🟡 |
| A ferramenta pode morar em `tests/` sem violar a política de edição | §10, restrição de política | Se a política for lida como impeditiva, o operador acrescenta `scripts/**` ao `reversa-config.json`, ou a ferramenta vai para `src/tools/` e passa a viajar na imagem 🟡 |

Nenhuma premissa vem de `[DÚVIDA]` não resolvida: o documento chegou ao plano com **0** marcadores.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Armazenamento dos arquivos enviados | `_reversa_sdd/architecture.md#1`; `_reversa_sdd/upload-gedcom/contracts.md#2.2` | contrato-alterado | A raiz passa a ser, no uso declarado, uma pasta do host fora do repositório; a regra de resolução e o leiaute dos nomes **não** mudam |
| Composição de contêineres | `_reversa_sdd/c4-containers.md`; `_reversa_sdd/addenda/008-persistencia-postgres-docker.md#o-que-a-extração-não-precisa-mudar` | contrato-alterado | O ponto de montagem deixa de ser `./src/uploads` e passa a ser a pasta canônica do host, com o mesmo alvo interno |
| Documentação do operador | `_reversa_sdd/inventory.md#4`; `README.md` | contrato-alterado | A variável entra na tabela do `README.md`; o destino canônico e o procedimento entram no `onboarding.md`; afirmações que deixam de ser verdadeiras são corrigidas |
| Instrumento de paridade | `_reversa_sdd/inventory.md#7` (fora do escopo de runtime); `_reversa_sdd/parity/harness.py` | **sem mudança** | O instrumento permanece byte a byte igual; o isolamento da pasta vem do invólucro (D-07) |
| Ferramenta de manutenção e invólucro | — | componente-novo | `migrar`, `manifesto` e `expurgo` em `tests/manutencao_de_uploads.py`; execução da paridade por `tests/rodar_paridade.py` (D-03, D-07) |
| Borda HTTP, casos de uso, núcleo, template, adaptadores | `src/app.py`, `src/application/`, `src/core/`, `src/parsers/`, `src/reporting/`, `src/utils/`, `src/ports/`, `src/templates/` | **sem mudança** | Provado por `diff` vazio (D-08) |

## 6. Delta no modelo de dados

- **Banco: nada muda.** Nenhum campo, nenhuma tabela, nenhuma migração de schema. As colunas
  `tree_ref` e `match_file_ref` (`src/application/dna_analysis.py:234-235`) continuam resolvíveis
  porque guardam o **nome** derivado de conteúdo, e o nome é preservado na migração.
- **Disco:** 36 arquivos e 27.932.474 bytes ganham uma segunda cópia na raiz nova, com o mesmo nome; a
  origem permanece intacta.
- Detalhe completo em: `_reversa_forward/010-uploads-fora-do-repositorio/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo é afetado. A superfície HTTP — rota, campos de formulário, códigos de status e
mensagens — fica intacta, e isso é provado por `diff` (D-08), não afirmado. Por esse motivo **não há
diretório `interfaces/`** nesta feature: o que muda é contrato de **operação** (onde a pasta vive e
quem a configura), e ele é documental.

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| n/a — nenhum contrato externo afetado | — | n/a |

## 8. Plano de migração

O destino canônico proposto é `D:\dados-genealogicos\uploads` — fora da árvore do repositório e no
mesmo volume do projeto. O operador confirma ou troca o caminho no passo 1 do `onboarding.md`; a
decisão vale para os dois modos.

1. **Inventário de origem:** nome e `sha256` de cada um dos 36 arquivos, mais o total de bytes.
2. **Criar a pasta canônica** fora do repositório.
3. **`migrar --origem src/uploads --destino <canônico>`:** cópia com conferência de `sha256` arquivo a
   arquivo, idempotente, com relatório ao final.
4. **Conferir:** 36 nomes no destino, cada `sha256` igual ao da origem, origem intacta.
5. **Apontar os dois modos para o mesmo caminho:** variável de sessão no modo local; pasta canônica
   montada no alvo interno no modo contêiner (D-02).
6. **Provar continuidade:** envio da árvore → busca de caminho → análise de DNA, sem "arquivo não
   existe mais".
7. **Provar o isolamento do instrumento:** executar a paridade e conferir inventário idêntico na pasta
   real.
8. **Manifesto e expurgo:** gerar o manifesto, revisar, rodar a simulação e, só depois, aplicar.
9. **Passo manual do operador, fora desta feature:** apagar `src/uploads/` — só depois de 4 e 6
   verdes, e é ele quem decide.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Esquecer a configuração no modo local e voltar a gravar dentro do repositório, **sem erro visível** | médio | alta | Procedimento em primeiro plano no `onboarding.md`, com a conferência por inventário da pasta do repositório logo após o primeiro envio; a alternativa (aviso no arranque) exigiria mexer em `src/`, e por isso ficou fora desta rodada |
| Divergência entre os dois destinos, quebrando a continuidade de uma página aberta | médio | média | D-01 e `RF-08`: um caminho canônico só, com teste que verifica a presença da variável na tabela do `README.md` |
| Perda de arquivo durante a migração | alto | baixa | D-04: cópia (nunca movimento), conferência por `sha256` arquivo a arquivo, relatório de divergências, origem preservada |
| Interrupção no meio da cópia (Ctrl+C, queda) | baixo | média | D-04: idempotência — repetir a operação não duplica nem regrava o que já confere |
| O expurgo remover dado real por classificação errada | alto | baixa | 4a e D-05: manifesto revisável, simulação obrigatória, remoção restrita ao manifesto, recusa de link simbólico e de caminho fora da pasta alvo |
| O invólucro alterar o que a paridade mede | alto | muito baixa | O `harness.py` não é tocado (D-07); a paridade é medida **antes e depois** (100 % nos dois) e o inventário da pasta real é comparado. Nada é presumido |
| Alguém invocar `harness.py` direto, sem o invólucro, e voltar a sujar a pasta real | médio | média | O `README.md` e o `onboarding.md` declaram `tests/rodar_paridade.py` como o caminho de execução; o sintoma é reconhecível de imediato pelo inventário, porque os nomes de sonda reaparecem |
| Montagem de pasta do host fora do projeto não funcionar no Docker Desktop | médio | média | Verificação explícita no `onboarding.md` §7, com recuo para volume nomeado declarado na hora — e o operador decide |
| A ferramenta em `tests/` ser confundida com teste ou removida numa limpeza | baixo | média | D-03: docstring explicando o porquê, entrada no `README.md` e teste próprio no mesmo diretório |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `diff` de `src/` vazio (D-08)
- [ ] Inventário por `sha256` idêntico entre origem e destino: 36 arquivos, 27.932.474 bytes
- [ ] Origem intacta após a migração, com os mesmos hashes
- [ ] Paridade medida em **100 %** pelo invólucro, com o `harness.py` byte a byte idêntico (D-07)
- [ ] Inventário da pasta real idêntico antes e depois de uma execução completa da paridade (`RF-04`)
- [ ] Simulação do expurgo não remove nada; a aplicação remove apenas o que está no manifesto e relata o resto
- [ ] A tabela de variáveis do `README.md` lista `ANALISADOR_UPLOAD_FOLDER`
- [ ] `regression-watch.md` gerado
- [ ] Nenhum arquivo do operador foi removido em nenhum passo desta feature

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-plan` | reversa |
