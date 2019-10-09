import argparse
import asyncio
import functools
import logging

import dns
from dns.message import Message
from quart import Quart
from quart import request, Response

from quart_doh.constants import DOH_JSON_CONTENT_TYPE, DOH_CONTENT_TYPE
from quart_doh.dns_resolver import DNSResolverClient
from quart_doh.utils import (
    configure_logger,
    create_http_wire_response,
    get_name_and_type_from_dns_question,
    create_http_json_response,
)

resolver_dns = None
app = Quart(__name__)


@app.route("/dns-query", methods=["GET", "POST"])
async def route_dns_query() -> Response:
    logger = logging.getLogger("doh-server")
    accept_header = request.headers.get("Accept")
    message = await get_name_and_type_from_dns_question(request)
    if not message:
        return Response("", status=400)
    try:
        loop = asyncio.get_running_loop()
        query_response = await loop.run_in_executor(
            None, functools.partial(resolver_dns.resolve, message)
        )
        if isinstance(query_response, Message):
            if query_response.answer:
                logger.debug("[DNS] " + str(query_response.answer[0]))
            else:
                logger.debug("[DNS] " + str(query_response.question[0]))
        else:
            logger.debug("[DNS] Timeout on " + resolver_dns.name_server)
            query_response = dns.message.make_response(message)
            query_response.set_rcode(dns.rcode.SERVFAIL)
    except Exception as ex:
        logger.exception(str(ex))
        return Response("", status=400)
    if request.method == "GET":
        if accept_header == DOH_JSON_CONTENT_TYPE:
            return await create_http_json_response(request, query_response)
        else:
            return await create_http_wire_response(request, query_response)
    elif request.method == "POST":
        if request.headers.get("content-type") == DOH_CONTENT_TYPE:
            return await create_http_wire_response(request, query_response)
        else:
            return Response("", status=405)


def parse_args():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable Debug mode")
    parser.add_argument(
        "--resolver",
        default="internal",
        help="Define the DNS resolver. Default [%(default)s]. Example 8.8.8.8",
    )
    parser.add_argument(
        "--cert",
        default="cert.pem",
        help="Define the certificate path. Default [%(default)s]",
    )
    parser.add_argument(
        "--key",
        default="key.pem",
        help="Define the path of the key. Default [%(default)s]",
    )
    parser.add_argument(
        "--port", type=int, default=443, help="Define the port. Default [%(default)s]"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Define the host. Default [%(default)s]"
    )
    return parser.parse_args()


def main(args):  # pragma: no cover
    if args.debug:
        level = "DEBUG"
    else:
        level = "WARNING"
    global resolver_dns
    resolver_dns = DNSResolverClient(args.resolver)
    logger = configure_logger("doh-server", level=level)
    configure_logger("quart.app", level=level)
    configure_logger("quart.serving", level=level)
    logger.info("Logger in {} mode".format(logging.getLevelName(logger.level)))
    app.run(
        host=args.host,
        port=args.port,
        certfile=args.cert,
        keyfile=args.key,
        debug=args.debug,
    )


if __name__ == "__main__":  # pragma: no cover
    args = parse_args()
    main(args)
