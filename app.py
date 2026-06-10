import streamlit as st
import pandas as pd
import plotly.express as px  # Librería para gráficos interactivos estilo Power BI
import io

# --- PESTAÑA 2: AUDITORÍA MASIVA + DASHBOARD ANALÍTICO ---
with tab2:
    st.header("🔬 Centro de Inteligencia y Dashboard Fiscal")
    st.markdown("""
    Cargá tu archivo vertical crudo. El sistema procesará la auditoría de oficio, 
    detectará los desvíos y consolidará un tablero gráfico interactivo de control de gestión.
    """)
    
    archivo = st.file_uploader("📂 Cargar Archivo de Fiscalización (.xlsx)", type=["xlsx"], key="uploader_dashboard")
    
    if archivo is not None:
        try:
            # Leer datos
            df_raw = pd.read_excel(archivo)
            
            # Validar columnas críticas de tu nueva plantilla
            columnas_requeridas = ['RUBRO', 'ING_ANUAL_PAIS', 'ANIO_FISCAL', 'MES_FISCAL', 'FACTURACION_MES', 'COEF_SM', 'PAGOS_MES']
            if not all(col in df_raw.columns for col in columnas_requeridas):
                st.error("❌ El archivo no cumple con la estructura requerida (RUBRO, ING_ANUAL_PAIS, ANIO_FISCAL, MES_FISCAL, FACTURACION_MES, COEF_SM, PAGOS_MES).")
            else:
                st.success("¡Datos cargados con éxito!")
                
                # --- PROCESAMIENTO MATEMÁTICO (IGUAL AL ANTERIOR) ---
                df = df_raw.copy()
                df['ING_ANUAL_PAIS'] = pd.to_numeric(df['ING_ANUAL_PAIS'], errors='coerce').fillna(0)
                df['ANIO_FISCAL'] = pd.to_numeric(df['ANIO_FISCAL'], errors='coerce').fillna(2026).astype(int)
                df['MES_FISCAL'] = pd.to_numeric(df['MES_FISCAL'], errors='coerce').fillna(1).astype(int)
                df['FACTURACION_MES'] = pd.to_numeric(df['FACTURACION_MES'], errors='coerce').fillna(0)
                df['COEF_SM'] = pd.to_numeric(df['COEF_SM'], errors='coerce').fillna(1)
                df['PAGOS_MES'] = pd.to_numeric(df['PAGOS_MES'], errors='coerce').fillna(0)
                
                # Ejecutar funciones de tu motor fiscal
                res_eval = df.apply(lambda r: evaluar_contribuyente(r['ANIO_FISCAL'], r['RUBRO'], r['ING_ANUAL_PAIS']), axis=1)
                df['Fisca_Tamaño'] = [r[0] for r in res_eval]
                df['Fisca_Alícuota_‰'] = [r[1] for r in res_eval]
                
                df['Fisca_Base_San_Martín'] = df['FACTURACION_MES'] * df['COEF_SM']
                df['Fisca_Tasa_por_Ingresos'] = (df['Fisca_Base_San_Martín'] * df['Fisca_Alícuota_‰']) / 1000
                
                res_minimos = df.apply(lambda r: calcular_minimo_empleados(1, r['ANIO_FISCAL'], r['MES_FISCAL']), axis=1)
                df['Fisca_Mínimo_Fijo'] = [r[1] for r in res_minimos]
                
                df['Fisca_Impuesto_Determinado'] = df[['Fisca_Tasa_por_Ingresos', 'Fisca_Mínimo_Fijo']].max(axis=1)
                df['Fisca_Diferencia_Desvío'] = df['Fisca_Impuesto_Determinado'] - df['PAGOS_MES']
                
                # Definición estricta de estados para los gráficos
                def definir_estado(x):
                    if x > 10: return "Inconsistente (Bajo Pago)"
                    elif x < -10: return "Saldo a Favor (Contribuyente)"
                    return "Correcto / Neteado"
                df['Fisca_Estado'] = df['Fisca_Diferencia_Desvío'].apply(definir_estado)

                # --- FILTROS DINÁMICOS DEL DASHBOARD (SIDEBAR) ---
                st.sidebar.header("🎯 Filtros del Dashboard")
                
                # Filtro de Año
                anios_disponibles = sorted(df['ANIO_FISCAL'].unique())
                anio_sel = st.sidebar.multiselect("Filtrar por Año Fiscal:", anios_disponibles, default=anios_disponibles)
                
                # Filtro de Mes
                meses_disponibles = sorted(df['MES_FISCAL'].unique())
                mes_sel = st.sidebar.multiselect("Filtrar por Mes:", meses_disponibles, format_func=lambda x: NOMBRES_MESES.get(x, x), default=meses_disponibles)
                
                # Filtro de Rubro
                rubros_disponibles = df['RUBRO'].unique()
                rubro_sel = st.sidebar.multiselect("Filtrar por Rubro/Actividad:", rubros_disponibles, default=rubros_disponibles)
                
                # Aplicar los filtros al dataframe que va a usar el Dashboard
                df_filtrado = df[
                    (df['ANIO_FISCAL'].isin(anio_sel)) & 
                    (df['MES_FISCAL'].isin(mes_sel)) & 
                    (df['RUBRO'].isin(rubro_sel))
                ]
                
                st.markdown("---")
                st.subheader("📊 Tablero de Control de Gestión de Inteligencia Fiscal")
                
                # --- PASO 1: TARJETAS DE MÉTRICAS PRINCIPALES (KPIs) ---
                total_contribuyentes = len(df_filtrado)
                df_inconsistentes = df_filtrado[df_filtrado['Fisca_Diferencia_Desvío'] > 10]
                cant_inconsistentes = len(df_inconsistentes)
                monto_total_evadido = df_inconsistentes['Fisca_Diferencia_Desvío'].sum()
                porcentaje_desvio = (cant_inconsistentes / total_contribuyentes * 100) if total_contribuyentes > 0 else 0
                
                kpi1, kpi2, kpi3 = st.columns(3)
                with kpi1:
                    st.metric(label="👥 Contribuyentes Auditados", value=f"{total_contribuyentes:,}")
                with kpi2:
                    st.metric(label="🔴 Casos con Inconsistencia", value=f"{cant_inconsistentes:,}", delta=f"{porcentaje_desvio:.1f}% del padrón", delta_color="inverse")
                with kpi3:
                    st.metric(label="💰 Monto Total Omitido Recuperable", value=f"$ {monto_total_evadido:,.2f}")
                
                st.markdown("---")
                
                # --- PASO 2: GRÁFICOS INTERACTIVOS (ESTILO POWER BI) ---
                col_graf1, col_graf2 = st.columns(2)
                
                with col_graf1:
                    st.markdown("##### 🍕 Distribución del Padrón por Estado de Auditoría")
                    # Gráfico de Torta con los estados
                    fig_torta = px.pie(
                        df_filtrado, 
                        names='Fisca_Estado', 
                        color='Fisca_Estado',
                        color_discrete_map={
                            "Inconsistente (Bajo Pago)": "#e63946",
                            "Correcto / Neteado": "#a8dadc",
                            "Saldo a Favor (Contribuyente)": "#457b9d"
                        },
                        hole=0.4
                    )
                    fig_torta.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig_torta, use_container_width=True)
                    
                with col_graf2:
                    st.markdown("##### 🏢 Monto Omitido ($) por Rubro / Actividad")
                    # Gráfico de Barras: Cuánta plata hay para recaudar por cada sector
                    df_rubro_monto = df_inconsistentes.groupby('RUBRO')['Fisca_Diferencia_Desvío'].sum().reset_index()
                    fig_barras = px.bar(
                        df_rubro_monto, 
                        x='RUBRO', 
                        y='Fisca_Diferencia_Desvío',
                        labels={'Fisca_Diferencia_Desvío': 'Monto Omitido ($)', 'RUBRO': 'Actividad'},
                        color='RUBRO',
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig_barras.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=300)
                    st.plotly_chart(fig_barras, use_container_width=True)
                
                st.markdown("---")
                
                # --- PASO 3: EVOLUCIÓN MENSUAL (Gráfico de Líneas si hay varios meses) ---
                if len(df_filtrado['MES_FISCAL'].unique()) > 1:
                    st.markdown("##### 📈 Evolución Mensual del Monto Total Omitido Detectado")
                    df_linea = df_inconsistentes.groupby(['ANIO_FISCAL', 'MES_FISCAL'])['Fisca_Diferencia_Desvío'].sum().reset_index()
                    df_linea['Periodo'] = df_linea['ANIO_FISCAL'].astype(str) + "-" + df_linea['MES_FISCAL'].astype(str).str.zfill(2)
                    df_linea = df_linea.sort_values('Periodo')
                    
                    fig_linea = px.line(
                        df_linea, x='Periodo', y='Fisca_Diferencia_Desvío', 
                        markers=True, text=df_linea['Fisca_Diferencia_Desvío'].apply(lambda x: f"${x:,.0f}")
                    )
                    fig_linea.update_traces(textposition="top center", line_color="#1e3d59")
                    st.plotly_chart(fig_linea, use_container_width=True)
                    st.markdown("---")

                # --- PASO 4: VISTA DE DATOS Y DESCARGA ---
                st.markdown("### 📋 Detalle de Contribuyentes Filtrados (Ordenado por Gravedad)")
                df_mostrar = df_filtrado.sort_values(by='Fisca_Diferencia_Desvío', ascending=False)
                st.dataframe(df_mostrar, use_container_width=True)
                
                # Botón de Descarga del Excel Filtrado
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_mostrar.to_excel(writer, index=False, sheet_name='Auditoria_Filtrada')
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar esta Vista Filtrada en Excel",
                    data=processed_data,
                    file_name="auditoria_dashboard_filtrado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Error al generar el Dashboard: {e}")
