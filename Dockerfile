# docker build -f Dockerfile -t quart-doh/doh-server .
# docker run --rm -p 443:443 quart-doh/doh-server
FROM python:3.7
EXPOSE 443/tcp
WORKDIR /src
COPY src /src
COPY Pipfile.lock /src
COPY Pipfile /src
COPY cert.pem /src
COPY key.pem /src
RUN pip install pipenv
RUN pipenv sync
CMD pipenv run python server.py
