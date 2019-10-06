import dns.message
import pytest
import requests

from client import ClientDOH
from constants import DOH_CONTENT_TYPE
from utils import doh_b64_encode

known_servers = [
    # URL
    "https://127.0.0.1/dns-query",
    "https://dns.google/dns-query",
    "https://cloudflare-dns.com/dns-query",
    "https://doh.opendns.com/dns-query",
    "https://doh.securedns.eu/dns-query",
]


class TestResponse:
    def test_query_post(self):
        client_doh = ClientDOH(known_servers[0], verify=False)
        response_body = client_doh.make_request(qname="www.example.com", rdtype="A")
        msg = dns.message.from_wire(response_body)
        assert len(msg.answer) == 1
        assert "www.example.com. " in str(msg.answer[0])

    def test_query_get(self):
        client_doh = ClientDOH(known_servers[0], verify=False)
        response_body = client_doh.make_request(
            qname="www.example.com", rdtype="A", get=True
        )
        msg = dns.message.from_wire(response_body)
        assert len(msg.answer) == 1
        assert "www.example.com. " in str(msg.answer[0])


class TestError:
    @pytest.mark.parametrize("server_url", known_servers)
    def test_get_accept_missing(self, server_url):
        q = dns.message.make_query(qname="www.example.com", rdtype="A")
        q.id = 0
        data = q.to_wire()
        payload = {"dns": doh_b64_encode(data)}
        r = requests.get(server_url, params=payload, verify=False)
        assert r.status_code == 200
        msg = dns.message.from_wire(r.content)
        assert msg.id == 0
        assert msg.rcode() == 0
        assert len(msg.answer) == 1
        assert "www.example.com. " in str(msg.answer[0])

    @pytest.mark.parametrize("server_url", known_servers)
    def test_post_content_type_missing(self, server_url):
        q = dns.message.make_query(qname="www.example.com", rdtype="A")
        q.id = 0
        data = q.to_wire()
        r = requests.post(server_url, data=data, verify=False)
        assert r.status_code in [400, 415]

    @pytest.mark.parametrize("server_url", known_servers)
    def test_get_invalid_qname(self, server_url):
        q = dns.message.make_query(qname="does_not_work", rdtype="A")
        q.id = 0
        data = q.to_wire()
        headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
        payload = {"dns": doh_b64_encode(data)}
        r = requests.get(server_url, params=payload, headers=headers, verify=False)
        assert r.status_code == 200
        msg = dns.message.from_wire(r.content)
        assert msg.id == 0
        assert msg.rcode() == 3
        assert len(msg.answer) == 0

    @pytest.mark.parametrize("server_url", known_servers)
    def test_post_invalid_qname(self, server_url):
        q = dns.message.make_query(qname="does_not_work", rdtype="A")
        q.id = 0
        data = q.to_wire()
        headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
        r = requests.post(server_url, data=data, headers=headers, verify=False)
        assert r.status_code == 200
        msg = dns.message.from_wire(r.content)
        assert msg.id == 0
        assert msg.rcode() == 3
        assert len(msg.answer) == 0
