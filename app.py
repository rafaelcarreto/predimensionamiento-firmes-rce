import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración de página (Para que ocupe todo el ancho y no quede espacio en blanco)
st.set_page_config(page_title="Diseño de Firmes 6.1-IC", layout="wide")

# 2. Diccionario de Firmes (Norma 6.1-IC para mezclas bituminosas)
# Esto es una simplificación de la norma para secciones flexibles/semi-rígidas
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

# (Tu código de carga de datos sigue igual)
@st.cache_data
def cargar_datos():
    return pd.read_csv("datos_carreteras.csv")

df = cargar_datos()

st.title("🛣️ Dimensionamiento de Firmes (Norma 6.1-IC)")

# --- DIVIDIMOS LA PANTALLA EN 2 COLUMNAS ---
col_controles, col_resultados = st.columns([1, 2]) # La derecha es el doble de ancha

with col_controles:
    st.subheader("1. Selección de Datos")
    provincia = st.selectbox("Provincia", sorted(df['provincia'].unique()))
    df_prov = df[df['provincia'] == provincia]
    
    carretera = st.selectbox("Carretera", sorted(df_prov['carretera'].unique()))
    df_carr = df_prov[df_prov['carretera'] == carretera]
    
    tramo = st.selectbox("Tramo", df_carr['tramo'])
    
    # Extraemos los datos del tramo
    datos_tramo = df_carr[df_carr['tramo'] == tramo].iloc[0]
    imd_base = datos_tramo['imd_total']
    pesados_base = datos_tramo['porcentaje_pesados']
    
    st.info(f"📊 **IMD Actual:** {int(imd_base)} veh/día\n\n🚚 **% Pesados:** {pesados_base}%")

    st.subheader("2. Parámetros de Diseño")
    tasa_crecimiento = st.number_input("Tasa de Crecimiento Anual (%)", value=2.0, step=0.5)
    horizonte = st.slider("Horizonte de Proyecto (Años)", 10, 30, 20)
    carriles = st.radio("Número de Carriles (por calzada)", [1, 2, 3], index=1)
    
    st.subheader("3. Capacidad Portante")
    explanada = st.selectbox("Categoría de la Explanada", ["E1", "E2", "E3"], index=1, help="Según Norma 6.1-IC")

# --- CÁLCULOS MATEMÁTICOS ---
# 1. IMD Pesados en el año inicial (mitad para cada sentido aprox, o total si es calzada única)
imdp_inicial = imd_base * (pesados_base / 100) / 2 

# 2. Factor de carriles (Norma 6.1-IC)
factor_carril = 1.0 if carriles == 1 else (0.5 if carriles == 2 else 0.4)
imdp_carril_diseno_inicial = imdp_inicial * factor_carril

# 3. Evolución del tráfico (Fórmula del interés compuesto)
# Calculamos el tráfico para el año intermedio del horizonte de proyecto según dicta la norma
factor_crecimiento = (1 + (tasa_crecimiento/100))**(horizonte/2)
imdp_proyecto = imdp_carril_diseno_inicial * factor_crecimiento

# Asignación de Categoría de Tráfico (Norma 6.1-IC)
if imdp_proyecto >= 4000:
    categoria_trafico = "T00"
elif imdp_proyecto >= 2000:
    categoria_trafico = "T0"
elif imdp_proyecto >= 800:
    categoria_trafico = "T1"
elif imdp_proyecto >= 200:
    categoria_trafico = "T2"
elif imdp_proyecto >= 50:
    categoria_trafico = "T3"
else:
    categoria_trafico = "T4"

with col_resultados:
    st.subheader("Resultados del Predimensionamiento")
    
    # Tarjetas visuales bonitas
    col1, col2, col3 = st.columns(3)
    col1.metric("IMDp Carril Diseño", f"{int(imdp_carril_diseno_inicial)} veh/día")
    col2.metric("IMDp Medio Proyecto", f"{int(imdp_proyecto)} veh/día")
    col3.metric("Categoría de Tráfico", categoria_trafico)
    
    # --- LA CAJA DE CRISTAL (Explicación) ---
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
        
    # --- GRÁFICO DE EVOLUCIÓN PARA RELLENAR ESPACIO ---
    st.markdown("### 📈 Evolución del Tráfico Pesado")
    años = list(range(0, horizonte + 1))
    trafico_anual = [imdp_carril_diseno_inicial * ((1 + (tasa_crecimiento/100))**a) for a in años]
    
    df_grafico = pd.DataFrame({"Año": años, "IMDp (Pesados/día)": trafico_anual})
    fig = px.line(df_grafico, x="Año", y="IMDp (Pesados/día)", markers=True, 
                  color_discrete_sequence=['#FF4B4B'])
    
    # Línea horizontal para marcar el límite de la categoría asignada
    if categoria_trafico == "T1": limite = 800
    elif categoria_trafico == "T2": limite = 200
    elif categoria_trafico == "T3": limite = 50
    else: limite = 2000
    fig.add_hline(y=limite, line_dash="dash", line_color="gray", annotation_text=f"Límite {categoria_trafico}")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- DISEÑO ESTRUCTURAL DEL FIRME ---
    st.markdown("### 🏗️ Sección Estructural Recomendada")
    st.info(f"Para un tráfico **{categoria_trafico}** y una explanada **{explanada}**, la sección tipo para mezclas bituminosas es:")
    
    # Buscamos la sección en nuestro diccionario
    try:
        seccion_recomendada = secciones_firme[categoria_trafico][explanada]
        st.success(seccion_recomendada)
    except KeyError:
        st.warning("La Norma 6.1-IC exige condiciones especiales (ej. estabilizaciones con cemento) para esta combinación extrema de tráfico y explanada. Se requiere estudio específico.")
