import streamlit as st
import folium
from folium import plugins
import yaml
import os
import json
import subprocess
from pathlib import Path

st.set_page_config(
    page_title="LiDAR Vélez-Málaga - Detección de Anomalías Arqueológicas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

st.title("🗺️ LiDAR Vélez-Málaga")
st.subheader("Detección de Anomalías Arqueológicas con IA")

# Sidebar for pipeline controls
with st.sidebar:
    st.header("⚙️ Pipeline de Procesamiento")
    
    st.markdown("### Configuración del Área")
    st.write(f"**Nombre:** {config['aoi']['name']}")
    bbox = config['aoi']['bbox']
    st.write(f"**Bounding Box:** W:{bbox[0]}, S:{bbox[1]}, E:{bbox[2]}, N:{bbox[3]}")
    st.write(f"**Zona UTM:** {config['aoi']['utm_zone']}")
    st.write(f"**Máx. descargas:** {config['aoi']['max_downloads']} tiles")
    
    st.markdown("---")
    st.markdown("### 🔄 Pasos del Pipeline")
    
    # Check status of each step
    has_laz = len(list(Path("data/laz").glob("*.laz"))) > 0 if Path("data/laz").exists() else False
    has_dem = Path("data/dem_velez.tif").exists()
    has_hillshade = Path("data/deriv/hill_45.tif").exists()
    has_svf = Path("data/deriv/svf.tif").exists()
    has_anomalies = Path("outputs/anomalies.geojson").exists()
    
    # Step 1: Download LAZ
    st.markdown("#### 1️⃣ Descargar LAZ")
    if has_laz:
        num_laz = len(list(Path("data/laz").glob("*.laz")))
        st.success(f"✓ {num_laz} archivos LAZ descargados")
    else:
        st.info("⏳ Archivos LAZ no descargados")
    
    if st.button("📥 Descargar tiles LAZ", disabled=has_laz, use_container_width=True):
        with st.spinner("Descargando tiles LAZ desde CNIG..."):
            try:
                result = subprocess.run(
                    ["python", "src/download.py"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    st.success("✅ Descarga completada")
                    if result.stdout:
                        with st.expander("Ver detalles"):
                            st.code(result.stdout)
                    st.rerun()
                else:
                    st.error("❌ Error en la descarga")
                    if result.stderr:
                        st.code(result.stderr)
                    if result.stdout:
                        st.code(result.stdout)
            except subprocess.TimeoutExpired:
                st.error("⏱️ Tiempo de espera agotado (10 min)")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 2: Generate DEM
    st.markdown("#### 2️⃣ Generar DEM")
    if has_dem:
        st.success("✓ DEM generado")
    else:
        st.info("⏳ DEM no generado")
    
    if st.button("🏔️ Generar DEM (requiere PDAL)", disabled=not has_laz or has_dem, use_container_width=True):
        with st.spinner("Generando DEM desde archivos LAZ... (puede tardar varios minutos)"):
            try:
                # Try PDAL pipeline
                result = subprocess.run(
                    ["pdal", "pipeline", "pipelines/laz2dem.json"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result.returncode == 0:
                    st.success("✅ DEM generado con PDAL")
                    if result.stdout:
                        with st.expander("Ver detalles"):
                            st.code(result.stdout)
                    st.rerun()
                else:
                    st.error("❌ Error ejecutando PDAL")
                    if result.stderr:
                        st.code(result.stderr)
                    if result.stdout:
                        st.code(result.stdout)
            except FileNotFoundError:
                st.error("⚠️ PDAL no está instalado en este entorno")
                st.info("💡 PDAL es necesario para procesar archivos LAZ. Instala PDAL para continuar.")
            except subprocess.TimeoutExpired:
                st.error("⏱️ Tiempo de espera agotado (10 min)")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 3: Process derivatives
    st.markdown("#### 3️⃣ Calcular Derivadas")
    if has_hillshade and has_svf:
        st.success("✓ Hillshade y SVF calculados")
    else:
        st.info("⏳ Derivadas no calculadas")
    
    if st.button("📐 Calcular Hillshade y SVF", disabled=not has_dem or (has_hillshade and has_svf), use_container_width=True):
        with st.spinner("Calculando hillshade y Sky View Factor..."):
            try:
                result = subprocess.run(
                    ["python", "src/process.py"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    st.success("✅ Derivadas calculadas")
                    if result.stdout:
                        with st.expander("Ver detalles"):
                            st.code(result.stdout)
                    st.rerun()
                else:
                    st.error("❌ Error calculando derivadas")
                    if result.stderr:
                        st.code(result.stderr)
                    if result.stdout:
                        st.code(result.stdout)
            except subprocess.TimeoutExpired:
                st.error("⏱️ Tiempo de espera agotado (5 min)")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Step 4: AI Detection
    st.markdown("#### 4️⃣ Detección con IA")
    if has_anomalies:
        st.success("✓ Anomalías detectadas")
    else:
        st.info("⏳ Detección no realizada")
    
    if st.button("🤖 Detectar Anomalías (Gemini)", disabled=not has_dem or has_anomalies, use_container_width=True):
        if not os.environ.get("GEMINI_API_KEY"):
            st.error("⚠️ Se requiere GEMINI_API_KEY")
            st.info("Configura tu API key de Gemini para usar esta función")
        else:
            with st.spinner("Analizando terreno con Gemini AI... (puede tardar 30-60 segundos)"):
                try:
                    result = subprocess.run(
                        ["python", "src/detect.py"],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        st.success("✅ Anomalías detectadas por IA")
                        if result.stdout:
                            with st.expander("Ver detalles"):
                                st.code(result.stdout)
                        st.rerun()
                    else:
                        st.error("❌ Error en detección con IA")
                        if result.stderr:
                            st.code(result.stderr)
                        if result.stdout:
                            st.code(result.stdout)
                except subprocess.TimeoutExpired:
                    st.error("⏱️ Tiempo de espera agotado (2 min)")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Reset button
    if st.button("🔄 Reiniciar Pipeline", use_container_width=True):
        if st.checkbox("Confirmar reinicio (eliminará datos procesados)"):
            import shutil
            for path in ["data/laz", "data/deriv", "outputs"]:
                if Path(path).exists():
                    shutil.rmtree(path)
            Path("data/dem_velez.tif").unlink(missing_ok=True)
            st.success("Pipeline reiniciado")
            st.rerun()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🗺️ Mapa de Anomalías")
    
    # Create base map
    center_lat = (bbox[1] + bbox[3]) / 2
    center_lon = (bbox[0] + bbox[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    # Add bounding box rectangle
    folium.Rectangle(
        bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
        color="blue",
        fill=False,
        weight=2,
        popup="Área de Estudio"
    ).add_to(m)
    
    # Load and display anomalies if available
    if has_anomalies:
        try:
            with open("outputs/anomalies.geojson", "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
            
            # Add markers for each anomaly
            for feature in geojson_data.get("features", []):
                coords = feature["geometry"]["coordinates"]
                props = feature["properties"]
                
                # Color coding by type
                color_map = {
                    "muro": "red",
                    "túmulo": "orange",
                    "fossa": "purple",
                    "camino": "green"
                }
                color = color_map.get(props.get("tipo", ""), "blue")
                
                # Create popup content
                popup_html = f"""
                <b>Tipo:</b> {props.get('tipo', 'N/A')}<br>
                <b>Confianza:</b> {props.get('score', 0):.2f}<br>
                <b>Justificación:</b> {props.get('justificacion', 'N/A')}
                """
                
                folium.CircleMarker(
                    location=[coords[1], coords[0]],
                    radius=8,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
        except Exception as e:
            st.error(f"Error cargando GeoJSON: {e}")
    
    # Display map
    st.components.v1.html(m._repr_html_(), height=600)

with col2:
    st.markdown("### 📊 Resultados")
    
    if has_anomalies:
        try:
            with open("outputs/anomalies.geojson", "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
            
            features = geojson_data.get("features", [])
            st.metric("Anomalías Detectadas", len(features))
            
            # Count by type
            types = {}
            for feature in features:
                tipo = feature["properties"].get("tipo", "desconocido")
                types[tipo] = types.get(tipo, 0) + 1
            
            st.markdown("#### Por Tipo:")
            for tipo, count in types.items():
                st.write(f"**{tipo.capitalize()}:** {count}")
            
            st.markdown("---")
            
            # List all anomalies
            st.markdown("#### Detalles:")
            for i, feature in enumerate(features, 1):
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                
                with st.expander(f"{i}. {props.get('tipo', 'N/A').capitalize()} (score: {props.get('score', 0):.2f})"):
                    st.write(f"**Coordenadas:** {coords[1]:.6f}, {coords[0]:.6f}")
                    st.write(f"**Justificación:** {props.get('justificacion', 'N/A')}")
            
            st.markdown("---")
            
            # Download button
            geojson_str = json.dumps(geojson_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📥 Descargar GeoJSON",
                data=geojson_str,
                file_name="velez_anomalies.geojson",
                mime="application/json",
                use_container_width=True
            )
        
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("No hay anomalías detectadas todavía. Completa el pipeline para detectarlas.")
        
        st.markdown("---")
        st.markdown("### ℹ️ Acerca de")
        st.write("""
        Esta aplicación utiliza datos LiDAR del PNOA (Plan Nacional de Ortofotografía Aérea) 
        para detectar posibles estructuras arqueológicas ocultas en Vélez-Málaga.
        
        **Técnicas utilizadas:**
        - Modelo Digital del Terreno (DEM)
        - Hillshade multi-direccional
        - Sky View Factor (SVF)
        - Análisis con IA (Gemini)
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>LiDAR Vélez-Málaga | "
    "Datos: PNOA-LiDAR 3ª Cobertura (CNIG) | IA: Google Gemini</div>",
    unsafe_allow_html=True
)
