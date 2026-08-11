# Onboarding QA

1. Ative o ambiente virtual (`venv\Scripts\activate`) e execute o servidor com `python app.py`.
2. Acesse `http://127.0.0.1:5000` no navegador.
3. Observe o formulário de upload de GEDCOM. O formulário deve ser a única área principal visível.
4. Selecione um arquivo `.ged` válido e clique no botão correspondente para "Carregar e Analisar".
5. Verifique se, após o arquivo carregar com sucesso, as abas "Buscar Conexão no GEDCOM" e "Analisador de DNA" aparecem logo abaixo.
6. Em qualquer fluxo que exiba o grafo de resultados (pesquisa de caminho ou matches de DNA), inspecione a inicialização do Mermaid.js visualizando o código fonte ou console do navegador para confirmar que `securityLevel` está definido como `'strict'`.
7. O spinner de carregamento deve ser exibido durante submissões de formulário, travando interações adicionais até a página recarregar.
