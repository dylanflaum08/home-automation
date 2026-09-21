import os

from dotenv import load_dotenv
from kasa import Credentials, DeviceConfig
from kasa.iot import IotPlug
from kasa.protocols import IotProtocol
from kasa.transports.klaptransport import KlapTransportV2

load_dotenv()


class KasaController:
    def __init__(self, host: str) -> None:
        username = os.getenv("KASA_USERNAME")
        password = os.getenv("KASA_PASSWORD")

        if not username or not password:
            raise RuntimeError(
                "KASA_USERNAME or KASA_PASSWORD is missing from .env"
            )

        credentials = Credentials(
            username=username,
            password=password,
        )

        config = DeviceConfig(
            host=host,
            credentials=credentials,
            timeout=10,
        )

        transport = KlapTransportV2(config=config)
        protocol = IotProtocol(transport=transport)

        self.plug = IotPlug(
            host=host,
            protocol=protocol,
        )

    async def connect(self) -> None:
        await self.plug.update()
        print(
            f"Connected to {self.plug.alias} "
            f"at {self.plug.host}"
        )

    async def turn_on(self) -> None:
        if self.plug.is_on:
            return

        await self.plug.turn_on()
        await self.plug.update()
        print("Lamp turned ON")

    async def turn_off(self) -> None:
        if not self.plug.is_on:
            return

        await self.plug.turn_off()
        await self.plug.update()
        print("Lamp turned OFF")

    async def disconnect(self) -> None:
        await self.plug.disconnect()