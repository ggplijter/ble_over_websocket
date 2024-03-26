import argparse
import asyncio
import copy
import logging
import uuid

import websockets
from custom_bleak.manager import BleakManager, BleState


logger = logging.getLogger(__name__)

WEBSOCKET_CONNECTIONS = set()
async def broadcast_handler(websocket, state):
    WEBSOCKET_CONNECTIONS.add(websocket)
    logger.info(
        f"New client. Websocket ID = {id(websocket)}. We now have {len(WEBSOCKET_CONNECTIONS)} clients"
    )
    try:
        while state != BleState.DISCONNECTED:
            logger.debug("SERVER waiting for data from filewatcher source client")

            data = await websocket.recv()

            clients = copy.copy(WEBSOCKET_CONNECTIONS)
            clients.remove(websocket)
            websockets.broadcast(clients, data)

    except websockets.exceptions.ConnectionClosed:
        WEBSOCKET_CONNECTIONS.remove(websocket)
        logger.info(
            f"Client disconnected.. Websocket ID = {id(websocket)}. {len(WEBSOCKET_CONNECTIONS)} clients remaining"
        )


async def main(args):
    mac_addr = args.address
    uuid_notify = uuid.UUID(args.uuid_notify)

    manager = BleakManager(
        ble_mac=mac_addr,
        ble_uuid=uuid_notify,
        ws_host="localhost",
        ws_port=8765,
    )

    websocket_server = websockets.serve(
        lambda _websocket: broadcast_handler(_websocket, manager.state),
        manager.ws_host,
        manager.ws_port,
    )

    await manager.ble_setup_and_config()

    await asyncio.gather(
        websocket_server,
        manager.poll_queue(),
        manager.ble_wait_for_commands(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    device_group = parser.add_mutually_exclusive_group(required=True)

    device_group.add_argument(
        "--address",
        metavar="<address>",
        help="the address of the bluetooth device to connect to",
    )

    parser.add_argument(
        "--uuid_notify",
        metavar="<uuid>",
        help="specify the uuid of the notification",
    )

    parser.add_argument(
        "--hostname",
        metavar="<hostname>",
        help="specify the ipaddress for the websocket",
    )

    parser.add_argument(
        "--port",
        metavar="<port>",
        help="specify the port for the websocket",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))
