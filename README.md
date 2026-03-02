# 🌍 IoT-Based Air Quality, Weather & Gas Leakage Monitoring System

## 📌 Project Overview

This project implements a real-time **Air Quality Index (AQI) Monitoring, Weather Monitoring, and Gas Leakage Detection System** using IoT architecture and the MQTT protocol.

The system collects environmental data from multiple sensors connected to a BeagleBone Black, processes the data using Python, stores it in MySQL, and enables intelligent decision-making through threshold-based alerts.

---

## 🧠 System Architecture

Sensors → BeagleBone Black → MQTT Publisher → MQTT Broker → MQTT Subscriber → Data Processing → MySQL Database → Alerts / Dashboard

---

## 🛠 Hardware Components

- BeagleBone Black
- BMP280 (Temperature & Pressure Sensor)
- DHT11 (Temperature & Humidity Sensor)
- MQ4 (Methane Gas Sensor)
- Power Supply
- Internet Connectivity

---

## 💻 Software Stack

| Layer              | Technology Used |
|--------------------|-----------------|
| Programming        | Python 3        |
| Communication      | MQTT Protocol   |
| Database           | MySQL           |
| OS (Edge Device)   | Debian (BBB)    |

---
## 📡 Features

### 1️⃣ Air Quality Monitoring
- Calculates AQI based on collected environmental parameters
- Stores processed data in MySQL
- Supports threshold-based alerting

### 2️⃣ Weather Monitoring
- Monitors temperature, humidity, and atmospheric pressure
- Enables environmental trend analysis

### 3️⃣ Gas Leakage Detection
- Detects methane gas using MQ135 sensor
- Generates alerts when gas levels exceed safety thresholds
---
