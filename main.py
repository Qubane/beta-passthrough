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
            hellworld_address: tuple[str, int],
    ):
        self.listening_address: tuple[str, int] = listening_address
        self.overworld_address: tuple[str, int] = overworld_address
        self.hellworld_address: tuple[str, int] = hellworld_address

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

    async def client_handler(self, cli_reader: asyncio.StreamReader, cli_writer: asyncio.StreamWriter):
        """
        Handles the client connection
        """

        srv_reader, srv_writer = await asyncio.open_connection(
            host=self.overworld_address[0],
            port=self.overworld_address[1])

        while not cli_writer.is_closing():
            # receive client message
            cli_msg = await cli_reader.read(READ_BUFFER_SIZE)
            srv_writer.write(cli_msg)
            await srv_writer.drain()

            # receive server message
            srv_msg = await srv_reader.read(READ_BUFFER_SIZE)
            cli_writer.write(srv_msg)
            await cli_writer.drain()

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
