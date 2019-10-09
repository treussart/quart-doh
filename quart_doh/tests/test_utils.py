from unittest.mock import Mock, MagicMock

import dns
import dns.message
import pytest
from quart import Response, Request
from quart.datastructures import Headers

from quart_doh.constants import DOH_CONTENT_TYPE, DOH_JSON_CONTENT_TYPE
from quart_doh.utils import (
    doh_b64_encode,
    doh_b64_decode,
    configure_logger,
    get_scheme,
    set_headers,
    extract_from_params,
    get_name_and_type_from_dns_question,
    create_http_wire_response,
    create_http_json_response,
)


@pytest.fixture
def query():
    q = dns.message.make_query(qname="example.com", rdtype="A", want_dnssec=False)
    q.id = 0
    return q


@pytest.fixture
def query_with_answer():
    q = dns.message.make_query(qname="example.com", rdtype="A", want_dnssec=False)
    qr = dns.message.make_response(q)
    answer = Mock()
    answer.ttl = 1
    qr.answer.append(answer)
    qr.to_wire = MagicMock(return_value="wire format")
    return qr


@pytest.fixture
def request_mock():
    mock = Mock()
    mock.is_secure = False
    mock.method = "GET"
    return mock


async def return_body():
    return "AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA"


class TestUtils:
    def test_doh_b64_encode(self):
        assert doh_b64_encode(b"test") == "dGVzdA"
        assert doh_b64_encode(b"test==te&111%") == "dGVzdD09dGUmMTExJQ"
        with pytest.raises(TypeError):
            doh_b64_encode(None)

    def test_doh_b64_decode(self):
        assert doh_b64_decode("dGVzdA") == b"test"
        assert doh_b64_decode("dGVzdD09dGUmMTExJQ") == b"test==te&111%"
        with pytest.raises(TypeError):
            doh_b64_decode(None)

    def test_configure_loggers(self):
        logger = configure_logger()
        assert logger.level == 10
        assert logger.name == "root"

        logger = configure_logger("test")
        assert logger.level == 10
        assert logger.name == "test"

        logger = configure_logger("test", "INFO")
        assert logger.level == 20
        assert logger.name == "test"

        logger = configure_logger("test", "info")
        assert logger.level == 20
        assert logger.name == "test"

        with pytest.raises(Exception):
            configure_logger("test", "test")

    def test_get_scheme(self, request_mock):
        assert get_scheme(request_mock) == "http"
        request_mock.is_secure = True
        assert get_scheme(request_mock) == "https"

    def test_set_headers(self, query, query_with_answer, request_mock):
        response = Response("", status=200)

        response = set_headers(request_mock, response, query)
        assert response.headers["authority"] == "quart_doh"
        assert response.headers["method"] == "GET"
        assert response.headers["scheme"] == "http"
        with pytest.raises(KeyError):
            response.headers["cache-control"]

        response = set_headers(request_mock, response, query_with_answer)
        assert response.headers["authority"] == "quart_doh"
        assert response.headers["method"] == "GET"
        assert response.headers["scheme"] == "http"
        assert response.headers["cache-control"] == "max-age=1"

    def test_extract_from_params(self):
        param = "AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA"
        assert str(extract_from_params(param).question[0]) == "s0.wp.com. IN AAAA"

        param = "AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgAAEAAEAAA"
        assert extract_from_params(param) is None

        param = "AQAAQDhAAMAAQAAAAAAAAthAAAAJDczODFmZDM2LTNiOTYtNDVmYS04MjQ2LWRkYzJkMmViYjQ2YQ==="
        assert extract_from_params(param) is None

        param = ""
        assert extract_from_params(param) is None

    @pytest.mark.asyncio
    async def test_get_name_and_type_from_dns_question(self):
        headers = Headers()
        headers.add(key="accept", value=DOH_CONTENT_TYPE)
        request = Request(
            headers=headers,
            method="GET",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"dns=AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA",
            root_path="",
            send_push_promise=None,
        )
        result = await get_name_and_type_from_dns_question(request)
        assert str(result.question[0]) == "s0.wp.com. IN AAAA"

        headers = Headers()
        headers.add(key="accept", value=DOH_JSON_CONTENT_TYPE)
        request = Request(
            headers=headers,
            method="GET",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"name=example.com&type=A",
            root_path="",
            send_push_promise=None,
        )
        result = await get_name_and_type_from_dns_question(request)
        assert str(result.question[0]) == "example.com. IN A"

        headers = Headers()
        headers.add(key="content-type", value=DOH_CONTENT_TYPE)
        request = Request(
            headers=headers,
            method="POST",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"dns=AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA",
            root_path="",
            send_push_promise=None,
        )
        request.body = return_body()
        result = await get_name_and_type_from_dns_question(request)
        assert result is None

        request = Request(
            headers=headers,
            method="GET",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"dns=AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAgACAAEAAEAAA",
            root_path="",
            send_push_promise=None,
        )
        result = await get_name_and_type_from_dns_question(request)
        assert result is None

    @pytest.mark.asyncio
    async def test_create_http_wire_response(self, query_with_answer):
        headers = Headers()
        headers.add(key="accept", value=DOH_CONTENT_TYPE)
        request = Request(
            headers=headers,
            method="GET",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"dns=AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA",
            root_path="",
            send_push_promise=None,
        )
        result = await create_http_wire_response(request, query_with_answer)
        assert result.status_code == 200
        assert result.headers.get("content-length") == "11"
        assert result.headers.get("content-type") == DOH_CONTENT_TYPE
        assert await result.get_data() == b"wire format"

        result = await create_http_wire_response(request, "query_with_answer")
        assert result.status_code == 200
        assert result.headers.get("content-length") == "17"
        assert result.headers.get("content-type") == "text/html; charset=utf-8"
        assert await result.get_data() == b"query_with_answer"

    @pytest.mark.asyncio
    async def test_create_http_json_response(self, query_with_answer):
        headers = Headers()
        headers.add(key="accept", value=DOH_CONTENT_TYPE)
        request = Request(
            headers=headers,
            method="GET",
            scheme="https",
            path="/dns-query",
            http_version="1.1",
            query_string=b"dns=AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA",
            root_path="",
            send_push_promise=None,
        )
        result = await create_http_json_response(request, query_with_answer)
        assert result.status_code == 200
        assert result.headers.get("content-length") == "2"
        assert result.headers.get("content-type") == DOH_JSON_CONTENT_TYPE
        assert await result.get_data() == b"{}"

        result = await create_http_json_response(request, "query_with_answer")
        assert result.status_code == 200
        assert result.headers.get("content-length") == "32"
        assert result.headers.get("content-type") == "text/html; charset=utf-8"
        assert await result.get_data() == b'{"content": "query_with_answer"}'
