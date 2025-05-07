# Rastreador de Satélites en Tiempo Real con CesiumJS y Python

Este proyecto permite visualizar satélites en tiempo real sobre un globo 3D utilizando **CesiumJS** para el visor y **Python** para calcular las posiciones satelitales a partir de datos TLE.

Incluye:
- Cálculo de posiciones con SGP4/Skyfield.
- Generación automática de archivos KML.
- Visualización en CesiumJS con trayectorias y filtros por grupos.
- Sistema de alertas cuando un satélite pasa cerca de tu estación base.
- Selección de estación base con clic derecho directamente en el mapa.

## 🚀 Requisitos

Python >= 3.8

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## 📂 Estructura del proyecto

```plaintext
├── satellite_tracker.py       # Script principal que calcula posiciones y genera el KML y alertas.
├── index.html                 # Visor CesiumJS.
├── satellite_positions.kml    # Archivo KML que se actualiza automáticamente.
├── alerta.json                # Archivo de alerta generado por el script.
├── sat_images/                # Carpeta con iconos de satélites (opcional pero recomendada).
├── tle/                       # Carpeta donde se descargan los TLE (creada automáticamente).
├── requirements.txt
└── README.md
```

## ⚙ Cómo usar

### 1️⃣ Ejecutar el rastreador

```bash
python satellite_tracker.py
```

El script descargará los TLE si es necesario, calculará las posiciones y actualizará `satellite_positions.kml` y `alerta.json` cada 3 minutos.

### 2️⃣ Lanzar el visor CesiumJS

Desde la carpeta donde está el `index.html`:

```bash
python -m http.server 8000
```

Luego abre tu navegador en:

```
http://localhost:8000/index.html
```

**Importante**: Abrir directamente el `index.html` con doble clic (file://) **no funcionará** por restricciones CORS. Usa siempre el servidor local.

## 🛰 Funciones disponibles en el visor

- Activar/desactivar grupos de satélites.
- Mostrar/ocultar trayectorias.
- Visualización de detalles de cada satélite con icono, altitud, país, operador, azimut y elevación.
- Alerta visual cuando un satélite pasa cerca de tu estación base.
- Cambiar estación base haciendo clic derecho en el mapa.

## 📝 Notas

- La ubicación inicial de la estación base es Madrid (Lat 40.4168, Lon -3.7038).
- Puedes modificar esa posición manualmente o haciendo clic derecho en el mapa.
- Las posiciones se actualizan cada minuto en el visor.
- Los TLE se consideran válidos si tienen menos de 30 días.

## NOTA: INGRESAR LA API DE CESIUM EN EL INDEX.HTML 

## 📄 Licencia

Proyecto educativo y personal. Puedes modificarlo y adaptarlo libremente.


