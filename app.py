import pandas as pd
import streamlit as st

# 1. Configuración de la interfaz
st.set_page_config(page_title="Cálculo de Firmes - MITMA", layout="wide")
st.title("🛣️ Pre-dimensionamiento de Firmes (Norma 6.1 IC)")
st.markdown("Herramienta interactiva para calcular la **Categoría de Tráfico Pesado** cruzando Open Data del MITMA con la normativa técnica.")

# 2. Carga de los datos en la nube
@st.cache_data
def cargar_datos():
    # Lee tu archivo limpio directamente desde GitHub
    return pd.read_csv('datos_carreteras.csv', encoding='utf-8')

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ Archivo 'datos_carreteras.csv' no encontrado.")
    st.stop()

# 3. Panel Lateral - Filtros de Ubicación
st.sidebar.header("1. Seleccionar Tramo")
provincia_seleccionada = st.sidebar.selectbox("Provincia", sorted(df['provincia'].unique()))
df_prov = df[df['provincia'] == provincia_seleccionada]

carretera_seleccionada = st.sidebar.selectbox("Vía (Autovía / Nacional)", sorted(df_prov['carretera'].unique()))
df_carr = df_prov[df_prov['carretera'] == carretera_seleccionada]

tramo_seleccionado = st.sidebar.selectbox("Tramo (Punto Kilométrico)", df_carr['tramo'])
datos_tramo = df_carr[df_carr['tramo'] == tramo_seleccionado].iloc[0]

# 4. Panel Lateral - Parámetros de la Vía
st.sidebar.markdown("---")
st.sidebar.header("2. Parámetros de Diseño")
crecimiento = st.sidebar.slider("Tasa de crecimiento anual (%)", 0.0, 5.0, 2.0, step=0.1)
vida_util = st.sidebar.selectbox("Horizonte de Proyecto (años)", [10, 15, 20, 30], index=2)
carriles = st.sidebar.number_input("Carriles por sentido", min_value=1, max_value=4, value=2)

# 5. Motor Matemático (Fórmulas 6.1 IC)
imd_sentido = datos_tramo['imd_total'] * 0.5
imd_pesados_sentido = datos_tramo['imd_pesado'] * 0.5

# Factor de distribución de pesados por carril derecho
f_carril = 1.0 if carriles <= 2 else 0.85

imdp_actual = imd_pesados_sentido * f_carril
imdp_proyecto = imdp_actual * ((1 + (crecimiento / 100)) ** vida_util)

# Asignación de Categoría T
if imdp_proyecto >= 4000:
    categoria = "T00"
elif imdp_proyecto >= 2000:
    categoria = "T0"
elif imdp_proyecto >= 800:
    categoria = "T1"
elif imdp_proyecto >= 200:
    categoria = "T2"
elif imdp_proyecto >= 50:
    categoria = "T3"
else:
    categoria = "T4"

# 6. Visualización de Resultados
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos de Aforo (MITMA 2024)")
    st.write(f"**Ubicación:** {datos_tramo['provincia']}")
    st.write(f"**Sección:** {datos_tramo['tramo']}")
    st.metric("IMD Total", f"{int(datos_tramo['imd_total']):,} veh/día".replace(",", "."))
    st.metric("% Vehículos Pesados", f"{datos_tramo['porcentaje_pesados']} %")

with col2:
    st.subheader("Análisis Normativa 6.1 IC")
    st.metric("IMDp (Año base)", f"{int(imdp_actual)} pesados/carril")
    st.metric(f"IMDp (Proyectado a {vida_util} años)", f"{int(imdp_proyecto)} pesados/carril")
    
    st.markdown(f"### Categoría Asignada: **{categoria}**")
    if categoria in ["T00", "T0", "T1"]:
        st.warning("⚠️ **Tráfico pesado elevado:** Se exige sección estructural de alta capacidad (mezclas bituminosas de alto módulo u hormigón).")
    else:
        st.success("✅ **Tráfico moderado/ligero:** Sección estructural estándar permitida.")
