# Sondas de matching de nomes (ferramenta de medicao)

Este diretorio guarda o **utilitario** que mede a decisao do motor de matching
(`core/matching.py`) sobre os **arquivos reais** de `src/uploads/`, e nao o resultado dele.
Nenhuma sonda daqui escreve em `src/uploads/`: elas so leem.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `therezinha_escolha.py` | Reproduz o caso `Therezinha Carvalho do Nascimento Souza` (CSV) x `Soraia Carvalho do Nascimento Souza` (GEDCOM): mostra quem o motor escolhe, com os numeros de `given`, `token`, `partial` e intersecao que decidiram |
| `therezinha_contraprova.py` | Monta uma arvore MINIMA com e sem o sobrenome que falta, para isolar a causa: com o nome exato na arvore o motor acerta; sem ele, cai na Soraia |
| `therezinha_decisiva.py` | A pergunta que separa "achou a pessoa certa" de "achou o nome maior": se a Soraia perder o `Souza`, a Therezinha passa a vencer |
| `therezinha_panorama.py` | Roda a analise COMPLETA sobre o GEDCOM e o CSV reais e lista todos os cartoes em que o nome do GEDCOM difere do nome do CSV |
| `identidade_medir.py` | Compara cinco definicoes possiveis de "nome divergente" (cru, normalizado, tokens, prenome, prenome + similaridade) e mede quantos cartoes cada uma marca |
| `identidade_regra.py` | Mede a regra que ficou implementada em `core/identidade_do_match.py`: quantos cartoes ficam `confirmada`, `grafia` e `a_confirmar`, com a lista de cada grupo |
| `identidade_e2e.py` | Monta o par real em arvore minima, renderiza o template com o resultado do nucleo e imprime a coluna do indice e o aviso do cartao |
| `corrigir_therezinha_ensaio.py` | O ensaio da correcao do dado real: mede antes e depois **numa copia**, sem tocar no arquivo ativo |
| `corrigir_therezinha.py` | A correcao aplicada ao dado real: guardas, backup, gravacao com a chave nova e conferencia |
| `corrigir_therezinha_verificar.py` | A verificacao final pela tela, pelo POST de producao, sobre o dado ja corrigido |
| `bfs_alcance.py` | Cruza os pares (raiz, match) da analise real e conta quantos cartoes a correcao da busca recupera |
| `bfs_efeito_no_cartao.py` | Mostra o cartao da Therezinha antes e depois, com a busca corrigida aplicada por `monkeypatch` (o codigo de producao nao e tocado) |
| `bfs_balanco.py` | Balanco por PESSOA: quantos cartoes ganharam caminho e quantos perderam (tem de ser zero) |
| `bfs_varredura.py` | Amostra deterministica de 1 a cada 40 pessoas da arvore: medida de alcance do defeito fora do funil do matching |
| `bfs_verificar_na_tela.py` | O cartao dela no HTML renderizado, depois da correcao |
| `identidade_medir.py` | (acima) as cinco definicoes de nome divergente |
| `regras_antes_depois.py` | Compara as regras candidatas de desempate nos 62 cartoes: quantos trocam de pessoa, quantos perdem cartao |
| `regras_detalhe.py` | Detalha os 10 casos de idade impossivel: quantos tem alternativa melhor e quantos nao tem |
| `janela_verificar_na_tela.py` | A coluna e o aviso de janela de vida no HTML renderizado |
| `gedmatch_1936_cruzar.py` | Cruza as pessoas da imagem do GEDmatch (Manoel de 1936, pais, esposa) com as arvores |
| `homonymo_onde_esta_1936.py` | Varredura de TODOS os .ged do projeto pelo Manoel de 1936 |
| `homonymo_idade_1936.py` | Primeira busca do nascido em 1936 nos GEDCOMs ativos |
| `v2_procurar_1936.py` | Procura no Adriano_Santos_V2.ged as pessoas da imagem do GEDmatch |
| `v2_comparar_arvores.py` | Compara V1, V2 e o GEDCOM antigo: quem tem quem |
| `v2_busca_decisiva.py` | Busca por DATA (1930-40, pais por janela) em vez de por nome |
| `v2_qual_arvore_casa_mais.py` | Roda a analise em V1 e V2 com o mesmo CSV: conexoes, caminhos, descartes |
| `grafico_manoel.py` | Os dados que alimentam o grafico do cartao do Manoel (caminho, MRCA, casal, Mermaid) |

## Como rodar

```powershell
$py = 'D:\Projetos\reversa_analisador_gelealogico\.venv\Scripts\python.exe'
$env:PYTHONIOENCODING = 'utf-8'   # os caminhos tem seta (→) e acentos

& $py therezinha_escolha.py
```

## Regras que valem para qualquer reuso

1. Estas sondas **leem** `src/uploads/` e nunca escrevem la: `therezinha_contraprova.py` e
   `therezinha_decisiva.py` montam a arvore de teste em memoria e gravam um `.ged`
   temporario **ao lado de si mesmas**, removido no fim.
2. O GEDCOM e o CSV reais tem milhares de registros: `therezinha_panorama.py` leva alguns
   minutos e usa ~2 GB de memoria.
3. Elas medem o motor de producao (`build_ged_indexes`, `match_candidates`, `dna_analysis`),
   e nao uma reimplementacao da regra: uma copia da regra mediria a copia.
