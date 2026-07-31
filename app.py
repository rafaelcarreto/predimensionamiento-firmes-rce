import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Diseño de Firmes 6.1-IC", layout="wide")

# --- DICCIONARIO COMPLETO NORMA 6.1-IC (Secciones Flexibles/Semirrígidas) ---
# Estructura: "Tipo de material": [Espesor en cm, "Color Hexadecimal para el gráfico"]
# MB = Mezcla Bituminosa, GC = Gravacemento, ZA = Zahorra Artificial
norma_61_ic = {
    "T00": {
        "E3": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [15, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}
    },
    "T0": {
        "E2": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [15, '#595959'], "Subbase (ZA)": [25, '#C2B280']},
        "E3": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [12, '#595959'], "Subbase (GC)": [20, '#8B7D6B']}
    },
    "T1": {
        "E2": {"Rodadura (AC)": [5, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [12, '#595959'], "Subbase (ZA)": [25, '#C2B280']},
        "E3": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [14, '#595959'], "Subbase (ZA)": [25, '#C2B280']}
    },
    "T2": {
        "E2": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [12, '#595959'], "Subbase (ZA)": [20, '#C2B280']},
        "E3": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (ZA)": [20, '#C2B280']}
    },
    "T3": {
        "E1": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [12, '#595959'], "Subbase (ZA)": [25, '#C2B280']},
        "E2": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (ZA)": [20, '#C2B280']},
        "E3": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [8, '#595959'], "Subbase (ZA)": [20, '#C2B280']}
    },
    "T4": {
        "E1": {"Rodadura (AC)": [5, '#2C2C2C'], "Subbase (ZA)": [25, '#C2B280']},
        "E2": {"Rodadura (AC)": [5, '#2C2C2C'], "Subbase (ZA)": [20, '#C2B280']},
        "E3": {"Rodadura (AC)": [5, '#2C2C2C'], "Subbase (ZA)": [20, '#C2B280']}
    }
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

# --- CÁLCULOS MATEMÁTICOS ---
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
        
    # --- REPRESENTACIÓN VISUAL DE LA SECCIÓN (NUEVO) ---
    st.markdown("### 🏗️ Sección Estructural Recomendada")
    
    try:
        paquete_firme = norma_61_ic[categoria_trafico][explanada]
        
        # Generar gráfico de capas con Plotly
        fig_seccion = go.Figure()
        
        # Recorremos el diccionario al revés para dibujar desde la subbase (abajo) hacia la rodadura (arriba)
        for capa, datos in reversed(list(paquete_firme.items())):
            espesor = datos[0]
            color = datos[1]
            
            fig_seccion.add_trace(go.Bar(
                x=['Sección del Firme'], 
                y=[espesor],
                name=capa,
                marker_color=color,
                text=f"<b>{capa}</b><br>{espesor} cm",
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='white', size=14),
                hoverinfo='none'
            ))

        fig_seccion.update_layout(
            barmode='stack',
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )
        
        # Mostramos la tabla resumen y el gráfico
        col_texto, col_grafico = st.columns([1, 1.5])
        with col_texto:
            st.info(f"**Tráfico:** {categoria_trafico} | **Explanada:** {explanada}")
            df_capas = pd.DataFrame([{"Capa": k, "Espesor (cm)": v[0]} for k, v in paquete_firme.items()])
            st.table(df_capas)
        with col_grafico:
            st.plotly_chart(fig_seccion, use_container_width=True, config={'displayModeBar': False})
            
    except KeyError:
        st.warning("⚠️ La Norma 6.1-IC exige condiciones especiales para esta combinación extrema (Ej. no se admite E1 para tráficos altos). Se requiere estudio de estabilización de suelos.")

    # --- MAPA INTERACTIVO CON FOLIUM (FONDO CLARO) ---
    st.markdown("### 🌍 Visor Cartográfico")
    vista_mapa = st.radio("Selecciona la vista del mapa:", ["📍 Vista Cercana", "🗺️ Mapa Completo"], horizontal=True)

    tramos_filtrados = []
    for feature in geojson_mapa['features']:
        prop = feature['properties']
        if prop.get('provincia') == provincia and prop.get('carretera') == carretera:
            tramos_filtrados.append(feature)

    lats, lons = [], []
    for feat in tramos_filtrados:
        coords = feat['geometry']['coordinates']
        if feat['geometry']['type'] == 'LineString':
            for pt in coords:
                lons.append(pt[0]); lats.append(pt[1])
        elif feat['geometry']['type'] == 'MultiLineString':
            for line in coords:
                for pt in line:
                    lons.append(pt[0]); lats.append(pt[1])

    if vista_mapa == "📍 Vista Cercana" and len(lats) > 0:
        centro = [sum(lats)/len(lats), sum(lons)/len(lons)]
        zoom_nivel = 11
    else:
        centro = [39.5, -3.0] 
        zoom_nivel = 6

    # Hemos cambiado el tiles a "CartoDB positron" para que se vea claro y útil
    m = folium.Map(location=centro, zoom_start=zoom_nivel, tiles="CartoDB positron")

    if len(tramos_filtrados) > 0:
        capa_geojson = {"type": "FeatureCollection", "features": tramos_filtrados}
        folium.GeoJson(
            capa_geojson,
            style_function=lambda x: {'color': '#FF4B4B', 'weight': 6, 'opacity': 0.9}
        ).add_to(m)
    else:
        st.warning("⚠️ No se ha encontrado la geometría cartográfica de esta carretera en el archivo.")

    st_folium(m, width="100%", height=400, returned_objects=[])

    # --- GRÁFICO DE EVOLUCIÓN ---
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
