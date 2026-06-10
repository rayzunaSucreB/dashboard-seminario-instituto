import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Dashboard S&I Bolivia", layout="wide")
st.title("📊 Dashboard Seminario & Instituto - Bolivia 2026")
st.markdown("**Actualización en tiempo real**")

# Carga de archivos
col1, col2 = st.columns(2)
with col1:
    insc_file = st.file_uploader("📌 Subir Inscritos.xlsx (2026)", type=["xlsx"])
with col2:
    pot_file = st.file_uploader("📌 Subir Potenciales.xlsx", type=["xlsx"])

@st.cache_data
def load_df(file):
    return pd.read_excel(file) if file is not None else None

insc = load_df(insc_file)
pot = load_df(pot_file)

if insc is None:
    st.warning("Sube al menos Inscritos.xlsx")
    st.stop()

# Preparación de datos
insc['Age'] = pd.to_numeric(insc.get('Age', None), errors='coerce')
insc['Confirmation Date'] = pd.to_datetime(insc.get('Confirmation Date', None), errors='coerce')
insc['Last Attended'] = pd.to_datetime(insc.get('Last Attended Week Date', None), errors='coerce')

stake_col = next((col for col in ['Stake - District', 'Stake'] if col in insc.columns), None)
ward_col = next((col for col in ['Ward - Branch', 'Ward'] if col in insc.columns), None)

def get_grupo(row):
    age = row.get('Age')
    if pd.isna(age): return "Sin edad"
    if age <= 17:
        if age <= 14: return "S1"
        elif age == 15: return "S2"
        elif age == 16: return "S3"
        else: return "S4"
    else:
        return "Instituto"

insc['Grupo'] = insc.apply(get_grupo, axis=1)

# Filtros en sidebar con cascada
st.sidebar.header("🔎 Filtros")
if stake_col:
    all_stakes = sorted(insc[stake_col].dropna().unique())
    selected_stakes = st.sidebar.multiselect("Estaca / Distrito", all_stakes, default=all_stakes)
    
    # Filtrar barrios según estacas seleccionadas
    filtered_wards = insc[insc[stake_col].isin(selected_stakes)][ward_col].dropna().unique()
    selected_wards = st.sidebar.multiselect("Barrio / Rama", sorted(filtered_wards), default=filtered_wards)
else:
    selected_stakes = []
    selected_wards = []

# Aplicar filtros
df = insc.copy()
if selected_stakes:
    df = df[df[stake_col].isin(selected_stakes)]
if selected_wards and ward_col:
    df = df[df[ward_col].isin(selected_wards)]

# Solo rangos deseados
df = df[(df['Age'] >= 13) & (df['Age'] <= 35)]

# Pestañas
tabs = st.tabs(["📈 Resumen", "👥 Grupos", "👤 Conversos", "📋 Listas", "🔄 No Volvieron 2026", "📤 Exportar"])

with tabs[0]:
    st.header("Resumen")
    c1,c2,c3 = st.columns(3)
    c1.metric("Total Actual", len(df))
    c2.metric("Seminarios", len(df[df['Age']<=17]))
    c3.metric("Institutos", len(df[df['Age']>=18]))

with tabs[4]:
    st.header("🔄 Quiénes No Volvieron en 2026")
    if pot is not None:
        pot['Last Attended'] = pd.to_datetime(pot.get('Last Attended Week Date', None), errors='coerce')
        pot['Year_2025'] =
