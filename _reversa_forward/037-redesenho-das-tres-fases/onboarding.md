# Onboarding: testar a feature `037` pela primeira vez

> Identificador: `037-redesenho-das-tres-fases`
> Data: `2026-10-20`
> Para quem nunca viu esta feature: siga na ordem. Cada passo diz o que fazer e o que deve aparecer.

## 0. Antes de começar

Você precisa de:

- Windows com PowerShell;
- o repositório em `D:\Projetos\reversa_analisador_gelealogico`;
- o `.venv` do projeto (Python 3.14) — **não** use o Python global;
- nenhum arquivo real de GEDCOM ou DNA à mão: os passos criam uma árvore **sintética**.

## 1. Conferir o ambiente

```powershell
cd D:\Projetos\reversa_analisador_gelealogico
.\.venv\Scripts\python.exe --version
```

Esperado: `Python 3.14.x`.

## 2. Rodar a suíte antes de olhar a tela

```powershell
py -3.14 -m pytest -q
```

Esperado: tudo verde, com os pulos de sempre. Anote o número de testes aprovados — ele vai ser comparado no fim.

## 3. Criar a árvore sintética

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'tests'); from fixtures.sample_gedcom import SAMPLE_GED; open(r'$env:TEMP\arvore_sintetica.ged','w',encoding='utf-8').write(SAMPLE_GED); print('ok')"
```

O arquivo fica em `%TEMP%\arvore_sintetica.ged`. Ele é sintético de propósito (Princípio I): nenhum dado de pessoa real.

## 4. Subir a aplicação

```powershell
.\.venv\Scripts\python.exe src\app.py
```

Abra o endereço que o processo imprime (por padrão `http://127.0.0.1:5000`).

> Se a variável `DATABASE_URL` estiver no ambiente e o driver não estiver instalado, a tela mostra um aviso não bloqueante. Não é defeito desta feature.

## 5. Primeira olhada: a navegação

1. A tela deve mostrar **três fases na barra lateral**, numeradas: `1. Árvores GEDCOM`, `2. Buscar Conexão no GEDCOM`, `3. Analisador de DNA`.
2. **Não deve haver** fileira de abas horizontais.
3. A fase 1 deve estar ativa (fundo destacado + peso diferente, não só cor).

## 6. Fase 1 — lista, contadores e envio

1. A tabela lista as árvores já armazenadas, com linhas alternadas.
2. Acima da tabela devem aparecer **dois contadores**: quantas árvores existem e quantas estão disponíveis. Nenhum outro número.
3. Na coluna de gerenciamento, `Abrir` e `Apagar` ficam empilhados, com espaço entre eles. `Abrir` só aparece no item disponível; `Apagar` aparece em todos, com o motivo escrito ao lado quando indisponível.
4. No bloco de envio, escolha `%TEMP%\arvore_sintetica.ged`: o texto do bloco deve trocar do padrão para o **nome do arquivo**.
5. Confirme o envio. Esperado: mensagem de sucesso igual à de sempre e a tela voltando **na fase 2**.

## 7. Fase 2 — busca documental

1. A caixa de status deve nomear a árvore aberta e oferecer `Escolher outra árvore`.
2. Os dois campos ficam lado a lado, com o botão `Encontrar Conexão` na mesma linha (em tela larga).
3. Digite `Car` em "Pessoa 1": a lista de sugestões deve abrir com `Carlos Silva` e filtrar a cada tecla.
4. Use ↓/↑ para percorrer e `Enter` para escolher. O foco deve permanecer no campo.
5. Digite algo que não existe (ex.: `Zzz`) e confirme a busca: **o texto digitado deve ser aceito**, e a busca deve responder do jeito de sempre.

## 8. Fase 3 — DNA

1. A caixa de status deve dizer o modo de análise.
2. O bloco 1 (CSV) deve agrupar a escolha da lista e o envio de arquivo.
3. O bloco 2 deve ter o nome e o botão `Analisar Matches de DNA` na mesma linha.
4. Digite `joao` (sem acento) em um campo de nome com a lista aberta: `Joao Silva` deve aparecer — o filtro ignora acento e caixa.

## 9. Degradação sem JavaScript

No navegador, desative o JavaScript (DevTools → Settings → Debugger → Disable JavaScript) e recarregue.

Esperado: as três fases continuam no documento, a fase 1 continua visível, e os campos de nome voltam a ser **campos de texto comuns**. Nenhum formulário pode ficar inutilizável.

## 10. Telefone

No modo responsivo, escolha 320 px de largura.

Esperado: a barra lateral vira faixa horizontal de três botões; nenhuma fase produz rolagem horizontal; a ação principal de cada fase fica abaixo do seu campo.

> A tabela de seis colunas rola **dentro** do próprio contêiner — isso é esperado e não conta como rolagem da página.

## 11. Tema

1. Acione o controle de tema: deve ir ao escuro, com o rótulo virando `Tema claro`.
2. Recarregue: a escolha deve ser lembrada.
3. Confira os textos das fases e da tabela no escuro — nada pode sumir.

## 12. Fechar a conferência

```powershell
py -3.14 -m pytest -q
git diff --stat
```

Esperado:

- suíte verde, com **mais** testes do que no passo 2;
- o diff lista `src/templates/index.html`, `src/assets/app.css` e os arquivos de teste — **nenhum** arquivo de `src/application/`, `src/ports/` ou `src/core/`;
- nenhum arquivo real em `uploads/` aparece no `git status`.

## Checklist manual (o que o teste automatizado não alcança)

- [ ] A lista do combobox abre ao digitar e fecha ao clicar fora
- [ ] `Esc` fecha sem apagar o texto
- [ ] `Enter` escolhe a opção destacada
- [ ] O foco nunca sai do campo durante a navegação por setas
- [ ] O leitor de tela anuncia o número de resultados (ou, sem leitor, a região viva existe no markup)
- [ ] Com JavaScript desligado, tudo continua utilizável
