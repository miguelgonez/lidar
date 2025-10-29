# LiDAR Vélez-Málaga - Archaeological Anomaly Detection

## Overview

This project is a complete pipeline for detecting hidden archaeological structures using PNOA-LiDAR data (3rd coverage) in Vélez-Málaga, Spain. The system downloads LiDAR tiles, generates Digital Elevation Models (DEMs), performs terrain analysis using hillshade and Sky View Factor (SVF) calculations, and employs Gemini AI to identify archaeological anomalies. Results are visualized on an interactive map and can be exported as GeoJSON for GIS applications.

The application is built with a Streamlit web interface and uses a configuration-driven approach to define areas of interest and processing parameters.

## User Preferences

Preferred communication style: Simple, everyday language.

**Critical Requirement**: This application ONLY processes real PNOA-LiDAR data from CNIG. No simulated, synthetic, or demo data is permitted. All archaeological anomalies must be detected from actual LiDAR measurements.

## System Architecture

### Frontend Architecture

**Web Interface**: Streamlit-based application (`app.py`)
- Provides an interactive web UI for controlling the processing pipeline
- Displays configuration details from `config.yaml` (AOI name, bounding box, UTM zone, max downloads)
- Shows pipeline status for each processing step (LAZ download, DEM generation, hillshade/SVF calculation, anomaly detection)
- Integrates Folium for interactive map visualization with detected anomalies
- Uses a sidebar for pipeline controls and configuration display

**Rationale**: Streamlit was chosen for rapid prototyping and ease of use, allowing non-technical users to interact with the LiDAR processing pipeline without command-line knowledge.

### Backend Architecture

**Configuration Management**: YAML-based configuration (`config.yaml`)
- Defines area of interest (AOI) with bounding box coordinates, UTM zone, and GCS bucket settings
- Configurable parameters for tile downloads, LAZ version, and processing limits
- Centralized configuration allows easy adjustment of study areas without code changes

**Pipeline Components**:

1. **Data Download** (`src/download.py`)
   - Asynchronous HTTP client using `aiohttp` for concurrent LAZ tile downloads
   - Reads tile index from CNIG (Spanish National Geographic Institute) ZIP file
   - Uses GeoPandas for spatial filtering of tiles intersecting the AOI
   - Implements semaphore-based concurrency control to prevent overwhelming the server
   - **Rationale**: Async I/O maximizes download throughput while respecting server limits

2. **DEM Generation** (`pipelines/laz2dem.json`)
   - PDAL pipeline for processing LAZ point clouds into raster DEMs
   - Applies SMRF (Simple Morphological Filter) for ground point classification
   - Filters to retain only ground-classified points (Classification[2:2])
   - Uses IDW interpolation with compression (ZSTD) for efficient storage
   - **Rationale**: PDAL provides industry-standard point cloud processing with established algorithms for ground classification
   - **Important**: PDAL installation is required; no alternative methods or demo data are provided

3. **Terrain Analysis** (`src/process.py`)
   - Multi-directional hillshade generation using GDAL (8 azimuth angles: 45° increments)
   - Sky View Factor (SVF) calculation using maximum filter approximation
   - **Rationale**: Multiple hillshade directions reveal subtle features from different lighting angles; SVF highlights topographic openness useful for detecting buried structures

4. **AI Detection** (`src/detect.py`)
   - Uses Google Gemini AI (gemini-2.5-flash/pro series) for visual anomaly detection
   - Creates normalized preview images from GeoTIFFs for AI analysis
   - Outputs anomalies as GeoJSON with classifications
   - **Rationale**: AI vision models can identify subtle patterns in terrain data that traditional algorithms might miss

### Data Storage Solutions

**File System Structure**:
- `data/laz/`: Downloaded LAZ point cloud files
- `data/dem_velez.tif`: Generated Digital Elevation Model
- `data/deriv/`: Derived products (hillshade_*.tif, svf.tif)
- `outputs/`: Analysis results (anomalies.geojson)
- `pipelines/`: PDAL processing pipeline definitions

**Rationale**: Simple file-based storage is appropriate for this geospatial workflow where data is primarily raster/vector files. No database is needed as processing is batch-oriented rather than transactional.

### Authentication and Authorization

**API Authentication**: 
- Gemini AI requires `GEMINI_API_KEY` environment variable
- No user authentication system (single-user application)

**Rationale**: Environment variable approach is standard for API keys and keeps secrets out of code/config files.

## External Dependencies

### Third-Party Services

1. **CNIG (Centro de Descargas)**: Spanish National Geographic Institute
   - Purpose: Source of PNOA-LiDAR tile data
   - Access: Public HTTP downloads via tile index
   - URL Pattern: `https://centrodedescargas.cnig.es/...`

2. **Google Gemini AI** (google-genai SDK)
   - Purpose: Visual analysis of terrain derivatives for anomaly detection
   - Model: gemini-2.5-flash or gemini-2.5-pro
   - Requires: API key via `GEMINI_API_KEY` environment variable
   - Note: SDK recently migrated from `google-generativeai` to `google-genai`

3. **Google Cloud Storage** (optional)
   - Referenced in config but not actively used in provided code
   - Configured via `gcs_bucket` parameter for potential cloud storage integration

4. **Google Earth Engine** (optional)
   - Referenced in config (`gee_project`) but not actively used
   - Potential future integration for additional satellite/terrain data

### Core Python Libraries

- **aiohttp/aiofiles**: Async HTTP client and file I/O for concurrent downloads
- **geopandas**: Geospatial data manipulation (tile filtering, vector operations)
- **rasterio**: Raster I/O and manipulation (GeoTIFF reading/writing)
- **streamlit**: Web application framework for UI
- **folium**: Interactive map visualization
- **scipy**: Scientific computing (maximum filter for SVF calculation)
- **PyYAML**: Configuration file parsing
- **Pillow (PIL)**: Image processing for AI input preparation
- **numpy**: Numerical array operations

### External Tools

1. **PDAL (Point Data Abstraction Library)**
   - Purpose: LiDAR point cloud processing
   - Invoked via: JSON pipeline definitions
   - Required: System installation (not Python package)

2. **GDAL (Geospatial Data Abstraction Library)**
   - Purpose: Raster processing (hillshade generation via `gdaldem`)
   - Invoked via: subprocess calls
   - Required: System installation with `gdaldem` command-line tool

**Note**: The application requires PDAL and GDAL system installations. It processes only authentic PNOA-LiDAR data from CNIG. External service integrations (GCS, GEE) are configured but optional for the core workflow.