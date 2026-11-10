# Adendo: grupos de triangulação — a evidência que vem de vários matches ao mesmo tempo

> Identificador: `055-grupos-de-triangulacao`
> Data: `2026-11-09`
> Cenário: **legado** (âncora em `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`,
> `_reversa_sdd/data-dictionary.md` e `_reversa_sdd/c4-components.md`)

## Vigência

Vigente desde 2026-11-09.

## Resumo da entrega

O analisador confrontava **um match por vez** com a árvore; o que ele não sabia — porque nunca teve o
dado — é que três matches podem compartilhar a **mesma faixa** do mesmo cromossomo, que é a evidência
mais forte de um ancestral comum **entre eles**. A feature passou a receber o **CSV de triangulação do
GEDmatch** (uma linha por par de kits, com `B37 Start`/`B37 End` e cM) como entrada opcional da Fase 3,
agrupou os pares que se sobrepõem de forma **fechada** e confrontou cada grupo com os cartões que a
análise já produzia. O grupo recebe um desfecho — **convergente**, **dividido**, **parcial** ou **sem
ancestral documentado** — e o bloco diz onde existe um ancestral que a árvore **não** tem.

A decisão de projeto mais importante da entrega é o **teste de fechamento**: grupo é o conjunto de três
ou mais kits com interseção comum **e todos os pares registrados**. Sobreposição geométrica sozinha não
é triangulação — medido na amostra real, 1.535 regiões têm interseção comum e apenas **28 grupos
fecham**. Sem o teste, o "maior grupo" do arquivo seria uma região de 0,40 Mb com 51 kits, que é
exatamente o falso positivo que a feature existe para recusar. Região curta com muitos kits recebe o
alerta de **acúmulo**, e não de parentesco.

O arquivo funciona **sem árvore** (mostra os grupos sem desfecho) e, junto da análise de DNA, com
desfecho. Nada do que existia mudou: o grupo **não** cria cartão, não soma cM entre pares, não altera
caminho, cM, veredito nem o CSV de descartes.

**25 de 25 ações concluídas.** Suíte: **2.046 passam / 9 pulados / 5 falham**, e as cinco falhas são
exatamente as pré-existentes da linha de base (quatro de `test_characterization_mermaid` e o literal
`1. Lista de Matches (CSV)`). São **32 testes novos**. Desempenho medido na amostra de 1.650 linhas:
**0,577 s** no total (parse 0,464 s + agrupamento 0,113 s), com **28 grupos** cobrindo **116 dos 351
kits**.

A tela de entrada mudou de **bytes**, não de pixels: `SHA_DA_TELA` foi de `3487986a…` (51.218) para
`82258c2b…` (52.768, **+1.550 bytes**), e o delta é o formulário da Fase 3 — o bloco de grupos não
aparece em `GET /`.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/architecture.md` | §3. Componentes e estrutura de pacotes | `componente-novo` | Dois módulos de núcleo puro (`core.triangulacao`, `core.triangulacao_no_cartao`), um adaptador (`parsers.triangulacao_gedmatch`), um caso de uso (`application.triangulacao`), um reportador (`reporting.csv_dos_grupos`) e uma rota (`POST /grupos.csv`) |
| `_reversa_sdd/architecture.md` | §5. O Fluxo que Define o Sistema | `regra-alterada` | O fluxo de DNA ganha um passo **derivado e opcional** depois do núcleo: quando o CSV de triangulação vem, os grupos são agrupados e classificados; exceção ali vira observação do arquivo, nunca bloqueio |
| `_reversa_sdd/domain.md` | §1. Glossário de Domínio | `regra-nova` | Entram **triangulação**, **grupo fechado** e **região de acúmulo**; o grupo é uma unidade de evidência que não decide parentesco |
| `_reversa_sdd/domain.md` | §2. A Regra Central do Domínio | `regra-alterada` | Os três eixos continuam valendo. O que se acrescenta é um **quarto tipo de leitura**, derivada e sem veredito: a evidência de grupo, que pode apontar um ancestral que o GEDCOM não tem e nunca reescreve o parentesco |
| `_reversa_sdd/domain.md` | §3.2. Evidência genética | `regra-nova` | Nenhum cM é somado entre pares: o grupo guarda o **mínimo e o máximo de par**, e a extensão da interseção em pares de bases. O piso de 10 cM **marca** o par mais fraco e não exclui o grupo |
| `_reversa_sdd/domain.md` | §3.8. Leitura tolerante do CSV | `regra-alterada` | O CSV de pares ganha adaptador próprio; a recusa por forma passa a **nomear o campo correto** ("CSV de Triangulação" / "Lista de Matches"), em vez de dizer que faltam colunas de Nome e cM |
| `_reversa_sdd/domain.md` | §3.9. Ordem de apresentação dos resultados | `regra-alterada` | Os grupos têm ordem própria e determinística — cromossomo em ordem natural, depois posição inicial, depois conjunto de kits — e **não** a ordem dos cartões |
| `_reversa_sdd/data-dictionary.md` | §8. Payload do núcleo → tela | `delta-de-dados` | `ResultadoDeAnalise` ganha `grupos` (padrão `()`), e o contexto da tela ganha `grupos`, `grupos_dados` e `triangulacao_sem_arvore`. Nenhuma tabela, coluna ou migração: o banco continua com as 6 tabelas |
| `_reversa_sdd/c4-components.md` | Componentes por unidade | `delta-de-contrato-externo` | A ação `triangulacao_analysis` entra no despacho **pré-árvore**; a ação `dna_analysis` ganha o campo opcional `triangulacao_csv`; a rota `POST /grupos.csv` entra no regime de `/descartes.csv` |

Nenhuma regra de matching, de cM, de travessia de grafo ou de persistência foi alterada. O único
comportamento existente que mudou é a **mensagem** de recusa de um arquivo de pares enviado no campo de
matches — antes "Colunas de Nome e cM não encontradas", agora o nome do campo correto. Para o CSV de
matches, nada mudou.

## Regras sob vigilância

Os itens `W001` a `W011` estão descritos em
`_reversa_forward/055-grupos-de-triangulacao/regression-watch.md`. Os quatro itens sem peso de
regressão (limiar de acúmulo, export nativo, reparo removido e custo do bloco) estão na seção de
observações do mesmo arquivo.

## Fontes

- `_reversa_forward/055-grupos-de-triangulacao/requirements.md`
- `_reversa_forward/055-grupos-de-triangulacao/roadmap.md`
- `_reversa_forward/055-grupos-de-triangulacao/actions.md`
- `_reversa_forward/055-grupos-de-triangulacao/progress.jsonl`
- `_reversa_forward/055-grupos-de-triangulacao/legacy-impact.md`
- `_reversa_forward/055-grupos-de-triangulacao/regression-watch.md`
- `_reversa_forward/055-grupos-de-triangulacao/evidence/SHA_DA_TELA.md`
- `_reversa_forward/055-grupos-de-triangulacao/evidence/medicoes.md`

## Atualização 2026-11-09

**O insumo desta entrega foi removido pela feature 056.** O operador decidiu não enviar mais o
CSV de triangulação; as regiões passam a nascer do próprio CSV de matches do Ancestor Projects.
Saíram de cena: o formulário da Fase 3, o campo opcional na ação de DNA, a ação
`triangulacao_analysis`, o adaptador de pares e o teste de fechamento. A rota `/grupos.csv` virou
`/regioes.csv`, e o bloco passou a se chamar **"Regiões compartilhadas"**.

O que **continua valendo** deste adendo: o desfecho documental derivado dos cartões, o alerta de
acúmulo, o agrupamento por cromossomo e a leitura derivada que não cria cartão. O que **não vale
mais**: o teste de fechamento dos pares, o piso de 10 cM como marca (virou filtro) e o nome do
bloco. Ver `_reversa_sdd/addenda/056-regioes-compartilhadas.md`.
