#!/usr/bin/env python3
"""
API de Detección y Reconocimiento de Placas Vehiculares (2 modelos YOLOv8)
============================================================================
- model_plate -> detecta TODAS las placas visibles en la imagen
- model_ocr   -> detecta caracteres individuales dentro del recorte de cada placa
                  (cada clase del modelo = un carácter A-Z, 0-9)

Flujo por cada placa detectada:
  recorte de la placa -> model_ocr -> caracteres con su coordenada X
  -> se ordenan izquierda a derecha -> se concatenan -> texto final de la placa

La imagen que se devuelve es la ORIGINAL completa, con cajas y texto dibujados
encima de cada placa detectada (no solo el recorte).
"""

import os
import base64
import logging
from typing import List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

# ------------------------------------------------------------------
# Config / Logging
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("yolo-plates-2models")
PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", "best_plate.pt")
OCR_MODEL_PATH = os.getenv("OCR_MODEL_PATH", "best_ocr.pt")
PLATE_CONF_THRESH = float(os.getenv("PLATE_CONF_THRESH", 0.4))
CHAR_CONF_THRESH = float(os.getenv("CHAR_CONF_THRESH", 0.3))
PORT = int(os.getenv("PORT", 8080))

# ------------------------------------------------------------------
# App init
# ------------------------------------------------------------------
app = FastAPI(title="API Detector de Placas Vehiculares (2 modelos YOLO)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ En producción cambia esto por el dominio/IP de tu app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Cargar modelos (una sola vez al iniciar el servidor)
# ------------------------------------------------------------------
logger.info("🔹 Cargando modelo de placas desde %s ...", PLATE_MODEL_PATH)
model_plate = YOLO(PLATE_MODEL_PATH)
logger.info("✅ Modelo de placas cargado.")

logger.info("🔹 Cargando modelo OCR (caracteres) desde %s ...", OCR_MODEL_PATH)
model_ocr = YOLO(OCR_MODEL_PATH)
logger.info("✅ Modelo OCR cargado.")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def leer_caracteres(plate_crop: np.ndarray):
    """
    Corre el modelo OCR sobre el recorte de UNA placa.
    Ordena los caracteres de izquierda a derecha (por x1) y arma el texto final.
    Devuelve (texto_placa, lista_de_caracteres_detectados).
    """
    if plate_crop is None or plate_crop.size == 0:
        return "", []

    results = model_ocr.predict(plate_crop, conf=CHAR_CONF_THRESH, verbose=False)
    boxes = results[0].boxes
    names = model_ocr.names

    if boxes is None or len(boxes) == 0:
        return "", []

    detecciones = []
    for i in range(len(boxes)):
        x1, y1, x2, y2 = boxes.xyxy[i].tolist()
        cls_id = int(boxes.cls[i])
        conf = float(boxes.conf[i])
        detecciones.append({
            "caracter": names[cls_id],
            "confianza": round(conf, 4),
            "x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2),
        })

    detecciones_ordenadas = sorted(detecciones, key=lambda d: d["x1"])
    texto_placa = "".join(d["caracter"] for d in detecciones_ordenadas)
    return texto_placa, detecciones_ordenadas


def image_to_base64_jpg(img_bgr: np.ndarray) -> str:
    """Convierte una imagen BGR a JPG en Base64."""
    _, buffer = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return base64.b64encode(buffer).decode("utf-8")


# ------------------------------------------------------------------
# Rutas
# ------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "API de placas (2 modelos YOLO) activa"}


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    """
    Recibe una imagen (multipart/form-data) y devuelve:
    {
        "success": true,
        "num_placas": 2,
        "placas": [
            {"texto": "ABC123", "confianza_deteccion": 0.91, "bbox": {...}, "caracteres": [...]},
            ...
        ],
        "image": "<base64 de la imagen ORIGINAL con cajas y texto dibujados>",
        "message": "OK"
    }
    """
    try:
        logger.info("📩 Petición recibida en /predict/")
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "No se pudo decodificar la imagen enviada"}

        logger.info("🧠 Detectando placas con el modelo 1...")
        results = model_plate.predict(frame, conf=PLATE_CONF_THRESH, verbose=False)
        boxes = results[0].boxes

        if boxes is None or len(boxes) == 0:
            img_b64 = image_to_base64_jpg(frame)
            return {
                "success": True,
                "num_placas": 0,
                "placas": [],
                "image": img_b64,
                "message": "No se detectó ninguna placa",
            }

        h, w = frame.shape[:2]
        placas_resultado = []

        # Se procesa CADA placa detectada en la imagen
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()
            conf_placa = float(boxes.conf[i])
            x1, y1, x2, y2 = int(max(0, x1)), int(max(0, y1)), int(min(w, x2)), int(min(h, y2))

            crop = frame[y1:y2, x1:x2].copy()
            texto_placa, caracteres = leer_caracteres(crop)

            placas_resultado.append({
                "texto": texto_placa,
                "confianza_deteccion": round(conf_placa, 4),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "caracteres": caracteres,
            })

            # Dibujar la caja y el texto sobre la imagen ORIGINAL
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = texto_placa if texto_placa else "placa"
            cv2.putText(frame, label, (x1, max(30, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        img_b64 = image_to_base64_jpg(frame)
        logger.info("✅ Placas detectadas: %s", [p["texto"] for p in placas_resultado])

        return {
            "success": True,
            "num_placas": len(placas_resultado),
            "placas": placas_resultado,
            "image": img_b64,
            "message": "OK",
        }

    except Exception as e:
        logger.exception("Error en /predict/: %s", e)
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando servidor en 0.0.0.0:%s", PORT)
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
