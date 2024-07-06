import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import connect, DeviceConnectConfiguration
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)

# Configuración del dispositivo
DEVICE_HOST = os.getenv("DEVICE_HOST")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

CREDENTIALS = AuthCredential(EMAIL, PASSWORD)

async def toggle_device(state: str):
    try:
        device_configuration = DeviceConnectConfiguration(
            host=DEVICE_HOST,
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
@app.get("/device/{state}")
async def control_device(state: str):
    response = await toggle_device(state)
    return {"message": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
