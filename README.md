# SwitchRCMInjector

Simple RCM payload injector for Nintendo Switch on macOS.

![Platform](https://img.shields.io/badge/platform-macOS-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Features

- Modern GUI with dark theme (CustomTkinter)
- Auto-detection of Switch in RCM mode
- Command-line interface available
- Real-time connection status
- Injection log output

## Requirements

- macOS
- Python 3.10+
- libusb
- Nintendo Switch V1 (unpatched)

## Installation

```bash
# Clone the repository
git clone https://github.com/AngelSalinasT/SwitchRCMInjector.git
cd SwitchRCMInjector

# Install libusb
brew install libusb

# Run setup script
./setup.sh
```

Or manually:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### GUI Application

```bash
source .venv/bin/activate
python3 app.py
```

### Command Line

```bash
source .venv/bin/activate
python3 inject.py payloads/hekate_ctcaer_6.3.1.bin
```

## How to Enter RCM Mode

1. Power off the Switch completely (hold Power for 12 seconds)
2. Insert RCM jig into the right Joy-Con rail
3. Hold **Volume +** button
4. While holding Volume +, press **Power** briefly
5. Screen should stay completely black
6. Connect USB-C cable to your Mac

## Payloads

Place your `.bin` payload files in the `payloads/` folder. The app will auto-detect them.

Recommended payloads:
- [Hekate](https://github.com/CTCaer/hekate/releases) - Bootloader/payload launcher
- [TegraExplorer](https://github.com/suchmememanyskill/TegraExplorer/releases) - File manager

## Troubleshooting

### Switch not detected
- Make sure the Switch is in RCM mode (screen completely black)
- Try a different USB-C cable
- Check that libusb is installed: `brew list libusb`

### Permission errors
- Run with sudo if needed: `sudo python3 inject.py payload.bin`

### Low battery issues
- If battery is very low (<3.5V), the Switch may not enter RCM
- Charge for 10-15 minutes and try again

## Based On

- [Fusée Gelée](https://github.com/Qyriad/fusee-launcher) exploit (CVE-2018-6242)
- [JTegraNX](https://github.com/dylwedma11748/JTegraNX) injection logic

## License

MIT License
