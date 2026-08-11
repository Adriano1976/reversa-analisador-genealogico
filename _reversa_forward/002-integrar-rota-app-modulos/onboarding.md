# Onboarding — integrar a rota index() do app.py com os modulos reconstruidos

> Identificador: `002-integrar-rota-app-modulos`
> Pré-requisitos: Python 3, dependências instaladas (`pip install -r analisador-genealogico/requirements.txt`)

## Como testar a feature pela primeira vez

1. **Preparação do ambiente**
   - Instale as dependências: `pip install -r analisador-genealogico/requirements.txt`
   - Confirme que os módulos movidos importam: `python -c "from analisador_genealogico.reconstructed import upload, path_search, dna_analysis"` (ajuste o nome do subpacote conforme a decisão de implementação)

2. **Suíte de testes**
   - Rode a suíte: `python -m pytest tests/` (esperado: 47 passed sem regressão)
   - Confirme que os imports dos testes foram atualizados para o novo caminho dos módulos

3. **Smoke manual (3 fluxos)**
   - Inicie a aplicação: `python analisador-genealogico/app.py`
   - Abra `http://localhost:5000`
   - **Fluxo 1 — Upload GEDCOM:** envie um `.ged` (ex.: os arquivos em `analisador-genealogico/uploads/`); confira a lista de nomes carregada
   - **Fluxo 2 — Path Search:** selecione duas pessoas; confira `text_path` e o gráfico Mermaid
   - **Fluxo 3 — DNA Analysis:** envie um CSV de matches + `root_name`; confira resultados ordenados por cM e a tabela de descartados
   - **Caso de erro:** envie um `root_name` inexistente e confira mensagem de erro com `success=False`

4. **Verificação de regressão visual**
   - Confira que o `templates/index.html` não foi alterado (diff vazio no template) e que o Mermaid continua renderizando com `securityLevel: 'strict'`
