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

# Dependencias primeiro, em camada propria: ela so e refeita quando o pin muda. O
# `requirements.txt` traz as versoes fixadas, incluindo `psycopg2-binary`, que existe em
# wheel `cp314` para Windows e para Linux — nao ha compilacao local.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# O codigo vem depois, para uma edicao em `src/` nao invalidar a camada de dependencias.
COPY src/ /app/src/

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
