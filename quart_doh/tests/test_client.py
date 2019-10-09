import dns.message
import pytest

from quart_doh.client import ClientDOH

"""
List of servers taken from
https://github.com/curl/curl/wiki/DNS-over-HTTPS#publicly-available-servers
"""
known_servers = [
    # URL
    "https://dns.google/dns-query",
    "https://cloudflare-dns.com/dns-query",
    "https://doh.opendns.com/dns-query",
    "https://doh.securedns.eu/dns-query",
]


class TestQuery:
    @pytest.mark.parametrize("server_url", known_servers)
    def test_query_post(self, server_url):
        client_doh = ClientDOH(server_url)
        response_body = client_doh.make_request(qname="www.example.com", rdtype="A")
        msg = dns.message.from_wire(response_body)
        assert msg.id == 0
        assert msg.rcode() == 0
        assert len(msg.answer) == 1
        assert "www.example.com. " in str(msg.answer[0])

    @pytest.mark.parametrize("server_url", known_servers)
    def test_query_get(self, server_url):
        client_doh = ClientDOH(server_url)
        response_body = client_doh.make_request(
            qname="www.example.com", rdtype="A", get=True
        )
        msg = dns.message.from_wire(response_body)
        assert msg.id == 0
        assert msg.rcode() == 0
        assert len(msg.answer) == 1
        assert "www.example.com. " in str(msg.answer[0])


class TestMain:
    def test_main(self):
        from quart_doh.client import main
        from collections import namedtuple

        args = namedtuple(
            "args", ["server", "get", "qname", "qtype", "dnssec", "noverify"]
        )
        args = args(
            "https://dns.google/dns-query", False, "www.example.com", "A", False, False
        )
        with pytest.raises(SystemExit) as ret:
            main(args)
        assert ret.type == SystemExit
        assert ret.value.code == 0
