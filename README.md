# quart-doh

quart-doh is a simple DOH (DNS Over HTTPS) server. It resolves DNS query on HTTP.

## Implementation

### RFC 8484

* https://www.rfc-editor.org/rfc/rfc8484.txt

### Json implementation

* https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/

## Quick start

`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

`pipenv sync -d`

`pipenv run doh_server`

## Use with Firefox

in about:config edit::

    network.trr.mode;3
    network.trr.uri;https://127.0.0.1/dns-query


For the URI, add your URI for your reverse proxy serving your Quart app.

Firefox seems to only accept port 443.

## Installation

### Via Pip

`pip install quart-doh`

Then :

Generate a certificate in the folder 'site-packages/quart_doh' :

`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

`doh-server --debug`

`doh-client --noverify`

### Via Docker

`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

`docker build -f Dockerfile -t quart-doh/doh-server .`

`docker run --rm -p 443:443 quart-doh/doh-server`
