import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Dashboard S&I Bolivia", layout="wide")
st.title("📊 Dashboard Seminario & Instituto - Bolivia")
st.markdown("**Actualización en tiempo real** - Sube tus archivos cuando quieras")

# Carga de archivos
col1, col2 = st.columns(2)
with col1:
    insc_file = st.file_uploader("📌 Subir Inscritos.xlsx", type=["xlsx"])
with col2:
    pot_file = st.file_uploader("📌 Subir Potenciales.xlsx", type=["xlsx"])

@st.cache_data
def load_df(file):
    if file is None:
        return None
    return pd.read_excel(file)

insc = load_df(insc_file)
pot = load_df(pot_file)

if insc is None and pot is None:
    st.warning("Sube al menos un archivo para ver el dashboard")
    st.stop()

# Preparación de datos
if insc is not None:
    insc['Age'] = pd.to_numeric(insc.get('Age', None), errors='coerce')
    insc['Confirmation Date'] = pd.to_datetime(insc.get('Confirmation Date', None), errors='coerce')
    insc['Sex'] = insc.get('Sex', 'Desconocido')
    
    # Filtros importantes
    stake_col = 'Stake - District' if 'Stake - District' in insc.columns else 'Stake'
    ward_col = 'Ward - Branch' if 'Ward - Branch' in insc.columns else 'Ward'
    
    def get_year_group(row):
        age = row.get('Age')
        if pd.isna(age):
            return "Sin edad"
        if age <= 17:
            if age <= 14: return "S1"
            elif age == 15: return "S2"
            elif age == 16: return "S3"
            else: return "S4"
        else:
            year = row.get('Year In Program', 1)
            return f"I{int(year)}" if year > 0 else "I1"
    
    insc['Grupo'] = insc.apply(get_year_group, axis=1)

# Filtros globales
st.sidebar.header("🔎 Filtros")
if insc is not None:
    selected_stakes = st.sidebar.multiselect("Estaca / Distrito", options=insc[stake_col].dropna().unique(), default=insc[stake_col].dropna().unique())
    selected_wards = st.sidebar.multiselect("Barrio / Rama", options=insc[ward_col].dropna().unique(), default=insc[ward_col].dropna().unique())
    
    df_filtered = insc[(insc[stake_col].isin(selected_stakes)) & (insc[ward_col].isin(selected_wards))]
else:
    df_filtered = pd.DataFrame()

# Pestañas
tabs = st.tabs(["📈 Resumen", "👥 Por Edades", "👤 Género y Conversos", "📋 Listas", "🔄 No Volvieron", "📤 Exportar"])

with tabs[0]:
    st.header("Resumen General")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Inscritos", len(df_filtered))
    if 'Average Attendance' in df_filtered.columns:
        c2.metric("Promedio Asistencia", f"{df_filtered['Average Attendance'].mean():.1%}")

with tabs[1]:
    st.header("Por Edades y Grupos")
    if not df_filtered.empty:
        st.dataframe(df_filtered.groupby('Grupo').size().reset_index(name='Cantidad'))
        fig = px.pie(df_filtered, names='Grupo', title="Distribución por Grupo")
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.header("Género y Nuevos Conversos")
    # (código de género y conversos se mantiene)

with tabs[3]:
    st.header("Listas de Nombres")
    if not df_filtered.empty:
        st.dataframe(df_filtered[['Student Name', 'Preferred Name', 'Age', 'Sex', 'Grupo', 'Average Attendance', stake_col, ward_col]])

# ... (el resto de pestañas se mantienen)

with tabs[5]:
    st.header("Exportar")
    if not df_filtered.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Inscritos')
        st.download_button("⬇️ Descargar filtrado", output.getvalue(), "Inscritos_Filtrado.xlsx")

st.caption("Dashboard para Raimundo Zuna - S&I Bolivia")
