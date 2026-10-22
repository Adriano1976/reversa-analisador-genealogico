# Contrato: DNA sem correspondência na árvore (cartões)

> Identificador: `039-dna-sem-correspondencia`
> Data: `2026-10-22`
> Rota: `POST /` com `action=dna_analysis`
> Formato: resposta `200 text/html` (a mesma página de resultados da análise de DNA)
>
> **Vigente:** o contrato atual é o dos **cartões**, na seção "Atualização 2026-10-22 (E003)";
> as seções 3–4 descrevem a primeira entrega, quando o item era um bloco separado.

## 1. Request

Nenhum campo novo. O contrato da análise de DNA continua o mesmo:

| Campo | Tipo | Obrigatório | Conteúdo |
|-------|------|-------------|----------|
| `action` | `str` | sim | `dna_analysis` |
| `gedcom_filename` | `str` | sim | Referência da árvore armazenada |
| `matches_csv_filename` | `str` | não | Referência do CSV armazenado; tem precedência sobre o upload |
| `matches_csv` | arquivo | não | CSV enviado no próprio formulário |
| `root_name` | `str` | sim | Nome da raiz, como o operador digitou |
| `promover` | `str` | não | Promoções já feitas, no formato `nome\|pid\|motivo`; não é usado pelo bloco |

## 2. Response

- `200` com a página de resultados, quando a análise conclui.
- O bloco é um fragmento HTML **dentro** dessa página; não há rota, JSON ou download novo.
- Ele só aparece quando a análise tem pelo menos um item que atenda à regra (seção 3).
- A resposta de erro (`404` para raiz inexistente, `422` para CSV/arquivo inválido) não muda e não
  contém o bloco.

## 3. Regra de presença

O bloco existe quando há um **descarte** com:

1. `cm >= 40,0`;
2. nenhum candidato com `compativel == True`;
3. `norm_name(csv_name)` diferente de todos os nomes com cartão aceito.

O item é por **(nome, kit)**; dois kits descartados do mesmo nome, sem cartão, são duas linhas. A
ordem é cM decrescente, com desempate por nome normalizado, nome cru e kit.

## 4. Contrato do HTML

| Elemento | Contrato |
|----------|----------|
| Container | `<details>` com `id="sem-correspondencia"`, classe que o distingue dos cartões (`bloco-sem-correspondencia`) e `open` |
| Título | `DNA sem correspondência na árvore (N)`, com N igual ao número de itens |
| Posição | Depois dos cartões de resultado e **antes** de `Matches descartados`, dentro da guarda dos descartes |
| Aviso | Texto que contém "não é parentesco documentado", "sinal de DNA a investigar" e "o cM sozinho não define a relação" |
| Recorte | Texto que informa que os mesmos nomes continuam na lista completa, com o motivo de cada recusa |
| Colunas | `Nome no CSV`, `Kit`, `cM`, `MRCA estimado` |
| MRCA | `<número> gerações`, com vírgula decimal e sem zeros à direita; ausente → `não informado` |
| Proibido | "Parentesco documental", "conexão com", diagrama, confronto, hipóteses, candidato, motivo e qualquer formulário/botão de promoção |

Exemplo mínimo (dados sintéticos, sem relação com o arquivo real):

```html
<details class="card bloco-sem-correspondencia" id="sem-correspondencia" open>
  <summary class="sumario-do-cartao">
    <div class="card-header"><h5 class="mb-0">DNA sem correspondência na árvore (1)</h5></div>
  </summary>
  <div class="card-body">
    <p class="alerta-aviso">
      Estes matches têm cM alto, mas a árvore não tem ninguém com nome compatível.
      Isto não é parentesco documentado: é um sinal de DNA a investigar.
      O cM sozinho não define a relação.
    </p>
    <p class="text-muted small">
      Os mesmos nomes estão na lista completa de matches descartados, com o motivo de cada recusa.
      O MRCA é a estimativa do relatório de DNA, não um ancestral documentado.
    </p>
    <table class="table table-sm align-middle">
      <thead><tr><th>Nome no CSV</th><th>Kit</th><th>cM</th><th>MRCA estimado</th></tr></thead>
      <tbody>
        <tr><td><strong>Fulano de Tal</strong></td><td>TG0000001</td><td>150,0</td><td>3,27 gerações</td></tr>
      </tbody>
    </table>
  </div>
</details>
```

## 5. Estados vazios e de borda

| Situação | Comportamento |
|----------|---------------|
| Nenhum item atende à regra | O bloco não é renderizado; nenhum espaço reservado fica na página |
| Análise com zero cartões, mas com um descarte de 150,0 cM sem compatível | O bloco é renderizado; a lista completa também |
| Item sem MRCA no CSV | A célula mostra `não informado`; nenhum número é inventado |
| Nome com cartão em outro kit | Nenhum kit desse nome entra no bloco; os descartes continuam na lista completa |
| Descarte com candidato compatível | Não entra no bloco; continua na lista completa com a promoção |
| Descarte de 39,9 cM | Não entra no bloco; continua na lista completa |

## 6. Determinismo e idempotência

- A mesma análise (mesmos cartões, mesmos descartes, mesmos cM/MRCA) produz o mesmo conjunto na
  mesma ordem, byte a byte no fragmento, independentemente da ordem do CSV ou do processo.
- O bloco não grava, não lê arquivo e não altera a lista completa; recarregar a mesma análise
  reproduz o mesmo HTML.

## 7. Erros

| Situação | O que acontece |
|----------|----------------|
| Raiz inexistente / CSV sem colunas / CSV ilegível | As exceções de domínio atuais; `404`/`422` com a tela de entrada, sem o bloco |
| Falha de persistência | A análise continua; o bloco não depende dela e aparece normalmente se houver itens |
| Erro inesperado | A tela de erro atual; nenhum bloco parcial |

Não há caminho de erro novo, timeout novo ou idempotência de escrita: o bloco é leitura pura.
**Timeout:** nenhum novo; o bloco não faz I/O e é renderizado junto com a página da análise, no tempo
que a rota já leva.

## 8. Compatibilidade

| Elemento | Garantia |
|----------|----------|
| `SHA_DA_TELA` (tela de entrada) | Não muda: o bloco está dentro do `{% if skipped_matches %}`, falso na entrada |
| Lista "Matches descartados" | Mesmos itens, ordem, motivos e candidatos |
| CSV de descartes | Mesmas nove colunas e mesmos cabeçalhos |
| Histórico (`skipped_match`) | Sem campo ou migração |
| Request da análise | Sem campo novo |

## 9. Testes que prendem este contrato

- `tests/test_sem_correspondencia.py` — seletor, ordem, limites, exclusão por cartão, MRCA ausente,
  HTML do bloco, zero itens, zero cartões.
- `tests/test_icone_de_atalho.py` — hash da tela de entrada.
- `tests/test_csv_de_descartes.py` — nove colunas e conteúdo da planilha.
- `tests/test_cartoes_recolhiveis.py` / `tests/test_estilo_da_tela.py` — o bloco não é um cartão de
  resultado nem o rodapé de descartes.

## Atualização 2026-10-22 (E001/E002)

O `<details id="sem-correspondencia">` **foi removido**. O contrato agora é o **cartão** na
lista de resultados, com o mesmo tratamento dos cartões "Parentesco documental não
encontrado":

- `<details class="card cartao-do-resultado" id="resultado-N">`, com o título
  `Análise de conexão com <strong>{csv_name}</strong>` e o rótulo
  `Parentesco documental não encontrado` na segunda linha do cabeçalho;
- as cinco seções do cartão (parentesco documental, evidência genética, possibilidades,
  confronto e observações), com `documentary.path = None` e `mermaid_data = None` — sem
  diagrama; o **MRCA estimado** do kit aparece na seção 2 (Evidência genética);
- sem "usar este candidato" e sem qualquer ação de promoção;
- o item continua na lista completa de descartes e no CSV de nove colunas; o resumo dos
  resultados diz que os N cartões sem correspondência também estão lá;
- o corte é **20,0 cM**; a análise real tem 68 cartões (8 aceitos + 60 sem correspondência)
  e 448 descartes.

O request, o status HTTP, os erros e os timeouts continuam os mesmos.

## Atualização 2026-10-22 (E003)

A E003 é limpeza interna: o HTML, o request, o status, os erros e os timeouts **não
mudam**. O que muda é de onde vem a contagem do resumo:

- `core.sem_correspondencia.selecionar` **sai**; o módulo fica só com a regra
  (`CM_MINIMO_SEM_CORRESPONDENCIA`, `nomes_com_cartao_aceito` e `elegivel`);
- `ResultadoDeAnalise.sem_correspondencia` passa a ser a **tupla dos cartões** marcados,
  na ordem da tela; o template usa apenas `|length`;
- a análise real continua com **68 cartões** (8 + 60) e **448 descartes**; a lista
  completa, o CSV de nove colunas e a promoção não mudam;
- `tests/test_sem_correspondencia.py` tem 15 testes; a suíte completa fica em
  **1409 passed, 9 skipped**.
