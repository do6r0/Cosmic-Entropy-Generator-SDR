import asyncio
import hashlib
import ssl
import numpy as np

# Database of cosmic radio noise sources:
# (id, use_ssl, host, port, freq_khz, band_id, short_title, description)
NODES = [
    (1, False, "websdr.camras.nl",           8901, 1296500.0, 0,
     "Dwingeloo 25m Dish — 1296.5 MHz (23 cm)",
     "Netherlands. Direct feed from the 25-meter radio telescope (galactic background, pulsars)."),

    (2, False, "websdr.camras.nl",           8901, 432500.0,  0,
     "Dwingeloo 25m Dish — 432.5 MHz (70 cm)",
     "Netherlands. 24/7 channel from the 25-meter dish (moonbounce/EME, cosmic background noise)."),

    (3, True,  "vhf-goonhilly.batc.org.uk",  443,  1296500.0, 0,
     "Goonhilly Earth Station — 1296.5 MHz (23 cm)",
     "United Kingdom. Deep-space communications station, clean 24/7 microwave spectrum."),

    (4, True,  "vhf-goonhilly.batc.org.uk",  443,  435500.0,  0,
     "Goonhilly Earth Station — 435.5 MHz (70 cm)",
     "United Kingdom. Satellite and space communications segment of the UHF band."),

    (5, False, "websdr.is0grb.it",           8903, 1296500.0, 0,
     "Sardinia IS0GRB — 1296.5 MHz (23 cm)",
     "Italy. High-altitude observatory located in a low-interference radio zone."),

    (6, False, "websdr.camras.nl",           8901, 20100.0,   9,
     "Dwingeloo Radio JOVE — 20.1 MHz",
     "Netherlands. Dedicated antenna for receiving decametric radio bursts from Jupiter and the Sun.")
]


async def collect_raw_tcp_stream(use_ssl, host, port, freq_khz, band_id, collect_bytes=16384):
    """Connects to WebSDR via a raw TCP/TLS socket and collects raw RF audio bytes."""
    ssl_ctx = None
    if use_ssl:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(host, port, ssl=ssl_ctx),
        timeout=4.0
    )

    raw_data = bytearray()
    try:
        path = f"/~~stream?f={freq_khz}&band={band_id}&lo=-2.7&hi=-0.3&mode=usb&name=cosmic_rng"
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"User-Agent: Mozilla/5.0\r\n"
            f"Connection: keep-alive\r\n\r\n"
        ).encode("ascii")

        writer.write(request)
        await writer.drain()

        param_cmd = f"GET /~~param?f={freq_khz}&band={band_id}&mute=0 HTTP/1.1\r\nHost: {host}\r\n\r\n".encode("ascii")
        writer.write(param_cmd)
        await writer.drain()

        deadline = asyncio.get_event_loop().time() + 4.0
        while len(raw_data) < collect_bytes and asyncio.get_event_loop().time() < deadline:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=2.0)
            if not chunk:
                break
            raw_data.extend(chunk)

    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

    return raw_data


async def run_collector(selected_nodes, collect_bytes=16384):
    """Iterates through the selected nodes and extracts 256-bit cosmic entropy."""
    for node_id, use_ssl, host, port, freq, band_id, title, _ in selected_nodes:
        print(f"\n[Connecting #{node_id}] {title}...")
        try:
            data = await collect_raw_tcp_stream(use_ssl, host, port, freq, band_id, collect_bytes)

            if data.startswith(b"HTTP/1.") and b"200 OK" not in data[:100]:
                first_line = data.split(b"\r\n", 1)[0].decode("ascii", errors="ignore")
                print(f"[Skipped] {host} responded: {first_line}")
                continue

            if len(data) >= 2048:
                # Strip the first 256 bytes of connection/sync headers
                clean_audio = bytes(data[256:])

                # Extract the 2 least significant bits (LSB) from each byte
                byte_array = np.frombuffer(clean_audio, dtype=np.uint8)
                lsb_bits = np.unpackbits(byte_array & 0b00000011)
                packed_entropy = np.packbits(lsb_bits).tobytes()

                # Cryptographic whitening via SHA-256
                cosmic_hash = hashlib.sha256(packed_entropy).hexdigest()
                return cosmic_hash, len(clean_audio), title
            else:
                print(f"[Skipped] {host} returned insufficient data ({len(data)} bytes).")

        except Exception as e:
            print(f"[Error] {host}: {type(e).__name__} — {e}")

    raise RuntimeError("Failed to retrieve a data stream from any of the selected servers.")


def select_menu():
    """Displays an interactive source selection menu on startup."""
    print("=== Cosmic Entropy Generator (WebSDR) ===")
    print("0. [Auto Mode] Iterate through all servers until the first successful capture\n")

    for node_id, _, _, _, _, _, title, desc in NODES:
        print(f"{node_id}. {title}")
        print(f"   └─ {desc}")

    while True:
        choice = input("\nEnter source number (0–6) [default 0]: ").strip()
        if choice == "" or choice == "0":
            return NODES
        if choice.isdigit():
            num = int(choice)
            matched = [n for n in NODES if n[0] == num]
            if matched:
                return matched
        print("Invalid input. Please enter a number between 0 and 6.")


if __name__ == "__main__":
    targets = select_menu()
    try:
        entropy_hex, total_bytes, active_title = asyncio.run(run_collector(targets))
        print("\n==============================================")
        print("Cosmic entropy successfully harvested!")
        print(f"Source: {active_title}")
        print(f"Raw RF bytes processed: {total_bytes}")
        print(f"256-bit key (SHA-256): {entropy_hex}")
        print("==============================================")
    except RuntimeError as err:
        print(f"\n[Failure] {err}")
