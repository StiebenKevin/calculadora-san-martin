import streamlit as st
import pandas as pd
from PIL import Image

# 1. Base de datos de topes municipales de San Martín
escalas_municipales = {
    "Agropecuario": {
        "tope_base": 244789000,     # Límite para alícuota 5 o 7 (Pequeño)
        "tope_art16": 368103000,    # Límite para alícuota 8 (Mediano)
        "tope_art17": 1187425000,   # Límite para alícuota 12 (Grande)
        "tope_art18": 3492431000    # Límite para alícuota 15 (Grande)
    },
    "Industria y Minería": {
        "tope_base": 723725000,
        "tope_art16": 1088308000,
        "tope_art17": 3510670000,
        "tope_art18": 10325497000
    },
    "Comercio": {
        "tope_base": 966148000,
        "tope_art16": 1453321000,
        "tope_art17": 4686623000,
        "tope_art18": 13784189000
    },
    "Servicios": {
        "tope_base": 236512000,
        "tope_art16": 355658000,
        "tope_art17": 1147282000,
        "tope_art18": 3374357000
    },
    "Construcción": {
        "tope_base": 289552000,
        "tope_art16": 458798000,
        "tope_art17": 1479990000,
        "tope_art18": 4352914000
    }
}

# 2. Función de clasificación bajo el criterio solicitado
def evaluar_contribuyente(sector, ingresos):
    if sector not in escalas_municipales:
        return "Sector No Válido", 0
    
    topes = escalas_municipales[sector]
    
    # Determinar Alícuota y Categoría según los tramos de la ordenanza
    if ingresos <= topes["tope_base"]:
        # Subdivisión interna estimada para aplicar alícuotas 5 y 7 dentro del tramo bajo
        alicuota = 5 if ingresos <= (topes["tope_base"] / 2) else 7
        return "Pequeño", alicuota
        
    elif ingresos <= topes["tope_art16"]:
        return "Mediano", 8
        
    elif ingresos <= topes["tope_art17"]:
        return "Grande", 12
        
    else:
        return "Grande", 15

# --- INTERFAZ DE STREAMLIT ---

# Cargar el logo institucional de San Martín para la interfaz
try:
    icono_muni = Image.open("logo_san_martin.png")
except:
    icono_muni = "🏢"  # Resguardo por si la imagen no se encuentra

# Configuración del navegador (Título de la pestaña y Logo de la pestaña)
st.set_page_config(
    page_title="Clasificador de Contribuyentes", 
    page_icon=icono_muni, 
    layout="wide"
)

# Insertar el logo institucional arriba en el cuerpo de la página
if isinstance(icono_muni, Image.Image):
    st.image(icono_muni, width=160)

st.title("Clasificador de Contribuyentes")
st.write("Herramienta interna para la determinación de categorías y alícuotas según ingresos anuales.")

# Definición de pestañas de trabajo
tab1, tab2 = st.tabs(["🔍 Consulta Individual", "📂 Procesamiento Masivo (Excel/CSV)"])

# --- PESTAÑA 1: CONSULTA INDIVIDUAL ---
with tab1:
    st.header("Calcular un Contribuyente")
    st.write("Ingrese los datos de la declaración jurada para obtener la clasificación inmediata.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sector_seleccionado = st.selectbox(
            "Seleccione el Sector Económico:",
            options=list(escalas_municipales.keys())
        )
        
    with col2:
        ingresos_ingresados = st.number_input(
            "Ingrese los Ingresos Anuales ($):",
            min_value=0,
            value=0,
            step=100000,
            format="%d"
        )
        
    if st.button("Evaluar Contribuyente", type="primary"):
        if ingresos_ingresados == 0:
            st.warning("Por favor, ingrese un monto superior a $0 para calcular.")
        else:
            categoria, alicuota = evaluar_contribuyente(sector_seleccionado, ingresos_ingresados)
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            
            c1.metric(label="Categoría Asignada", value=categoria)
            c2.metric(label="Alícuota Aplicable", value=f"{alicuota} ‰")
            
            st.info(f"El contribuyente de **{sector_seleccionado}** con ingresos declarados por **${ingresos_ingresados:,.2f}** fue clasificado correctamente.")

# --- PESTAÑA 2: PROCESAMIENTO MASIVO ---
with tab2:
    st.header("Subir padrón o listado")
    st.write("Cargue un archivo con el formato adecuado para liquidar de forma masiva.")
    
    st.markdown("""
    > 📋 **Requisito del archivo:** El archivo Excel o CSV debe contener al menos dos columnas rotuladas en la primera fila como: **Sector** e **Ingresos**.
    """)
    
    archivo_subido = st.file_uploader("Subir archivo Excel o CSV", type=["csv", "xlsx"])
    
    if archivo_subido is not None:
        try:
            # Lectura del archivo según su extensión
            if archivo_subido.name.endswith('.csv'):
                df_user = pd.read_csv(archivo_subido)
            else:
                df_user = pd.read_excel(archivo_subido)
                
            st.success("¡Archivo cargado con éxito!")
            
            # Normalizar los nombres de las columnas (quita espacios y pone la primera letra en mayúscula)
            df_user.columns = [c.strip().capitalize() for c in df_user.columns]
            
            if 'Sector' in df_user.columns and 'Ingresos' in df_user.columns:
                
                if st.button("Ejecutar Clasificación Masiva"):
                    with st.spinner("Procesando registros..."):
                        # Aplicar la lógica fila por fila
                        res = df_user.apply(lambda row: evaluar_contribuyente(row['Sector'], row['Ingresos']), axis=1)
                        df_user['Categoría Municipal'] = [r[0] for r in res]
                        df_user['Alícuota (‰)'] = [r[1] for r in res]
                        
                    st.write("### Vista previa del resultado:")
                    st.dataframe(df_user)
                    
                    # Generación del archivo Excel de salida guardado en la memoria buffer
                    @st.cache_data
                    def convertir_df(df):
                        import io
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Contribuyentes_Clasificados')
                        return output.getvalue()
                        
                    excel_data = convertir_df(df_user)
                    st.download_button(
                        label="📥 Descargar Excel Procesado",
                        data=excel_data,
                        file_name='contribuyentes_clasificados.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            else:
                st.error("Error crítico: No se encontraron las columnas requeridas 'Sector' e 'Ingresos'. Verifique los títulos de su planilla.")
                
        except Exception as e:
            st.error(f"Ocurrió un error inesperado al leer el archivo: {e}")