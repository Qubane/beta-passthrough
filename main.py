import asyncio
import logging


class Application:
    def __init__(
            self,
            listening_port: int,
            server_overworld_port: int,
            server_hellworld_port: int | None = None,
            binding_address: str = "0.0.0.0"
    ):
        self.binding_address: str = binding_address
        self.listening_port: int = listening_port
        self.overworld_port: int = server_overworld_port
        self.hellworld_port: int | None = server_hellworld_port

        self.server: asyncio.Server | None = None

        self.logger: logging.Logger = logging.getLogger(__name__)

    def run(self):
        """
        Starts the passthrough proxy
        """

        async def coro():
            self.server = await asyncio.start_server(
                client_connected_cb=self.client_handler,
                host=self.binding_address,
                port=self.listening_port)

            self.logger.info(f"Proxy listening on '{self.binding_address}:{self.listening_port}'")
            async with self.server:
                try:
                    await self.server.serve_forever()
                except asyncio.exceptions.CancelledError:
                    pass
            self.logger.info("Proxy stopped")

        asyncio.run(coro())

    async def client_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        Handles the client connection
        """


def main():
    app = Application(
        listening_port=25565,
        server_overworld_port=20000)


if __name__ == '__main__':
    main()
