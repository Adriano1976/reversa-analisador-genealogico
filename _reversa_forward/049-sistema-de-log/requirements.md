# Requirements: sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O analisador **não tem observabilidade**. As cinco units da extração declaram, uma a uma, "nenhum
log, métrica ou trace", e o servidor inteiro tem **nove** chamadas de registro dispersas em dois
arquivos mais **um** `print` de inicialização. Consequência prática: o operador não consegue
responder depois "quando este arquivo saiu da lista, e a pedido de quem?", e quem depura não
consegue ligar a linha de erro ao acesso que a causou.

Esta feature entrega o sistema de registro em camadas que o operador especificou: configuração
central com três destinos de papéis distintos, identificador por requisição, registro de acesso,
trilha de auditoria separada, máscara de privacidade aplicada **também ao traceback**, medição
nomeada de etapas e a operação correspondente (container, rotação, retenção e pasta em disco). Ela
fecha a decisão **14** do `gaps.md` — "logar as duas tentativas de aposentar" — e substitui a
afirmação "nenhum log" dos cinco RNF das units.

Fica **fora** desta feature, por decisão do próprio plano: o formato estruturado para consumo por
ferramenta externa (item 4, declarado opcional).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/upload-gedcom/requirements.md#requisitos-não-funcionais` | "Nenhum log, métrica ou trace é emitido. A única saída textual é o `print` de inicialização" | 🟢 |
| `_reversa_sdd/analise-dna/requirements.md#requisitos-não-funcionais` | "Nenhum log, métrica ou trace. O aviso de persistência chega à tela, mas não ao log" | 🟢 |
| `_reversa_sdd/busca-caminho/requirements.md#requisitos-não-funcionais` | "Nenhum log, métrica ou trace. A única visibilidade é o texto do caminho, o diagrama e os avisos" | 🟢 |
| `_reversa_sdd/tela-de-entrada/requirements.md#requisitos-não-funcionais` | "Um log na unit: `app.logger.exception` quando o GEDCOM alcançado não pode ser lido. Nenhuma métrica, nenhum log de listagem ou de aposentadoria" | 🟢 |
| `_reversa_sdd/recursos-da-tela/requirements.md#requisitos-não-funcionais` | "Nenhum log, métrica ou trace. A ausência de arte não é registrada em lugar nenhum" | 🟢 |
| `_reversa_sdd/tela-de-entrada/tasks.md#lacunas-pendentes-🔴` | Lacuna 5: "nenhuma tentativa de aposentar deixa rastro no servidor. Decidir se isso é aceitável para uma ação destrutiva do ponto de vista do operador" | 🟢 |
| `_reversa_sdd/questions.md#pergunta-14` | As três saídas (logar as duas tentativas / aceitar / logar só o fracasso) e a recomendação de logar **as duas** | 🟢 |
| `_reversa_sdd/gaps.md#5-fechadas-nesta-rodada--21-lacunas` | Linha 14: "Aposentadoria sem log → **Logar as duas tentativas** → Agendado". É a decisão que esta feature executa | 🟢 |
| `_reversa_sdd/domain.md#5` | **29 literais** de mensagem de contrato, dos quais **7** são provados por golden file (captura congelada da tela); `RN-18` já fixou o texto de recusa de conteúdo | 🟢 |
| `_reversa_sdd/domain.md#36-a-tela-de-entrada-listar-escolher-e-aposentar` | `RN-14`: aposentar **move e nunca apaga**; a mensagem de sucesso/falha é contrato da tela | 🟢 |
| `_reversa_sdd/architecture.md#6` | O padrão `[A-Z]{2}\d{7}` é o que identifica kit de DNA na leitura do CSV — o mesmo padrão que a máscara de privacidade precisa cobrir | 🟢 |
| `_reversa_sdd/permissions.md#5` | `P-07`: dado pessoal persistido sem retenção; `P-08`: superfície pública. Não há sessão nem identidade — o "quem" da auditoria é o processo, não o usuário | 🟢 |
| `.reversa/principles.md#i` | "Dados reais de terceiros … jamais podem ser commitados, em nenhum caminho: nem em `uploads/`, nem em fixtures, golden files, capturas de tela, **logs**" | 🟢 |
| `tests/test_cache_de_arvores.py#test_o_log_conta_acerto_e_reconstrucao_sem_dado_pessoal` | Precedente do próprio projeto: a única linha de log do adaptador é testada afirmando que **nenhum nome** aparece nela | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador do analisador | Saber depois o que aconteceu com o arquivo dele | Abre o log de auditoria e vê a linha do dia em que a árvore saiu da lista, com a hora e o desfecho |
| Operador, sem terminal | Diagnosticar sem abrir o navegador | Um erro aparece na tela com frase própria; o rastro completo já está no console e no arquivo |
| Quem depura o sistema | Ligar a exceção ao acesso que a produziu | Copia o identificador de requisição de uma linha de erro e encontra a linha de acesso correspondente |
| Quem reimplementa o sistema | Não repetir o "nenhum log" | Lê o RNF de observabilidade e sabe quais eventos são auditáveis e o que nunca pode ser gravado |

## 4. Regras de negócio novas ou alteradas

1. **RN-01 — Três destinos, um papel cada.** Console (operação), arquivo geral rotativo
   (diagnóstico) e trilha de auditoria em arquivo próprio, que **não** propaga para os outros
   dois. Uma linha de auditoria não pode virar eco no log geral. 🟢
   - Origem no legado: `_reversa_sdd/tela-de-entrada/requirements.md#requisitos-não-funcionais`
   - Tipo: nova

2. **RN-02 — O nível vem do ambiente, e o ajuste por módulo é permitido.** Um nível global e a
   possibilidade de nomear módulos isolados com nível próprio, para não subir o volume do sistema
   inteiro só para ver um parser. 🟢
   - Origem no legado: convenção `ANALISADOR_*` já praticada em `ANALISADOR_UPLOAD_FOLDER`,
     `ANALISADOR_HOST`, `ANALISADOR_PORT`, `ANALISADOR_THREADS` e `ANALISADOR_CACHE_DE_ARVORE`
   - Tipo: nova

3. **RN-03 — Toda requisição tem um identificador curto, e ele liga acesso e erro.** O
   identificador é gerado pelo servidor, devolvido no cabeçalho da resposta e repetido na linha de
   acesso e em toda linha de erro daquela requisição. Valor enviado pelo cliente **não** é
   reaproveitado: aceitá-lo permitiria injetar texto arbitrário na trilha. 🟡
   - Origem no legado: `_reversa_sdd/architecture.md#2` (processo único, multi-thread, sem sessão)
   - Tipo: nova

4. **RN-04 — Toda ação que mexe em arquivo do operador ou produz resultado deixa linha de
   auditoria.** São auditáveis: envio de GEDCOM, substituição no reenvio (GEDCOM e CSV), as
   **duas** tentativas de aposentar (sucesso **e** falha), análise de DNA e busca de caminho.
   Cada linha carrega **ação, desfecho, identificação do arquivo, IP do cliente e identificador da
   requisição**; a identificação do arquivo é a **chave de conteúdo seguida da extensão**, e nunca
   o rótulo visível (sessão de esclarecimentos de 2026-10-25). 🟢
   - Origem no legado: `_reversa_sdd/gaps.md#5-fechadas-nesta-rodada--21-lacunas` (decisão 14);
     `_reversa_sdd/questions.md#pergunta-14`; `_reversa_sdd/domain.md#36-a-tela-de-entrada-listar-escolher-e-aposentar` (`RN-14`)
   - Tipo: alterada — a extração afirma "nenhum log de aposentadoria" e a decisão já registrada é
     logar as duas tentativas

5. **RN-05 — Nenhum dado pessoal em nenhum destino, inclusive no traceback.** A proibição do
   Princípio I vale para os três destinos. Como a regra sozinha depende de disciplina de quem
   escreve a mensagem, ela vem acompanhada de uma **máscara** aplicada a toda linha registrada, o
   que inclui o texto do traceback (o rastro da pilha de chamadas): identificador de kit no padrão
   já usado pela leitura do CSV e endereço de e-mail. 🟢
   - Origem no legado: `.reversa/principles.md#i`; `_reversa_sdd/architecture.md#6`;
     `tests/test_cache_de_arvores.py#test_o_log_conta_acerto_e_reconstrucao_sem_dado_pessoal`
   - Tipo: nova

6. **RN-06 — A tela perde o texto interno da exceção; o rastro fica no log.** As três mensagens
   que hoje interpelam a exceção na frase mostrada ao operador **mantêm o prefixo atual**
   ("Ocorreu um erro:" / "Erro ao processar GEDCOM:") e passam a terminar em **"O detalhe foi
   registrado no log."** — texto fixo, decidido na sessão de esclarecimentos de 2026-10-25. O
   traceback continua sendo registrado. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#5` (29 literais, 7 provados por golden);
     `_reversa_sdd/domain.md#35-upload-armazenamento-e-reenvio` (`RN-18`, precedente de texto
     fixo escolhido a dedo)
   - Tipo: alterada — **é mudança de contrato de tela**, não polimento, e por isso exige atualizar
     golden e fixture de paridade. **Conflito declarado com o Princípio II** (comportamento
     observável é preservado): a mudança é de comportamento observável de propósito, e por isso
     percorre o fluxo de requisito em vez de se apresentar como refatoração

7. **RN-07 — A medição é nomeada e em milissegundos.** A carga da árvore é medida por etapa
   nomeada, para que o ganho do cache (features 025 e 047) seja lido do próprio sistema em vez de
   de um cronômetro externo. 🟢
   - Origem no legado: `_reversa_sdd/addenda/025-desempenho-carga-arvore.md`;
     `_reversa_sdd/addenda/047-cache-dos-indices-da-arvore.md`
   - Tipo: nova

8. **RN-08 — Os destinos mudam de forma com o ambiente, e a pasta não é versionada.** No
   container a saída é o fluxo padrão do processo, com rotação no orquestrador; a pasta de
   auditoria é volume publicado. Fora do container, a pasta é escolhida por variável de ambiente,
   com o mesmo padrão de resolução da pasta de upload. A pasta de log nunca entra no
   versionamento nem no contexto de build. 🟢
   - Origem no legado: `_reversa_sdd/c4-containers.md`; `.dockerignore` (lista de permissão);
     `_pasta_uploads()` como precedente de resolução de pasta
   - Tipo: nova

9. **RN-09 — Nenhuma dependência nova de runtime.** A entrega usa apenas a biblioteca padrão da
   linguagem; o arquivo de dependências de runtime não ganha linha. 🟢
   - Origem no legado: `requirements.txt` (lista de runtime); precedente da biblioteca de imagem,
     que gera arte de teste e ficou fora do arquivo de dependências de runtime
   - Tipo: nova

10. **RN-10 — A trilha de auditoria tem prazo declarado de 90 dias, e o expurgo é do operador.**
    O sistema **não apaga sozinho**: ele nomeia o prazo na própria configuração e deixa o descarte
    com quem responde pelo dado. Decidido na sessão de esclarecimentos de 2026-10-25, pelo
    precedente do projeto de não construir retenção automática no legado. 🟢
    - Origem no legado: `_reversa_sdd/gaps.md#5-fechadas-nesta-rodada--21-lacunas` (decisão 5,
      `L-29`/`P-07`: retenção e expurgo como requisito do alvo)
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | A configuração de registro é central e única: nível global e nível por módulo, ambos lidos do ambiente na subida | Must | Subir com nível `DEBUG` muda as três saídas sem tocar código; nomear um módulo com nível próprio muda só as linhas dele | 🟢 |
| RF-02 | Os três destinos existem com papéis distintos, e o de auditoria não propaga para os outros | Must | Uma ação auditada escreve no arquivo de auditoria e **não** duplica a linha no arquivo geral | 🟢 |
| RF-03 | Cada requisição gera um identificador curto, devolvido no cabeçalho da resposta | Must | Duas requisições seguidas trazem identificadores diferentes; o valor aparece na linha de acesso daquela requisição | 🟢 |
| RF-04 | Existe uma linha de acesso por requisição, com método, rota, situação da resposta e duração em milissegundos | Must | Uma requisição `POST` de análise produz exatamente uma linha de acesso, com a situação e a duração | 🟢 |
| RF-05 | Envio de GEDCOM e substituição no reenvio são auditados, com desfecho e contagens | Must | Envio novo, envio idêntico e envio que substitui produzem três linhas distinguíveis | 🟢 |
| RF-06 | Aposentar é auditado nas **duas** tentativas, sucesso e falha | Must | Aposentar arquivo existente e aposentar referência inexistente produzem uma linha cada, com desfecho distinto | 🟢 |
| RF-07 | Análise de DNA e busca de caminho são auditadas com as contagens do resultado, nunca com nomes | Must | Análise com N matches e M descartados registra N e M; o texto da linha não contém nenhum nome da árvore | 🟢 |
| RF-08 | A máscara de privacidade é aplicada a toda linha registrada, **inclusive ao traceback** | Must | Uma exceção cuja mensagem carrega nome, e-mail ou identificador de kit chega ao log com esses trechos mascarados | 🟢 |
| RF-09 | A carga da árvore é medida por etapa nomeada, com milissegundos | Should | A linha de medição nomeia a etapa e traz a duração em milissegundos; não contém dado pessoal | 🟢 |
| RF-10 | A operação está resolvida para container e para execução direta, e a pasta de log fica fora do versionamento e do contexto de build | Must | No container a saída é o fluxo padrão com rotação declarada; fora dele a pasta vem do ambiente; a pasta não aparece em `git status` nem no contexto de build | 🟢 |
| RF-11 | As três mensagens de tela que hoje interpelam a exceção mantêm o prefixo e passam a terminar em "O detalhe foi registrado no log.", e o traceback vai para o log | Must | Nenhuma das três respostas renderizadas contém texto interno de exceção, e todas terminam na frase fixa; a linha de erro correspondente existe no log | 🟢 |
| RF-12 | A entrega vem com os testes de auditoria (dois desfechos), de identificador de requisição e de privacidade | Must | O teste de privacidade roda uma análise com fixture sintética e afirma que **nenhum nome** do arquivo aparece no log capturado | 🟢 |
| RF-13 | A decisão de observabilidade fica registrada como decisão de arquitetura e as cinco RNF "nenhum log" são convergidas na extração | Should | Existe a nova decisão no acervo de decisões; a convergência das units é feita no `/reversa-sync` | 🟢 |
| RF-14 | Toda linha de auditoria carrega ação, desfecho, chave de conteúdo com extensão, IP do cliente e identificador de requisição | Must | A linha de um aposentar traz os cinco campos; o rótulo visível do arquivo não aparece nela | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Privacidade | Nenhum nome de pessoa, rótulo visível de arquivo do operador, e-mail ou identificador de kit em nenhum dos três destinos, nem no traceback. A linha de auditoria identifica o arquivo pela chave de conteúdo com extensão | Princípio I lista **logs** explicitamente entre os caminhos proibidos; decisão de 2026-10-25 | 🟢 |
| Privacidade | A máscara é proteção em profundidade, não substituta da regra: mensagem nova continua obrigada a não passar nome adiante | Uma `KeyError` pode carregar o nome como chave do próprio texto da exceção | 🟢 |
| Paridade | Nenhuma saída de tela muda, **exceto** as três mensagens do RF-11; quando elas mudarem, golden e fixture de paridade são atualizados no mesmo commit | Paridade 100 % em 6 fixtures; 7 literais provados por golden | 🟢 |
| Desempenho | O registro não pode dominar o custo da requisição: uma linha por evento, sem formatação pesada no caminho quente | O parse da árvore real custa ~20,9 s e o dossiê ~1,73 s — o registro precisa ficar fora dessa ordem de grandeza | 🟡 |
| Operação | Sem dependência nova de runtime; sem serviço externo de coleta | `requirements.txt` é lista de runtime e o container não tem coletor | 🟢 |
| Operação | Retenção: 5 arquivos de 5 MB no log geral; a trilha de auditoria tem prazo **declarado de 90 dias** e o expurgo é **manual**, do operador — o sistema não apaga sozinho | Decisão de 2026-10-25; precedente `L-29`/`P-07` (retenção como requisito do alvo, não do legado); prazo em dias por causa da LGPD (a lei de proteção de dados pessoais) | 🟢 |
| Concorrência | As quatro threads do processo escrevem nos mesmos destinos sem intercalar linha pela metade, e duas requisições simultâneas nunca trocam de identificador | O processo é multi-thread com 4 threads e sem estado de domínio compartilhado; o identificador por requisição é justamente o que não pode vazar de uma thread para outra | 🟢 |
| Segurança | O identificador de requisição nunca é aceito do cliente | Texto de cliente em arquivo de log é vetor de injeção de linha | 🟡 |
| Testes | Suíte continua verde a partir do marco de 1656 passam / 9 pulados; fixtures sintéticas, nunca arquivo de `src/uploads/` | Addendo de 2026-10-24; Princípio I e Princípio III | 🟢 |
| Acessibilidade do diagnóstico | Toda linha de auditoria é legível por uma pessoa, sem ferramenta: data, ação, desfecho e identificador na mesma linha | O sistema é operado por uma pessoa, sem coletor externo | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Aposentar com sucesso deixa rastro
  Dado que existe um arquivo na lista da tela
  Quando o operador aposenta esse arquivo
  Então a resposta é a de sucesso, igual à de hoje
  E a trilha de auditoria ganha uma linha com a ação de aposentar, o desfecho de sucesso e o identificador da requisição

Cenário: Aposentar que falha também deixa rastro
  Dado que a referência enviada não corresponde a nenhum arquivo da pasta
  Quando o operador tenta aposentar
  Então a resposta é a de falha, igual à de hoje
  E a trilha de auditoria ganha uma linha com a ação de aposentar e o desfecho de falha

Cenário: A linha de auditoria identifica o arquivo sem nomeá-lo
  Dado que o operador aposenta um arquivo cujo rótulo contém nome de pessoa
  Quando a linha de auditoria é gravada
  Então a linha traz a chave de conteúdo com a extensão, o IP, o identificador da requisição e o desfecho
  E o rótulo visível do arquivo não aparece no texto da linha

Cenário: Envio novo, envio idêntico e substituição são distinguíveis na auditoria
  Dado que a pasta já tem o mesmo conteúdo de um envio anterior
  Quando o operador envia o mesmo arquivo de novo
  Então a resposta continua dizendo que o arquivo foi carregado
  E as linhas de auditoria dos três casos trazem desfechos diferentes entre si

Cenário: O identificador da requisição liga acesso e erro
  Dado que uma requisição provoca uma falha inesperada
  Quando a resposta chega
  Então o cabeçalho traz o identificador daquela requisição
  E a linha de acesso e a linha de erro trazem o mesmo identificador

Cenário: Duas requisições simultâneas não trocam de identificador
  Dado que duas requisições são atendidas ao mesmo tempo em threads diferentes
  Quando as duas respostas chegam
  Então cada uma traz o próprio identificador
  E nenhuma linha de auditoria de uma carrega o identificador da outra

Cenário: Nenhum nome do arquivo aparece no log
  Dado uma árvore sintética com pessoas de nome conhecido e um relatório de DNA sintético
  Quando a análise de DNA é executada
  Então o log capturado não contém nenhum desses nomes
  E a linha de auditoria da análise existe, com as contagens do resultado

Cenário: A máscara alcança o traceback
  Dado que uma exceção é levantada com um identificador de kit e um e-mail no texto
  Quando a exceção é registrada
  Então o texto dos dois aparece mascarado na linha registrada
  E o restante da mensagem continua legível

Cenário: A tela não mostra mais o texto interno da exceção
  Dado que a análise de DNA falha de forma inesperada
  Quando a tela é renderizada
  Então a mensagem mantém o prefixo "Ocorreu um erro:" e termina em "O detalhe foi registrado no log."
  E a mensagem não contém o texto interno da exceção
  E o traceback correspondente está no log

Cenário: O custo da carga da árvore é medido
  Dado que uma árvore é carregada a partir da referência
  Quando a carga termina
  Então uma linha de medição nomeia a etapa e traz a duração em milissegundos

Cenário: O container escreve no fluxo padrão
  Dado a aplicação em execução no container
  Quando uma requisição é atendida
  Então a linha de acesso sai no fluxo padrão do processo
  E a trilha de auditoria é gravada na pasta publicada como volume

Cenário: O nível vem do ambiente e a auditoria não vaza para o arquivo geral
  Dado a aplicação iniciada com o nível informado no ambiente
  Quando uma ação auditável é executada
  Então as linhas daquele nível aparecem nos destinos correspondentes
  E a linha de auditoria não aparece de novo no arquivo geral

Cenário: A decisão de observabilidade fica registrada
  Dado que a feature é concluída
  Quando a entrega é convergida na extração
  Então existe a decisão de arquitetura de observabilidade no acervo de decisões
  E as cinco RNF de observabilidade das units deixam de afirmar "nenhum log"
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-08 + RNF de privacidade | Must | É o único requisito cuja violação não tem conserto depois: dado pessoal em log não se "desgrava" |
| RF-06 | Must | É a decisão 14 do `gaps.md`, agendada desde 2026-10-11 |
| RF-01, RF-02 | Must | Sem configuração central e destinos separados, os demais requisitos não têm onde morar |
| RF-03, RF-04 | Must | É o que liga o erro ao acesso; sem isso o log de erro continua órfão |
| RF-05, RF-07 | Must | As ações que mexem em arquivo e produzem resultado são a razão de existir da auditoria |
| RF-14 | Must | É o que torna a linha de auditoria utilizável sem violar o Princípio I: identifica o arquivo pela chave, não pelo nome |
| RF-11 | Must | Fecha a exposição de texto interno de exceção na tela, e é mudança de contrato declarada |
| RF-12 | Must | Princípio III: nenhuma mudança sem teste que a cubra |
| RF-10 | Must | O container é onde a falha é invisível: sem operação resolvida, o resto não é verificável em uso |
| RF-09 | Should | Serve à decisão de cache, não bloqueia a entrega |
| RF-13 | Should | Registra a decisão e evita que a reimplementação repita o "nenhum log" |
| Formato estruturado para ferramenta externa (item 4 do plano) | Could | Explicitamente opcional no plano e fora de escopo |

## 9. Esclarecimentos

### Sessão 2026-10-25

- **Q:** O plano pede o "rótulo do arquivo" em cada linha de auditoria, mas o rótulo é o nome que
  o operador deu ao arquivo — e nomes reais da pasta incluem nome de pessoa. O que a linha grava?
  **R:** **Chave de conteúdo com a extensão.** O rótulo visível nunca é registrado. Alguns nomes
  reais medidos na pasta do operador mostram por que: o rótulo pode carregar nome de pessoa, e o
  arquivo de auditoria sobrevive à requisição. A identificação passa a ser a mesma chave de 16
  hexadecimais que já nomeia o arquivo armazenado.

- **Q:** O plano diz "cerca de 90 dias" e, na mesma frase, que o prazo é decisão do operador. Como
  a trilha termina?
  **R:** **Prazo de 90 dias declarado, expurgo manual.** O sistema nomeia o prazo na configuração e
  **não** apaga sozinho. Segue o precedente do projeto de não construir retenção automática no
  legado (`L-29`/`P-07`: retenção e expurgo como requisito do alvo). Consequência registrada: o
  acúmulo de dado pessoal na trilha fica sob responsabilidade do operador.

- **Q:** As três mensagens que hoje mostram o texto interno da exceção precisam perder o texto
  interno. O que entra no lugar?
  **R:** **Prefixo atual + "O detalhe foi registrado no log."** O prefixo de cada uma permanece
  ("Ocorreu um erro:" nas duas últimas, "Erro ao processar GEDCOM:" na primeira) e a frase final é
  fixa. É a mudança de contrato de tela que exige atualizar golden e fixture de paridade no mesmo
  commit.

- **Q:** O plano pede o IP do cliente em cada linha auditada. O que gravar?
  **R:** **O IP, como o plano pede.** Em acesso local ele identifica a máquina, não a pessoa; passa
  a identificar o aparelho quando a aplicação atende a rede, e é justamente aí que ele responde
  "de qual aparelho saiu esta ação". O IP entra no prazo de retenção de 90 dias.

## 10. Lacunas

Nenhuma dúvida em aberto. As três que existiam foram resolvidas na sessão de 2026-10-25 e estão
registradas em §9; as decisões correspondentes viraram `RN-04`, `RN-06`, `RN-10` e `RF-14`. Ficam
os três pontos técnicos abaixo, que são de verificação na fase de plano, não de decisão de produto:

- 🟡 **Duplicação com o registro de acesso do servidor HTTP.** O servidor já registra uma linha
  por requisição no nível informativo. A linha própria do RF-04 é a que carrega o identificador;
  a duplicação visual no console é aceitável para o operador ou o registro do servidor deve ser
  silenciado? [Verificar na fase de plano]

- 🟡 **A pasta de log na raiz esbarra na política de edição do legado.** O `allowedPaths` de
  `.reversa/reversa-config.json` cobre `src/**`, `tests/**`, `docker/**`, `docker-compose.yml`,
  `.dockerignore`, `requirements.txt` e `docs/**`, mas **não** o `.gitignore`. A linha que ignora a
  pasta de log no versionamento não pode ser escrita sem o operador liberar esse caminho — é
  bloqueio de política, não de código, e precisa ser resolvido antes do `/reversa-coding`.

- 🟡 **O expurgo manual da auditoria depende de disciplina, não de mecanismo.** O prazo de 90 dias
  está declarado (`RN-10`) e nada o faz cumprir: nenhum aviso, nenhum lembrete. Se o operador
  esquecer, a trilha cresce com IP e chaves de conteúdo além do prazo declarado.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-25 | Versão inicial gerada por `/reversa-requirements` a partir do plano de implantação de sistema de log anexado pelo operador | reversa |
| 2026-10-25 | Sessão de esclarecimentos: 4 respostas integradas (`RN-04`, `RN-06`, `RN-10`, `RF-14`), 3 marcadores `[DÚVIDA]` zerados | reversa |
