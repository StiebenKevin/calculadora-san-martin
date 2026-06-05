import streamlit as st
import pandas as pd
from PIL import Image
import io

# Configuración de la página
st.set_page_config(page_title="Calculadora de Alícuotas - San Martín", page_icon="📊", layout="wide")

# Intentar cargar el logo municipal
try:
    image = Image.open('logo_san_martin.png')
    st.image(image, width=250)
except:
    st.subheader("Municipalidad de General San Martín")

st.title("📊 Calculadora de Alícuotas")

# 1. ESTRUCTURA DE ESCALAS POR AÑO FISCAL (2025 y 2026 Corregidas)
escalas_por_anio = {
    2026: {
        "Agropecuario": {"limite_5_a_7": 244789000, "limite_7_a_8": 368103000, "limite_8_to_12": 1187425000, "limite_12_to_15": 3492431000},
        "Industria y Minería": {"limite_5_a_7": 723725000, "limite_7_a_8": 1088308000, "limite_8_to_12": 3510670000, "limite_12_to_15": 10325497000},
        "Comercio": {"limite_5_a_7": 966148000, "limite_7_a_8": 1453321000, "limite_8_to_12": 4686623000, "limite_12_to_15": 13784189000},
        "Servicios": {"limite_5_a_7": 236512000, "limite_7_a_8": 355658000, "limite_8_to_12": 1147282000, "limite_12_to_15": 3374357000},
        "Construcción": {"limite_5_a_7": 289552000, "limite_7_a_8": 458798000, "limite_8_to_12": 1479990000, "limite_12_to_15": 4352914000}
    },
    2025: {
        "Agropecuario": {"limite_5_a_7": 188939000, "limite_7_a_8": 284118000, "limite_8_to_12": 916506000, "limite_12_to_15": 2695609000},
        "Industria y Minería": {"limite_5_a_7": 558602000, "limite_7_a_8": 840003000, "limite_8_to_12": 2709687000, "limite_12_to_15": 7969664000},
        "Comercio": {"limite_5_a_7": 745715000, "limite_7_a_8": 1121376000, "limite_8_to_12": 3617338000, "limite_12_to_15": 10639232000},
        "Servicios": {"limite_5_a_7": 182550000, "limite_7_a_8": 274512000, "limite_8_to_12": 885522000, "limite_12_to_15": 2604474000},
        "Construcción": {"limite_5_a_7": 223489000, "limite_7_a_8": 354120000, "limite_8_to_12": 1142320000, "limite_12_to_15": 3359767000}
    }
}

# 2. FUNCIÓN DE EVALUACIÓN MULTIANUAL
def evaluar_contribuyente(anio, sector, ingresos):
    if anio not in escalas_por_anio:
        return "Año No Válido", 0
    
    escalas_anio = escalas_por_anio[anio]
    if sector not in escalas_anio:
        return "Sector No Válido", 0
    
    topes = escalas_anio[sector]
    
    if ingresos < topes["limite_5_a_7"]:
        return "Pequeño", 5
    elif ingresos < topes["limite_7_a_8"]:
        return "Pequeño", 7
    elif ingresos < topes["limite_8_to_12"]:
        return "Mediano", 8
    elif ingresos < topes["limite_12_to_15"]:
        return "Grande", 12
    else:
        return "Grande", 15

# 3. SELECTOR DE AÑO GLOBAL
col_anio, _ = st.columns([1, 2])
with col_anio:
    anio_sel = st.selectbox("📅 Seleccione el Año de la Ordenanza:", [2026, 2025])

st.write(f"Trabajando con la ordenanza impositiva del período: **{anio_sel}**")
st.markdown("---")

# Pestañas de la aplicación
tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Calculadora Masiva (Excel)"])

with tab1:
    st.header(f"Consulta Individual ({anio_sel})")
    
    col1, col2 = st.columns(2)
    with col1:
        sector_sel = st.selectbox("Seleccione la actividad:", list(escalas_por_anio[anio_sel].keys()))
    with col2:
        ingresos_num = st.number_input("Ingrese los Ingresos Brutos Anuales del periodo fiscal anterior ($):", min_value=0.0, step=10000.0, format="%.2f")
        
    if st.button("Calcular Alícuota"):
        cat, alic = evaluar_contribuyente(anio_sel, sector_sel, ingresos_num)
        st.success(f"**Resultado {anio_sel}:** Categoría: **{cat}** | Alícuota Asignada: **{alic} ‰**")
        
        # Panel informativo dinámico según el año seleccionado
        t = escalas_por_anio[anio_sel][sector_sel]
        st.info(f"Rangos aplicados para {sector_sel} en el período {anio_sel}:\n"
                f"- Menos de ${t['limite_5_a_7']:,} ➡️ 5‰ (Pequeño)\n"
                f"- Desde ${t['limite_5_a_7']:,} hasta ${t['limite_7_a_8']-1:,} ➡️ 7‰ (Pequeño)\n"
                f"- Desde ${t['limite_7_a_8']:,} hasta ${t['limite_8_to_12']-1:,} ➡️ 8‰ (Mediano)\n"
                f"- Desde ${t['limite_8_to_12']:,} hasta ${t['limite_12_to_15']-1:,} ➡️ 12‰ (Grande)\n"
                f"- ${t['limite_12_to_15']:,} o más ➡️ 15‰ (Grande)")

with tab2:
    st.header(f"Control de Alicuota")
    st.markdown(f"Subí el Excel. El cruce y cálculo se realizará con los parámetros de **{anio_sel}**.")
    
    archivo = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            st.write("📋 Vista previa")
            st.dataframe(df.head(5))
            
            columnas = df.columns.tolist()
            col_sec = st.selectbox("Seleccioná la columna de ACTIVIDAD:", columnas)
            col_ing = st.selectbox("Seleccioná la columna de INGRESOS:", columnas)
            
            if st.button("Procesar y Buscar"):
                # Se pasa el anio_sel seleccionado globalmente
                resultados = df.apply(lambda r: evaluar_contribuyente(anio_sel, r[col_sec], r[col_ing]), axis=1)
                
                df['Año_Fiscal_Auditado'] = anio_sel
                df['Categoría_Calculada'] = [res[0] for res in resultados]
                df['Alícuota_Calculada_‰'] = [res[1] for res in resultados]
                
                st.success(f"¡Procesamiento completado usando la escala {anio_sel}!")
                st.dataframe(df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name=f'Control_{anio_sel}')
                processed_data = output.getvalue()
                
                st.download_button(
                    label=f"📥 Descargar Excel Controlado {anio_sel}",
                    data=processed_data,
                    file_name=f"control_fiscal_{anio_sel}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
