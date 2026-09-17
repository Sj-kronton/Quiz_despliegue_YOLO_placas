# Plate Detector App

Aplicación para detección y reconocimiento de placas vehiculares utilizando una aplicación móvil desarrollada con **Expo / React Native / TypeScript** y una API desplegada en **AWS EC2** con modelos **YOLOv11**.
Para el quiz de ciencias de datos.

## Arquitectura

```text
📱 Teléfono
   │
   │ Expo Go
   ▼
💻 PC
   │
   │ Expo
   ▼
☁️ AWS EC2
   │
   ├── FastAPI
   ├── YOLOv11 - Detección de placas
   └── YOLOv11 - Reconocimiento de caracteres
```

---

# Inicio del proyecto

Para ejecutar el proyecto se deben realizar los siguientes pasos.

## 1. Conectarse a la VM de AWS

Desde **PowerShell en Windows**, conectarse mediante SSH:

```powershell
ssh -i "C:\Users\juana\OneDrive\Desktop\modelos\llavebike.pem" ubuntu@ec2-52-7-98-230.compute-1.amazonaws.com
```

> La ruta de la clave `.pem` y la dirección de la VM pueden cambiar dependiendo de la configuración de AWS.

---

## 2. Moverse a la carpeta del proyecto

Una vez conectado a la VM de AWS:

```bash
cd ~/proyecto
```

---

## 3. Activar el entorno virtual de Python

Activar el entorno virtual utilizado por la API:

```bash
source venv/bin/activate
```

La terminal debería mostrar algo similar a:

```text
(venv) ubuntu@ip-172-31-22-87:~/proyecto$
```

---

## 4. Iniciar la API de FastAPI y los modelos YOLO

Ejecutar:

```bash
python3 app.py
```

La API debería iniciar en el puerto `8080` y mostrar un mensaje similar a:

```text
Uvicorn running on http://0.0.0.0:8080
```

**No cerrar esta terminal**, ya que la API debe permanecer ejecutándose mientras se utiliza la aplicación móvil.

---

## 5. Abrir una segunda ventana de PowerShell

En el PC, abrir **otra ventana de PowerShell**.

La primera ventana permanece conectada a AWS y mantiene funcionando la API.

---

## 6. Moverse a la carpeta del proyecto Expo

Desde la nueva PowerShell:

```powershell
cd "C:\Users\juana\OneDrive\Desktop\plate-detector-app"
```

Para comprobar que se está en la carpeta correcta:

```powershell
dir
```

Deberían aparecer archivos como:

```text
App.tsx
package.json
tsconfig.json
```

---

## 7. Iniciar Expo

Ejecutar:

```powershell
npx expo start
```

Expo iniciará el servidor de desarrollo y mostrará un código QR en la terminal.

Por ejemplo:

```text
Starting project at ...
Metro waiting on ...
› Scan the QR code above with Expo Go
```

---

## 8. Abrir el proyecto en Expo Go

En el teléfono:

1. Abrir **Expo Go**.
2. Escanear el código QR mostrado por Expo.
3. Esperar a que Expo Go cargue la aplicación.
4. La aplicación podrá utilizar la API desplegada en AWS para realizar las detecciones.

---

# Flujo completo

Una vez iniciado todo, el flujo será:

```text
┌──────────────────┐
│   Teléfono       │
│   Expo Go        │
└────────┬─────────┘
         │
         │ Imagen
         ▼
┌──────────────────┐
│   Aplicación     │
│   Expo / React   │
│   Native         │
└────────┬─────────┘
         │
         │ HTTP POST
         │ /predict/
         ▼
┌─────────────────────────────┐
│          AWS EC2            │
│                             │
│          FastAPI            │
│             │               │
│             ▼               │
│       YOLOv11 #1             │
│     Detecta la placa         │
│             │               │
│             ▼               │
│       YOLOv11 #2             │
│   Detecta los caracteres     │
└─────────────┬───────────────┘
              │
              │ Resultado JSON
              ▼
        📱 Aplicación
```

## Notas

* La **API de FastAPI** se ejecuta en la VM de AWS.
* La aplicación **Expo** se ejecuta desde el PC durante el desarrollo.
* **Expo Go** se utiliza en el teléfono para visualizar y probar la aplicación.
* La API utiliza el puerto `8080`.
* La VM de AWS debe permitir las conexiones necesarias al puerto utilizado por la API.
* La aplicación móvil debe estar configurada con la dirección pública de la API para poder enviar las imágenes.


# Proceso de creacion del proyecto

## Un informe corto sobre como se desarrollo el proyecto

1. usando el comando "scp" desde powershell se subieron los archivos app.py, best_plate.py y best_ocr.py

* app.py fue configurado para no utilizar una libreria de OCR, sino en su lugar utilizar un segundo modelo de YOLOv11 entrenado para el proposito de OCR, que recibiera el resultado del primer modelo (el que detecta placas) y devolver el resultado.
* best_plate.py y best_ocr.py fueron entrenados en Colab usando YOLOv11 y 2 datasets de Roboflow, un dataset de 1.100 imagenes aproximadas de placas de vehiculo y aproximadamente 6.000 imagenes de letras y numeros para OCR, respectivamente.

2. Se creo un entorno en python desde el cual se lanzo la api (app.py)

3. Se verifico que el procesamiento correcto de datos y el flujo de app.py sea correcto con http://52.7.98.230:8080/docs#/

4. Se instalo node.js localmente

5. Se uso Expo para crear la aplicacion (app.tsx y app.json) que se ejecutaran localmente y se conectaran con la API de aws.

6. Se uso Expo GO en el celular para acceder a la aplicacion, verificar y evaluar el proyecto al completo de reconocimiento de placas de vehiculos colombianos.