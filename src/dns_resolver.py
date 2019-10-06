from dns import resolver, query, exception
from dns.message import Message

from constants import DOH_SERVER


class DNSResolverClient:
    @staticmethod
    async def resolve(message: Message) -> Message:
        maximum = 4
        timeout = 0.4
        response_message = 0
        if DOH_SERVER["NAME_SERVERS"] == "internal":
            name_server = resolver.get_default_resolver().nameservers[0]
        else:
            name_server = DOH_SERVER["NAME_SERVERS"]
        done = False
        tests = 0
        while not done and tests < maximum:
            try:
                response_message = query.udp(message, name_server, timeout=timeout)
                done = True
            except exception.Timeout:
                tests += 1
        return response_message
