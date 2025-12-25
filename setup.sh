#!/bin/bash
# Setup script for SwitchRCMInjector

echo "=== SwitchRCMInjector Setup ==="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no esta instalado"
    exit 1
fi

# Check for libusb
if ! brew list libusb &> /dev/null; then
    echo "Instalando libusb..."
    brew install libusb
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
fi

# Activate and install dependencies
echo "Instalando dependencias..."
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Setup completado!"
echo "Para inyectar un payload:"
echo "  source .venv/bin/activate"
echo "  python3 inject.py payloads/hekate_ctcaer_6.3.1.bin"
