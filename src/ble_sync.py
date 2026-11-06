from micropython import const
import bluetooth
import struct

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_MANUFACTURER = const(0xFF)

# 0xFFFF is the Bluetooth company id reserved for internal/testing use.
# The 4 bytes after it carry the animation step counter (little endian).
_COMPANY_ID = const(0xFFFF)

class BLESync:
    def __init__(self, name, frame_callback):
        self.name = name
        self.frame_callback = frame_callback
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._connections = set()
        self._payload = self._advertising_payload(name=self.name)
        self._advertise()
        self._frame_num = 0

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            self._connections.add(conn_handle)
            print("Connected:", addr)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            self._connections.remove(conn_handle)
            self._advertise()
            print("Disconnected:", addr)
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            # Handle incoming data if necessary

    def _advertising_payload(self, name=None, frame_step=None):
        # Every advertising structure is: length byte, type byte, then
        # (length - 1) value bytes. The old code packed the flags twice
        # with no value byte and appended the frame number with no length
        # byte at all, so scanners could not parse the frame number out.
        payload = bytearray()
        payload.extend(struct.pack("BBB", 2, _ADV_TYPE_FLAGS, 0x06))
        if name:
            name_bytes = name.encode()
            payload.extend(struct.pack("BB", len(name_bytes) + 1, _ADV_TYPE_NAME) + name_bytes)
        if frame_step is not None:
            mfr = struct.pack("<HI", _COMPANY_ID, frame_step & 0xFFFFFFFF)
            payload.extend(struct.pack("BB", len(mfr) + 1, _ADV_TYPE_MANUFACTURER) + mfr)
        return payload

    def _advertise(self):
        self._ble.gap_advertise(100_000, adv_data=self._payload)

    def sync_frames(self, t, frame_step=None):
        """Advertise the current animation step and fire the callback.

        frame_step may be the shared step from a FrameClock
        (src/time_sync.py): every badge then broadcasts a step derived
        from the same absolute time base instead of a private counter,
        so a listener can align to the group even without WiFi/NTP.
        With no frame_step given, this counts up locally as before."""
        if frame_step is None:
            self._frame_num += 1
        else:
            self._frame_num = frame_step
        payload = self._advertising_payload(name=self.name, frame_step=self._frame_num)
        self._ble.gap_advertise(100_000, adv_data=payload)
        self.frame_callback(self._frame_num)

    def get_frame_num(self):
        return self._frame_num

    @staticmethod
    def frame_step_from_advertising(adv_data):
        """Pull the frame step out of a peer's advertising payload (as
        produced by sync_frames). Returns None if it isn't there."""
        i = 0
        while i + 1 < len(adv_data):
            length = adv_data[i]
            if length == 0:
                break
            if (adv_data[i + 1] == _ADV_TYPE_MANUFACTURER and length >= 7
                    and i + 2 + 6 <= len(adv_data)):
                company_id, step = struct.unpack("<HI", bytes(adv_data[i + 2:i + 8]))
                if company_id == _COMPANY_ID:
                    return step
            i += length + 1
        return None
