# User Stories — Fluxo `upload-gedcom`

> Re-extração de **2026-10-05** (nível **Completo**). Artefato novo: o nível `essencial` não o gerava.
> Persona única do sistema. Fontes: `upload-gedcom/requirements.md`, `upload-gedcom/design.md`, `domain.md` §3.5, `permissions.md`
> Escala de confiança: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

---

## Persona

**Genealogista Genético.** Trabalha sozinho, na própria máquina. Tem a árvore da família em um arquivo GEDCOM exportado de um site de genealogia e a lista de matches de DNA em CSV exportado do GEDmatch (ou similar). **Não há login**: a aplicação não sabe quem ele é. 🟢

## História principal

> **Como** genealogista genético, **quero** carregar minha árvore GEDCOM no analisador **para que** as outras duas análises (busca de caminho e cruzamento com DNA) tenham sobre o que operar.

**Valor de negócio:** é a porta de entrada do sistema. Sem upload bem-sucedido, **nada** mais funciona. 🟢

**Regras que o usuário não vê, mas recebe:**

| Regra | Efeito percebido |
| --- | --- |
| A validação é de **conteúdo** (`0 HEAD`), não de extensão | Um GEDCOM legítimo sem `.ged` é aceito — ele não é recusado por detalhe de nome 🟢 |
| O arquivo é gravado sob **chave derivada do conteúdo** | Reenviar a mesma árvore não duplica nem sobrescreve nada 🟢 |
| A **extensão original é preservada** | Um CSV enviado por engano continua `.csv`, e não é renomeado para `.ged` 🟢 |
| O teto de corpo é de **16 MB**, aplicado antes de ler | Um arquivo gigante é recusado **sem** consumir disco 🟢 |
| O parâmetro de continuidade é uma **chave**, não uma sessão | Ele pode continuar a análise após recarregar a página, porque o valor viaja no formulário 🟢 |

## Histórias secundárias

### US-U-02 — Recusa clara de arquivo inválido

> **Como** genealogista, **quero** ser informado **por que** meu arquivo foi recusado **para que** eu saiba o que corrigir, em vez de receber um erro genérico.

#### Critérios de aceite

```gherkin
Dado que enviei um arquivo que não é GEDCOM
Quando o upload é processado
Então a tela diz "Arquivo não reconhecido como GEDCOM: não começa com a declaração 0 HEAD."
E nenhum arquivo é gravado em disco

Dado que enviei um arquivo vazio
Quando o upload é processado
Então o motivo informado é "arquivo vazio"

Dado que enviei um arquivo de 20 MB
Quando o upload é processado
Então a resposta tem status HTTP 413
E a mensagem é "Arquivo maior que o limite de 16 MB."
```

### US-U-03 — Recarga limpa da árvore

> **Como** genealogista, **quero** que carregar uma árvore nova **substitua** a anterior por completo **para que** eu não veja resultado misturando duas famílias.

#### Critérios de aceite

```gherkin
Dado que uma árvore com 1.000 pessoas está carregada
Quando carrego uma árvore diferente com 10 pessoas
Então o estado contém exatamente as 10 pessoas da nova árvore
E nenhuma pessoa da anterior permanece consultável
```

### US-U-04 — Continuidade entre requisições

> **Como** genealogista, **quero** que a análise seguinte use exatamente a árvore que carreguei **para que** o resultado corresponda ao arquivo que escolhi.

#### Critérios de aceite

```gherkin
Dado que carreguei uma árvore e recebi a chave do arquivo
Quando submeto uma busca de caminho
Então o servidor re-parseia o arquivo a partir da chave que enviei
E o resultado é calculado sobre a árvore daquele arquivo

Dado que enviei um valor de chave manipulado, fora da forma aceita
Quando submeto a busca
Então a resposta é "Erro: Arquivo '<valor>' não existe mais."
E nenhum arquivo fora da pasta de upload é aberto
```

### US-U-05 — Recuperação após erro de parsing

> **Como** genealogista, **quero** que um GEDCOM malformado **não** derrube a aplicação **para que** eu possa tentar outro arquivo.

#### Critérios de aceite

```gherkin
Dado que enviei um GEDCOM sintaticamente inválido
Quando o parse falha
Então a tela mostra "Erro ao processar GEDCOM: <detalhe>"
E a aplicação continua no ar
E a árvore anterior permanece íntegra
```

## Fluxo resumido

1. Abre `/` e recebe o formulário. 🟢
2. Escolhe o arquivo `.ged` e envia. 🟢
3. O sistema lê o conteúdo inteiro, valida-o e só então grava sob a chave de conteúdo. 🟢
4. O sistema parseia `INDI`/`FAM`, monta o grafo e devolve a **lista ordenada de nomes**. 🟢
5. A tela confirma a carga e guarda a **chave de conteúdo** no formulário. 🟢

## Exceções e o que o usuário vê

| Exceção | Mensagem |
| --- | --- |
| Nenhum arquivo no campo | `"Nenhum arquivo GEDCOM enviado."` 🟢 |
| Arquivo sem nome | `"Nenhum arquivo selecionado."` 🟢 |
| Conteúdo recusado | `"Arquivo não reconhecido como GEDCOM: {motivo}."` 🟢 |
| Corpo acima do teto | `"Arquivo maior que o limite de 16 MB."` com `413` 🟢 |
| Falha de parse | `"Erro ao processar GEDCOM: {e}"` 🟢 |
| Chave ausente ou inválida | `"Erro: Arquivo GEDCOM não encontrado."` / `"Erro: Arquivo '{valor}' não existe mais."` 🟢 |

## O que esta história **não** cobre

| Fora de escopo | Por quê |
| --- | --- |
| Autenticação ou escolha de usuário | O sistema **não tem** usuário, sessão, papel ou permissão (`permissions.md`) 🔴 |
| Seleção de qual árvore usar | Só existe uma árvore por vez, e ela é a do arquivo endereçado pela chave 🟢 |
| Histórico de uploads | Nada é registrado: o arquivo é gravado e nunca apagado pelo sistema 🔴 |
| Correção de problemas no GEDCOM | O GEDCOM é tratado como autoridade; o sistema **avisa**, não corrige 🟢 |

## Lacunas que afetam esta história 🔴

- **`L-16`:** com 4 threads e estado global reescrito por requisição, dois uploads/análises simultâneos podem trocar de árvore entre o parse e o uso.
- **`P-05`:** o CSV de DNA **não** passa por validação de conteúdo — a assimetria em relação ao GEDCOM não tem decisão registrada.
- **`P-04`:** `app.secret_key` está no código sem consumidor; vira chave de forja caso alguém introduza sessão.
- **`L-21`:** não há decisão de negócio sobre não persistir resultados.

---

*Gerado pelo Reversa-Writer em 2026-10-05 (re-extração, nível completo).*
