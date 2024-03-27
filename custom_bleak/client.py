# -*- coding: utf-8 -*-
"""
Custom BLE Client for Windows 10 systems, implemented with bleak.

Created on 2024-03-26 by ggplijter
"""

import asyncio
import logging
from typing import Optional, Set, Union, cast

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.client import NotifyCallback
from bleak.backends.device import BLEDevice
from bleak.backends.winrt.client import (
    BleakClientWinRT,
    WinRTClientArgs,
    _ensure_success,
)
from bleak.exc import BleakError
from winrt.windows.devices.bluetooth.genericattributeprofile import (
    GattCharacteristic,
    GattCharacteristicProperties,
    GattClientCharacteristicConfigurationDescriptorValue,
    GattValueChangedEventArgs,
)

logger = logging.getLogger(__name__)


class CustomBleakClientWinRT(BleakClientWinRT):
    """Native Windows Bleak Client.

    Args:
        address_or_ble_device (str or BLEDevice): The Bluetooth address of the BLE peripheral
            to connect to or the ``BLEDevice`` object representing it.
        services: Optional set of service UUIDs that will be used.
        winrt (dict): A dictionary of Windows-specific configuration values.
        **timeout (float): Timeout for required ``BleakScanner.find_device_by_address`` call. Defaults to 10.0.
    """

    def __init__(
        self,
        address_or_ble_device: Union[BLEDevice, str],
        services: Optional[Set[str]] = None,
        *,
        winrt: WinRTClientArgs,
        **kwargs,
    ):
        super(CustomBleakClientWinRT, self).__init__(address_or_ble_device=address_or_ble_device, services=services, winrt=winrt, **kwargs)

    async def start_notify(
        self,
        characteristic: BleakGATTCharacteristic,
        callback: NotifyCallback,
        **kwargs,
    ) -> None:
        """
        Activate notifications/indications on a characteristic.

        Keyword Args:
            force_indicate (bool): If this is set to True, then Bleak will set up a indication request instead of a
                notification request, given that the characteristic supports notifications as well as indications.
        """
        winrt_char = cast(GattCharacteristic, characteristic.obj)

        # If we want to force indicate even when notify is available, also check if the device
        # actually supports indicate as well.
        if not kwargs.get("force_indicate", False) and (
            winrt_char.characteristic_properties & GattCharacteristicProperties.NOTIFY
        ):
            cccd = GattClientCharacteristicConfigurationDescriptorValue.NOTIFY

        # added by ggplijter 26/03/2024
        elif kwargs.get("force_notify", False) and (
            winrt_char.characteristic_properties & GattCharacteristicProperties.INDICATE
        ):
            cccd = GattClientCharacteristicConfigurationDescriptorValue.NOTIFY
        # added by ggplijter 26/03/2024

        elif (
            winrt_char.characteristic_properties & GattCharacteristicProperties.INDICATE
        ):
            cccd = GattClientCharacteristicConfigurationDescriptorValue.INDICATE
        else:
            raise BleakError(
                "characteristic does not support notifications or indications"
            )

        loop = asyncio.get_running_loop()

        def handle_value_changed(
            sender: GattCharacteristic, args: GattValueChangedEventArgs
        ):
            value = bytearray(args.characteristic_value)
            return loop.call_soon_threadsafe(callback, value)

        event_handler_token = winrt_char.add_value_changed(handle_value_changed)
        self._notification_callbacks[characteristic.handle] = event_handler_token

        try:
            _ensure_success(
                await winrt_char.write_client_characteristic_configuration_descriptor_async(
                    cccd
                ),
                None,
                f"Could not start notify on {characteristic.handle:04X}",
            )
        except BaseException:
            # This usually happens when a device reports that it supports indicate,
            # but it actually doesn't.
            if characteristic.handle in self._notification_callbacks:
                event_handler_token = self._notification_callbacks.pop(
                    characteristic.handle
                )
                winrt_char.remove_value_changed(event_handler_token)

            raise
