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

# 1. ESCALAS OFICIALES ACTUALIZADAS (Corregidas según imagen)
# Columnas: Agro, Industria, Comercio, Servicios, Construcción
# Filas: Tope Base (5%), Tope Art 16 (8%), Tope Art 17 (12%), Superior (15%)
escalas_municipales = {
    "Agropecuario": {
        "tope_base": 244789000,
        "tope_art16": 368103000,
        "tope_art17": 1187425000
    },
    "Industria y Minería": {
        "tope_base": 723725000,
        "tope_art16": 1088308000,
        "tope_art17": 3510670000
    },
    "Comercio": {
        "tope_base": 966148000,
        "tope_art16": 1453321000,
        "tope_art17": 4686623000
    },
    "Servicios": {
        "tope_base": 236512000,
        "tope_art16": 355658000,
        "tope_art17": 1147282000
    },
    "Construcción": {
        "tope_base": 289552000,
        "tope_art16": 458798000,
        "tope_art17": 1479990000
    }
}

# 2. FUNCIÓN DE EVALUACIÓN (Lógica directa de topes)
def evaluar_contribuyente(sector, ingresos):
    if sector not in escalas_municipales:
        return "Sector No Válido", 0
    
    topes = escalas_municipales[sector]
    
    # Menor o igual al primer tope -> 5% y Pequeño
    if ingresos <= topes["tope_base"]:
        return "Pequeño", 5
    # Menor o igual al segundo tope -> 8% y Mediano
    elif ingresos <= topes["tope_art16"]:
        return "Mediano", 8
    # Menor o igual al tercer tope -> 12% y Grande
    elif ingresos <= topes["tope_art17"]:
        return "Grande", 12
    # Si supera el tercer tope -> 15% y Grande
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
        
        # Mostrar rango para claridad del usuario
        t = escalas_municipales[sector_sel]
        st.info(f"Parámetros de control para {sector_sel}:\n"
                f"- Hasta ${t['tope_base']:,} -> 5‰\n"
                f"- Hasta ${t['tope_art16']:,} -> 8‰\n"
                f"- Hasta ${t['tope_art17']:,} -> 12‰\n"
                f"- Más de ${t['tope_art17']:,} -> 15‰")

with tab2:
    st.header("Control de Inconsistencias Masivo")
    st.markdown("Subí el Excel con el padrón para cruzar los datos y calcular diferencias automáticamente.")
    
    archivo = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo is not None:
        try:
            df = pd.read_excel(archivo)
            st.write("📋 Vista previa de los datos cargados:")
            st.dataframe(df.head(5))
            
            # Columnas requeridas
            columnas = df.columns.tolist()
            
            col_sec = st.selectbox("Seleccioná la columna de SECTOR/ACTIVIDAD:", columnas)
            col_ing = st.selectbox("Seleccioná la columna de INGRESOS/EMISIÓN:", columnas)
            
            if st.button("Procesar y Buscar Inconsistencias"):
                # Aplicar la función fila por fila
                resultados = df.apply(lambda r: evaluar_contribuyente(r[col_sec], r[col_ing]), axis=1)
                
                df['Categoría_Calculada'] = [res[0] for res in resultados]
                df['Alícuota_Calculada_‰'] = [res[1] for res in resultados]
                
                st.success("¡Procesamiento completado con éxito!")
                st.dataframe(df)
                
                # Botón para descargar el resultado
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
