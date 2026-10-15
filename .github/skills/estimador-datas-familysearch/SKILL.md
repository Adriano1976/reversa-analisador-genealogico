---
name: estimador-datas-familysearch
description: >-
  Estima faixas aproximadas de datas de nascimento e casamento para preencher
  lacunas em árvores genealógicas, a partir de premissas heurísticas
  configuráveis (idade no casamento, intervalo entre filhos). Use esta skill
  sempre que o usuário pedir para estimar, calcular ou preencher data de
  nascimento ou casamento faltante em uma árvore genealógica, trabalhar com
  arquivo GEDCOM (.ged) que tenha pessoas sem data de nascimento, perguntar em
  que ano alguém deve ter nascido a partir de dados parciais, ou pedir para
  completar lacunas de datas em pesquisa familiar brasileira ou portuguesa.
  Produz datas no formato GEDCOM (ABT ano) com faixa de incerteza, nunca
  sobrescreve datas já documentadas, e sinaliza estimativas biologicamente
  implausíveis, como mãe com menos de 12 ou mais de 45 anos no parto.
---

# Estimador de Datas Genealógicas

Estima anos aproximados de nascimento e casamento quando faltam dados documentados,
a partir de eventos relacionados conhecidos (casamento, nascimento do primeiro filho).

## Origem e limite das premissas

As premissas padrão (homem casa aos 25, mulher aos 21, primeiro filho 1 ano após o
casamento, 2 anos entre irmãos) são heurísticas genealógicas comuns, **não uma norma
oficial do FamilySearch ou de qualquer outra instituição**. Sempre apresente os
resultados como estimativas, nunca como fatos documentados.

Essas premissas refletem padrões aproximados de países ocidentais no século XX.
Para famílias de Sergipe e de Portugal/Açores em séculos anteriores (contexto comum
nas árvores deste usuário), é comum encontrar casamentos e primeiros filhos bem mais
jovens — ajuste os parâmetros de `Premissas` antes de aplicar em massa, e prefira
calibrar a partir de casos documentados da própria árvore quando houver pelo menos
alguns.

## Como usar

1. Rode `scripts/estimador.py` (ou importe `EstimadorGenealogico`) para gerar as
   estimativas a partir do dado conhecido (ano de casamento, ano do 1º filho, etc.).
2. Toda estimativa sai como `Estimativa(ano, minimo, maximo)`, com `.gedcom()` no
   formato `ABT <ano>` pronto para entrar em um arquivo `.ged`.
3. **Nunca aplique a uma pessoa que já tem `BIRT`/`DATE` ou `MARR`/`DATE` no GEDCOM.**
   A skill é só para preencher lacunas, não para corrigir ou substituir dados
   existentes.
4. Quando a mãe tiver ano de nascimento conhecido, passe-o para
   `casamento_a_partir_do_primeiro_filho` — a função sinaliza em
   `alerta_idade_parto` se a idade estimada no parto for implausível (abaixo de 12 ou
   acima de 45 anos), para revisão manual antes de aceitar a estimativa.
5. Ao aplicar em um GEDCOM inteiro: primeiro liste as pessoas sem `BIRT`/`DATE` (ver
   `references/aplicacao_gedcom.md`), depois busque, para cada uma, um evento
   relacionado com data conhecida (casamento próprio, nascimento de um filho,
   casamento dos pais) antes de estimar. Apresente as estimativas em tabela para
   revisão do usuário — não grave direto no arquivo sem confirmação.

## Referências

- `references/aplicacao_gedcom.md` — como localizar pessoas sem data e qual evento
  relacionado usar como ponto de partida, por tipo de lacuna.
