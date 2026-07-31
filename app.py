import streamlit as st
import pandas as pd
import plotly.express as px
import json
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Diseño de Firmes 6.1-IC", layout="wide")

# --- DICCIONARIO DE FIRMES ---
secciones_firme = {
    "T00": {"E3": "Rodadura: 3cm (BBTM) | Intermedia: 8cm (AC) | Base: 14cm (AC) | Subbase: 25cm (Zahorra)"},
    "T0":  {"E2": "Rodadura: 3cm (BBTM) | Intermedia: 7cm (AC) | Base: 15cm (AC) | Subbase: 25cm (Zahorra)",
            "E3": "Rodadura: 3cm (BBTM) | Intermedia: 7cm (AC) | Base: 12cm (AC) | Subbase: 25cm (Zahorra)"},
    "T1":  {"E2": "Rodadura: 5cm (AC) | Intermedia: 7cm (AC) | Base: 12cm (AC) | Subbase: 25cm (Zahorra)",
            "E3": "Rodadura: 5cm (AC) | Base: 14cm (AC) | Subbase: 25cm (Zahorra)"},
    "T2":  {"E2": "Rodadura: 5cm (AC) | Base: 12cm (AC) | Subbase: 20cm (Zahorra)",
            "E3": "Rodadura: 5cm (AC) | Base: 10cm (AC) | Subbase: 20cm (Zahorra)"},
    "T3":  {"E1": "Rodadura: 5cm (AC) | Base: 12cm (AC) | Subbase: 25cm (Zahorra)",
            "E2": "Rodadura: 5cm (AC) | Base: 10cm (AC) | Subbase: 20cm (Zahorra)",
            "E3": "Rodadura: 5cm (AC) | Base: 8cm (AC) | Subbase: 20cm (Zahorra)"},
    "T4":  {"E1": "Rodadura: 5cm (AC) | Subbase: 25cm (Zahorra)",
            "E2": "Rodadura: 5cm (AC) | Subbase: 20cm (Zahorra)",
            "E3": "Rodadura: 5cm (AC) | Subbase: 20cm (Zahorra)"}
}

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos_csv():
    return pd.read_csv("datos_carreteras.csv")

@st.cache_data
def cargar_mapa_geojson():
    with open('mapa_carreteras_ligero.geojson', 'r', encoding='utf-8') as f:
        return json.load(f)

df = cargar_datos_csv()
geojson_mapa = cargar_mapa_geojson()

st.title("🛣️ Dimensionamiento de Firmes (Norma 6.1-IC)")

col_controles, col_resultados = st.columns([1, 2]) 

with col_controles:
    st.subheader("1. Selección de Datos")
    provincia = st.selectbox("Provincia", sorted(df['provincia'].unique()))
    df_prov = df[df['provincia'] == provincia]
    
    carretera = st.selectbox("Carretera", sorted(df_prov['carretera'].unique()))
    df_carr = df_prov[df_prov['carretera'] == carretera]
    
    tramo = st.selectbox("Tramo", df_carr['tramo'])
    
    datos_tramo = df_carr[df_carr['tramo'] == tramo].iloc[0]
    imd_base = datos_tramo['imd_total']
    pesados_base = datos_tramo['porcentaje_pesados']
    
    st.info(f"📊 **IMD Actual:** {int(imd_base)} veh/día\n\n🚚 **% Pesados:** {pesados_base}%")

    st.subheader("2. Parámetros de Diseño")
    tasa_crecimiento = st.number_input("Tasa de Crecimiento Anual (%)", value=2.0, step=0.5)
    horizonte = st.slider("Horizonte de Proyecto (Años)", 10, 30, 20)
    carriles = st.radio("Número de Carriles (por calzada)", [1, 2, 3], index=1)
    
    st.subheader("3. Capacidad Portante")
    explanada = st.selectbox("Categoría de la Explanada", ["E1", "E2", "E3"], index=1)

# --- CÁLCULOS ---
imdp_inicial = imd_base * (pesados_base / 100) / 2 
factor_carril = 1.0 if carriles == 1 else (0.5 if carriles == 2 else 0.4)
imdp_carril_diseno_inicial = imdp_inicial * factor_carril
factor_crecimiento = (1 + (tasa_crecimiento/100))**(horizonte/2)
imdp_proyecto = imdp_carril_diseno_inicial * factor_crecimiento

if imdp_proyecto >= 4000: categoria_trafico = "T00"
elif imdp_proyecto >= 2000: categoria_trafico = "T0"
elif imdp_proyecto >= 800: categoria_trafico = "T1"
elif imdp_proyecto >= 200: categoria_trafico = "T2"
elif imdp_proyecto >= 50: categoria_trafico = "T3"
else: categoria_trafico = "T4"

with col_resultados:
    st.subheader("Resultados del Predimensionamiento")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("IMDp Carril Diseño", f"{int(imdp_carril_diseno_inicial)} veh/día")
    col2.metric("IMDp Medio Proyecto", f"{int(imdp_proyecto)} veh/día")
    col3.metric("Categoría de Tráfico", categoria_trafico)
    
    with st.expander("🔍 Ver desglose de cálculo y normativa"):
        st.markdown(f"""
        **Fórmula aplicada (Norma 6.1-IC):**
        * $IMD_p$ inicial por sentido = IMD total $\\times$ % pesados / 2
        * Coeficiente de carril para {carriles} carriles = {factor_carril}
        * $IMD_p$ carril diseño = {int(imdp_carril_diseno_inicial)} pesados/día
        
        **Cálculo a futuro:**
        Se proyecta a la mitad de la vida útil ({horizonte/2} años) con un crecimiento del {tasa_crecimiento}%.
        * $IMD_p$ proyecto = {int(imdp_carril_diseno_inicial)} $\\times (1 + {tasa_crecimiento/100})^{{{horizonte/2}}}$ = **{int(imdp_proyecto)} pesados/día**
        """)
        
    st.markdown("### 🏗️ Sección Estructural Recomendada")
    try:
        st.success(secciones_firme[categoria_trafico][explanada])
    except KeyError:
        st.warning("La Norma 6.1-IC exige condiciones especiales para esta combinación extrema. Se requiere estudio específico.")

    # --- MAPA INTERACTIVO CON FOLIUM ---
    st.markdown("### 🌍 Visor Cartográfico")
    vista_mapa = st.radio("Selecciona la vista del mapa:", ["📍 Vista Cercana", "🗺️ Mapa Completo"], horizontal=True)

    # 1. Filtrar el GeoJSON para sacar solo la carretera seleccionada
    tramos_filtrados = []
    for feature in geojson_mapa['features']:
        prop = feature['properties']
        match_prov = prop.get('provincia') == provincia
        match_carr = prop.get('carretera') == carretera
        # Si el shapefile tuviera el campo 'tramo', lo usaría. Si no, dibuja toda la vía en la provincia.
        match_tramo = prop.get('tramo') == tramo if 'tramo' in prop else True

        if match_prov and match_carr and match_tramo:
            tramos_filtrados.append(feature)

    # 2. Calcular el centro exacto de la carretera para la cámara
    lats, lons = [], []
    for feat in tramos_filtrados:
        coords = feat['geometry']['coordinates']
        geom_type = feat['geometry']['type']
        
        if geom_type == 'LineString':
            for pt in coords:
                lons.append(pt[0])
                lats.append(pt[1])
        elif geom_type == 'MultiLineString':
            for line in coords:
                for pt in line:
                    lons.append(pt[0])
                    lats.append(pt[1])

    # 3. Ajustar el zoom según el botón seleccionado
    if vista_mapa == "📍 Vista Cercana" and len(lats) > 0:
        centro = [sum(lats)/len(lats), sum(lons)/len(lons)]
        zoom_nivel = 11
    else:
        centro = [39.5, -3.0] # Centro geográfico de la Península
        zoom_nivel = 6

    # 4. Dibujar el mapa en tono oscuro estilo ingeniería
    m = folium.Map(location=centro, zoom_start=zoom_nivel, tiles="CartoDB dark_matter")

    if len(tramos_filtrados) > 0:
        capa_geojson = {"type": "FeatureCollection", "features": tramos_filtrados}
        folium.GeoJson(
            capa_geojson,
            style_function=lambda x: {'color': '#FF4B4B', 'weight': 6, 'opacity': 0.9}
        ).add_to(m)
    else:
        st.warning("⚠️ No se ha encontrado la geometría cartográfica de esta carretera en el archivo.")

    # 5. Renderizar el mapa en Streamlit
    st_folium(m, width="100%", height=400, returned_objects=[])

    # --- GRÁFICO DE EVOLUCIÓN AL FINAL ---
    st.markdown("### 📈 Evolución del Tráfico Pesado")
    años = list(range(0, horizonte + 1))
    trafico_anual = [imdp_carril_diseno_inicial * ((1 + (tasa_crecimiento/100))**a) for a in años]
    
    df_grafico = pd.DataFrame({"Año": años, "IMDp (Pesados/día)": trafico_anual})
    fig = px.line(df_grafico, x="Año", y="IMDp (Pesados/día)", markers=True, color_discrete_sequence=['#FF4B4B'])
    
    if categoria_trafico == "T1": limite = 800
    elif categoria_trafico == "T2": limite = 200
    elif categoria_trafico == "T3": limite = 50
    else: limite = 2000
    fig.add_hline(y=limite, line_dash="dash", line_color="gray", annotation_text=f"Límite {categoria_trafico}")
    
    st.plotly_chart(fig, use_container_width=True)
