import asyncio
import logging
import time
from enum import StrEnum, auto

import websockets
from bleak import BleakClient

from custom_bleak.client import CustomBleakClientWinRT
from interfaces.wtal.callbacks import notify_callback
logger = logging.getLogger(__name__)


class BleState(StrEnum):
    IDLE = auto()
    CONNECTED = auto()
    NOTIFYING = auto()
    STOPPED = auto()
    DISCONNECTED = auto()


class BleakManager(object):
    state = BleState.IDLE
    t_init = time.time()
    packet_idx = 1
    queue = asyncio.Queue()
    def __init__(self, ble_mac, ble_uuid, ws_host="localhost", ws_port=7654):
        self.ble_mac = ble_mac
        self.ble_uuid = ble_uuid
        self.ws_host = ws_host
        self.ws_port = ws_port

        # self.state = BleState.IDLE
        # self.t_init = time.time()
        # self.packet_idx = 1
        # self.queue = asyncio.Queue()

        self.client = BleakClient(
            address_or_ble_device=self.ble_mac,
            timeout=30.0,
            backend=CustomBleakClientWinRT,
        )

    async def ble_setup_and_config(self):
        await self.client.connect()
        logger.info("Connected to BLE device")
        self.state = BleState.CONNECTED

    async def poll_queue(self):
        await asyncio.sleep(0.01)
        uri = f"ws://{self.ws_host}:{self.ws_port}"
        async with websockets.connect(uri) as ws:
            while True:
                epoch, idx, data = await self.queue.get()
                if (epoch, idx, data) == (-1, -1, None):
                    logger.info("stopping poll_queue")
                    break
                await ws.send(f"{epoch:7.3f}sec | {idx} | {len(data)=}")

        logger.info("closed poll_queue")

    async def ble_wait_for_commands(self):

        # async_lambda = lambda: asyncio.ensure_future(asyncio.run(lambda char, data: notify_callback(char, data, self.queue))
        async_lambda = lambda: asyncio.ensure_future(asyncio.sleep(1).then(lambda _: print("Async lambda executed")))

        await asyncio.sleep(0.01)
        uri = f"ws://{self.ws_host}:{self.ws_port}"
        async with websockets.connect(uri) as ws:
            while True:
                data = await ws.recv()
                if data == "start" and self.state in [
                    BleState.STOPPED,
                    BleState.CONNECTED,
                ]:
                    await self.client.start_notify(
                        self.ble_uuid,
                        # lambda char, data: notify_callback(char, data, self.queue),
                        async_lambda,
                        force_notify=True,  # was needed for a specific sensor to force notification-mode
                    )
                    logger.info("Start notifying ble device")
                    self.state = BleState.NOTIFYING

                elif data == "stop" and self.state in [BleState.NOTIFYING]:
                    await self.client.stop_notify(self.ble_uuid)
                    logger.info("Stopped notifying ble device")
                    self.state = BleState.STOPPED

                elif data == "disconnect" and self.state in [
                    BleState.NOTIFYING,
                    BleState.STOPPED,
                    BleState.CONNECTED,
                ]:
                    await self.client.disconnect()
                    await self.queue.put((-1, -1, None))
                    self.state = BleState.DISCONNECTED
                    logger.info("Disconnected ble device, stopping this script now")
                    break

        logger.info("closed ble_wait_for_commands")

    async def callback_handler(self, _, _data):
        await self.queue.put(
            (
                time.time() - self.t_init,
                self.packet_idx,
                _data,
            )
        )
        self.packet_idx += 1
