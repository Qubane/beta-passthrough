import signal
import asyncio
import logging
import requests
import logging.handlers
from secret import DISCORD_WEBHOOK
from source.client import Client


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

        self.clients: dict[str, Client] = dict()

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

    def stop(self, *args):
        """
        Stops the proxy
        """

        self.server.close()

    async def client_handler(self, cli_reader: asyncio.StreamReader, cli_writer: asyncio.StreamWriter):
        """
        Handles the client connection
        """

        # make client
        client = Client(cli_reader, cli_writer)

        # connect to server
        srv_reader, srv_writer = await asyncio.open_connection(
            host=self.overworld_address[0],
            port=self.overworld_address[1])

        # connect client to server
        await client.initial_connection(srv_reader, srv_writer)

        # start communication
        await client.start_communication()


def main():
    app = Application(
        listening_address=('0.0.0.0', 25565),
        overworld_address=('127.0.0.1', 20000))
    app.run()


if __name__ == '__main__':
    from source.settings import init_logging
    init_logging()

    main()
