import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration
from plugp100.discovery.tapo_discovery import TapoDiscovery
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)


class DeviceRequest(BaseModel):
    device_host: str
    email: str
    password: str

class Credentials(BaseModel):
    email: str
    password: str

from pydantic import BaseModel

class DeviceInfo(BaseModel):
    device_id: str
    hardware_id: str
    oem_id: str
    firmware_version: str
    hardware_version: str
    ip: str
    mac: str
    nickname: str
    model: str
    type: str
    overheated: bool
    ssid: str
    signal_level: int
    rssi: int
    friendly_name: str
    has_set_location_info: bool
    latitude: int
    longitude: int
    timezone: str
    time_difference: int
    language: str
    is_hardware_v2: bool
    
    
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", 
  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/devices", response_model=list[DeviceInfo])
async def get_devices(credentials: Credentials):
    try:
        auth_credentials = AuthCredential(credentials.email, credentials.password)
        
        discovered_devices = await TapoDiscovery.scan(timeout=5)
        detailed_devices = []
        
        for device in discovered_devices:
            device_configuration = DeviceConnectConfiguration(
                host=device.ip,
                credentials=auth_credentials
            )
            connected_device = await connect(device_configuration)
            await connected_device.update()
            
            device_info = DeviceInfo(
                device_id=connected_device.device_info.device_id,
                hardware_id=connected_device.device_info.hardware_id,
                oem_id=connected_device.device_info.oem_id,
                firmware_version=connected_device.device_info.firmware_version,
                hardware_version=connected_device.device_info.hardware_version,
                ip=connected_device.device_info.ip,
                mac=connected_device.device_info.mac,
                nickname=connected_device.device_info.nickname,
                model=connected_device.device_info.model,
                type=connected_device.device_info.type,
                overheated=connected_device.device_info.overheated,
                ssid=connected_device.device_info.ssid,
                signal_level=connected_device.device_info.signal_level,
                rssi=connected_device.device_info.rssi,
                friendly_name=connected_device.device_info.friendly_name,
                has_set_location_info=connected_device.device_info.has_set_location_info,
                latitude=connected_device.device_info.latitude,
                longitude=connected_device.device_info.longitude,
                timezone=connected_device.device_info.timezone,
                time_difference=connected_device.device_info.time_difference,
                language=connected_device.device_info.language,
                is_hardware_v2=connected_device.device_info.is_hardware_v2
            )
            
            detailed_devices.append(device_info)
        
        return detailed_devices
    except Exception as e:
        logger.error(f"Error al descubrir dispositivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    
async def toggle_device(state: str, device_host: str, credentials: AuthCredential):
    try:
        device_configuration = DeviceConnectConfiguration(
            host=device_host,
            credentials=credentials
        )
        device = await connect(device_configuration)
        await device.update()
        logger.info(f"Dispositivo conectado y actualizado: {device}")
        
        if state == "on":
            await device.turn_on()
            return "Dispositivo encendido"
        elif state == "off":
            await device.turn_off()
            return "Dispositivo apagado"
        else:
            raise ValueError("Estado no reconocido. Use 'on' o 'off'.")
    except Exception as e:
        logger.error(f"Error al cambiar el estado del dispositivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/device/{state}")
async def control_device(state: str, device_request: DeviceRequest):
    auth_credentials = AuthCredential(device_request.email, device_request.password)
    response = await toggle_device(state, device_request.device_host, auth_credentials)
    return {"message": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

