import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration
from plugp100.discovery.tapo_discovery import TapoDiscovery
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)

# Configuración de las credenciales
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
CREDENTIALS = AuthCredential(EMAIL, PASSWORD)

class DeviceRequest(BaseModel):
    device_host: str

@app.get("/devices")
async def get_devices():
    try:
        discovered = await TapoDiscovery.scan(timeout=5)
        devices = []
        for discovered_device in discovered:
            try:
                device = await discovered_device.get_tapo_device(CREDENTIALS)
                await device.update()
                devices.append({
                    'ip': discovered_device.ip,
                    'type': type(device).__name__,
                    'protocol': device.protocol_version,
                    'raw_state': device.raw_state
                })
                await device.client.close()
            except Exception as e:
                logger.error(f"Failed to update {discovered_device.ip} {discovered_device.device_type}", exc_info=e)
        return {"devices": devices}
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def toggle_device(state: str, device_host: str):
    try:
        device_configuration = DeviceConnectConfiguration(
            host=device_host,
            credentials=CREDENTIALS
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
    response = await toggle_device(state, device_request.device_host)
    return {"message": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
