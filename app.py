import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Dashboard S&I Bolivia", layout="wide", page_icon="📊")
st.title("📊 Dashboard Profesional S&I Bolivia 2026")
st.markdown("**Herramienta para Presidencias y Líderes**")

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

# Preparación de datos
insc['Age'] = pd.to_numeric(insc.get('Age', None), errors='coerce')
insc['Confirmation Date'] = pd.to_datetime(insc.get('Confirmation Date', None), errors='coerce')
insc['Last Attended'] = pd.to_datetime(insc.get('Last Attended Week Date', None), errors='coerce')

stake_col = 'Stake - District' if 'Stake - District' in insc.columns else 'Stake'
ward_col = 'Ward - Branch' if 'Ward - Branch' in insc.columns else 'Ward'

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

# Filtros laterales (cascada)
st.sidebar.header("🔎 Filtros")
stakes = sorted(insc[stake_col].dropna().unique())
selected_stakes = st.sidebar.multiselect("Estaca / Distrito", stakes, default=stakes)

df_stake = insc[insc[stake_col].isin(selected_stakes)] if selected_stakes else insc
wards = sorted(df_stake[ward_col].dropna().unique())
selected_wards = st.sidebar.multiselect("Barrio / Rama", wards, default=wards)

df = df_stake[df_stake[ward_col].isin(selected_wards)] if selected_wards else df_stake

# Pestañas
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Resumen", "📍 Por Estaca y Barrio", "🧑‍🚀 Nuevos Conversos", "🔄 No Volvieron", "📋 Listas", "📤 Exportar"])

with tab1:
    st.header("Resumen General")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inscritos 2026", len(df))
    c2.metric("Seminarios (13-17)", len(df[df['Age'] <= 17]))
    c3.metric("Institutos (18+)", len(df[df['Age'] >= 18]))
    
    # Nuevos Conversos (corregido)
    cutoff = datetime.now() - timedelta(days=365)
    nuevos = df[df['Confirmation Date'] >= cutoff] if 'Confirmation Date' in df.columns else pd.DataFrame()
    c4.metric("Nuevos Conversos (1 año)", len(nuevos))

with tab2:
    st.header("📍 Por Estaca y Barrio")
    summary = df.groupby([stake_col, ward_col]).size().reset_index(name='Inscritos')
    st.dataframe(summary, use_container_width=True)
    
    fig = px.bar(summary, x=ward_col, y='Inscritos', color=stake_col, title="Inscritos por Barrio")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("🔄 No Volvieron 2026")
    if pot is not None:
        pot['Last Attended'] = pd.to_datetime(pot.get('Last Attended Week Date', None), errors='coerce')
        nombres_insc = set(df['Student Name'].astype(str).str.lower().str.strip())
        no_volvieron = pot[
            (pot['Last Attended'].dt.year == 2025) & 
            ~pot['Student Name'].astype(str).str.lower().str.strip().isin(nombres_insc)
        ]
        st.success(f"No volvieron en 2026 (asistieron 2025): **{len(no_volvieron)}**")
        st.dataframe(no_volvieron[['Student Name', 'Age', 'Sex', 'Last Attended', stake_col, ward_col]])

with tab5:
    st.header("📋 Listas Detalladas")
    st.dataframe(df[['Student Name', 'Age', 'Sex', 'Grupo', stake_col, ward_col, 'Average Attendance']], use_container_width=True)

with tab6:
    st.header("Exportar")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Descargar Excel", output.getvalue(), "Dashboard_SI_2026.xlsx")

st.caption("Dashboard para Raimundo Zuna - S&I Bolivia")
