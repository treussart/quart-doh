import contextlib
import multiprocessing
import os
import time
from collections import namedtuple

import dns.message
import pytest
import requests

from quart_doh.constants import DOH_CONTENT_TYPE
from quart_doh.server import main
from quart_doh.utils import doh_b64_encode

known_servers = [
    # URL
    "https://127.0.0.1:8000/dns-query",
    "https://dns.google/dns-query",
    "https://cloudflare-dns.com/dns-query",
    "https://doh.opendns.com/dns-query",
    "https://doh.securedns.eu/dns-query",
]


dir_path = os.path.dirname(os.path.realpath(__file__))


@contextlib.contextmanager
def connect(port, server_url):
    if server_url.startswith("https://127.0.0.1"):
        print(dir_path)
        cert = dir_path + "/../../cert.pem"
        key = dir_path + "/../../key.pem"
        args = namedtuple("args", ["debug", "resolver", "cert", "key", "port", "host"])
        args = args(
            True, "8.8.8.8", cert, key, str(port), "127.0.0.1"
        )
        p = multiprocessing.Process(target=main, name="Main", args=(args,))
        p.start()
        time.sleep(2)
        yield
        p.terminate()
    else:
        yield


@pytest.fixture
def dns_query_answer():
    q = dns.message.make_query(qname="www.example.com", rdtype="A")
    q.id = 0
    return q.to_wire()


@pytest.fixture
def dns_query_no_answer():
    q = dns.message.make_query(qname="test.local", rdtype="A")
    q.id = 0
    return q.to_wire()


def assert_answer(r):
    assert r.status_code == 200
    msg = dns.message.from_wire(r.content)
    assert msg.id == 0
    assert msg.rcode() == 0
    assert len(msg.answer) == 1
    assert "www.example.com. " in str(msg.answer[0])


def assert_no_answer(r):
    assert r.status_code == 200
    msg = dns.message.from_wire(r.content)
    assert msg.id == 0
    assert msg.rcode() == 3
    assert len(msg.answer) == 0


@pytest.mark.integration
class TestIntegrationServer:
    @pytest.mark.parametrize("server_url", known_servers)
    def test_get_valid(self, server_url, dns_query_answer):
        with connect(8000, server_url):
            headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
            payload = {"dns": doh_b64_encode(dns_query_answer)}
            r = requests.get(server_url, params=payload, headers=headers, verify=False)
            assert_answer(r)

    @pytest.mark.parametrize("server_url", known_servers)
    def test_post_valid(self, server_url, dns_query_answer):
        with connect(8000, server_url):
            headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
            r = requests.post(
                server_url, data=dns_query_answer, headers=headers, verify=False
            )
            assert_answer(r)

    @pytest.mark.parametrize("server_url", known_servers)
    def test_get_accept_missing(self, server_url, dns_query_answer):
        with connect(8000, server_url):
            payload = {"dns": doh_b64_encode(dns_query_answer)}
            r = requests.get(server_url, params=payload, verify=False)
            assert_answer(r)

    @pytest.mark.parametrize("server_url", known_servers)
    def test_post_content_type_missing(self, server_url, dns_query_answer):
        with connect(8000, server_url):
            r = requests.post(server_url, data=dns_query_answer, verify=False)
            assert r.status_code in [400, 415]

    @pytest.mark.parametrize("server_url", known_servers)
    def test_get_invalid_qname(self, server_url, dns_query_no_answer):
        with connect(8000, server_url):
            headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
            payload = {"dns": doh_b64_encode(dns_query_no_answer)}
            r = requests.get(server_url, params=payload, headers=headers, verify=False)
            assert_no_answer(r)

    @pytest.mark.parametrize("server_url", known_servers)
    def test_post_invalid_qname(self, server_url, dns_query_no_answer):
        with connect(8000, server_url):
            headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
            r = requests.post(
                server_url, data=dns_query_no_answer, headers=headers, verify=False
            )
            assert_no_answer(r)
