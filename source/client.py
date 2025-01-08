import asyncio


class Client:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        self.server_reader: asyncio.StreamReader | None = None
        self.server_writer: asyncio.StreamWriter | None = None

        self.username: str = "undefined"
        self.connected: bool = False

    async def initial_connection(self, srv_reader: asyncio.StreamReader, srv_writer: asyncio.StreamWriter):
        """
        Initial connection to the server
        :param srv_reader: server reader
        :param srv_writer: server writer
        """

    async def cli2srv(self):
        """
        Client to server communication
        """

    async def srv2cli(self):
        """
        Server to client communication
        """
