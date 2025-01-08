import os
import signal
import asyncio
import logging
import logging.handlers


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
                filename=f"{LOGS_DIRECTORY}/discord.log",
                encoding="utf-8",
                maxBytes=2 ** 20 * 32,  # 32 MiB
                backupCount=5),
            logging.StreamHandler()])


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

        signal.signal(signal.SIGINT, self.stop)

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

    def stop(self, *args):
        """
        Stops the proxy
        """

        self.server.close()


def main():
    app = Application(
        listening_port=25565,
        server_overworld_port=20000)
    app.run()


if __name__ == '__main__':
    init_logging()
    main()
