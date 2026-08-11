# Investigation

## Pesquisa de Fundo
A interface do usuário é concentrada em um único arquivo de template `templates/index.html`. O arquivo original utiliza Bootstrap 5 para a estrutura visual e componentes (abas, cartões, forms). A inicialização do Mermaid.js é feita através do CDN no final do corpo da página.
O `app.py` expõe variáveis Jinja2 (como `gedcom_filename`, `message`, `success`, `all_names`, `path_result`, `dna_results`, `skipped_matches`) que o template deve processar e renderizar.

## Segurança do Mermaid
Na versão original, a inicialização ocorre com:
`mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });`
A documentação do Mermaid afirma que `loose` permite renderizar tags HTML, o que é um vetor conhecido de XSS se o input não for higienizado. Mudar para `strict` converte automaticamente tags não seguras e protege o renderizador, sacrificando caso o código original fizesse uso pesado de injeções HTML nos rótulos de vértices. A mitigação definida é testar visualmente.
