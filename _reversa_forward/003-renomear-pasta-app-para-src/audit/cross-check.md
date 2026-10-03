# Cross-check: renomear a raiz da aplicação de `analisador-genealogico/` para `src/`

> Identificador da feature: `003-renomear-pasta-app-para-src`
> Data: `2026-10-02`
> Artefatos auditados:
> - `_reversa_forward/003-renomear-pasta-app-para-src/requirements.md`
> - `_reversa_forward/003-renomear-pasta-app-para-src/roadmap.md`
> - `_reversa_forward/003-renomear-pasta-app-para-src/actions.md`
> Auditoria estritamente leitora. Nenhum dos artefatos auditados foi alterado.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 6 |
| LOW | 5 |
| **Total** | **12** |

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | HIGH | Cobertura | A execução documentada da aplicação não é verificada por nenhuma ação, e a justificativa de D-06 afirma cobertura que a suíte não dá | `actions.md` (Fases 3-5), `roadmap.md#3` (D-06), `requirements.md#5` (RF-09) e `#7` (cenário 2) |
| A002 | MEDIUM | Sanidade do actions | T017 e T018 estão marcadas `[//]`, mas T017 grava resíduo dentro do diretório que T018 varre | `actions.md` (Fase 5, T017 e T018) |
| A003 | MEDIUM | Cobertura | O cenário de aceite do upload é verificado apenas por um teste que não roda neste ambiente | `requirements.md#7` (cenário 3), `roadmap.md#8` (passo 2), `actions.md` (T016) |
| A004 | MEDIUM | Consistência | O mesmo conceito aparece com quatro nomes diferentes entre os documentos | `requirements.md#1`, `requirements.md#4` (RN-01), `roadmap.md#1` e `#5`, `actions.md` |
| A005 | MEDIUM | Sanidade do actions | T020 atribui ao ciclo de codificação a publicação do adendo, que o próprio pipeline do framework roteia para o skill de convergência | `actions.md` (T020, T021), `roadmap.md#10` |
| A006 | MEDIUM | Cobertura | RF-01 tem ações de mutação, mas nenhuma ação verifica o estado final do arranjo físico | `requirements.md#5` (RF-01), `actions.md` (Fase 3 e Fase 5) |
| A007 | MEDIUM | Coerência com o legado | A remoção de dois arquivos herdados é autorizada pela política e decidida pelo usuário, mas a regra não-negociável do projeto continua redigida sem ressalva | `AGENTS.md` (Regra não-negociável), `requirements.md#9` (segunda passada), `actions.md` (T006) |
| A008 | LOW | Cobertura | Quatro requisitos não têm decisão numerada no roadmap | `requirements.md#5` (RF-03, RF-04, RF-05, RF-10), `roadmap.md#3` e `#8` (passos 6 e 7) |
| A009 | LOW | Cobertura | Seis decisões de não-ação não têm ação correspondente | `roadmap.md#3` (D-03, D-04, D-06, D-07, D-09, D-10) |
| A010 | LOW | Consistência | A contagem de pontos de alteração do requisito de testes segue imprecisa no texto do requisito, embora corrigida no plano | `requirements.md#5` (RF-03), `roadmap.md#3` (D-09) |
| A011 | LOW | Coerência com o legado | A documentação de extração aponta a pasta de upload para um símbolo que não existe mais no núcleo, e o adendo previsto não menciona essa citação | `_reversa_sdd/architecture.md#3.3`, `actions.md` (T020) |
| A012 | LOW | Sanidade do actions | T021 é executada por outro pipeline e, por isso, não é fechável dentro do ciclo de codificação | `actions.md` (T021) |

## Detalhamento dos findings HIGH

### A001 — a execução documentada da aplicação não tem verificação, e D-06 alega cobertura inexistente

**Impacto.** A decisão D-06 do roadmap justifica não criar teste novo com a afirmação: "A suíte já cobre o que um caminho errado quebraria: importação do aplicativo, `root_path` forçado e renderização da tela." Isso é verdade para o aplicativo **importado como módulo**, com o caminho de busca manipulado pelo próprio teste. Não é verdade para o aplicativo **executado como script**, que é o comando que a documentação publica e que o cenário de aceite descreve: nesse modo, o diretório do script passa a ser a primeira entrada do caminho de busca, e a importação do núcleo depende disso. São dois modos de execução distintos, e o segundo não é exercitado por nenhuma ação do plano.

A consequência prática é assimétrica: se o comando documentado quebrar, a suíte continua verde, o comparador de paridade continua em 100% e o critério de pronto fecha — porque nenhum gate olha para esse caminho. O defeito só apareceria para quem clonar o repositório e seguir a documentação.

**Direção da correção.** É correção humana, e há duas saídas legítimas: acrescentar manualmente uma ação de verificação ao `actions.md` (o skill que gera ações não é reexecutável sem reciclar IDs, então a via é edição manual), ou reabrir a decisão D-06 por `/reversa-clarify` caso se prefira cobrir o modo de execução com teste automatizado. Este relatório não executa nenhuma das duas.

## Detalhamento dos findings MEDIUM

### A002 — paralelismo marcado sobre recurso compartilhado

T017 tem como alvo um arquivo de evidência no diretório da feature, e T018 também. Pelo critério literal do eixo 4.2, elas não compartilham o **arquivo alvo** declarado, e por isso o marcador `[//]` é formalmente aceitável. Na prática, porém, o comparador de paridade grava resíduo dentro de `_reversa_sdd/parity/` — cópias dos coletores e arquivos de observação — e é exatamente esse diretório que T018 varre em busca de referência residual. Executadas em paralelo, a varredura pode encontrar o caminho antigo dentro de um artefato gerado pela própria execução vizinha, produzindo um falso positivo, ou ler o diretório no meio da geração. A direção é remover o marcador de paralelismo de uma das duas, ou declarar dependência de T018 para com T017.

### A003 — o gate do cenário de upload não é exercido neste ambiente

O cenário de aceite que verifica o ciclo de gravar e reencontrar o arquivo armazenado é coberto por um teste que está entre os 15 que falham por permissão de diretório temporário neste ambiente. O requisito está correto e a cobertura existe no papel; o que não existe é a **execução** dela. Como o mesmo cenário é o que protege o contrato mais sensível da feature (o arquivo precisa continuar sendo encontrado pela mesma chave depois da movimentação da pasta), vale registrar que a verificação depende de um ambiente com diretório temporário gravável.

### A004 — quatro nomes para o mesmo conceito

O conceito central aparece como "raiz da aplicação" e "diretório do código" no requirements (que os declara equivalentes), como "raiz de código" no roadmap e nas ações, e como "raiz de caminho" na regra RN-01 — sendo que este último é um conceito **diferente**, o de entrada do caminho de busca de módulos. Os dois primeiros são sinônimos aceitos; o terceiro não é sinônimo e pode ser lido como se fosse. A direção é fixar um único termo para o diretório e reservar "raiz de caminho" exclusivamente para a noção de importação.

### A005 — a publicação do adendo pertence a outro estágio do pipeline

T020 manda publicar o adendo, e T021 depende dela. No pipeline do próprio framework, a convergência da entrega na extração é trabalho de um skill posterior ao ciclo, e a matriz de roteamento trata "entrega concluída sem adendo" como estágio próprio. Do jeito que está, o critério de pronto desta feature inclui um item que o ciclo de codificação não fecha sozinho — o que não impede a execução, mas impede declarar a feature pronta ao final das 21 ações. A direção é mover T020 e T021 para o estágio de convergência ou aceitar explicitamente que o critério de pronto só fecha depois dele.

### A006 — RF-01 sem verificação de estado final

As ações T004 a T008 produzem o arranjo físico exigido pelo requisito, mas nenhuma delas verifica que o arranjo **resultante** é o esperado: existência da nova pasta de upload sob a nova raiz, arquivo de dependências na raiz, ausência dos três artefatos extintos. A varredura de T018 procura o nome antigo, o que é outra coisa. O critério de pronto lista esse item como caixa a marcar, mas sem ação que produza a evidência.

### A007 — regra não-negociável redigida sem a ressalva da política

A remoção de dois arquivos herdados foi decidida explicitamente pelo usuário e está registrada, com justificativa, na sessão de esclarecimentos; a autorização vem da política de edição do legado, que libera o caminho. O texto da regra não-negociável do projeto, porém, continua afirmando que arquivos pré-existentes do legado nunca são apagados, sem mencionar que a política pode autorizar o contrário. Um executor que leia a regra antes da política recusa T006. A direção é reconciliar a redação da regra — ato do mantenedor, não deste relatório.

## Itens verificados que passaram

### Cobertura

- Todos os 13 requisitos funcionais têm ao menos uma ação que os produz ou verifica, exceto pela lacuna de verificação registrada em A006.
- Os cenários de suíte, paridade, referência residual, resíduos removidos e vazamento de dado real têm ação correspondente e evidência declarada.
- Nenhum requisito funcional ficou fora do roadmap: os 13 aparecem citados por identificador.

### Consistência

- Todos os identificadores citados existem: RF-01 a RF-13 definidos na tabela de requisitos, D-01 a D-10 definidos no roadmap, T001 a T021 definidos nas tabelas de ações. Nenhum identificador fantasma.
- As 20 dependências declaradas apontam para identificadores existentes e todos são de numeração anterior, o que também descarta ciclo.
- O diretório de contratos externos foi corretamente omitido, e o roadmap declara a omissão em vez de deixar seção vazia.
- Todas as âncoras de documentação de extração citadas existem nos arquivos correspondentes (`architecture.md#1`, `#3.3`, `#5`, `#6`; `dependencies.md#1`; `inventory.md#2`, `#4`; `code-analysis.md#1`; `domain.md#4.1`, `#7`).

### Coerência com o legado

- Nenhuma decisão do roadmap contradiz regra confirmada do modelo de domínio. Os cinco princípios do projeto foram avaliados um a um e nenhum conflita.
- Todos os componentes citados existem no legado: arquivo de entrada, pacote do núcleo, pasta de upload, e os diretórios de instrumentação.
- O contrato do upload permanece preservado: a chave derivada do conteúdo não muda com a movimentação, e o adendo vigente do defeito de upload sustenta essa leitura.
- Ponto favorável verificado: a remoção, já commitada, do resíduo que resolvia a pasta de upload por caminho relativo ao diretório corrente elimina a única armadilha que a renomeação poderia reativar. Sem essa remoção, a feature teria um risco a mais.

### Sanidade do actions

- Dependências sem ciclos, em ordem topológica válida; a cadeia mais longa tem 8 ações, e a contagem declarada no resumo confere.
- As 17 ações marcadas como paralelizáveis têm arquivos alvo disjuntos pelo critério do eixo. A ressalva é o par registrado em A002, cujo conflito não está no alvo declarado, e sim no diretório que uma grava e a outra varre.
- Nenhuma ação de responsabilidade alheia ao framework foi incluída: não há ação de configuração de ambiente de desenvolvimento, de execução de lint ou de abertura de proposta de integração.
- A pré-condição que depende do usuário foi corretamente mantida **fora** da lista de ações e registrada como nota de execução, em vez de virar ação que o agente não pode concluir.
