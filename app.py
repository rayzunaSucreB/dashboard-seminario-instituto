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

stake_col = next((col for col in ['Stake - District', 'Stake'] if col in insc.columns), 'Stake - District')
ward_col = next((col for col in ['Ward - Branch', 'Ward'] if col in insc.columns), 'Ward - Branch')

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

# Filtros cascada
st.sidebar.header("🔎 Filtros")
all_stakes = sorted(insc[stake_col].dropna().unique()) if stake_col in insc.columns else []
selected_stakes = st.sidebar.multiselect("Estaca / Distrito", all_stakes, default=all_stakes)

filtered_df = insc[insc[stake_col].isin(selected_stakes)] if selected_stakes else insc
all_wards = sorted(filtered_df[ward_col].dropna().unique()) if ward_col in filtered_df.columns else []
selected_wards = st.sidebar.multiselect("Barrio / Rama", all_wards, default=all_wards)

df = filtered_df[filtered_df[ward_col].isin(selected_wards)] if selected_wards else filtered_df

# Solo rangos deseados
df = df[(df['Age'] >= 13) & (df['Age'] <= 35)]

# Pestañas
tabs = st.tabs(["📈 Resumen", "👥 Grupos", "📋 Listas", "🔄 No Volvieron 2026", "📤 Exportar"])

with tabs[0]:
    st.header("Resumen General")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Filtrado", len(df))
    c2.metric("Seminarios (13-17)", len(df[df['Age'] <= 17]))
    c3.metric("Institutos (18-35)", len(df[df['Age'] >= 18]))

with tabs[3]:
    st.header("🔄 Quiénes No Volvieron en 2026")
    if pot is not None:
        pot['Last Attended'] = pd.to_datetime(pot.get('Last Attended Week Date', None), errors='coerce')
        pot['Year_2025'] = pot['Last Attended'].dt.year == 2025
        
        nombres_insc = set(df['Student Name'].astype(str).str.lower().str.strip())
        no_volvieron = pot[
            (pot['Year_2025'] == True) & 
            ~pot['Student Name'].astype(str).str.lower().str.strip().isin(nombres_insc)
        ]
        
        st.success(f"**Asistieron en 2025 pero no volvieron en 2026: {len(no_volvieron)}**")
        st.dataframe(no_volvieron[['Student Name', 'Age', 'Sex', 'Last Attended', stake_col, ward_col]].head(50))
    else:
        st.info("Sube Potenciales.xlsx para ver esta comparación")

with tabs[4]:
    st.header("Exportar")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Descargar datos actuales", output.getvalue(), "Dashboard_Actual.xlsx")

st.caption("Dashboard para Raimundo Zuna - S&I Bolivia")
