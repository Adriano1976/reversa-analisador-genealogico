# Onboarding: imprimir o resultado de uma pessoa

> Identificador: `050-imprimir-resultado-por-pessoa`
> Data: `2026-10-26`
> Para quem vai testar a feature pela primeira vez, sem conhecer o código.

## 1. O que você vai ver

Cada cartão de resultado da análise de DNA — o bloco "Análise de conexão com ..." — ganha um comando
**Imprimir** no cabeçalho, ao lado do "Voltar". Ele abre o diálogo de impressão do navegador com um
documento de **uma pessoa**: as cinco seções do cartão, os anexos abertos e o diagrama do caminho
numa folha própria no fim.

## 2. Pré-requisitos

- Windows com o projeto em `D:\Projetos\reversa_analisador_gelealogico`
- O interpretador oficial é o `.venv` do projeto (Python 3.14)
- Os quatro navegadores instalados: Chrome, Edge, Firefox e Safari (se houver)

## 3. Preparar arquivos sintéticos (nunca use arquivo real)

O teste usa **fixture sintética**, como manda o Princípio I. Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -c "from tests.fixtures.sample_dna import DNA_GED, DNA_CSV_OITO_CONEXOES; open('arvore-sintetica.ged','w',encoding='utf-8').write(DNA_GED); open('matches-sinteticos.csv','w',encoding='utf-8').write(DNA_CSV_OITO_CONEXOES)"
```

Isso cria `arvore-sintetica.ged` (a árvore) e `matches-sinteticos.csv` (oito conexões). A raiz do
exemplo é **Carlos Silva Souza**.

## 4. Subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

A saída informa o endereço (`Servindo com waitress em http://0.0.0.0:5000`). Abra
`http://127.0.0.1:5000` no navegador.

## 5. Rodar a análise

1. Na fase 1, envie `arvore-sintetica.ged` (ou escolha a árvore já na lista).
2. Na fase 3, envie `matches-sinteticos.csv` e informe a raiz **Carlos Silva Souza**.
3. Clique em analisar. A tela mostra a lista de cartões — no exemplo, oito.

## 6. Imprimir uma conexão

1. Clique em **Imprimir** no cartão de uma pessoa (não precisa abrir o cartão antes).
2. O diálogo de impressão abre. Na pré-visualização, confira:
   - [ ] aparece **só** aquele cartão — nenhum outro nome, nenhum formulário, nenhuma barra de fases;
   - [ ] o topo identifica a árvore, o CSV e a raiz, e mostra "Impresso em ...";
   - [ ] as cinco seções estão lá, inclusive as tabelas que estavam recolhidas;
   - [ ] o diagrama do caminho está numa folha própria, no fim, com título;
   - [ ] não aparecem o "Voltar", o chevron nem o próprio botão "Imprimir";
   - [ ] o rodapé com a origem aparece em todas as folhas (anote se não aparecer);
   - [ ] os selos de estado estão legíveis, com borda e texto escuro.
3. Salve como PDF (opção do próprio diálogo) em `evidence/` — **só com fixture sintética**.
4. Feche o diálogo (imprimindo ou cancelando).

## 7. O que deve acontecer depois de fechar

- [ ] O cartão volta a ficar **fechado** (se estava fechado antes).
- [ ] A lista continua na mesma página.
- [ ] Nada foi recarregado: a tela não pisca e o resultado não é recalculado.

## 8. Casos de borda

| Caso | Como testar | O que deve acontecer |
|------|-------------|----------------------|
| Cartão fechado | Imprimir sem abrir | Imprime aberto, com os anexos; depois volta a fechar |
| Sem caminho documental | Uma conexão que não tem caminho | Sai o texto do caminho e **nenhuma folha de diagrama** |
| Tema escuro | Ligar o tema escuro e imprimir | A pré-visualização sai **clara**, com tinta escura |
| Teclado | Tab até o botão, Enter | O diálogo abre e o cartão **não** recolhe nem abre |
| Cancelar | Abrir o diálogo e cancelar | Tela volta ao estado anterior, sem resíduo |
| Sem internet | Desligar a rede e imprimir | O texto sai; o desenho pode faltar — e não pode sair quadro vazio |

## 9. Roteiro nos quatro navegadores

Repita o passo 6 em cada um e registre o resultado:

| Navegador | Isola o cartão | Diagrama em folha própria | Rodapé em todas as folhas | Selos legíveis | Observações |
|-----------|----------------|---------------------------|---------------------------|----------------|-------------|
| Chrome | | | | | |
| Edge | | | | | |
| Firefox | | | | | |
| Safari | | | | | |

> A numeração "página N de M" **não** é entregue pelo documento (ver `roadmap.md#D-07`). Ela pode
> aparecer no rodapé nativo do navegador; deixe a opção de cabeçalho/rodapé ligada para conferir.

## 10. Conferir que a impressão não chama o servidor

1. Abra o DevTools (F12) → aba **Network** → filtro **Fetch/XHR**.
2. Clique em **Imprimir**.
3. A lista deve continuar vazia. Nenhuma requisição, nenhuma análise recalculada.

## 11. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| O documento mostra a página inteira | A folha de estilo não carregou (`GET /app.css` com erro) | Recarregar; conferir o console |
| O diagrama sai em branco | Bloqueio de CDN (sem rede) ou o desenho não terminou | Conferir a rede; reimprimir depois de abrir o cartão |
| O rodapé aparece só na última folha | Navegador não repete `position: fixed` | Anotar o navegador e a versão em `evidence/` (`R-05`) |
| Selo com fundo branco e texto invisível | Regra de impressão do selo não carregou | Recarregar; conferir `@media print` na folha |
| Nenhum botão "Imprimir" | Estado sem resultados (tela de entrada) | É o esperado: não há cartão para imprimir |

## 12. Limpeza

```powershell
Remove-Item arvore-sintetica.ged, matches-sinteticos.csv
```

Se os arquivos de teste ficaram na pasta de uploads da aplicação, aposente-os pela própria lista —
o sistema nunca apaga, só move para `_aposentados/`.
