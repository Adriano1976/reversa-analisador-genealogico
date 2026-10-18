# Requirements: validador de dados de DNA × GEDCOM

> Identificador: `028-validador-de-dados-dna`
> Data: `2026-10-18`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Documento pedido pelo operador em 2026-10-18. O literal de máquina do terceiro estado é
> `ERRO CRONICO / QUEBRA DE LINHA` (sem acento), exatamente como pedido; na prosa ele aparece
> sempre nessa forma para não haver duas grafias.

## 1. Resumo executivo

O operador precisa de um módulo que responda, para cada comparação entre um kit de DNA e uma pessoa
do GEDCOM, se a **linha documental é temporalmente viável** — e não apenas se o cM cai numa faixa.
Hoje o sistema responde quatro estados (`COMPATIVEL`, `POSSIVEL`, `CONFLITANTE`, `INCONCLUSIVO`) sobre
a compatibilidade cM × parentesco, e tem duas verificações parciais: a janela de vida do match e a
profundidade do caminho contra o `MRCA` do próprio kit. Falta a verificação que cruza as **datas de
nascimento dos dois lados**, a **profundidade documental** e o **cM** para estimar o MRCA e acusar
conflitos biológicos críticos — por exemplo, um doador vivo ligado a um ancestral do século XVII por
um caminho curto demais.

Esta feature entrega `src/core/validator.py` (regras puras), uma fachada de leitura em
`src/application/validacao.py` e testes unitários com fixtures sintéticas. O veredito é um **campo
novo**, com três literais, e **não substitui** os quatro estados existentes nem altera o contrato da
tela (escopo confirmado na sessão de esclarecimentos de 2026-10-18, §9).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#2-a-regra-central-do-dominio-tres-eixos-que-nao-se-contaminam` | Documental, genético e confronto são eixos separados; o DNA nunca altera o parentesco documental | 🟢 |
| `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto` | Os quatro estados, seus gatilhos e o contrato literal das mensagens | 🟢 |
| `_reversa_sdd/domain.md#31-parentesco-documental` | Idade de genitor fora de **12–70 anos** marca `plausible: False` e gera `data_impossivel`, sem invalidar o vínculo | 🟢 |
| `_reversa_sdd/domain.md#32-evidencia-genetica` | Chave `(nome, kit)`; **kits diferentes nunca somam cM** | 🟢 |
| `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | 27 relações publicadas, 6 não publicadas; nenhum número é inventado | 🟢 |
| `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes` | O núcleo não conhece HTTP; `core/` não importa `parsers/` (ADR-25) | 🟢 |
| `_reversa_sdd/architecture.md#4-modelo-de-dados` | `None` significa "não sei / não existe", nunca zero | 🟢 |
| `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md` | O veredicto do doador e a moldura do cartão quando a idade é impossível | 🟢 |
| `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md` | Idade acima de **122** veta o parentesco apresentado; a árvore **tem** o caminho e isso é declarado | 🟢 |
| `_reversa_forward/027-harmonizar-topo-da-tela/requirements.md` | A tela é congelada por hash e por testes; mudança de contrato é feature separada | 🟢 |
| `.reversa/principles.md#i` | Dados reais de DNA/GEDCOM nunca entram no versionamento; teste usa fixture sintética | 🟢 |
| `.reversa/principles.md#iii` | Nenhuma mudança sem teste que a cubra | 🟢 |
| `.reversa/principles.md#v` | Toda suposição de genealogia genética cita a fonte e a data de consulta | 🟢 |

### 2.1 O que já existe e **não** será reimplementado

| Componente | O que já responde | Por que não basta |
|------------|-------------------|-------------------|
| `core.documentary_relationship` | Caminho, `degrees.a_up`/`b_up`, meioses, MRCA e `hop_evidence` por salto | Não olha o cM nem estima o ano do MRCA |
| `core.janela_de_vida` | O **match** escolhido pode ter doado? (`>122` é impossível) | Não verifica o **doador** nem a viabilidade da linha inteira |
| `core.profundidade_do_caminho` | A árvore afirma a mesma profundidade que o `MRCA` do kit? | Depende da coluna `MRCA`; não usa datas de nascimento nem a idade por lado |
| `core.evidence_comparison` | cM × parentesco documental, em quatro estados | Não é um veredito de viabilidade temporal e não acusa quebra de linha |
| `core.relationship_hypotheses` | Tabela publicada do Shared cM Project 4.0, com `meioses` por relação | Não converte gerações em anos nem estima o MRCA |
| `core.genetic_evidence` | cM total, maior segmento, `MRCA` do kit, chave `(nome, kit)` | É descritivo; não decide nada |

### 2.2 A lacuna que esta feature fecha

1. **Nenhum componente compara a data de nascimento do doador com a do MRCA documentado.** A janela
   de vida olha o match; o doador (a raiz que fez o teste) nunca é o sujeito da checagem.
2. **Nenhum componente verifica a idade por lado.** A divisão `meioses / 2` usada em
   `profundidade_do_caminho` é uma média; um caminho com 2 gerações de um lado e 10 do outro pode
   esconder um salto impossível.
3. **Nenhum componente estima o ano do MRCA a partir do cM.** O `MRCA` do kit é lido, mas não é
   confrontado com a data que o GEDCOM declara.
4. **Nenhum componente devolve um veredito único de validação de dados.** As três verificações
   existentes são independentes e nenhuma é autoritativa para "conflito biológico crítico".

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Operador / genealogista | Saber se o parentesco apresentado é temporalmente possível antes de usá-lo | Recebe um cartão com cM compatível, mas o caminho liga o doador vivo a um ancestral de 1650 em duas gerações |
| Auditor de dados | Revisar um lote de comparações e separar o que foi validado do que quebrou | Exporta o resultado do validador e encontra os `ERRO CRONICO / QUEBRA DE LINHA` com o código da anomalia |
| Desenvolvedor do legado | Acrescentar a regra sem tocar nos quatro estados nem na tela | Chama `validar_comparacao` a partir de um teste, sem a borda HTTP e sem arquivo |
| Revisor de privacidade | Garantir que nenhum dado real entrou nos testes | Confere que a fixture é sintética e que `git status` não lista `uploads/` |

## 4. Regras de negócio novas ou alteradas

### 4.1 Definições operacionais

| Termo | Definição nesta feature |
|-------|--------------------------|
| **Doador** | A pessoa que fez o teste de DNA; no fluxo atual, a raiz escolhida no GEDCOM. |
| **Match** | A pessoa do GEDCOM associada ao kit pelo casamento de nome já existente. |
| **MRCA documentado** | O ancestral comum que o caminho do GEDCOM declara, com o nascimento que o GEDCOM traz. |
| **MRCA estimado** | O ano de nascimento do MRCA derivado do cM do kit (e, quando existir, da coluna `MRCA` do próprio relatório). |
| **Profundidade documental** | `degrees.a_up` (lado do doador) + `degrees.b_up` (lado do match), em saltos pai-filho. |
| **Idade por lado** | Anos entre o nascimento do descendente e o nascimento do MRCA, divididos pelas gerações daquele lado. |
| **Doador vivo** | `ano_referencia - nasc_doador <= 122`, com `ano_referencia` calculado como em `janela_de_vida`. |
| **Linha datada** | Caminho em que **todos** os saltos têm data de nascimento nos dois extremos. |

**Siglas.** **GEDCOM** é o formato de árvore genealógica (`.ged`); **cM** é centiMorgan, a unidade de
recombinação genética; **MRCA** é *Most Recent Common Ancestor*, o ancestral comum mais recente;
**SCP 4.0** é o Shared cM Project 4.0, a tabela publicada de cM por relação.

### 4.2 Regras

1. **RN-01: o cM é sempre o total de um kit, nunca a soma de kits.** Cada kit é validado
   separadamente; dois kits do mesmo nome produzem dois resultados. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#32-evidencia-genetica`
   - Tipo: nova (para o validador), preservada do domínio

2. **RN-02: a estimativa de gerações até o MRCA usa, nesta ordem, o `MRCA` do kit e a tabela
   Shared cM Project 4.0.** Se o kit traz `MRCA > 0`, ele é a estimativa (método `mrca_do_kit`);
   senão, usa a mediana das `meioses` das relações publicadas que contêm o cM, dividida por 2
   (método `scp40:mediana`). Sem nenhum dos dois, não há estimativa. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40`;
     `src/core/profundidade_do_caminho.py`
   - Tipo: nova (métrica confirmada em 2026-10-18: cM total do kit, ver §9)

3. **RN-03: o ano do MRCA é estimado como `nasc_doador - geracoes_kit × G`.** `G` é o intervalo
   de geração em anos, estimado pela **mediana dos intervalos pai-filho da própria árvore** com
   ambas as datas e dentro de 12–70; com menos de 3 amostras, usa-se o prior declarado de **25
   anos**. A janela do MRCA vem das `meioses` mínima e máxima dos candidatos; quando só existe o
   `MRCA` do kit, a janela é `±2` gerações. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental` (limites 12–70);
     Fenner (2005) para a variabilidade do intervalo (ver §4.3)
   - Tipo: nova (regra confirmada em 2026-10-18: mediana da árvore + fallback de 25, ver §9)

4. **RN-04: a linha é temporalmente viável quando a idade por lado fica entre 12 e 70 anos.**
   Para cada lado com pelo menos uma geração, calcula-se
   `(nasc_descendente - nasc_mrca) / geracoes_do_lado`; fora de 12–70, há conflito crítico
   (`PROFUNDIDADE_TEMPORAL_INCOMPATIVEL`). O mesmo limite vale para cada salto pai-filho datado
   (`GENITOR_FORA_DA_JANELA_BIOLOGICA`). Além disso, o MRCA não pode nascer depois — ou no mesmo
   ano — de um descendente com geração maior que zero (`MRCA_POSTERIOR_A_DESCENDENTE`). 🟢
   - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental`;
     `src/core/documentary_relationship.py` (`IDADE_MINIMA_GENITOR`/`IDADE_MAXIMA_GENITOR`)
   - Tipo: nova (a regra já existe por salto; passa a existir por lado e para o doador)

5. **RN-05: o cM precisa sustentar a profundidade documental.** Se a comparação de quatro estados
   já existe, o estado dela é o insumo: `CONFLITANTE` vira conflito crítico
   (`CONFLITO_CM_DOCUMENTAL`); `POSSIVEL` e `INCONCLUSIVO` mantêm o resultado inconclusivo. Sem
   essa comparação, o validador usa a envoltória das relações publicadas que contêm o cM: a
   profundidade documental pode ficar no máximo **2 meioses** fora de `[mínimo, máximo]`
   (`CM_INCOMPATIVEL_COM_PROFUNDIDADE`). 🟡
   - Origem no legado: `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto`;
     `src/core/evidence_comparison.py`
   - Tipo: nova (composição, não reimplementação)

6. **RN-06: o MRCA documentado precisa caber na janela estimada pelo cM.** Se o GEDCOM declara o
   nascimento do MRCA e ele fica fora da janela de RN-03 por mais de **2 gerações**, há conflito
   crítico (`MRCA_DOCUMENTADO_FORA_DA_JANELA`). Se a data é estimada (`ABT`, `EST`, `CAL`, `BEF`,
   `AFT`, `CIRCA`, `APPROX`), o achado é **atenção** (`MRCA_DOCUMENTADO_FORA_DA_JANELA_ESTIMADO`),
   não crítico, e o resultado é `INCONCLUSIVO`. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental` (qualificadores de data);
     `src/core/janela_de_vida.py`
   - Tipo: nova

7. **RN-07: doador vivo em linha incompatível é conflito biológico crítico.** Se o doador está vivo
   e qualquer conflito crítico desta seção foi acusado (salto, idade por lado, cM × profundidade,
   MRCA fora da janela ou MRCA posterior), o resultado recebe também
   `DOADOR_VIVO_EM_LINHA_INCOMPATIVEL`. O caso típico é o doador nascido no século XX ligado a um
   ancestral do século XVII por um caminho curto demais. 🟢
   - Origem no legado: `_reversa_sdd/addenda/016-janela-de-vida-veta-o-parentesco.md` (122 anos);
     `_reversa_sdd/addenda/015-veredicto-do-doador-no-cartao.md`
   - Tipo: nova

8. **RN-08: o status segue a precedência `ERRO CRONICO / QUEBRA DE LINHA` > `INCONCLUSIVO` >
   `VALIDADO`.** Um conflito crítico vence qualquer dado faltante; um dado faltante vence a
   validação. Com vários kits, vence o pior status na mesma ordem. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto` (precedência
     conservadora entre kits)
   - Tipo: nova

9. **RN-09: `VALIDADO` exige a linha inteira datada e sem contradição.** Só há `VALIDADO` quando:
   cM utilizável; comparação existente ausente ou `COMPATIVEL`; nascimentos do doador, do match e do
   MRCA presentes e **exatos**; todos os saltos do caminho datados e plausíveis; identidade não
   ambígua; e nenhuma atenção aberta. Dados parciais podem provar um erro, mas **nunca** provam uma
   validação. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#4-modelo-de-dados` (`None` é "não sei");
     `.reversa/principles.md#iii`
   - Tipo: nova

10. **RN-10: dado ausente ou impreciso é `INCONCLUSIVO`, nunca erro.** Falta de caminho, de data,
    de cM, de kit, de cobertura publicada, identidade ambígua, data estimada e kit múltiplo sem
    consenso produzem `INCONCLUSIVO` com o código correspondente. "Não sei" não é "quebrou". 🟢
    - Origem no legado: `_reversa_sdd/domain.md#31-parentesco-documental` ("sem data para julgar,
      `plausible` é `None`")
    - Tipo: preservada

11. **RN-11: o validador não substitui nem renomeia os quatro estados.** O resultado novo é um campo
    separado (`validacao`), com os três literais desta feature; `COMPATIVEL`, `POSSIVEL`,
    `CONFLITANTE` e `INCONCLUSIVO` continuam existindo, com o mesmo texto e a mesma classe CSS. 🟢
    - Origem no legado: `_reversa_sdd/domain.md#21-os-quatro-estados-do-confronto`;
      `_reversa_sdd/architecture.md#5-o-fluxo-que-define-o-sistema` (ADR-15)
    - Tipo: preservada

12. **RN-12: a validação é determinística e pura.** O núcleo não lê arquivo, não consulta relógio e
    não usa estado global; `ano_referencia` entra por parâmetro. Ordenações são explícitas e não
    dependem da iteração de `set`. 🟢
    - Origem no legado: `.reversa/principles.md#ii`; `_reversa_sdd/architecture.md#3-componentes-e-estrutura-de-pacotes`
    - Tipo: nova

13. **RN-13: a validação só vale para linha consanguínea.** O caminho percorrido é o de filiação
    (pai/mãe → filho), e um caminho por afinidade não é validado como linhagem biológica: ele
    devolve `INCONCLUSIVO` com `AFINIDADE_NAO_BIOLOGICA`. Aresta de casamento nunca é tratada como
    aresta de sangue. 🟢
    - Origem no legado: `.reversa/principles.md#iv`; `_reversa_sdd/domain.md#31-parentesco-documental`
    - Tipo: preservada (explicitada para esta feature)

> **Princípios aplicados.** I (fixture sintética), II (comportamento dos quatro estados preservado),
> III (todo código novo coberto por teste), IV (só filiação é linhagem), V (todo limiar cita a
> fonte). Nenhum conflito com princípio ativo.

### 4.3 Valores de domínio e fontes

| Constante | Valor | Fonte | Confidência |
|-----------|-------|-------|-------------|
| `IDADE_MINIMA_GENITOR` | 12 anos | `_reversa_sdd/domain.md#31-parentesco-documental`; `src/core/documentary_relationship.py` | 🟢 |
| `IDADE_MAXIMA_GENITOR` | 70 anos | idem | 🟢 |
| `IDADE_IMPOSSIVEL` | 122 anos | `src/core/janela_de_vida.py`; adendo `016` | 🟢 |
| `INTERVALO_DE_GERACAO_PADRAO` | 25 anos | Prior declarado do projeto, adotado em 2026-10-18. A literatura não tem consenso e o intervalo varia por sexo e população: Fenner, J. N. *Cross-cultural estimation of the human generation interval for use in genetics-based population divergence studies*. Am J Phys Anthropol. 2005;128(2):415–423. DOI [10.1002/ajpa.20188](https://doi.org/10.1002/ajpa.20188). Consultado em 2026-10-18 | 🟡 |
| `TOLERANCIA_DE_MEIOSES` | 2 meioses | Heurística desta feature, declarada; não é número da fonte | 🟡 |
| `TOLERANCIA_DE_GERACOES` | 2 gerações | Heurística desta feature, declarada | 🟡 |
| Tabela de relações | Shared cM Project 4.0 | `src/core/relationship_hypotheses.py`; `_reversa_sdd/domain.md#33-possibilidades-shared-cm-project-40` | 🟢 |
| `LIMITE_SEGMENTO_FRACO` | 15 cM | `src/core/genetic_evidence.py` (não decide o MRCA; só marca evidência fraca) | 🟢 |

> **Por que 25 e não um número único da literatura.** O valor de 25 é um **prior do projeto**, e não
> uma calibração. A fonte acima mostra que não há consenso e que o intervalo real é maior e varia
> por sexo; por isso a primeira escolha é a **mediana da própria árvore**, e o prior só entra quando
> a árvore não tem amostra suficiente. A escolha foi confirmada em 2026-10-18 (ver §9); trocar o
> prior exige nova decisão, não um ajuste escondido no código.

### 4.4 Códigos de anomalia

| Código | Severidade | Gatilho | Status resultante |
|--------|------------|---------|-------------------|
| `GENITOR_FORA_DA_JANELA_BIOLOGICA` | crítico | Salto pai-filho datado com idade < 12 ou > 70 | `ERRO CRONICO / QUEBRA DE LINHA` |
| `MRCA_POSTERIOR_A_DESCENDENTE` | crítico | MRCA nasce depois (ou no mesmo ano) de um descendente com geração > 0 | `ERRO CRONICO / QUEBRA DE LINHA` |
| `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` | crítico | Idade por lado fora de 12–70 | `ERRO CRONICO / QUEBRA DE LINHA` |
| `CM_INCOMPATIVEL_COM_PROFUNDIDADE` | crítico | Profundidade documental a mais de 2 meioses da envoltória publicada | `ERRO CRONICO / QUEBRA DE LINHA` |
| `MRCA_DOCUMENTADO_FORA_DA_JANELA` | crítico | MRCA documentado fora da janela estimada por mais de 2 gerações (data exata) | `ERRO CRONICO / QUEBRA DE LINHA` |
| `CONFLITO_CM_DOCUMENTAL` | crítico | Comparação de quatro estados = `CONFLITANTE` | `ERRO CRONICO / QUEBRA DE LINHA` |
| `DOADOR_VIVO_EM_LINHA_INCOMPATIVEL` | crítico | Doador vivo + qualquer conflito crítico acima | `ERRO CRONICO / QUEBRA DE LINHA` |
| `MRCA_DOCUMENTADO_FORA_DA_JANELA_ESTIMADO` | atenção | Mesmo gatilho, com data estimada | `INCONCLUSIVO` |
| `SEM_DATA_DE_NASCIMENTO` | informativo | Falta data do doador, do match ou do MRCA | `INCONCLUSIVO` |
| `DATA_ESTIMADA` | informativo | Data com qualificador (`ABT`, `EST`, `CAL`, `BEF`, `AFT`, `CIRCA`, `APPROX`) | `INCONCLUSIVO` |
| `SEM_EVIDENCIA` | informativo | Nenhum kit de DNA utilizável no arquivo | `INCONCLUSIVO` |
| `SEM_COBERTURA_DE_CM` | informativo | cM sem relação publicada e sem `MRCA` do kit | `INCONCLUSIVO` |
| `SEM_CAMINHO_DOCUMENTAL` | informativo | Nenhum caminho no GEDCOM | `INCONCLUSIVO` |
| `IDENTIDADE_AMBIGUA` | informativo | Homônimos não resolvidos | `INCONCLUSIVO` |
| `COMPARACAO_POSSIVEL` | informativo | Comparação de quatro estados = `POSSIVEL` | `INCONCLUSIVO` |
| `COMPARACAO_INCONCLUSIVA` | informativo | Comparação de quatro estados = `INCONCLUSIVO` | `INCONCLUSIVO` |
| `AFINIDADE_NAO_BIOLOGICA` | informativo | O caminho chega ao outro ramo por casamento, não por filiação | `INCONCLUSIVO` |
| `MULTIPLOS_KITS` | informativo | Mais de um kit para o mesmo nome, com estados diferentes | pior status entre os kits |

### 4.5 Contrato do resultado

O resultado de uma comparação é um dicionário com, no mínimo:

| Campo | Tipo | Conteúdo |
|-------|------|----------|
| `status` | `str` | Um dos três literais: `VALIDADO`, `INCONCLUSIVO`, `ERRO CRONICO / QUEBRA DE LINHA` |
| `motivo` | `str` | Uma frase para o operador, sem jargão de código |
| `codigos` | `list[dict]` | `{codigo, severidade, mensagem}`; ordenada por severidade e depois por código |
| `kit` | `str \| None` | O kit avaliado |
| `cm` | `float \| None` | cM total do kit, nunca somado entre kits |
| `mrca_estimado` | `dict` | `{ano, ano_min, ano_max, geracoes, metodo}`; `None` quando não há dado |
| `mrca_documentado` | `dict` | `{id, ano, impreciso}`; `None` quando não há caminho |
| `geracoes_documentais` | `dict` | `{doador, match, total}` |
| `comparacao_existente` | `str \| None` | O estado de quatro valores, quando fornecido |

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | `estimar_mrca(cm, nasc_doador, mrca_do_kit, relacoes, intervalo_de_geracao)` devolve a estimativa do ano do MRCA, a janela e o método usado | Must | Para 200 cM e doador nascido em 1970, devolve `geracoes` > 0, `metodo` preenchido e `ano` dentro da janela; sem cM, devolve `None` e não lança exceção | 🟢 |
| RF-02 | `validar_comparacao(comparacao)` devolve o contrato de §4.5 sem ler arquivo e sem consultar relógio | Must | A mesma entrada produz o mesmo dicionário em duas chamadas; a função não importa `parsers`, `application` nem a borda HTTP | 🟢 |
| RF-03 | `validar_arquivos(caminho_gedcom, caminho_dna, nome_doador, ano_referencia=None)` lê os dois arquivos, cruza os kits com os matches e devolve uma lista de resultados | Must | Com GEDCOM e CSV sintéticos, devolve um resultado por kit; a árvore é parseada uma vez e reutilizada; nenhum match é inventado | 🟢 |
| RF-04 | A validação por lado calcula a idade por geração do doador e do match e acusa `PROFUNDIDADE_TEMPORAL_INCOMPATIVEL` fora de 12–70 | Must | Caminho com doador nascido em 1985, MRCA em 1650 e 2 gerações no lado do doador resulta em erro, com o código presente | 🟢 |
| RF-05 | A validação por salto acusa `GENITOR_FORA_DA_JANELA_BIOLOGICA` quando um salto datado tem idade < 12 ou > 70 | Must | Salto pai-filho de 11 anos resulta em erro; salto de 31 anos não gera o código | 🟢 |
| RF-06 | A coerência cM × profundidade acusa `CM_INCOMPATIVEL_COM_PROFUNDIDADE` quando a profundidade documental fica a mais de 2 meioses da envoltória publicada | Must | 25 cM com caminho de irmãos (2 meioses) resulta em erro; 200 cM com caminho de 2C (4 meioses) não resulta | 🟢 |
| RF-07 | O MRCA documentado é comparado com a janela estimada e acusa `MRCA_DOCUMENTADO_FORA_DA_JANELA` quando a data exata fica fora por mais de 2 gerações | Must | MRCA documentado em 1650 com cM que estima MRCA em 1880 resulta em erro; a mesma diferença com data `ABT` resulta em `INCONCLUSIVO` | 🟢 |
| RF-08 | O doador vivo em linha incompatível recebe `DOADOR_VIVO_EM_LINHA_INCOMPATIVEL` | Must | Doador nascido em 1985 (vivo em 2026) com conflito crítico recebe o código; doador nascido em 1850 não recebe | 🟢 |
| RF-09 | O status final respeita a precedência e é agregado entre kits pelo pior | Must | Um kit `VALIDADO` e outro `ERRO CRONICO / QUEBRA DE LINHA` produzem resultado final de erro; dois `INCONCLUSIVO` produzem `INCONCLUSIVO` | 🟢 |
| RF-10 | Dados ausentes ou imprecisos produzem `INCONCLUSIVO` com código, nunca erro | Must | Match sem data de nascimento produz `INCONCLUSIVO` e `SEM_DATA_DE_NASCIMENTO`; MRCA com `ABT` produz `INCONCLUSIVO`, `DATA_ESTIMADA` e, se fora da janela, o código de atenção | 🟢 |
| RF-11 | O módulo tem docstrings explicando as fórmulas, os limiares e as fontes, e anotações de tipo nas funções públicas | Should | Inspeção do arquivo mostra a fonte de 12–70, de 122, do prior de 25 e da tabela SCP 4.0; a verificação de tipos do projeto não introduz erro novo | 🟡 |
| RF-12 | Os testes unitários cobrem os três status, todos os códigos críticos e os casos de borda de §7 | Must | A suíte de testes do projeto passa no `.venv`; cada código crítico tem ao menos um teste | 🟢 |
| RF-13 | Caminho por afinidade não é validado como linhagem consanguínea | Must | Caminho com status de afinidade devolve `INCONCLUSIVO` e `AFINIDADE_NAO_BIOLOGICA`; nenhum veredito de erro é emitido só por ser afinidade | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Arquitetura | `core/validator.py` não importa `parsers/`, `application/`, a borda HTTP nem `reporting/`; a fachada de leitura fica em `application/validacao.py` | O núcleo é puro e a árvore entra por parâmetro (ADR-24/25); o ciclo `core/` ↔ `parsers/` já foi fechado | 🟢 |
| Privacidade | Nenhum dado real de DNA/GEDCOM entra em código, teste, fixture ou documentação; só fixture sintética | `.reversa/principles.md#i`; `tests/fixtures/` só tem dado sintético | 🟢 |
| Determinismo | Mesma entrada produz exatamente a mesma saída; ordenações explícitas; sem dependência de `PYTHONHASHSEED` | O projeto já fechou o desempate por `xref_id` e registra a lacuna L-25 | 🟢 |
| Testabilidade | As regras são funções puras; o teste não precisa de banco, rede, borda HTTP ou arquivo real | O projeto usa `tests/fixtures/` e `.venv` | 🟢 |
| Concorrência | n/a: não há estado compartilhado, cache de módulo nem escrita; a validação é pura e reentrante | O projeto já removeu o estado global mutável (ADR-24) | 🟢 |
| Desempenho | A validação é O(nº de saltos + nº de relações candidatas) por comparação; a fachada parseia a árvore uma vez por chamada | O fluxo atual reparseia a árvore a cada requisição; não introduzir segunda passada | 🟡 |
| Compatibilidade | Python 3.14.6 do `.venv`; nenhuma dependência nova | `requirements.txt` é lista de runtime e o projeto evita dependência nova | 🟢 |
| Observabilidade | O resultado carrega `motivo` e `codigos`; não há `print` nem log de dado pessoal | O projeto usa avisos `{code, message}` | 🟢 |
| Documentação | Docstrings explicam o "porquê" dos limiares e citam a fonte e a data de consulta | `.reversa/principles.md#v` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: comparação validada com datas completas
  Dado um doador nascido em 1970 e um match nascido em 1950
  E um MRCA documentado nascido em 1880, com 4 meioses (2 de cada lado)
  E um kit com 200 cM e comparação existente COMPATIVEL
  Quando o validador roda a comparação
  Então o status é VALIDADO
  E não há código de severidade crítica

Cenário: doador vivo ligado a ancestral do século XVII por caminho curto
  Dado um doador nascido em 1985, vivo no ano de referência
  E um MRCA documentado nascido em 1650
  E um caminho com 2 gerações no lado do doador
  Quando o validador roda a comparação
  Então o status é ERRO CRONICO / QUEBRA DE LINHA
  E os códigos incluem PROFUNDIDADE_TEMPORAL_INCOMPATIVEL
  E os códigos incluem DOADOR_VIVO_EM_LINHA_INCOMPATIVEL

Cenário: leitura e cruzamento de arquivos
  Dado um GEDCOM sintético e um CSV de DNA sintético com um kit
  Quando o validador lê e cruza os dois arquivos
  Então devolve um resultado para o kit
  E a árvore é parseada uma vez
  E nenhum match é inventado

Cenário: salto pai-filho com idade impossível
  Dado um caminho com um salto pai-filho de 11 anos
  Quando o validador roda a comparação
  Então o status é ERRO CRONICO / QUEBRA DE LINHA
  E o código GENITOR_FORA_DA_JANELA_BIOLOGICA está presente

Cenário: cM alto contra caminho de irmãos
  Dado um kit com 25 cM
  E um caminho documental de 2 meioses (irmãos)
  Quando o validador roda a comparação
  Então o status é ERRO CRONICO / QUEBRA DE LINHA
  E o código CM_INCOMPATIVEL_COM_PROFUNDIDADE está presente

Cenário: data de nascimento ausente
  Dado um match sem data de nascimento no GEDCOM
  Quando o validador roda a comparação
  Então o status é INCONCLUSIVO
  E o código SEM_DATA_DE_NASCIMENTO está presente
  E nenhum código crítico é inventado

Cenário: data estimada do MRCA
  Dado um MRCA documentado como "ABT 1700"
  E a janela estimada pelo cM não contém 1700
  Quando o validador roda a comparação
  Então o status é INCONCLUSIVO
  E o código MRCA_DOCUMENTADO_FORA_DA_JANELA_ESTIMADO tem severidade de atenção

Cenário: estimativa do MRCA a partir do cM
  Dado um kit com 200 cM e um doador nascido em 1970
  E uma árvore cujo intervalo de geração mediano é 25 anos
  Quando o validador estima o MRCA
  Então devolve um ano estimado, uma janela e o método usado
  E a estimativa não é apresentada como parentesco confirmado

Cenário: caminho por afinidade
  Dado um caminho que chega ao outro ramo por casamento, e não por filiação
  Quando o validador roda a comparação
  Então o status é INCONCLUSIVO
  E o código AFINIDADE_NAO_BIOLOGICA está presente

Cenário: documentação e testes acompanham a entrega
  Dado o módulo de validação implementado
  Quando a suíte do projeto roda no ambiente oficial
  Então todos os testes passam
  E as docstrings citam a fonte dos limiares 12–70, 122 e 25
  E cada código crítico tem ao menos um teste

Cenário: cM sem cobertura publicada
  Dado um kit com um valor de cM que nenhuma relação da versão 4.0 cobre
  E sem a coluna MRCA do kit
  Quando o validador roda a comparação
  Então o status é INCONCLUSIVO
  E o código SEM_COBERTURA_DE_CM está presente

Cenário: múltiplos kits para o mesmo nome
  Dado dois kits do mesmo nome, um VALIDADO e outro ERRO CRONICO / QUEBRA DE LINHA
  Quando o validador agrega os resultados
  Então o resultado final é ERRO CRONICO / QUEBRA DE LINHA
  E os dois resultados por kit continuam disponíveis

Cenário: comparação existente conflitante
  Dado um confronto de quatro estados com status CONFLITANTE
  Quando o validador roda a comparação
  Então o status é ERRO CRONICO / QUEBRA DE LINHA
  E o código CONFLITO_CM_DOCUMENTAL está presente
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem estimativa e sem contrato não há módulo de validação |
| RF-03 | Must | É o "ler e cruzar" pedido pelo operador |
| RF-04, RF-05, RF-06, RF-07 | Must | São os conflitos biológicos críticos que a feature existe para detectar |
| RF-08, RF-09 | Must | O status e a agregação são o produto da feature |
| RF-10 | Must | Evita transformar "não sei" em "quebrou" |
| RF-11 | Should | Documentação e tipos são exigidos pelo projeto, mas não mudam o veredito |
| RF-12 | Must | `.reversa/principles.md#iii` |
| RF-13 | Must | `.reversa/principles.md#iv`: aresta de casamento não é aresta de sangue |
| Integração na tela | Won't (esta feature) | O pedido é o módulo; o contrato de tela é congelado e uma mudança de UI é feature separada (confirmado em §9) |

## 9. Esclarecimentos

### Sessão 2026-10-18

- **Q:** Onde o status do validador deve aparecer nesta entrega?
  **R:** Só módulo + testes. A entrega não toca na tela nem no contrato dos quatro estados; a
  exibição no cartão/relatório fica para uma feature seguinte, se o operador quiser.
- **Q:** Qual valor de cM deve alimentar a estimativa do MRCA?
  **R:** cM total do kit. O maior segmento continua apenas como marca de evidência fraca abaixo de
  15 cM e não entra na estimativa do MRCA.
- **Q:** Qual intervalo de geração usar na conversão de gerações em anos?
  **R:** A mediana dos intervalos pai-filho datados da própria árvore, com fallback de 25 anos quando
  houver menos de 3 amostras. O valor fixo foi descartado.

## 10. Lacunas

Nenhuma lacuna aberta após a sessão de esclarecimentos de 2026-10-18. As três dúvidas iniciais foram
resolvidas em §9.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-18 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-18 | Sessão de esclarecimentos: escopo módulo + testes, cM total e intervalo mediano da árvore com fallback de 25 | reversa |
