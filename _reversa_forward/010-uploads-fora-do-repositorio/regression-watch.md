# Regras sob vigilância — feature `010-uploads-fora-do-repositorio`

> Data: `2026-10-09`
> Origem dos itens: `_reversa_forward/010-uploads-fora-do-repositorio/legacy-impact.md`
> Natureza desta entrega: **nenhuma regra de domínio modificada**. Os itens abaixo vigiam o contrato de
> operação que a feature passou a declarar e as regras que ela **não** podia tocar.

## Itens sob vigilância

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|------------------------------|---------------------|-------------------|
| **W001** | `_reversa_sdd/upload-gedcom/contracts.md#2.2` | A pasta continua resolvida **uma vez, no import**, ancorada no arquivo do app, com `ANALISADOR_UPLOAD_FOLDER` sobrepondo | presença | Resolução por diretório corrente; leitura do ambiente a cada requisição; caminho de escrita divergindo do de leitura |
| **W002** | `_reversa_sdd/upload-gedcom/contracts.md#2.2` (linha "Remoção") e `_reversa_sdd/state-machines.md#5` | A aplicação **nunca** apaga um arquivo enviado; o expurgo é ferramenta separada, por manifesto e com simulação | ausência | Qualquer `unlink`, `os.remove`, `shutil.rmtree` ou `tempfile` em `src/`; expurgo automático no runtime |
| **W003** | `_reversa_sdd/upload-gedcom/contracts.md#2.1` | O nome no disco continua `<16 hexadecimais>__<nome visível>`, com a chave vinda do conteúdo | presença | Forma fechada afrouxada; chave aleatória em vez de derivada do conteúdo; renomeação de arquivo na migração |
| **W004** | `docker-compose.yml`, serviço `app` (feature 010) | A pasta canônica do host é montada no alvo interno que o app deriva (`/app/src/uploads`) | presença | Volta do ponto de montagem para `./src/uploads`; alvo interno diferente do derivado por `__file__` |
| **W005** | `README.md` §Configuração de execução e §Testes (feature 010) | A tabela de configuração lista `ANALISADOR_UPLOAD_FOLDER`, e a paridade é executada por `tests/rodar_paridade.py` | presença | Tabela incompleta outra vez; `README.md` apontando o `harness.py` direto como caminho de execução |
| **W006** | `_reversa_sdd/parity/harness.py` (feature 010, `D-07`) | O instrumento de paridade permanece **byte a byte igual** ao que a extração descreve | ausência de alteração | Qualquer edição no `harness.py`: a paridade passaria a medir com régua diferente da congelada, e a afirmação de 100 % perderia valor |
| **W007** | `tests/manutencao_de_uploads.py` (feature 010, `D-06`) | O expurgo remove **apenas** o que está no manifesto e **nunca** remove cópias idênticas: elas são relatadas | presença | Remoção fora do manifesto; deduplicação automática; remoção sem conferência de `sha256`; seguir link simbólico |
| **W008** | `_reversa_sdd/addenda/006`, `007` e `008` (vigentes) | Os adendos continuam válidos: o leiaute em disco não mudou e nenhum arquivo do operador foi renomeado ou removido | presença | Arquivo do operador ausente ou com hash diferente do inventário de `evidence/inventario-origem.txt` |

## Observações (sem peso de regressão)

Estas não são regras extraídas de código; entram aqui porque são o resultado desta entrega e ainda não
foram confirmadas por uma re-extração:

- **`RF-01` a `RF-08` implementados e medidos.** As evidências estão em
  `_reversa_forward/010-uploads-fora-do-repositorio/evidence/`, e o resumo com os números está no §16 do
  `onboarding.md` da feature.
- **O expurgo real não foi executado.** Os 18 arquivos de resíduo de instrumento (6.631 bytes) continuam
  em `src/uploads/`, e o manifesto está gerado e revisável em `evidence/manifesto-residuo.txt`. A remoção
  é decisão do operador.
- **Quatro arquivos sintéticos de sonda** ficaram no destino canônico durante as provas
  (`*__sonda_t014.ged` e `*__sonda_t014.csv`). São de fixture, não do operador.
- **Três grupos de duplicatas foram encontrados no dado do operador** e preservados: três cópias da
  árvore unificada, três de `Famílias_Sergipanas.csv` e duas de `Adriano_Santos.ged`. A decisão sobre
  elas continua aberta e é do operador.
- **O `harness.py` segue capaz de sujar a pasta real** se for invocado direto, sem o invólucro. É
  consequência declarada de `D-07` e está registrada no `investigation.md` da feature.

## Histórico de re-extrações

| Data | Extração | Veredito |
|------|----------|----------|
| — | — | Nenhuma re-extração executada desde esta entrega |

## Arquivadas

| ID | Item | Motivo | Data |
|----|------|--------|------|
| — | — | Nenhum item arquivado | — |
