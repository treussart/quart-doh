import dns
import pytest
from dns.message import Message

from quart_doh.dns_resolver import DNSResolverClient


@pytest.fixture
def resolver_internal():
    return DNSResolverClient()


@pytest.fixture
def resolver_external():
    return DNSResolverClient("8.8.8.8")


@pytest.fixture
def resolver_not_exist():
    return DNSResolverClient("10.13.23.45")


@pytest.fixture
def query_ok():
    q = dns.message.make_query(qname="example.com", rdtype="A", want_dnssec=False)
    q.id = 0
    return q


@pytest.fixture
def query_not_ok():
    q = dns.message.make_query(qname="qname", rdtype="A", want_dnssec=False)
    q.id = 0
    return q


class TestDNSResolver:
    def test_dns_resolver_internal_no_answer(self, resolver_internal, query_not_ok):
        result_msg = resolver_internal.resolve(query_not_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 0
        assert result_msg.rcode() == 3
        assert resolver_internal.name_server != "8.8.8.8"

    def test_dns_resolver_internal_answer(self, resolver_internal, query_ok):
        result_msg = resolver_internal.resolve(query_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 1
        assert result_msg.rcode() == 0
        assert resolver_internal.name_server != "8.8.8.8"

    def test_dns_resolver_external_no_answer(self, resolver_external, query_not_ok):
        result_msg = resolver_external.resolve(query_not_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 0
        assert result_msg.rcode() == 3
        assert resolver_external.name_server == "8.8.8.8"

    def test_dns_resolver_external_answer(self, resolver_external, query_ok):
        result_msg = resolver_external.resolve(query_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 1
        assert result_msg.rcode() == 0
        assert resolver_external.name_server == "8.8.8.8"

    def test_dns_resolver_not_exist(self, resolver_not_exist, query_not_ok):
        result_msg = resolver_not_exist.resolve(query_not_ok)
        assert result_msg == 0
