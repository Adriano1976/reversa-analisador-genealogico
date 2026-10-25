# Onboarding: testar o sistema de log completo

> Identificador: `049-sistema-de-log`
> Data: `2026-10-25`
> Para quem vai ver a feature funcionando pela primeira vez, sem ler o código.

## 1. Antes de começar

1. O interpretador oficial é o `.venv/` do projeto — não use o global:
   `.venv\Scripts\python.exe --version`
2. A pasta de upload precisa ter **pelo menos uma árvore** para os testes de auditoria fazerem
   sentido. Uma árvore sintética serve; arquivo real do operador **não** deve ser usado em teste
   (Princípio I).
3. Se a aplicação já estiver no ar, pare-a: a guarda de instância única recusa a segunda.

## 2. Rodar sem container (Windows local)

1. Suba a aplicação:

   ```powershell
   .venv\Scripts\python.exe src\app.py
   ```

2. Observe a primeira linha no console. Ela diz o endereço e o número de threads — antes era um
   `print`, agora é uma linha de log com o mesmo texto:

   ```
   Servindo com waitress em http://127.0.0.1:5000 com 4 threads
   ```

3. Abra `http://127.0.0.1:5000`. A tela é a mesma de antes: esta feature **não muda a tela**.
4. Confira a pasta criada ao lado de `src/`:

   ```powershell
   Get-ChildItem logs
   ```

   Você deve ver `analisador.log` e `analisador.auditoria.<data>.log`.

## 3. Ver o identificador de requisição

1. Abra o navegador, clique com o botão direito → Inspecionar → aba Rede, e recarregue a página.
2. Selecione a requisição de `GET /` e olhe os **cabeçalhos da resposta**: existe
   `X-Request-ID: <8 hex>`. Recarregue de novo: o valor muda.
3. No arquivo `logs/analisador.log`, a linha de acesso daquela requisição traz o **mesmo** valor:

   ```
   acesso: GET / -> 200 (12 ms) id=a3f19c2e
   ```

   Se você forçar um erro (passo 5), a linha de erro traz o mesmo `id` — é o que liga o erro ao
   acesso que o causou.

## 4. Ver a auditoria das duas tentativas de aposentar

Este é o desfecho que fechou a decisão 14 do projeto.

1. Na tela, aba "Árvores", clique em **Apagar** em um arquivo e confirme.
2. Abra `logs/analisador.auditoria.<data>.log`. Deve haver uma linha com `acao=aposentar`,
   `desfecho=sucesso`, a **chave de 16 hexadecimais** do arquivo (não o nome dele), a extensão, o IP
   e o `id` da requisição.
3. Force a falha: com o arquivo já aposentado, use o botão voltar do navegador e clique em Apagar de
   novo. A tela mostra a mensagem de falha de sempre, e a auditoria ganha **outra** linha, agora com
   `desfecho=falha`.
4. Confirme que a linha **não** contém o nome do arquivo:

   ```powershell
   Select-String -Path logs\analisador.auditoria.*.log -Pattern 'Sandro' -SimpleMatch
   ```

   Nenhum resultado é o esperado.

## 5. Ver a mensagem nova e o traceback no log

1. Envie um arquivo que não é GEDCOM (renomeie qualquer `.txt` para `.ged`).
2. A tela mostra:

   ```
   Erro ao processar GEDCOM: O detalhe foi registrado no log.
   ```

   **Antes** desta feature a tela mostrava o texto interno da exceção (por exemplo, o erro do
   parser). Agora o rastro está no arquivo.
3. Em `logs/analisador.log`, procure a linha de erro daquela requisição: ela traz o traceback, com o
   `id` da requisição.

## 6. Ver a máscara de privacidade

1. Rode uma análise de DNA com um CSV sintético cujo conteúdo force erro, e cujo texto de exceção
   carregue um e-mail ou um identificador de kit (`AB1234567`).
2. No log, os dois aparecem mascarados; o resto da mensagem continua legível.
3. O teste automatizado equivalente é o de privacidade da suíte (ver §8) — ele afirma que **nenhum
   nome** de pessoa da árvore aparece no log capturado.

## 7. Rodar em container

1. Preencha o `.env` (usuário, senha, banco e `DATABASE_URL`) — o compose recusa subir sem ele.
2. Suba:

   ```powershell
   docker compose up -d --build
   ```

3. Acompanhe o fluxo padrão do container:

   ```powershell
   docker compose logs -f app
   ```

   As linhas de acesso aparecem ali, com o `id`. A rotação é do orquestrador (`json-file`, 5 × 5 MB).
4. A trilha de auditoria aparece no host em `./logs/`, porque a pasta é volume publicado.
5. **Negativo útil:** comente o volume `./logs` no `compose.yaml` e suba de novo. A aplicação **sobe
   normalmente**, escreve no fluxo padrão e avisa uma vez que a pasta não pôde ser usada. Nenhuma
   requisição falha por causa disso.

## 8. Rodar o que prova

```powershell
# a suíte inteira (marco: 1656 passam / 9 pulados)
.venv\Scripts\python.exe -m pytest -q

# só os testes desta feature
.venv\Scripts\python.exe -m pytest tests\test_registro_de_auditoria.py tests\test_identificador_de_requisicao.py tests\test_privacidade_do_log.py -q

# paridade continua em 100 %
.venv\Scripts\python.exe tests\rodar_paridade.py
```

> Os nomes dos três arquivos de teste acima são a proposta do plano; se o `actions.md` os renomear, o
> comando acompanha.

## 9. O que **não** mudou (para não procurar defeito onde não há)

- A tela, o HTML e o `ETag` das artes: byte a byte os mesmos.
- Os `404` das artes, o `413` do teto de upload e o `400` do `Host` recusado.
- As mensagens de **erro de domínio** (as de `application/traducao.py`): elas continuam com o texto
  do domínio, porque são tradução de erro previsto, não de exceção inesperada.
- O banco: nenhuma tabela nova, nenhuma coluna nova.
