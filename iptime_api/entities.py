from enum import Enum
from pydantic import BaseModel, model_validator
from typing import Optional

class FirmwareUpgradeStatus(Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    WRITING = "writing"

class Router(BaseModel):
    name: str
    id: str
    company: str
    type: str
    oui: str
    mac: str
    board: str
    version: str
    wan_mac: str
    reboot_period: int
    homepage: str
    mesh_support: str
    mesh_support_role: list[str]

class Station(BaseModel):
    mac: str
    type: str  # "wired" 또는 "wireless"
    agent_mac: Optional[str] = None
    nickname: Optional[str] = None
    ip: Optional[str] = None
    wan_ip: str
    timestamp: int
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    ptype: str
    up_bytes: Optional[int] = None
    down_bytes: Optional[int] = None
    connection: str

    # 공통 속성 외에 조건부 속성
    # Wired-specific
    link: Optional[int] = None
    port: Optional[int] = None
    up_error: Optional[int] = None
    up_mcast: Optional[int] = None
    down_mcast: Optional[int] = None

    # Wireless-specific
    if_type: Optional[str] = None
    mode: Optional[str] = None
    channel: Optional[str] = None
    uplink: Optional[int] = None
    downlink: Optional[int] = None
    connected_ts: Optional[int] = None
    rssi: Optional[int] = None
    caps: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def validate_type_specific_fields(cls, values):
        device_type = values.get("type")
        connection = values.get("connection")
        if device_type == "wired":
            if connection == "WIRED":
                required_fields = ["link", "port", "up_mcast", "down_mcast", "up_error"]
                for field in required_fields:
                    if field not in values or values[field] is None:
                        raise ValueError(f"'{field}' is required for type 'wired'")
        elif device_type == "wireless":
            required_fields = [
                "if_type", "mode", "channel", "uplink", "downlink", "connected_ts", "rssi", "caps"
            ]
            for field in required_fields:
                if field not in values or values[field] is None:
                    raise ValueError(f"'{field}' is required for type 'wireless'")
        else:
            raise ValueError("Invalid type: must be 'wired' or 'wireless'")
        return values
