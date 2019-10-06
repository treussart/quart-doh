import argparse

import dns.message
import requests

from quart_doh.constants import DOH_CONTENT_TYPE
from quart_doh.utils import doh_b64_encode


class ClientDOH:
    def __init__(self, server, verify: bool = True):
        self.server = server
        self.verify = verify

    def make_request(
        self, qname: str, rdtype: str, get: bool = False, dnssec: bool = False
    ) -> bytes:
        q = dns.message.make_query(qname=qname, rdtype=rdtype, want_dnssec=dnssec)
        q.id = 0
        data = q.to_wire()
        headers = {"accept": DOH_CONTENT_TYPE, "content-type": DOH_CONTENT_TYPE}
        if get:
            payload = {"dns": doh_b64_encode(data)}
            r = requests.get(
                self.server, params=payload, headers=headers, verify=self.verify
            )
            return r.content
        else:
            r = requests.post(
                self.server, data=data, headers=headers, verify=self.verify
            )
            return r.content


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server",
        default="https://127.0.0.1/dns-query",
        help="URL of the server that will receive the request",
    )
    parser.add_argument(
        "--get", action="store_true", help="Enable Get method instead of Post."
    )
    parser.add_argument(
        "--qname",
        default="www.example.com",
        help="Name to query for. Default [%(default)s]",
    )
    parser.add_argument(
        "--qtype", default="A", help="Type of query. Default [%(default)s]"
    )
    parser.add_argument(
        "--dnssec", action="store_true", help="Enable DNSSEC validation."
    )
    parser.add_argument(
        "--noverify",
        action="store_false",
        help="Disable verify certificates in SSL handshake.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    client_doh = ClientDOH(args.server, args.noverify)
    response_body = client_doh.make_request(
        qname=args.qname, rdtype=args.qtype, get=args.get, dnssec=args.dnssec
    )
    msg = dns.message.from_wire(response_body)
    print(msg.to_text())


if __name__ == "__main__":
    main()
