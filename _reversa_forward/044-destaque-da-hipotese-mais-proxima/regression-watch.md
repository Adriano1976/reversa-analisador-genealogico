# Regression watch: destaque da hipótese mais próxima

> Identificador: `044-destaque-da-hipotese-mais-proxima`
> Data: `2026-10-22`
> Escopo: o que precisa continuar verdadeiro quando `/reversa` rodar de novo sobre este código.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|---|---|---|---|---|
| W001 | `src/core/relationship_hypotheses.py` (`BANDA_DE_DESTAQUE`, `MAXIMO_DE_DESTAQUES`) | O destaque continua sendo **1,5×** a menor distância, com teto **3** | valor | a tela passa a destacar quatro, ou a banda vira um número fixo de linhas |
| W002 | `src/core/relationship_hypotheses.py` (`destaque_das_candidatas`) | O destaque **marca** a candidata e **não** remove ninguém da lista | presença | `possible_relationships` encolhe para três |
| W003 | `src/core/relationship_hypotheses.py` (`destaque_das_candidatas`) | A ressalva traz o tamanho do conjunto, a negativa de confirmação e o GEDCOM como fonte do parentesco | presença | o texto passa a dizer "mais provável" ou perde a contagem |
| W004 | `src/templates/index.html` (bloco 3) | Nenhuma linha da tabela é escondida, e a destacada é uma linha dela | presença | a tabela passa a mostrar só as destacadas |
| W005 | `src/core/relationship_hypotheses.py` | `distancia_da_media` é `\|média publicada − cM\|`, e a soma de qualquer coisa continua proibida | valor | aparece peso, média ponderada ou percentual |

## Observações (sem peso de regressão)

- 🟡 **Os três casos de referência são do arquivo real, não inventados**: 9,05 cM (um destaque),
  42,6 cM (dois) e 154,5 cM (três). Eles existem no `Famílias_Sergipanas.csv` e estão presos por
  teste; se a fonte mudar a média de alguma linha, o teste fica vermelho e a banda precisa ser
  reavaliada — o que é o comportamento desejado.
- 🟡 **A distribuição medida depende do recorte:** 423/32/1 sobre os **456 kits** do CSV e 57/10/1
  sobre os **68 cartões** da análise. Não são números contraditórios — são populações diferentes,
  e o cartão (que exige casar com a árvore) concentra valores mais altos, onde o empate é mais
  comum.
- 🟡 **O ponto de partida é um só nos dois recortes:** o kit `AZ4078391` (154,5 cM) é o único caso
  de três destaques. Se um dia houver mais de um, não é defeito — é a banda encontrando outro
  empate de três vias.
- 🟡 **A caixa não usa cor de veredito.** `border-left` na cor primária e fundo `--surface-2`; nada
  de verde ou vermelho, porque o destaque não decide nada.
- 🟡 **A convenção de `meioses` é declarada, e o ponto aberto é outro.** A coluna de
  `SCP40_ROWS` é "a chave da relação, não o total do caminho" — está documentado em
  `core/validator.py`, que deriva o total da chave. O que merece decisão é
  `core/evidence_comparison._janela_do_documental` passar um **total** a `meioses_window`,
  cuja coluna guarda **chaves**. Ver a correção registrada no `regression-watch` da 043.
