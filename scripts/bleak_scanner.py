"""
Service Explorer
----------------

An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.

Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import argparse
import asyncio
import logging

from bleak import BleakClient, BleakScanner

log_level = logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

BLE_MAC_ADDR = "EF:92:E5:F8:49:CE"

async def main():
    logger.info("starting scan...")

    device = await BleakScanner.find_device_by_address(BLE_MAC_ADDR)
    print(device)
    async with BleakClient(device) as client:
        logger.info("connected")

        for service in client.services:
            logger.info("[Service] %s", service)

            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(
                            "  [Characteristic] %s (%s), Value: %r",
                            char,
                            ",".join(char.properties),
                            value,
                        )
                    except Exception as e:
                        logger.error(
                            "  [Characteristic] %s (%s), Error: %s",
                            char,
                            ",".join(char.properties),
                            e,
                        )

                else:
                    logger.info(
                        "  [Characteristic] %s (%s)", char, ",".join(char.properties)
                    )

                for descriptor in char.descriptors:
                    try:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        logger.info("    [Descriptor] %s, Value: %r", descriptor, value)
                    except Exception as e:
                        logger.error("    [Descriptor] %s, Error: %s", descriptor, e)

        logger.info("disconnecting...")

    logger.info("disconnected")


if __name__ == "__main__":
    asyncio.run(main())
