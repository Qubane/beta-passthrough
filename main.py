import os
import signal
import asyncio
import logging
import requests
import logging.handlers
from secret import DISCORD_WEBHOOK


READ_BUFFER_SIZE: int = 2 ** 12
LOGS_DIRECTORY: str = "logs"


def init_logging():
    # create 'logs' directory
    if not os.path.isdir(LOGS_DIRECTORY):
        os.mkdir(LOGS_DIRECTORY)

    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        format="[{asctime}] [{levelname:<8}] {name}: {message}",
        handlers=[
            logging.handlers.RotatingFileHandler(
                filename=f"{LOGS_DIRECTORY}/proxy.log",
                encoding="utf-8",
                maxBytes=2 ** 20 * 32,  # 32 MiB
                backupCount=5),
            logging.StreamHandler()])


class Application:
    def __init__(
            self,
            listening_address: tuple[str, int],
            overworld_address: tuple[str, int],
            hellworld_address: tuple[str, int] | None = None,
    ):
        self.listening_address: tuple[str, int] = listening_address
        self.overworld_address: tuple[str, int] = overworld_address
        self.hellworld_address: tuple[str, int] | None = hellworld_address

        self.server: asyncio.Server | None = None

        self.clients: dict[str, dict] = dict()

        self.logger: logging.Logger = logging.getLogger(__name__)

        signal.signal(signal.SIGINT, self.stop)

    def run(self):
        """
        Starts the passthrough proxy
        """

        async def coro():
            self.server = await asyncio.start_server(
                client_connected_cb=self.client_handler,
                host=self.listening_address[0],
                port=self.listening_address[1])

            self.logger.info(f"Proxy listening on '{self.listening_address[0]}:{self.listening_address[1]}'")
            async with self.server:
                try:
                    await self.server.serve_forever()
                except asyncio.exceptions.CancelledError:
                    pass
            self.logger.info("Proxy stopped")

        asyncio.run(coro())

    def update_client(self, host: str, **kwargs):
        """
        Updates client info
        :param host: client address
        :param kwargs: fields to update
        """

        if host not in self.clients:
            self.clients[host] = dict()

        self.clients[host].update(kwargs)

    def delete_client(self, host: str):
        """
        Deletes client from client list
        :param host: client address
        """

        if host in self.clients:
            self.clients.pop(host)

    def post_message(self, message: str):
        """
        Posts a message
        """

        return

        async def coro():
            requests.post(DISCORD_WEBHOOK, json={"content": message})

        asyncio.create_task(coro())

    async def client_handler(self, cli_reader: asyncio.StreamReader, cli_writer: asyncio.StreamWriter):
        """
        Handles the client connection
        """

        # fetch client peername
        client_host = cli_writer.get_extra_info("peername").__str__()

        # write client to client list
        self.update_client(client_host, connected=True)

        # log
        self.logger.info(f"Client '{client_host}' connected")

        # connect to server
        srv_reader, srv_writer = await asyncio.open_connection(
            host=self.overworld_address[0],
            port=self.overworld_address[1])

        # create transmission tasks
        cli2srv = asyncio.create_task(self.handle_srv2cli(client_host, srv_reader, cli_writer))
        srv2cli = asyncio.create_task(self.handle_cli2srv(client_host, cli_reader, srv_writer))

        # wait while user is connected
        while self.clients[client_host]["connected"]:
            await asyncio.sleep(0.1)

        # when user disconnects, post disconnect message and delete the user
        self.post_message(f"{self.clients[client_host]['username']} left the server!")
        self.delete_client(client_host)

        # cancel server to client transmission
        srv2cli.cancel()

        # log
        self.logger.info(f"Client '{client_host}' disconnected")

    async def handle_cli2srv(self, host: str, cli_reader: asyncio.StreamReader, srv_writer: asyncio.StreamWriter):
        """
        Handles server to client connection
        """

        # fetch username
        username = await cli_reader.read(READ_BUFFER_SIZE)
        self.update_client(host, username=username[3:].decode("ascii"), connected=True)

        # post about user joining
        self.post_message(f"{self.clients[host]['username']} joined the server!")

        # notify server
        srv_writer.write(username)
        await srv_writer.drain()

        # client to server transmission loop
        while self.clients[host]["connected"]:
            message = await cli_reader.read(READ_BUFFER_SIZE)
            self.check_raw_message(message)
            srv_writer.write(message)
            await srv_writer.drain()

    async def handle_srv2cli(self, host: str, srv_reader: asyncio.StreamReader, cli_writer: asyncio.StreamWriter):
        """
        Handles server to client connection
        """

        # server to client transmission loop
        while self.clients[host]["connected"]:
            message = await srv_reader.read(READ_BUFFER_SIZE)
            if message == b'':
                self.update_client(host, connected=False)

            cli_writer.write(message)
            await cli_writer.drain()

    def check_raw_message(self, message: bytes):
        """
        Checks raw message
        :param message: raw message
        """

        # chat messages
        # b'\x03\x00' + [msg_length + 1;1byte] + b'\n'
        if (idx := message.find(b'\x03\x00')) > -1:
            self.handle_chat_messages(message[idx+3:message.find(b'\n', idx)].decode("ascii"))

    def handle_chat_messages(self, message: str):
        """
        Handles chat messages
        :param message: chat message
        """

        self.logger.info(message)

    def stop(self, *args):
        """
        Stops the proxy
        """

        self.server.close()


def main():
    app = Application(
        listening_address=('0.0.0.0', 25565),
        overworld_address=('192.168.1.64', 25565))
    app.run()


if __name__ == '__main__':
    init_logging()
    main()
