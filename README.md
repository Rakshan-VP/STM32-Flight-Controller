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

