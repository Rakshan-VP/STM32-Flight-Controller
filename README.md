# 🛩️ STM32 Flight Controller – GUI-Controlled Drone via PC

A full-featured development project to create a **graphical user interface (GUI)** for controlling a drone using an STM32-based flight controller and NRF24L01 communication module. This project uses **PlatformIO with VS Code** on Linux and targets **Arduino framework** development with DFU mode flashing.

---

## 📦 Hardware Overview

### ✈️ Drone Flight Controller
- **Board:** STM32F401 Blackpill
- **IMU:** MPU6050 (Gyroscope + Accelerometer)
- **Magnetometer:** HMC5883L
- **Communication Module:** NRF24L01 (SPI)
- **PWM Outputs:** 6 (for ESCs or servos)
- **Firmware Upload Mode:** DFU (Device Firmware Upgrade)

### 🖥️ Ground Station Transceiver
- **Board:** Arduino Nano
- **Communication Module:** NRF24L01
- **Purpose:** Interface with PC over Serial for GUI ↔️ Drone communication

---

## 🛠️ Development Environment

- **Platform:** Visual Studio Code
- **Extension:** [PlatformIO IDE](https://platformio.org/install/ide?install=vscode)
- **Operating System:** Linux (tested on Ubuntu/Debian)
- **Framework:** Arduino (STM32 support via STM32duino)
- **Upload Method:** `dfu-util` (direct USB bootloader)

---

## 🚀 Getting Started

### ✅ 1. Install Requirements

```bash
# Install VS Code (if not installed)
sudo snap install code --classic

# Install dfu-util
sudo apt update
sudo apt install dfu-util
```

### 🧩 2. Set Up PlatformIO in VS Code
1. Open Visual Studio Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for PlatformIO IDE
4. Click Install

> This will install PlatformIO Core and all required toolchains.

### 📁 3. Create a New Project
1. Click the PlatformIO alien icon (bottom-left sidebar)
2. Click "New Project"
3. Set project name: stm32_flight_controller
4. Board: **BlackPill F401CC**
5. Framework: **Arduino**
6. Click Finish

> Wait for PlatformIO to finish setting up the project environment.

### 📄 4. Add Provided Source Files
After the project is created:
1. Replace all files inside the **src/ folder** with the **.cpp** files provided in this repository.
2. Replace the default **platformio.ini** file in the project root with the following configuration:

```ini
[env:blackpill_f401cc]
platform = ststm32
board = blackpill_f401cc
framework = arduino
upload_protocol = dfu
monitor_speed = 115200
```

### 🔧 5. Build the Project
You can build the firmware using either method:

✅ Using GUI:
1. Click the PlatformIO alien icon
2. Navigate to Project Tasks → Build

✅ Using Terminal:
```bash
pio run
```

### ⬆️ 6. Upload Firmware via DFU
🧷 Enter DFU Mode:
1. Hold down the **BOOT0** button on your STM32 board
2. Press and release the **RESET** button
3. Release **BOOT0**

Your device should now appear as **STM32 BOOTLOADER** in **lsusb**.
```bash
Bus 001 Device 003: ID 0483:df11 STMicroelectronics STM Device in DFU Mode.
```
🚀 Upload the Firmware:

✅ GUI Method:
1. Click **PlatformIO → Upload**

✅ Terminal Method:
```bash
pio run --target upload
```
This uses **dfu-util** to flash the firmware over **USB**.


