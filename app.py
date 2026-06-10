import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Dashboard S&I Bolivia", layout="wide", page_icon="📊")
st.title("📊 DASHBOARD PROFESIONAL S&I BOLIVIA 2026")
st.markdown("**Herramienta para Presidencias y Líderes de Seminario e Instituto**")

# Carga de archivos
col1, col2 = st.columns(2)
with col1:
    insc_file = st.file_uploader("📌 Inscritos 2026", type=["xlsx"])
with col2:
    pot_file = st.file_uploader("📌 Potenciales", type=["xlsx"])

@st.cache_data
def load_df(file):
    return pd.read_excel(file) if file is not None else None

insc = load_df(insc_file)
pot = load_df(pot_file)

if insc is None:
    st.warning("Sube Inscritos.xlsx para comenzar")
    st.stop()

# Preparación robusta de datos
insc['Age'] = pd.to_numeric(insc.get('Age', pd.Series([])), errors='coerce')
insc['Confirmation Date'] = pd.to_datetime(insc.get('Confirmation Date', pd.Series([])), errors='coerce')
insc['Last Attended'] = pd.to_datetime(insc.get('Last Attended Week Date', pd.Series([])), errors='coerce')

stake_col = next((col for col in ['Stake - District', 'Stake'] if col in insc.columns), None)
ward_col = next((col for col in ['Ward - Branch', 'Ward'] if col in insc.columns), None)

def get_grupo(age):
    if pd.isna(age): return "Sin edad"
    if age <= 17:
        if age <= 14: return "S1"
        elif age == 15: return "S2"
        elif age == 16: return "S3"
        else: return "S4"
    else:
        return "Instituto"

insc['Grupo'] = insc['Age'].apply(get_grupo)

# Filtros laterales cascada
st.sidebar.header("🔎 Filtros")
stakes = sorted(insc[stake_col].dropna().unique()) if stake_col else []
selected_stakes = st.sidebar.multiselect("Estaca / Distrito", stakes, default=stakes)

df_stake = insc[insc[stake_col].isin(selected_stakes)] if stake_col and selected_stakes else insc
wards = sorted(df_stake[ward_col].dropna().unique()) if ward_col else []
selected_wards = st.sidebar.multiselect("Barrio / Rama", wards, default=wards)

df = df_stake[df_stake[ward_col].isin(selected_wards)] if ward_col and selected_wards else df_stake

# Pestañas
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resumen General", "📍 Por Estaca y Barrio", "🧑‍🚀 Nuevos Conversos", 
    "🔄 No Volvieron", "📋 Listas Detalladas", "📤 Exportar"
])

with tab1:
    st.header("Resumen General")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inscritos 2026", len(df))
    c2.metric("Seminarios (13-17)", len(df[df['Age'] <= 17]))
    c3.metric("Institutos (18+)", len(df[df['Age'] >= 18]))
    cutoff = datetime.now() - timedelta(days=365)
    nuevos = df[df['Confirmation Date'] >= cutoff] if 'Confirmation Date' in df.columns else pd.DataFrame()
    c4.metric("Nuevos Conversos (1 año)", len(nuevos))

with tab2:
    st.header("📍 Por Estaca y
