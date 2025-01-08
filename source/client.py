import asyncio
from source.settings import READ_BUFFER_SIZE


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

        self.server_reader = srv_reader
        self.server_writer = srv_writer

        # client connection request
        # 02 00 [length;1 byte] [username]
        message = await self.reader.read(READ_BUFFER_SIZE)
        self.server_writer.write(message)
        await self.server_writer.drain()

        # server accept connection response
        # 02 00 01 2D
        message = await self.server_reader.read(READ_BUFFER_SIZE)
        self.writer.write(message)
        await self.writer.drain()

    async def start_communication(self):
        """
        Starts communication between client and server
        """

        if self.server_reader is None:
            raise Exception("Not connected")

    async def cli2srv(self):
        """
        Client to server communication
        """

        while self.connected:
            message = await self.reader.read(READ_BUFFER_SIZE)
            self.server_writer.write(message)
            await self.server_writer.drain()

    async def srv2cli(self):
        """
        Server to client communication
        """

        while self.connected:
            message = await self.server_reader.read(READ_BUFFER_SIZE)
            self.writer.write(message)
            await self.writer.drain()
