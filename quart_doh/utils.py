import base64
import binascii
import json
import logging
import os
from string import Template

import dns
from dns import message
from dns.message import Message
from quart import Response, Request

from quart_doh.constants import (
    AUTHORITY,
    DOH_CONTENT_TYPE,
    DOH_JSON_CONTENT_TYPE,
    DOH_DNS_PARAM,
    DOH_DNS_JSON_PARAM,
)

dir_path = os.path.dirname(os.path.realpath(__file__))


def doh_b64_decode(s: str) -> bytes:
    """Base 64 urlsafe decode, add padding as needed.
    :param s: input base64 encoded string with potentially missing padding.
    :return: decodes bytes
    """
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def doh_b64_encode(s: bytes) -> str:
    """Base 64 urlsafe encode and remove padding.
    :param s: input bytes-like object to be encoded.
    :return: urlsafe base 64 encoded string.
    """
    return base64.urlsafe_b64encode(s).decode("utf-8").rstrip("=")


def configure_logger(name: str = "", level: str = "DEBUG"):
    """
    :param name: (optional) name of the logger, default: ''.
    :param level: (optional) level of logging, default: DEBUG.
    :return: a logger instance.
    """
    logging.basicConfig(format="%(asctime)s: %(levelname)8s: %(message)s")
    logger = logging.getLogger(name)
    level_name = level.upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise Exception("Invalid log level name : %s" % level_name)
    logger.setLevel(level)
    return logger


def get_scheme(request: Request) -> str:
    if request.is_secure:
        return "https"
    else:
        return "http"


def set_headers(
    request: Request, response: Response, query_response: Message
) -> Response:
    response.headers["authority"] = AUTHORITY
    response.headers["method"] = request.method
    response.headers["scheme"] = get_scheme(request)
    ttl = 0
    if query_response.answer:
        ttl = min(r.ttl for r in query_response.answer)
    if query_response.answer:
        response.headers["cache-control"] = "max-age=" + str(ttl)
    return response


def extract_from_params(dns_request: str) -> Message:
    logger = logging.getLogger("doh-server")
    try:
        dns_request_decoded = doh_b64_decode(dns_request)
        return dns.message.from_wire(dns_request_decoded)
    except binascii.Error as ex:
        logger.info(str(ex))
    except Exception as ex:
        logger.exception(ex)


async def get_name_and_type_from_dns_question(request: Request) -> Message:
    logger = logging.getLogger("doh-server")
    accept_header = request.headers.get("Accept")
    if request.method == "GET":
        if accept_header == DOH_JSON_CONTENT_TYPE:
            qname = request.args.get(DOH_DNS_JSON_PARAM["name"], None)
            rdtype = request.args.get(DOH_DNS_JSON_PARAM["type"], None)
            if qname and rdtype:
                return dns.message.make_query(qname=qname, rdtype=rdtype)
        else:
            dns_request = request.args.get(DOH_DNS_PARAM, None)
            if dns_request:
                return extract_from_params(dns_request)
    elif request.method == "POST" and request.content_type == DOH_CONTENT_TYPE:
        body = await request.get_data()
        if body:
            try:
                return message.from_wire(body)
            except Exception as ex:
                logger.info(str(ex))


async def create_http_wire_response(
    request: Request, query_response: Message
) -> Response:
    logger = logging.getLogger("doh-server")
    logger.debug(
        "[HTTP] " + str(request.method) + " " + str(request.headers.get("Accept"))
    )
    if isinstance(query_response, Message):
        query_response.id = 0
        body = query_response.to_wire()
        response = Response(body, content_type=DOH_CONTENT_TYPE)
        response.headers["content-length"] = str(len(body))
        return set_headers(request, response, query_response)
    else:
        return Response(query_response)


async def create_http_json_response(
    request: Request, query_response: Message
) -> Response:
    logger = logging.getLogger("doh-server")
    logger.debug(
        "[HTTP] " + str(request.method) + " " + str(request.headers.get("Accept"))
    )
    response = Response(json.dumps({}), content_type=DOH_JSON_CONTENT_TYPE)
    if isinstance(query_response, Message):
        if query_response.answer:
            answers = []
            for answer in query_response.answer[0]:
                answers.append(str(answer))
            with open(dir_path + "/template.json", "r", encoding="UTF-8") as template:
                s = Template(template.read())
                response.content = json.dumps(
                    s.substitute(
                        data=json.dumps(answers),
                        name=query_response.answer[0].name,
                        type=query_response.answer[0].rdtype,
                        ttl=query_response.answer[0].ttl,
                    )
                )
        return set_headers(request, response, query_response)
    else:
        return Response(json.dumps({"content": str(query_response)}), status=200)
