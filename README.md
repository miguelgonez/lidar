# LiDAR Vélez-Málaga - Detección de Anomalías Arqueológicas

Pipeline completo para detectar estructuras arqueológicas ocultas utilizando datos PNOA-LiDAR 3ª cobertura en Vélez-Málaga, España.

## Características

- **Descarga automática** de tiles LiDAR desde el Centro de Descargas del CNIG
- **Generación de DEM** (Modelo Digital del Terreno) desde archivos LAZ
- **Análisis de derivadas**: Hillshade multi-direccional y Sky View Factor (SVF)
- **Detección con IA**: Utiliza Gemini AI para identificar anomalías arqueológicas
- **Visualización interactiva**: Mapa con anomalías clasificadas por tipo
- **Exportación GeoJSON**: Descarga los resultados para uso en GIS

## Configuración

### 1. Área de Estudio

Edita `config.yaml` para ajustar el área de interés:

```yaml
aoi:
  name: velez-malaga
  bbox: [-4.25, 36.70, -4.00, 36.85]   # W,S,E,N
  utm_zone: 30
  max_downloads: 5        # número de tiles a descargar
```

### 2. API Key de Gemini

Para usar la detección con IA, necesitas configurar tu API key de Gemini:

1. Obtén tu API key en [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Configúrala como variable de entorno `GEMINI_API_KEY`

## Uso

### Interfaz Web (Streamlit)

Ejecuta la aplicación:

```bash
streamlit run app.py --server.port 5000
```

Luego sigue los pasos en la interfaz:

1. **Descargar tiles LAZ** - Descarga datos LiDAR del CNIG
2. **Generar DEM** - Crea el modelo digital del terreno (requiere PDAL)
3. **Calcular Hillshade y SVF** - Genera derivadas para análisis
4. **Detectar Anomalías** - Usa Gemini AI para identificar estructuras

**Nota importante:** Esta aplicación trabaja únicamente con datos LiDAR reales del PNOA. No se utilizan datos simulados o sintéticos.

### Línea de Comandos

También puedes ejecutar cada paso individualmente:

```bash
# 1. Descargar tiles LAZ
python src/download.py

# 2. Generar DEM (requiere PDAL instalado)
pdal pipeline pipelines/laz2dem.json

# 3. Calcular derivadas
python src/process.py

# 4. Detectar anomalías con IA
python src/detect.py
```

## Estructura del Proyecto

```
lidar-velez/
├── app.py                    # Aplicación Streamlit principal
├── config.yaml               # Configuración del área de estudio
├── data/                     # Datos procesados
│   ├── laz/                  # Archivos LAZ descargados
│   ├── dem_velez.tif         # DEM generado
│   └── deriv/                # Derivadas (hillshade, SVF)
├── outputs/                  # Resultados
│   └── anomalies.geojson     # Anomalías detectadas
├── pipelines/
│   └── laz2dem.json          # Pipeline PDAL para DEM
└── src/
    ├── download.py           # Descarga de tiles LAZ
    ├── process.py            # Cálculo de derivadas
    └── detect.py             # Detección con IA
```

## Tipos de Anomalías Detectadas

El sistema clasifica las anomalías en:

- **Muro**: Estructuras lineales elevadas
- **Túmulo**: Montículos circulares/ovales
- **Fossa**: Depresiones o zanjas
- **Camino**: Trazados lineales antiguos

Cada anomalía incluye:
- Coordenadas geográficas
- Tipo de estructura
- Puntuación de confianza (0-1)
- Justificación del análisis

## Requisitos del Sistema

- Python 3.11+
- GDAL (para hillshade)
- PDAL (requerido para procesamiento LAZ)
- Gemini API key (para detección con IA)

## Dependencias Python

Ver `pyproject.toml` o instalar manualmente:

```bash
pip install streamlit aiohttp aiofiles geopandas pyyaml rasterio scipy folium pillow google-genai
```

## Créditos

- **Datos LiDAR**: PNOA-LiDAR 3ª Cobertura - [Centro Nacional de Información Geográfica (CNIG)](https://centrodedescargas.cnig.es/)
- **IA**: Google Gemini
- **Metodología**: Análisis arqueológico con LiDAR

## Licencia

Este proyecto es una herramienta de demostración para análisis arqueológico con LiDAR.
Los datos PNOA-LiDAR están sujetos a las condiciones de uso del CNIG.
