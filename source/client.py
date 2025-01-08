import asyncio
import logging
from source.settings import READ_BUFFER_SIZE


class Client:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, **kwargs):
        self.reader: asyncio.StreamReader = reader
        self.writer: asyncio.StreamWriter = writer

        self.server_reader: asyncio.StreamReader | None = None
        self.server_writer: asyncio.StreamWriter | None = None

        self.logger: logging.Logger | None = None

        self.username: str = "undefined"
        self.connected: bool = False

        self.clients: dict[str, Client] = kwargs.get("clients", dict())

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
        self.connected = True

        self.logger = logging.getLogger(f"{__name__}.{self.username}")
        self.logger.info("Client connected!")

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

        self.logger.info("Client disconnected!")

    async def cli2srv(self):
        """
        Client to server communication
        """

        while self.connected:
            message = await self.reader.read(READ_BUFFER_SIZE)
            self.server_writer.write(self.client_message_monitor(message))
            await self.server_writer.drain()

    async def srv2cli(self):
        """
        Server to client communication
        """

        while self.connected:
            message = await self.server_reader.read(READ_BUFFER_SIZE)
            if message == b'':
                self.connected = False
            self.writer.write(self.server_message_monitor(message))
            await self.writer.drain()

    def client_message_monitor(self, message: bytes) -> bytes:
        """
        Monitors client sent messages.
        :param message: message from client
        :return: possibly modified message
        """

        match message[:2]:
            case b'\x03\x00':  # chat messages
                if message[3:4] == b'/':
                    response = message[:2] + self.process_command(message[4:message[2]+3]) + message[message[2]+3:]
                else:
                    response = message
            case _:
                response = message
        return response

    def server_message_monitor(self, message) -> bytes:
        """
        Monitors server sent messages.
        :param message: message from server
        :return: possible modified message
        """

        match message[:2]:
            case _:
                pass
        return message

    def process_command(self, command: bytes) -> bytes:
        """
        Processes the command
        :param command: chat / command
        :return: response
        """

        if command == b'list':
            msg = b'Online: ' + b'; '.join(client.username.encode("ascii") for client in self.clients.values())
            return len(msg).to_bytes(1) + msg
        return command
