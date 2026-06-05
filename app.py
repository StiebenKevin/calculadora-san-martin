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

st.title("📊 Calculadora de Alícuotas e Inconsistencias Fiscales")
st.markdown("Herramienta interna para la Dirección de Inteligencia Fiscal")

# 1. ESCALAS OFICIALES (Límites exactos de tu tabla)
escalas_municipales = {
    "Agropecuario": {
        "limite_5_a_7": 244789000,
        "limite_7_a_8": 368103000,
        "limite_8_to_12": 1187425000,
        "limite_12_to_15": 3492431000
    },
    "Industria y Minería": {
        "limite_5_a_7": 723725000,
        "limite_7_a_8": 1088308000,
        "limite_8_to_12": 3510670000,
        "limite_12_to_15": 10325497000
    },
    "Comercio": {
        "limite_5_a_7": 966148000,
        "limite_7_a_8": 1453321000,
        "limite_8_to_12": 4686623000,
        "limite_12_to_15": 13784189000
    },
    "Servicios": {
        "limite_5_a_7": 236512000,
        "limite_7_a_8": 355658000,
        "limite_8_to_12": 1147282000,
        "limite_12_to_15": 3374357000
    },
    "Construcción": {
        "limite_5_a_7": 289552000,
        "limite_7_a_8": 458798000,
        "limite_8_to_12": 1479990000,
        "limite_12_to_15": 4352914000
    }
}

# 2. FUNCIÓN DE EVALUACIÓN CORREGIDA (Cortes basados en pisos de alícuota)
def evaluar_contribuyente(sector, ingresos):
    if sector not in escalas_municipales:
        return "Sector No Válido", 0
    
    topes = escalas_municipales[sector]
    
    # Menor estricto al primer tope -> 5% (Pequeño)
    if ingresos < topes["limite_5_a_7"]:
        return "Pequeño", 5
    # Desde el primer tope hasta antes del segundo -> 7% (Pequeño)
    elif ingresos < topes["limite_7_a_8"]:
        return "Pequeño", 7
    # Desde el segundo tope hasta antes del tercero -> 8% (Mediano)
    elif ingresos < topes["limite_8_to_12"]:
        return "Mediano", 8
    # Desde el tercer tope hasta antes del cuarto -> 12% (Grande)
    elif ingresos < topes["limite_12_to_15"]:
        return "Grande", 12
    # Si iguala o supera el cuarto tope -> 15% (Grande)
    else:
        return "Grande", 15

# Pestañas de la aplicación
tab1, tab2 = st.tabs(["🧮 Calculadora Individual", "📂 Procesamiento Masivo (Excel)"])

with tab1:
    st.header("Consulta Individual de Contribuyente")
    
    col1, col2 = st.columns(2)
    with col1:
        sector_sel = st.selectbox("Seleccione el Sector de Actividad:", list(escalas_municipales.keys()))
    with col2:
        ingresos_num = st.number_input("Ingrese los Ingresos Brutos Anuales ($):", min_value=0.0, step=10000.0, format="%.2f")
        
    if st.button("Calcular Alícuota"):
        cat, alic = evaluar_contribuyente(sector_sel, ingresos_num)
        st.success(f"**Resultado:** Categoría: **{cat}** | Alícuota Asignada: **{alic} ‰**")
        
        # Panel informativo con los rangos exactos por sector
        t = escalas_municipales[sector_sel]
        st.info(f"Rangos de control aplicados para {sector_sel}:\n"
                f"- Menos de ${t['limite_5_a_7']:,} ➡️ 5‰ (Pequeño)\n"
                f"- Desde ${t['limite_5_a_7']:,} hasta ${t['limite_7_a_8']-1:,} ➡️ 7‰ (Pequeño)\n"
                f"- Desde ${t['limite_7_a_8']:,} hasta ${t['limite_8_to_12']-1:,} ➡️ 8‰ (Mediano)\n"
                f"- Desde ${t['limite_8_to_12']:,} hasta ${t['limite_12_to_15']-1:,} ➡️ 12‰ (Grande)\n"
                f"- ${t['limite_12_to_15']:,} o más ➡️ 15‰ (Grande)")

with tab2:
    st.header("Control de Inconsistencias Masivo")
    st.markdown("Subí el Excel con el padrón para cruzar los datos y calcular diferencias automáticamente.")
    
    archivo = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            st.write("📋 Vista previa de los datos cargados:")
            st.dataframe(df.head(5))
            
            columnas = df.columns.tolist()
            col_sec = st.selectbox("Seleccioná la columna de SECTOR/ACTIVIDAD:", columnas)
            col_ing = st.selectbox("Seleccioná la columna de INGRESOS/EMISIÓN:", columnas)
            
            if st.button("Procesar y Buscar Inconsistencias"):
                resultados = df.apply(lambda r: evaluar_contribuyente(r[col_sec], r[col_ing]), axis=1)
                
                df['Categoría_Calculada'] = [res[0] for res in resultados]
                df['Alícuota_Calculada_‰'] = [res[1] for res in resultados]
                
                st.success("¡Procesamiento completado con éxito!")
                st.dataframe(df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Control_Tasas')
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Excel Controlado",
                    data=processed_data,
                    file_name="resultado_control_fiscal.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
