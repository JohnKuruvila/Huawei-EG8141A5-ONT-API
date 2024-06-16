import time
from datetime import datetime

import requests
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from huawei_eg8141a5_api import EG8141A5

router = EG8141A5("192.168.18.1")

router.login("Epuser", "epuserpassword")
optic_info = router.get_optic_info()
wan_info = router.get_wan_info()
eth_info = router.get_eth_info()
device_info = router.get_device_info()
router.logout()

client = InfluxDBClient(
    url="http://localhost:8086",
    token="token",
    org="users",
)
write_api = client.write_api(write_options=SYNCHRONOUS)

influxdb_data = [
    {
        "measurement": "Router_Stats",
        "time": time.time_ns(),
        "fields": {
            "transOpticPower": optic_info["transOpticPower"],
            "revOpticPower": optic_info["revOpticPower"],
            "voltage": float(optic_info["voltage"]),
            "temperature": float(optic_info["temperature"]),
            "bias": float(optic_info["bias"]),
            "OpticalLinkTime": float(optic_info["LinkTime"]),
            "LosStatus": float(optic_info["LosStatus"]),
            "WAN_BytesSent": float(wan_info["BytesSent"]),
            "WAN_BytesReceived": float(wan_info["BytesReceived"]),
            "WAN_Uptime": float(wan_info["Uptime"]),
            "LAN1_txBytes": eth_info["LAN1"]["txBytes"],
            "LAN1_rxBytes": eth_info["LAN1"]["rxBytes"],
            "LAN2_txBytes": eth_info["LAN2"]["txBytes"],
            "LAN2_rxBytes": eth_info["LAN2"]["rxBytes"],
            "LAN3_txBytes": eth_info["LAN3"]["txBytes"],
            "LAN3_rxBytes": eth_info["LAN3"]["rxBytes"],
            "LAN4_txBytes": eth_info["LAN4"]["txBytes"],
            "LAN4_rxBytes": eth_info["LAN4"]["rxBytes"],
            "CpuUsage": device_info["cpuUsed"],
            "MemoryUsage": device_info["memUsed"],
            "DeviceUptime": device_info["dev_uptime"],
        },
    }
]

write_api.write("router-stats", "users", influxdb_data)
