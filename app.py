import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Diseño de Firmes 6.1-IC", layout="wide")

# --- DICCIONARIO COMPLETO NORMA 6.1-IC (Catálogo BOE) ---
# Estructura: "Nomenclatura": {"desc": "Explicación técnica", "capas": {"Material": [Espesor cm, "Color Hexadecimal"]}}
norma_61_ic = {
    "T00": {
        "E3": {
            "Sección 0031 (Firme Flexible)": {"desc": "Mezcla bituminosa sobre zahorra artificial. Recomendado para facilitar el mantenimiento futuro por fresado.", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [20, '#595959'], "Subbase (ZA)": [25, '#C2B280']}},
            "Sección 0032 (Firme Semirrígido)": {"desc": "Mezcla bituminosa sobre gravacemento. Gran resistencia a la deformación bajo cargas extremas (evita roderas).", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [14, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}},
            "Sección 0033 (Firme Rígido)": {"desc": "Pavimento continuo de hormigón armado. Máxima durabilidad, requiere juntas de dilatación.", "capas": {"Losa Hormigón (HF)": [28, '#D3D3D3'], "Hormigón Magro (HM)": [15, '#A9A9A9']}}
        }
    },
    "T0": {
        "E3": {
            "Sección 031 (Firme Flexible)": {"desc": "Solución en asfalto de alto espesor sobre capa granular.", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [15, '#595959'], "Subbase (ZA)": [25, '#C2B280']}},
            "Sección 032 (Firme Semirrígido)": {"desc": "Base tratada con cemento para tráficos T0 propensos a fatiga.", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [10, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}},
            "Sección 033 (Firme Rígido)": {"desc": "Solución en hormigón de alta durabilidad.", "capas": {"Losa Hormigón (HF)": [25, '#D3D3D3'], "Hormigón Magro (HM)": [15, '#A9A9A9']}}
        },
        "E2": {
            "Sección 021 (Firme Flexible)": {"desc": "Opción admitida sobre explanada media con alto espesor asfáltico.", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [20, '#595959'], "Subbase (ZA)": [25, '#C2B280']}},
            "Sección 022 (Firme Semirrígido)": {"desc": "Opción semirrígida adaptada a explanada E2.", "capas": {"Rodadura (BBTM)": [3, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [14, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}}
        }
    },
    "T1": {
        "E3": {
            "Sección 131 (Firme Flexible)": {"desc": "Opción estándar en asfalto para tráfico T1.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Intermedia (AC)": [5, '#404040'], "Base (AC)": [10, '#595959'], "Subbase (ZA)": [25, '#C2B280']}},
            "Sección 132 (Firme Semirrígido)": {"desc": "Opción con base tratada con cemento para mayor rigidez.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}}
        },
        "E2": {
            "Sección 121 (Firme Flexible)": {"desc": "Opción flexible sobre explanada E2 (Muy frecuente).", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Intermedia (AC)": [7, '#404040'], "Base (AC)": [13, '#595959'], "Subbase (ZA)": [25, '#C2B280']}},
            "Sección 122 (Firme Semirrígido)": {"desc": "Opción semirrígida sobre explanada E2.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Intermedia (AC)": [5, '#404040'], "Base (AC)": [8, '#595959'], "Subbase (GC)": [25, '#8B7D6B']}}
        }
    },
    "T2": {
        "E3": {
            "Sección 231 (Firme Flexible)": {"desc": "Mezcla bituminosa sobre Zahorra Artificial.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (ZA)": [20, '#C2B280']}},
            "Sección 232 (Firme Semirrígido)": {"desc": "Mezcla bituminosa sobre Suelocemento.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [7, '#595959'], "Subbase (SC)": [20, '#A09070']}}
        },
        "E2": {
            "Sección 221 (Firme Flexible)": {"desc": "Mezcla bituminosa sobre Zahorra Artificial.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [15, '#595959'], "Subbase (ZA)": [20, '#C2B280']}},
            "Sección 222 (Firme Semirrígido)": {"desc": "Mezcla bituminosa sobre Suelocemento.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (SC)": [20, '#A09070']}}
        }
    },
    "T3": {
        "E3": {
            "Sección 331 (Firme Flexible)": {"desc": "Firme económico para baja intensidad de pesados.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [7, '#595959'], "Subbase (ZA)": [20, '#C2B280']}}
        },
        "E2": {
            "Sección 321 (Firme Flexible)": {"desc": "Mezcla bituminosa sobre ZA.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [10, '#595959'], "Subbase (ZA)": [20, '#C2B280']}}
        },
        "E1": {
            "Sección 311 (Firme Flexible)": {"desc": "Requiere mayor espesor asfáltico debido a la baja calidad de la explanada (E1).", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Base (AC)": [15, '#595959'], "Subbase (ZA)": [25, '#C2B280']}}
        }
    },
    "T4": {
        "E3": {
            "Sección 431 (Firme Flexible)": {"desc": "Capa asfáltica mínima por normativa sobre buena explanada.", "capas": {"Rodadura (AC)": [5, '#2C2C2C'], "Subbase (ZA)": [20, '#C2B280']}}
        },
        "E2": {
            "Sección 421 (Firme Flexible)": {"desc": "Capa asfáltica media sobre ZA.", "capas": {"Rodadura (AC)": [8, '#2C2C2C'], "Subbase (ZA)": [20, '#C2B280']}}
        },
        "E1": {
            "Sección 411 (Firme Flexible)": {"desc": "Paquete robusto exigido para compensar la explanada deficiente (E1).", "capas": {"Rodadura (AC)": [12, '#2C2C2C'], "Subbase (ZA)": [25, '#C2B280']}}
        }
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

# AHORA COLOCAMOS LAS DOS COLUMNAS MÁS EQUILIBRADAS
col_controles, col_resultados = st.columns([1.1, 1.5]) 

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
    carriles = st.radio("Número de Carriles (por calzada)", [1, 2, 3], index=1, horizontal=True)
    
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

    # MOVEMOS LA GRÁFICA DE EVOLUCIÓN AQUÍ PARA LLENAR EL HUECO BLANCO
    st.markdown("---")
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
        
    st.markdown("### 🏗️ Catálogo de Secciones (Norma 6.1-IC)")
    
    try:
        opciones_firme = norma_61_ic[categoria_trafico][explanada]
        nombres_opciones = list(opciones_firme.keys())
        
        st.write("Selecciona la alternativa constructiva deseada para ver su sección:")
        opcion_elegida = st.radio("Alternativas legales:", nombres_opciones, horizontal=True, label_visibility="collapsed")
        
        datos_opcion = opciones_firme[opcion_elegida]
        st.info(f"💡 **Justificación Técnica:** {datos_opcion['desc']}")
        
        # Generador del gráfico de capas
        fig_seccion = go.Figure()
        capas = datos_opcion['capas']
        
        # Dibujamos al revés para que la base quede abajo y la rodadura arriba
        for capa, datos in reversed(list(capas.items())):
            espesor = datos[0]
            color = datos[1]
            
            fig_seccion.add_trace(go.Bar(
                x=['Sección Transversal'], 
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
            height=300, # Reducimos altura para compactar el diseño
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )
        
        col_t, col_g = st.columns([1, 1.5])
        with col_t:
            df_capas = pd.DataFrame([{"Capa": k, "Espesor (cm)": v[0]} for k, v in capas.items()])
            st.table(df_capas)
        with col_g:
            st.plotly_chart(fig_seccion, use_container_width=True, config={'displayModeBar': False})
            
    except KeyError:
        st.error("⚠️ La Norma 6.1-IC prohíbe esta combinación (Ej: Explanada E1 para tráficos pesados T00/T0). Requiere cimiento mejorado o estabilización de suelos.")

    # --- MAPA INTERACTIVO (Folium Claro) ---
    st.markdown("### 🌍 Visor Cartográfico del Tramo")
    
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

    if len(lats) > 0:
        centro = [sum(lats)/len(lats), sum(lons)/len(lons)]
        zoom_nivel = 10
    else:
        centro = [39.5, -3.0] 
        zoom_nivel = 6

    m = folium.Map(location=centro, zoom_start=zoom_nivel, tiles="CartoDB positron")

    if len(tramos_filtrados) > 0:
        capa_geojson = {"type": "FeatureCollection", "features": tramos_filtrados}
        folium.GeoJson(
            capa_geojson,
            style_function=lambda x: {'color': '#FF4B4B', 'weight': 6, 'opacity': 0.9}
        ).add_to(m)

    st_folium(m, width="100%", height=350, returned_objects=[])
