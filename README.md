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

Generate a certificate and a private key :

`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

`doh-server --debug --cert [path]cert.pem --key [path]key.pem`

`doh-client --noverify`

### Via Docker

`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes`

`docker build -f Dockerfile -t quart-doh/doh-server .`

`docker run --rm -p 443:443 quart-doh/doh-server`


## Benchmark

Macbook Pro 2019
Processor 2,4 GHz Intel Core i5
Memory 8 GB 2133 MHz LPDDR3

`apib -c 100 -d 60 @benchmark_get_url.txt`
<pre>
HTTP/1.1
Duration:             60.024 seconds
Attempted requests:   15757
Successful requests:  15757
Non-200 results:      0
Connections opened:   100
Socket errors:        0

Throughput:           262.511 requests/second
Average latency:      376.399 milliseconds
Minimum latency:      103.082 milliseconds
Maximum latency:      2846.580 milliseconds
Latency std. dev:     456.340 milliseconds
50% latency:          202.483 milliseconds
90% latency:          862.423 milliseconds
98% latency:          2044.469 milliseconds
99% latency:          2409.697 milliseconds

Client CPU average:    0%
Client CPU max:        0%
Client memory usage:    0%

Total bytes sent:      2.25 megabytes
Total bytes received:  5.08 megabytes
Send bandwidth:        0.30 megabits / second
Receive bandwidth:     0.68 megabits / second
</pre>
