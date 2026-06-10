import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Dashboard S&I Bolivia", layout="wide")
st.title("📊 Dashboard Seminario & Instituto - Bolivia")
st.markdown("**Actualización en tiempo real** - Sube tus archivos cuando quieras")

# --- Carga de archivos ---
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

# --- Preparación de datos ---
if insc is not None:
    insc['Age'] = pd.to_numeric(insc['Age'], errors='coerce')
    insc['Confirmation Date'] = pd.to_datetime(insc['Confirmation Date'], errors='coerce')
    insc['Sex'] = insc.get('Sex', 'Desconocido')
    
    # Clasificación Seminary / Institute
    def get_year_group(row):
        age = row['Age']
        if pd.isna(age):
            return "Sin edad"
        if age <= 17:
            # Seminary
            if age <= 14:
                return "S1"
            elif age == 15:
                return "S2"
            elif age == 16:
                return "S3"
            else:
                return "S4"
        else:
            # Institute - I1 si es primer año (aprox)
            return "I1" if row.get('Year In Program', 0) == 1 or row.get('1st Term', 0) == 1 else f"I{int(row.get('Year In Program', 1))}"
    
    insc['Grupo'] = insc.apply(get_year_group, axis=1)

# --- Pestañas ---
tabs = st.tabs(["📈 Resumen", "👥 Por Edades y Grupos", "👤 Género y Nuevos Conversos", "📋 Listas de Nombres", "🔄 No Volvieron", "📤 Exportar"])

with tabs[0]:
    st.header("Resumen General")
    c1, c2, c3, c4 = st.columns(4)
    if insc is not None:
        c1.metric("Total Inscritos", len(insc))
        c2.metric("Promedio Asistencia", f"{insc['Average Attendance'].mean():.1%}" if 'Average Attendance' in insc.columns else "N/A")
    if pot is not None:
        c3.metric("Total Potenciales", len(pot))
    
    if insc is not None:
        fig = px.histogram(insc, x='Age', color='Grupo', title="Distribución de Edades")
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.header("Por Edades y Grupos (S1-S4 / I1)")
    if insc is not None:
        st.dataframe(insc.groupby('Grupo').size().reset_index(name='Cantidad'))
        fig = px.pie(insc, names='Grupo', title="Distribución por Grupo")
        st.plotly_chart(fig)

with tabs[2]:
    st.header("Género y Nuevos Conversos")
    col_a, col_b = st.columns(2)
    with col_a:
        if insc is not None:
            fig = px.pie(insc, names='Sex', title="Por Género")
            st.plotly_chart(fig)
    
    with col_b:
        st.subheader("Nuevos Conversos")
        days = st.slider("Días atrás para considerar nuevo converso", 30, 730, 365)
        cutoff = datetime.now() - timedelta(days=days)
        if insc is not None:
            nuevos = insc[insc['Confirmation Date'] >= cutoff]
            st.metric("Nuevos Conversos", len(nuevos))
            if not nuevos.empty:
                st.dataframe(nuevos[['Student Name', 'Age', 'Confirmation Date', 'Grupo']])

with tabs[3]:
    st.header("Listas de Nombres")
    if insc is not None:
        filtro_grupo = st.multiselect("Filtrar por Grupo", options=insc['Grupo'].unique(), default=insc['Grupo'].unique())
        df_filtrado = insc[insc['Grupo'].isin(filtro_grupo)]
        st.dataframe(df_filtrado[['Student Name', 'Preferred Name', 'Age', 'Sex', 'Grupo', 'Average Attendance', 'Ward - Branch']])

with tabs[4]:
    st.header("🔍 Quiénes No Volvieron")
    st.info("Compara Inscritos actuales con Potenciales o datos anteriores")
    if insc is not None and pot is not None:
        # Simple comparación por nombre
        nombres_insc = set(insc['Student Name'].str.lower().str.strip())
        potenciales_no_insc = pot[~pot['Student Name'].str.lower().str.strip().isin(nombres_insc)]
        st.write(f"**Potenciales que aún no están inscritos ({len(potenciales_no_insc)})**")
        st.dataframe(potenciales_no_insc[['Student Name', 'Age', 'Sex', 'Confirmation Date']])

with tabs[5]:
    st.header("Exportar e Imprimir")
    if insc is not None:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            insc.to_excel(writer, sheet_name='Inscritos', index=False)
        st.download_button("⬇️ Descargar Inscritos completo", output.getvalue(), "Inscritos_Procesado.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    st.info("Usa Ctrl + P para imprimir cualquier pestaña")

st.caption("Dashboard hecho para Raymundo Zuna - S&I Sucre/Bolivia 🚀")
