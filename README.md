# Cosmic Entropy Generator (WebSDR TRNG)

A lightweight, browserless True Random Number Generator (TRNG) written in Python.  It harvests live cosmic radio noise—such as galactic background radiation, pulsar emissions, lunar echoes, and decametric bursts from Jupiter and the Sun—from public radio telescopes and deep-space ground stations via the WebSDR network, converting raw RF chaos into cryptographically whitened 256-bit keys.

---

## Features

* **Genuine Physical Entropy:**  Relies on unpredictable astrophysical and quantum-thermal radio fluctuations rather than deterministic pseudo-random algorithms.
* **Headless & Lightweight:**  Connects directly to WebSDR servers over raw TCP/TLS sockets without requiring a web browser or heavy third-party HTTP/WebSocket wrappers.
* **Multi-Node Failover:**  Includes six curated VHF, UHF, and microwave channels across observatories in the Netherlands, the United Kingdom, and Italy.  Supports both manual source selection and automatic sequential fallback.
* **Cryptographic Whitening:**  Extracts the two least significant bits (LSB) from each incoming audio byte to discard codec artefacts, then processes the bit stream through **SHA-256** to guarantee uniform distribution.

---

## Available Cosmic Sources

| ID | Observatory / Station | Frequency | Band | Primary Astrophysical Targets |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Dwingeloo 25m Dish (Netherlands) | `1296.5 MHz` | 23 cm | Galactic background, pulsars, deep-space microwave noise |
| **2** | Dwingeloo 25m Dish (Netherlands) | `432.5 MHz` | 70 cm | Earth-Moon-Earth (EME) reflections, cosmic background |
| **3** | Goonhilly Earth Station (UK) | `1296.5 MHz` | 23 cm | Clean 24/7 microwave spectrum from a deep-space station |
| **4** | Goonhilly Earth Station (UK) | `435.5 MHz` | 70 cm | Satellite and near-space UHF segment |
| **5** | Sardinia IS0GRB (Italy) | `1296.5 MHz` | 23 cm | High-altitude, low-interference microwave reception |
| **6** | Dwingeloo Radio JOVE (Netherlands) | `20.1 MHz` | 15 m | Decametric radio bursts from Jupiter and solar storms |

---

## Prerequisites

* **Python 3.8** or higher.
* **NumPy** for high-speed bitwise manipulation.

---

## Installation

1. **Clone or download the repository**

2. **Install the required dependency:**

   ```bash
   pip install numpy
   ```

---

## Usage

Run the script from your terminal:

```bash
python sdr_entropy.py
```

Upon launch, an interactive menu will appear:

```text
=== Cosmic Entropy Generator (WebSDR) ===
0. [Auto Mode] Iterate through all servers until the first successful capture

1. Dwingeloo 25m Dish — 1296.5 MHz (23 cm)
   └─ Netherlands. Direct feed from the 25-meter radio telescope (galactic background, pulsars).
...
Enter source number (0–6) [default 0]:
```

* **Automatic Failover Mode:**  Press `Enter` or type `0`.  The script will test each observatory in order of priority until it secures a live RF stream.
* **Targeted Mode:**  Enter a number between `1` and `6` to harvest entropy exclusively from that specific antenna.

### Example Output

```text
[Connecting #1] Dwingeloo 25m Dish — 1296.5 MHz (23 cm)...

==============================================
Cosmic entropy successfully harvested!
Source: Dwingeloo 25m Dish — 1296.5 MHz (23 cm)
Raw RF bytes processed: 16128
256-bit key (SHA-256): 8f4b2e91c0a7d35e6b12f9480c3d7a1e5b8f2c4d6a9e0137f5b8c2d4e6a1f309
==============================================
```

---

## How It Works

1. **Socket Handshake:**  Opens an asynchronous TCP or TLS stream directly to the chosen WebSDR server and tunes the receiver to an open cosmic frequency in Upper Sideband (`USB`) mode.
2. **Stream Capture:**  Collects `16,384` bytes of digitised radio noise over approximately four seconds, stripping the initial `256` bytes to discard connection headers.
3. **Entropy Extraction:**  Isolates the two least significant bits (`byte & 0b00000011`) of every byte, capturing thermal and quantum receiver fluctuations while eliminating audio compression patterns.
4. **Hashing:**  Packs the extracted bits into a byte array and computes a **SHA-256** digest, yielding a clean 256-bit cryptographic seed.

---

## Etiquette & Fair Use

Public WebSDR servers are maintained by volunteers and radio astronomy foundations (such as CAMRAS and BATC).  This script connects for only a few seconds per run and immediately closes the socket afterwards.  Please avoid running continuous, high-frequency polling loops so that listener slots remain available for human operators.
