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

        self.username = message[3:].decode("ascii")

        # server accept connection response
        # 02 00 01 2D
        message = await self.server_reader.read(READ_BUFFER_SIZE)
        self.writer.write(message)
        await self.writer.drain()

        self.connected = True

    async def start_communication(self):
        """
        Starts communication between client and server
        """

        # check for initial connection
        if self.server_reader is None:
            raise Exception("Not connected")

        # start communication
        cli2srv = asyncio.create_task(self.cli2srv())
        srv2cli = asyncio.create_task(self.srv2cli())

        # while connected -> wait
        while self.connected:
            await asyncio.sleep(0.1)

        # close server connection
        cli2srv.cancel()

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

    async def client_message_monitor(self, message: bytes) -> bytes:
        """
        Monitors client sent messages.
        :param message: message from client
        :return: possibly modified message
        """
