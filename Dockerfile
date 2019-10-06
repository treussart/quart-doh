# docker build -f Dockerfile -t quart_doh/doh-server .
# docker run --rm -p 443:443 quart_doh/doh-server
FROM python:3.7
EXPOSE 443/tcp
WORKDIR /src
COPY quart_doh /src/quart_doh
COPY Pipfile.lock /src
COPY Pipfile /src
COPY cert.pem /src
COPY key.pem /src
RUN pip install pipenv
RUN pipenv sync
ENV PYTHONPATH "${PYTHONPATH}:/src"
CMD pipenv run python quart_doh/server.py
