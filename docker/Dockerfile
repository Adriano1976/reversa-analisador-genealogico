# Imagem da aplicacao (D-10, D-11).
#
# O contexto de build e a RAIZ do projeto, e o `.dockerignore` de la e lista de PERMISSAO:
# so `requirements.txt` e `src/` entram. O `COPY` abaixo e estreito de proposito — duas
# origens nomeadas, nunca a raiz —, para que o `.dockerignore` seja defesa em profundidade e
# nao a unica barreira. O GEDCOM real do operador vive em `src/uploads/`, reexcluido no fim
# daquele arquivo (Principio I).
#
# O Dockerfile mora em `docker/` e o contexto e a raiz: o Docker o le do disco pelo `-f`, e
# ele NAO precisa estar dentro do contexto.

FROM python:3.14-slim

WORKDIR /app

# Identidade do BUILD, para a defasagem ficar visivel sem abrir o container.
#
# O codigo entra por `COPY src/ /app/src/`, entao a imagem e um RETRATO do dia do build:
# editar `src/` no host NAO chega ao container, e nao havia como saber a idade do que estava
# rodando sem entrar no container e ler os arquivos — foi assim que uma imagem de 2026-10-09
# continuou servindo o codigo anterior a feature 011 sem ninguem notar.
#
# Duas marcas resolvem isso, e nenhuma delas depende de o operador lembrar de nada:
#
#   `org.opencontainers.image.revision` -> o commit, quando `REVISAO` e informado no build
#   `/app/CONSTRUIDO_EM`                -> o instante do build, gravado sempre
#
# A revisao e opcional porque `git` nao esta na imagem e `.git/` nao entra no contexto de
# build (o `.dockerignore` e lista de permissao): o commit so pode vir de fora, e um valor
# padrao honesto e melhor do que um rotulo vazio.
#
# O `ARG` e o `LABEL` que os produzem ficam no FIM do arquivo, e isso NAO e questao de estilo:
# um `ARG` declarado aqui em cima passaria a fazer parte da chave de cache do
# `RUN pip install --no-cache-dir -r requirements.txt`, e mudar `REVISAO` reinstalaria todas as
# dependencias. **Medido em 2026-10-11**, na primeira versao desta mudanca: o build imprimiu
# `#10 13.71 Installing build dependencies: started` com o `REVISAO` novo, exatamente a camada
# que o rebuild do dia a dia precisa manter. Aqui fica so o registro da decisao.

# Dependencias primeiro, em camada propria: ela so e refeita quando o pin muda. O
# `requirements.txt` traz as versoes fixadas, incluindo `psycopg2-binary`, que existe em
# wheel `cp314` para Windows e para Linux — nao ha compilacao local.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# O codigo vem depois, para uma edicao em `src/` nao invalidar a camada de dependencias.
COPY src/ /app/src/

# Carimbo do INSTANTE do build, dentro da imagem. Fica aqui, e nao no comeco, por causa do
# cache: esta camada muda a cada build, e tudo o que viesse DEPOIS dela seria refeito junto —
# `COPY src/` e o `pip install` ficariam sem cache justamente no rebuild que o operador faz
# toda vez que mexe no codigo.
#
# `date` vem do proprio `python:3.14-slim` (Debian com coreutils), entao nao ha dependencia
# nova nem pacote instalado so para carimbar.
RUN date -u +%Y-%m-%dT%H:%M:%SZ > /app/CONSTRUIDO_EM

# A revisao vira rotulo AQUI — depois do `pip install` e do `COPY` do codigo, que sao as
# camadas caras. Um `ARG` so afeta o cache do que vem DEPOIS dele; por isso ele nasce neste
# ponto do arquivo, e nao no topo (ver o comentario de identidade do build, no comeco).
ARG REVISAO=desconhecida
LABEL org.opencontainers.image.revision=$REVISAO

# A pasta de upload e resolvida por `__file__` em `src/app.py` (`_pasta_uploads`), entao
# dentro do container ela e `/app/src/uploads` — e e exatamente onde o compose monta o bind
# mount. Nao ha variavel de ambiente envolvida: escrita e leitura usam o mesmo caminho.
#
# O endereco de escuta e `0.0.0.0` DENTRO do container porque a publicacao de porta do Docker
# chega pelo IP do container, nunca pelo loopback dele. O ato explicito de atender a rede
# continua existindo, e ele mora na linha `ports:` do compose, publicada em `127.0.0.1`
# (D-10) — que e onde ele e verificavel.
ENV ANALISADOR_HOST=0.0.0.0
ENV ANALISADOR_PORT=5000

EXPOSE 5000

# `src/app.py` sobe o waitress e mantem a guarda de instancia unica: no Linux aquele bloco
# cai no ramo `SO_REUSEADDR = 0`, e um segundo processo no mesmo container e recusado.
#
# O interpretador e o do container. O `.venv/` do host NAO e copiado — ele esta fora da lista
# de permissao do `.dockerignore`, e o proprio `.gitignore` ja o exclui do repositorio.
CMD ["python", "src/app.py"]
