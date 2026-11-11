# Desempenho medido — árvore grande e CSV de matches

> Medido em `2026-11-10`, com os arquivos reais da pasta de uploads.
> GEDCOM: `Adriano_Santos_v3_tratado.ged` (12,5 MB, **19.403 pessoas**).
> CSV: `DNA_Nordestino.csv` (783 segmentos, **606 kits**).

## O que o operador espera, e por quê

O tempo percebido é quase todo **parse do GEDCOM**, não o CSV.

| Etapa | Tempo medido | Quando acontece |
|---|---:|---|
| Parse do GEDCOM | **92 s a 243 s** | ao abrir/escolher a árvore; só de novo se o cache esvaziar |
| 1ª análise do CSV (índices frios) | **21,6 s a 30,4 s** | primeira análise daquela árvore no processo |
| 2ª análise do CSV (cache quente) | **11,5 s a 15,9 s** | análises seguintes |
| Agrupamento das regiões | **0,005 s** | em toda análise |

A variação grande entre medições é da máquina (o mesmo parse levou 92 s numa janela e 243 s em
outra, com o computador sob carga). A razão entre as etapas se manteve.

## Por que o parse é caro

Perfil do `ged4py` (biblioteca de leitura de GEDCOM):

- o arquivo é aberto com `io.FileIO` **sem buffer**, e a leitura é **caractere por caractere**:
  **25,6 milhões** de chamadas a `read` para 12,5 MB;
- a construção do índice de nível 0 varre o arquivo inteiro (~113 s no perfil) e a materialização
  dos registros lê o arquivo outra vez (~183 s no perfil, com overhead do profiler).

Passar um buffer em memória (`BytesIO`) **não resolveu**: 96,9 s contra 116,2 s com buffer de
8 MB — o custo é o laço Python por caractere, não o syscall.

## O que foi feito nesta rodada

1. **Memoização de `norm_name`** (`lru_cache`, 50 mil entradas). A análise chama a normalização
   ~69 mil vezes; medido, a taxa de acerto no primeiro CSV foi de **72 %** (49.880 acertos para
   19.269 misses). O valor é puro, então nenhuma decisão muda.
2. **Relógio no indicador de carregamento**: mostra a etapa ("Cruzando os matches…", "Lendo o
   GEDCOM…") e os segundos decorridos, em vez da frase fixa.
3. **Medição no log**: cada análise passa a registrar `medicao: analise_dna: N ms (cartoes=X,
   regioes=Y)`; o parse já registrava `medicao: carregar_arvore`.

## O que ainda pode ser feito, com o custo de cada caminho

| Caminho | Ganho esperado | Risco |
|---|---|---|
| Cache persistente da árvore em disco | elimina o parse de 92–243 s em reinícios | alto: os registros do `ged4py` carregam referência ao arquivo e não são serializáveis como estão |
| Construir os offsets de nível 0 por conta própria e chamar `read_record` | corta ~metade do parse (elimina a varredura de índice) | alto: mexe em detalhe interno do parser e no contrato de paridade |
| Trocar o parser de GEDCOM | 5–10× | alto: muda a forma dos registros que o núcleo consome |
| Pré-aquecer os índices ao escolher a árvore | desloca ~20 s da análise para a abertura | baixo, mas não reduz o total |
| Manter o servidor vivo e a mesma árvore selecionada | 2ª análise em diante: 11–16 s | nenhum — é o comportamento atual |

## Recomendação operacional

- Escolher a árvore **pela lista**, uma vez, e não reenviá-la a cada análise: reenviar cria outro
  arquivo e paga o parse de novo.
- Não reiniciar o servidor entre a escolha da árvore e a análise.
- Com o cache ligado (`ANALISADOR_CACHE_DE_ARVORE`, padrão), a segunda análise é a metade da
  primeira.
