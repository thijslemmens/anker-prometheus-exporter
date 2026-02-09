from prometheus_client import Gauge, Info, start_http_server
import asyncio
from aiohttp import ClientSession
from api.api import AnkerSolixApi
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "60"))
ANKER_EMAIL = os.getenv("ANKER_USER")
ANKER_PASSWORD = os.getenv("ANKER_PASSWORD")

if not ANKER_EMAIL or not ANKER_PASSWORD:
    raise ValueError("ANKER_EMAIL and ANKER_PASSWORD environment variables are required")

anker_soc = Gauge("anker_battery_soc", "Battery state of charge", ["device_name", "device_sn"])
anker_capacity = Gauge("anker_battery_capacity_wh", "Battery total capacity", ["device_name", "device_sn"])
anker_energy = Gauge("anker_battery_energy_wh", "Current battery energy", ["device_name", "device_sn"])
anker_charging_power = Gauge("anker_charging_power_w", "Charging power", ["device_name", "device_sn"])
anker_bat_charge_power = Gauge("anker_bat_charge_power_w", "Battery charge power", ["device_name", "device_sn"])
anker_bat_discharge_power = Gauge("anker_bat_discharge_power_w", "Battery discharge power", ["device_name", "device_sn"])
anker_solar_power_1 = Gauge("anker_solar_power_1_w", "Solar input 1", ["device_name", "device_sn"])
anker_solar_power_2 = Gauge("anker_solar_power_2_w", "Solar input 2", ["device_name", "device_sn"])
anker_ac_power = Gauge("anker_ac_power_w", "AC output power", ["device_name", "device_sn"])
anker_to_home_load = Gauge("anker_to_home_load_w", "Power to home", ["device_name", "device_sn"])
anker_charging_status = Gauge("anker_charging_status", "Charging status (0=idle,1=charging,2=discharging)", ["device_name", "device_sn"])
anker_wifi_online = Gauge("anker_wifi_online", "WiFi connection status", ["device_name", "device_sn"])

device_info = Info("anker_device", "Anker device information", ["device_name", "device_sn"])


async def fetch_metrics():
    async with ClientSession() as session:
        api = AnkerSolixApi(ANKER_EMAIL, ANKER_PASSWORD, "1", session)
        await api.update_sites()
        await api.update_device_details()

        for sn, dev in api.devices.items():
            name = dev.get("name", dev.get("alias", "Unknown"))
            
            if dev.get("type") == "solarbank":
                anker_soc.labels(device_name=name, device_sn=sn).set(dev.get("battery_soc", 0))
                anker_capacity.labels(device_name=name, device_sn=sn).set(dev.get("battery_capacity", 0))
                anker_energy.labels(device_name=name, device_sn=sn).set(dev.get("battery_energy", 0))
                anker_charging_power.labels(device_name=name, device_sn=sn).set(dev.get("charging_power", 0))
                anker_bat_charge_power.labels(device_name=name, device_sn=sn).set(dev.get("bat_charge_power", 0))
                anker_bat_discharge_power.labels(device_name=name, device_sn=sn).set(dev.get("bat_discharge_power", 0))
                anker_solar_power_1.labels(device_name=name, device_sn=sn).set(dev.get("solar_power_1", 0))
                anker_solar_power_2.labels(device_name=name, device_sn=sn).set(dev.get("solar_power_2", 0))
                anker_ac_power.labels(device_name=name, device_sn=sn).set(dev.get("ac_power", 0))
                anker_to_home_load.labels(device_name=name, device_sn=sn).set(dev.get("to_home_load", 0))
                anker_charging_status.labels(device_name=name, device_sn=sn).set(dev.get("charging_status", 0))
                anker_wifi_online.labels(device_name=name, device_sn=sn).set(1 if dev.get("wifi_online") else 0)

                device_info.labels(device_name=name, device_sn=sn).info({
                    "device_type": dev.get("type", ""),
                    "device_pn": dev.get("device_pn", ""),
                    "sw_version": dev.get("sw_version", ""),
                    "wifi_name": dev.get("wifi_name", ""),
                })


async def run_exporter():
    while True:
        try:
            await fetch_metrics()
        except Exception as e:
            print(f"Error fetching metrics: {e}")
        await asyncio.sleep(REFRESH_INTERVAL)


def main():
    start_http_server(METRICS_PORT)
    print(f"Prometheus metrics server started on port {METRICS_PORT}")
    asyncio.run(run_exporter())


if __name__ == "__main__":
    main()
