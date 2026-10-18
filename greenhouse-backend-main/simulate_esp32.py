"""
ESP32 Telemetry Live Simulator
Simulates a physical ESP32 sending sensor telemetry to the backend.
Can target local FastAPI server or the production Render deployment.
"""

import argparse
import math
import random
import sys
import time
import requests

DEFAULT_URL = "https://greenhouse-backend-oo6p.onrender.com"
DEFAULT_DEVICE_ID = "greenhouse-01"
DEFAULT_DEVICE_KEY = "change_this_to_another_long_random_string_789"


def run_simulation(base_url: str, device_id: str, device_key: str, interval: float):
    endpoint = f"{base_url.rstrip('/')}/sensors/data"
    print("=" * 60)
    print("  SMART GREENHOUSE - ESP32 TELEMETRY SIMULATOR")
    print(f"  Target:    {endpoint}")
    print(f"  Device ID: {device_id}")
    print(f"  Interval:  {interval}s")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    # Base starting metrics
    temp_base = 26.5
    hum_base = 62.0
    soil_base = 48.0
    light_base = 65.0
    step = 0

    headers = {
        "Content-Type": "application/json",
        "x-device-key": device_key,
    }

    while True:
        step += 1
        # Create natural sinusoidal wave fluctuations with subtle random noise
        temp = round(temp_base + 4.0 * math.sin(step * 0.15) + random.uniform(-0.4, 0.4), 1)
        hum = round(hum_base - 5.0 * math.sin(step * 0.15) + random.uniform(-0.8, 0.8), 1)
        soil = round(soil_base - (step * 0.2) % 30 + random.uniform(-0.5, 0.5), 1)
        if soil < 15:
            soil = 75.0  # simulated irrigation refill
        light = round(light_base + 25.0 * math.sin(step * 0.1) + random.uniform(-1.5, 1.5), 0)
        light = max(0.0, min(100.0, light))

        payload = {
            "device_id": device_id,
            "temperature": temp,
            "humidity": hum,
            "soil_moisture": soil,
            "light_intensity": light,
        }

        try:
            start_time = time.time()
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            latency_ms = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                print(f"[LIVE {time.strftime('%H:%M:%S')}] Pushed: Temp={temp}°C, Hum={hum}%, Soil={soil}%, Light={light}% (Status: {resp.status_code}, {latency_ms}ms)", flush=True)
            else:
                print(f"[FAIL {time.strftime('%H:%M:%S')}] Status: {resp.status_code} - {resp.text}", flush=True)
        except Exception as e:
            print(f"[ERROR {time.strftime('%H:%M:%S')}] Connection failed: {e}", flush=True)

        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate live ESP32 data upload")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base backend URL")
    parser.add_argument("--device", default=DEFAULT_DEVICE_ID, help="Device ID")
    parser.add_argument("--key", default=DEFAULT_DEVICE_KEY, help="Device API key")
    parser.add_argument("--interval", type=float, default=3.0, help="Send interval in seconds")
    args = parser.parse_args()

    try:
        run_simulation(args.url, args.device, args.key, args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
        sys.exit(0)
