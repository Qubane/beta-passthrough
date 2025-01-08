import asyncio


class Application:
    def __init__(self, listening_port: int, server_overworld_port: int, server_hellworld_port: int | None = None):
        self.listening_port: int = listening_port
        self.overworld_port: int = server_overworld_port
        self.hellworld_port: int | None = server_hellworld_port

    def run(self):
        """
        Starts the passthrough proxy
        """

        async def coro():
            pass

        asyncio.run(coro())


def main():
    app = Application(
        listening_port=25565,
        server_overworld_port=20000)


if __name__ == '__main__':
    main()
