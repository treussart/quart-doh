from dns import resolver, query, exception
from dns.message import Message


class DNSResolverClient:
    def __init__(self, name_server: str = "internal"):
        self.name_server = name_server

    async def resolve(self, message: Message) -> Message:
        maximum = 4
        timeout = 0.4
        response_message = 0
        if self.name_server == "internal":
            self.name_server = resolver.get_default_resolver().nameservers[0]
        done = False
        tests = 0
        while not done and tests < maximum:
            try:
                response_message = query.udp(message, self.name_server, timeout=timeout)
                done = True
            except exception.Timeout:
                tests += 1
        return response_message
