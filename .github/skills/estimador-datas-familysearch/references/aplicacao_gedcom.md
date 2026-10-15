# Aplicando o estimador a um arquivo GEDCOM (.ged)

## 1. Localizar quem não tem data

Uma pessoa (`INDI`) pode estar sem data de nascimento de duas formas:

- Sem bloco `1 BIRT` nenhum.
- Com `1 BIRT`, mas sem `2 DATE` dentro dele (às vezes só há `2 PLAC`).

O mesmo vale para `1 MARR` dentro de uma família (`FAM`).

## 2. Escolher o evento de partida, por tipo de lacuna

Antes de estimar, procure — nessa ordem de preferência — um evento relacionado
com data conhecida:

1. **Casamento da própria pessoa** (`FAM` em que ela é `HUSB`/`WIFE`, com
   `MARR`/`DATE`) → use `nascimentos_a_partir_do_casamento`.
2. **Nascimento do filho mais velho** (menor data entre os `CHIL` da família) →
   use `casamento_a_partir_do_primeiro_filho`, passando o ano de nascimento da
   mãe se ele já for conhecido, para checar o alerta de idade no parto.
3. **Nascimento de irmãos com data conhecida** → use `projetar_filhos` a partir
   do irmão mais próximo com data, ajustando o `intervalo_entre_filhos` pela
   posição na fratria.
4. **Nada disso disponível** → não estime; marque como "sem base para estimativa"
   em vez de inventar uma faixa sem apoio em nenhum evento da própria árvore.

## 3. Como registrar a estimativa

- Use sempre `Estimativa.gedcom()` → produz `ABT <ano>`, compatível com o
  parser GEDCOM padrão.
- Nunca grave sobre uma pessoa que já tem `DATE` documentada.
- Ao propor as estimativas para o usuário, apresente em tabela com colunas:
  nome, lacuna (nascimento/casamento), evento usado como base, ano estimado,
  faixa, e alerta (se houver). Peça confirmação antes de escrever no arquivo.

## 4. Calibrando as premissas para esta árvore

Famílias de Sergipe e dos Açores em séculos anteriores ao XX frequentemente
casavam e tinham o primeiro filho mais cedo do que os padrões ocidentais do
século XX. Se a árvore já tiver uma quantidade razoável de casos documentados
(casamento + nascimento dos cônjuges, por exemplo), vale calcular a média real
desses casos e usar como `Premissas` customizada em vez dos valores padrão.
