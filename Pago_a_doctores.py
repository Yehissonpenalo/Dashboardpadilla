import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import re
import requests

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Pagos a Doctores",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados - Diseño Apple
st.markdown("""
<style>
    /* Diseño minimalista tipo Apple */
    .main-header {
        font-size: 2.8rem;
        color: #1d1d1f;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 20px;
        border: none;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card h3 {
        color: #6e6e73;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card h2 {
        color: #1d1d1f;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
    }
    
    .positive-value {
        color: #34c759 !important;
    }
    
    .negative-value {
        color: #ff3b30 !important;
    }
    
    .section-header {
        background: linear-gradient(135deg, #007aff 0%, #005bb9 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 16px;
        margin: 2rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f5f5f7;
        border-radius: 12px 12px 0 0;
        gap: 8px;
        padding: 15px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #007aff;
        color: white;
    }
    
    /* Botones modernos */
    .stButton button {
        background: linear-gradient(135deg, #007aff 0%, #005bb9 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,122,255,0.3);
    }
    
    /* Sidebar moderno */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4eaf1 100%);
    }
    
    /* Select boxes modernos */
    .stSelectbox div div {
        border-radius: 12px;
        border: 1px solid #d2d2d7;
    }
    
    /* Date input moderno */
    .stDateInput div div {
        border-radius: 12px;
        border: 1px solid #d2d2d7;
    }
    
    /* Dataframes modernos */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* Reporte para impresión */
    .print-report {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    
    .print-header {
        text-align: center;
        margin-bottom: 30px;
        border-bottom: 2px solid #007aff;
        padding-bottom: 20px;
    }
    
    .print-section {
        margin-bottom: 25px;
        page-break-inside: avoid;
    }
    
    .print-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 12px;
    }
    
    .print-table th {
        background: #007aff;
        color: white;
        padding: 10px;
        text-align: left;
    }
    
    .print-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #e5e5e7;
    }
    
    .print-total {
        background: #f5f7fa;
        font-weight: 600;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

class DashboardPagos:
    def __init__(self):
        self.df = None
        self.doctores = []
        self.datos_cargados = False
        self.google_sheet_url = "https://docs.google.com/spreadsheets/d/1bCijCPK4hCX4v0jJ4KW7RtO1Vu7CDWDrn769OkBHpLU/edit?usp=sharing"
        self.columna_referidor = None

    def cargar_datos_google_sheets(self):
        """Cargar datos directamente desde Google Sheets sin autenticación"""
        try:
            # Convertir el URL de edición a URL de exportación CSV
            sheet_id = "1bCijCPK4hCX4v0jJ4KW7RtO1Vu7CDWDrn769OkBHpLU"
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            # Descargar los datos
            response = requests.get(csv_url)
            response.raise_for_status()
            
            # Leer el CSV
            self.df = pd.read_csv(BytesIO(response.content))

            # Estandarizar nombres de columnas
            self.df.columns = self.df.columns.str.strip().str.lower().str.replace(' ', '_')

            # Convertir columnas numéricas
            columnas_numericas = [
                'pago_por_seguro', 'pago_privado', 'laboratorio', 'gastos',
                'monto_a_pagar_por_tarifario', '10%_retencion', 'monto_total_a_pagar'
            ]
            
            for col in columnas_numericas:
                if col in self.df.columns:
                    try:
                        self.df[col] = self.df[col].astype(str)
                        self.df[col] = self.df[col].str.replace('$', '', regex=False)
                        self.df[col] = self.df[col].str.replace(',', '', regex=False)
                        self.df[col] = self.df[col].str.strip()
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
                    except Exception as e:
                        st.error(f"Error procesando columna {col}: {str(e)}")
                        self.df[col] = 0

            # Convertir fecha si existe la columna
            if 'fecha' in self.df.columns:
                self.df['fecha'] = pd.to_datetime(self.df['fecha'], errors='coerce')

            # Lista de doctores
            if 'doctor_a_pagar' in self.df.columns:
                self.doctores = sorted(self.df['doctor_a_pagar'].dropna().unique())

            self.datos_cargados = True
            return True

        except Exception as e:
            st.error(f"Error al cargar desde Google Sheets: {str(e)}")
            st.error("Asegúrate de que el Google Sheet esté configurado para acceso público")
            self.datos_cargados = False
            return False

    def detectar_columna_referidor(self):
        """Detectar automáticamente la columna que contiene el nombre del doctor referidor"""
        if self.df is None:
            return None
            
        posibles_nombres = ['doctor_referidor', 'referidor', 'doctor_referido', 
                           'medico_referidor', 'dr_referidor', 'referido_por', 'referidor_doctor']
        
        for col in self.df.columns:
            col_lower = col.lower()
            for posible in posibles_nombres:
                if posible in col_lower:
                    return col
        return None

    def procesar_pagos(self):
        """Procesar pagos según reglas establecidas"""
        if self.df is None:
            return

        self.df['pago_total_paciente'] = self.df['pago_por_seguro'].fillna(0) + self.df['pago_privado'].fillna(0)

        # Inicializar columnas
        columnas_resultado = [
            'pago_doctor', 'pago_referidor', 'retencion', 'retencion_10',
            'descuento_lab', 'descuento_gastos', 'cargo_por_ars',
            'costes', 'ingreso_clinica', 'monto_final_pago', 'rentabilidad'
        ]
        for col in columnas_resultado:
            self.df[col] = 0.0

        for idx, row in self.df.iterrows():
            try:
                pago_total = float(row.get('pago_total_paciente', 0) or 0)
                pago_doctor = 0.0
                pago_referidor = 0.0
                retencion = 0.0
                cargo_ars = 0.0

                # Cargo ARS
                pago_seguro_val = float(row.get('pago_por_seguro', 0) or 0)
                if pago_seguro_val > 0:
                    cargo_ars = pago_total * 0.10

                # Pago a referidor
                p_ref = str(row.get('paciente_refido', '')).strip().lower()
                p_ref = p_ref.replace('sí', 'sí')
                es_referido = bool(re.match(r'^(si|sí|s[ií]|yes|true|1)$', p_ref))
                if es_referido:
                    pago_referidor = pago_total * 0.10

                # Tipo de pago
                cobra_por_porcentaje = False
                if 'cobra_por_porcentaje' in self.df.columns and pd.notna(row.get('cobra_por_porcentaje')):
                    cobra_por_porcentaje = str(row.get('cobra_por_porcentaje')).strip().lower() in ['si', 'sí', 'yes', 'true', '1']

                if cobra_por_porcentaje:
                    porcentaje = 0.5
                    if '%_de_pago' in self.df.columns and pd.notna(row.get('%_de_pago')):
                        try:
                            porcentaje = float(str(row['%_de_pago']).replace('%', '').strip()) / 100
                        except:
                            porcentaje = 0.5

                    pago_doctor = pago_total * porcentaje
                    laboratorio = float(row.get('laboratorio', 0) or 0)
                    gastos = float(row.get('gastos', 0) or 0)
                    descuentos = laboratorio + gastos
                    pago_doctor = max(0, pago_doctor - descuentos - cargo_ars)
                    retencion = pago_doctor * 0.10
                    pago_doctor = pago_doctor - retencion
                    descuento_lab = laboratorio
                    descuento_gastos = gastos

                else:
                    pago_tarifario = float(row.get('monto_a_pagar_por_tarifario', 0) or 0)
                    pago_base = max(0, pago_tarifario - cargo_ars)
                    retencion = pago_base * 0.10
                    pago_doctor = pago_base - retencion
                    descuento_lab = 0.0
                    descuento_gastos = 0.0

                # Cálculos finales
                costes = retencion + descuento_lab + descuento_gastos + cargo_ars
                ingreso_clinica = pago_total - (pago_doctor + costes + pago_referidor)
                rentabilidad_pct = (ingreso_clinica / pago_total * 100) if pago_total > 0 else 0

                # Actualizar fila
                self.df.at[idx, 'pago_doctor'] = pago_doctor
                self.df.at[idx, 'pago_referidor'] = pago_referidor
                self.df.at[idx, 'retencion'] = retencion
                self.df.at[idx, 'retencion_10'] = retencion
                self.df.at[idx, 'descuento_lab'] = descuento_lab
                self.df.at[idx, 'descuento_gastos'] = descuento_gastos
                self.df.at[idx, 'cargo_por_ars'] = cargo_ars
                self.df.at[idx, 'costes'] = costes
                self.df.at[idx, 'ingreso_clinica'] = ingreso_clinica
                self.df.at[idx, 'monto_final_pago'] = pago_doctor
                self.df.at[idx, 'rentabilidad'] = rentabilidad_pct

            except Exception as e:
                continue

    def calcular_metricas_totales(self):
        """Calcular métricas totales para tarjetas (rentabilidad total como % ponderado)"""
        if self.df is None:
            return {}

        try:
            pago_total_paciente = self.df['pago_total_paciente'].sum() if 'pago_total_paciente' in self.df.columns else 0
            pago_doctor = self.df['pago_doctor'].sum() if 'pago_doctor' in self.df.columns else 0
            pago_referidor = self.df['pago_referidor'].sum() if 'pago_referidor' in self.df.columns else 0
            retencion = self.df['retencion'].sum() if 'retencion' in self.df.columns else 0
            laboratorio = self.df['laboratorio'].sum() if 'laboratorio' in self.df.columns and pd.api.types.is_numeric_dtype(self.df['laboratorio']) else 0
            gastos = self.df['gastos'].sum() if 'gastos' in self.df.columns and pd.api.types.is_numeric_dtype(self.df['gastos']) else 0
            cargo_ars = self.df['cargo_por_ars'].sum() if 'cargo_por_ars' in self.df.columns else 0
            ingreso_clinica_total = self.df['ingreso_clinica'].sum() if 'ingreso_clinica' in self.df.columns else 0
            costes_total = self.df['costes'].sum() if 'costes' in self.df.columns else 0

            # Rentabilidad total (% ponderado)
            rentabilidad_total_pct = (ingreso_clinica_total / pago_total_paciente * 100) if pago_total_paciente > 0 else 0

            metricas = {
                'total_ingresos': pago_total_paciente,
                'total_pagos_doctores': pago_doctor,
                'total_pagos_referidores': pago_referidor,
                'total_retenciones': retencion,
                'total_laboratorio': laboratorio,
                'total_gastos': gastos,
                'total_cargo_ars': cargo_ars,
                'total_costes': costes_total,
                'total_ingreso_clinica': ingreso_clinica_total,
                'total_rentabilidad': rentabilidad_total_pct,  # %
                'total_procedimientos': len(self.df),
                'doctores_unicos': len(self.doctores) if hasattr(self, 'doctores') else 0
            }
            return metricas
        except Exception as e:
            st.error(f"Error calculando métricas: {str(e)}")
            return {}

    def obtener_pagos_por_doctor(self):
        """Resumen de pagos por doctor"""
        if self.df is None or 'doctor_a_pagar' not in self.df.columns:
            return pd.DataFrame()

        try:
            pagos_doctor = self.df.groupby('doctor_a_pagar').agg({
                'pago_doctor': 'sum',
                'retencion': 'sum',
                'rentabilidad': 'mean',  # promedio % rentabilidad por doctor
                'ingreso_clinica': 'sum',
                'paciente': 'count'
            }).reset_index()

            pagos_doctor.columns = ['Doctor', 'Total a Pagar', 'Total Retenido', 'Rentabilidad % Promedio', 'Ingreso Clínica', 'N° Procedimientos']
            pagos_doctor['Promedio por Procedimiento'] = pagos_doctor['Total a Pagar'] / pagos_doctor['N° Procedimientos'].replace(0, 1)

            return pagos_doctor.sort_values('Total a Pagar', ascending=False)
        except Exception as e:
            st.error(f"Error obteniendo pagos por doctor: {str(e)}")
            return pd.DataFrame()

    def obtener_pagos_por_referidor(self):
        """Resumen de pagos por doctor referidor"""
        if self.df is None or 'doctor_referidor' not in self.df.columns or 'paciente_refido' not in self.df.columns:
            return pd.DataFrame()

        try:
            df_referidos = self.df[
                self.df['paciente_refido'].astype(str).str.lower().str.contains('si|sí|yes|true|1') &
                (self.df['pago_referidor'] > 0)
            ]
            if len(df_referidos) == 0:
                return pd.DataFrame()

            pagos_referidor = df_referidos.groupby('doctor_referidor').agg({
                'pago_referidor': 'sum',
                'pago_total_paciente': 'sum',
                'paciente': 'count'
            }).reset_index()

            pagos_referidor.columns = ['Doctor Referidor', 'Total a Pagar', 'Monto Total Referidos', 'N° Pacientes Referidos']
            pagos_referidor['Porcentaje Pagado'] = (pagos_referidor['Total a Pagar'] / pagos_referidor['Monto Total Referidos'] * 100).round(2)

            return pagos_referidor.sort_values('Total a Pagar', ascending=False)
        except Exception as e:
            st.error(f"Error obteniendo pagos por referidor: {str(e)}")
            return pd.DataFrame()

    def filtrar_por_fecha(self, fecha_inicio, fecha_fin):
        """Filtrar por rango de fechas"""
        if self.df is None or 'fecha' not in self.df.columns:
            return self.df
        try:
            mask = (self.df['fecha'] >= fecha_inicio) & (self.df['fecha'] <= fecha_fin)
            return self.df.loc[mask]
        except Exception as e:
            st.error(f"Error filtrando por fecha: {str(e)}")
            return self.df

    def generar_reporte_impresion(self, doctor_seleccionado, fecha_inicio, fecha_fin):
        """Generar reporte optimizado para impresión en hoja 8 1/2 x 11"""
        if self.df is None or 'doctor_a_pagar' not in self.df.columns:
            return ""
        
        try:
            # Filtrar datos
            df_filtrado = self.filtrar_por_fecha(fecha_inicio, fecha_fin)
            if doctor_seleccionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['doctor_a_pagar'] == doctor_seleccionado]
            
            if df_filtrado.empty:
                return ""
            
            # Agrupar por paciente y procedimiento
            reporte_agrupado = df_filtrado.groupby(['paciente', 'procedimiento']).agg({
                'pago_total_paciente': 'sum',
                'laboratorio': 'sum',
                'gastos': 'sum',
                'retencion_10': 'sum',
                'monto_final_pago': 'sum'
            }).reset_index()
            
            # Totales generales
            total_general = df_filtrado.agg({
                'pago_total_paciente': 'sum',
                'laboratorio': 'sum',
                'gastos': 'sum',
                'retencion_10': 'sum',
                'monto_final_pago': 'sum'
            })
            
            # Crear HTML para impresión
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reporte de Pagos - {doctor_seleccionado}</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        padding: 20px;
                        color: #333;
                        line-height: 1.4;
                    }}
                    .print-container {{
                        max-width: 800px;
                        margin: 0 auto;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 3px solid #007aff;
                        padding-bottom: 20px;
                    }}
                    .header h1 {{
                        color: #1d1d1f;
                        margin: 0 0 10px 0;
                        font-size: 28px;
                    }}
                    .header-info {{
                        display: flex;
                        justify-content: space-between;
                        margin-top: 15px;
                        font-size: 14px;
                        color: #666;
                    }}
                    .doctor-info {{
                        background: #f5f7fa;
                        padding: 20px;
                        border-radius: 12px;
                        margin-bottom: 25px;
                    }}
                    .summary-grid {{
                        display: grid;
                        grid-template-columns: repeat(4, 1fr);
                        gap: 15px;
                        margin-bottom: 25px;
                    }}
                    .summary-card {{
                        background: white;
                        padding: 15px;
                        border-radius: 12px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .summary-card h3 {{
                        margin: 0;
                        font-size: 14px;
                        color: #666;
                        font-weight: 500;
                    }}
                    .summary-card .value {{
                        font-size: 20px;
                        font-weight: 600;
                        color: #007aff;
                        margin: 8px 0 0 0;
                    }}
                    .table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        font-size: 12px;
                    }}
                    .table th {{
                        background: #007aff;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: 500;
                    }}
                    .table td {{
                        padding: 10px;
                        border-bottom: 1px solid #e5e5e7;
                    }}
                    .table tr.total-row {{
                        background: #f5f7fa;
                        font-weight: 600;
                    }}
                    .table tr.total-row td {{
                        border-top: 2px solid #007aff;
                        font-size: 13px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 40px;
                        color: #666;
                        font-size: 12px;
                        border-top: 1px solid #e5e5e7;
                        padding-top: 20px;
                    }}
                    @media print {{
                        body {{ padding: 15px; }}
                        .summary-grid {{ page-break-inside: avoid; }}
                        .table {{ page-break-inside: avoid; }}
                    }}
                </style>
            </head>
            <body>
                <div class="print-container">
                    <div class="header">
                        <h1>🏥 Reporte de Pagos a Doctores</h1>
                        <div class="header-info">
                            <div>Doctor: <strong>{doctor_seleccionado}</strong></div>
                            <div>Período: <strong>{fecha_inicio} a {fecha_fin}</strong></div>
                            <div>Generado: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong></div>
                        </div>
                    </div>
                    
                    <div class="summary-grid">
                        <div class="summary-card">
                            <h3>Total Procedimientos</h3>
                            <div class="value">{len(df_filtrado)}</div>
                        </div>
                        <div class="summary-card">
                            <h3>Total a Pagar</h3>
                            <div class="value">${total_general['monto_final_pago']:,.2f}</div>
                        </div>
                        <div class="summary-card">
                            <h3>Total Retenido</h3>
                            <div class="value">${total_general['retencion_10']:,.2f}</div>
                        </div>
                        <div class="summary-card">
                            <h3>Total Gastos</h3>
                            <div class="value">${total_general['laboratorio'] + total_general['gastos']:,.2f}</div>
                        </div>
                    </div>
                    
                    <h2>Detalle por Paciente y Procedimiento</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Paciente</th>
                                <th>Procedimiento</th>
                                <th>Ingreso Total</th>
                                <th>Gastos</th>
                                <th>Retención</th>
                                <th>Total a Pagar</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            # Agregar filas de datos
            for _, row in reporte_agrupado.iterrows():
                html_content += f"""
                            <tr>
                                <td>{row['paciente']}</td>
                                <td>{row['procedimiento']}</td>
                                <td>${row['pago_total_paciente']:,.2f}</td>
                                <td>${row['laboratorio'] + row['gastos']:,.2f}</td>
                                <td>${row['retencion_10']:,.2f}</td>
                                <td>${row['monto_final_pago']:,.2f}</td>
                            </tr>
                """
            
            # Agregar totales
            html_content += f"""
                            <tr class="total-row">
                                <td colspan="2"><strong>TOTAL GENERAL</strong></td>
                                <td><strong>${total_general['pago_total_paciente']:,.2f}</strong></td>
                                <td><strong>${total_general['laboratorio'] + total_general['gastos']:,.2f}</strong></td>
                                <td><strong>${total_general['retencion_10']:,.2f}</strong></td>
                                <td><strong>${total_general['monto_final_pago']:,.2f}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div class="footer">
                        <p>Reporte generado automáticamente por Sistema de Pagos Clínica Padilla</p>
                        <p>© 2024 Clínica Padilla - Todos los derechos reservados</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            st.error(f"Error generando reporte de impresión: {str(e)}")
            return ""

    def mostrar_dashboard(self):
        """Render del dashboard"""
        st.markdown('<h1 class="main-header">🏥 Dashboard de Pagos a Doctores</h1>', unsafe_allow_html=True)

        # Cargar datos al iniciar
        if not self.datos_cargados:
            with st.spinner('Cargando datos desde Google Sheets...'):
                if not self.cargar_datos_google_sheets():
                    st.error("No se pudieron cargar los datos desde Google Sheets.")
                    st.info("""
                    **Solución de problemas:**
                    1. Asegúrate de que el Google Sheet esté configurado para acceso público
                    2. Ve a 'Compartir' > 'Configuración de acceso general' > 'Cualquier persona con el enlace'
                    3. Selecciona 'Lector' como nivel de acceso
                    """)
                    return
                self.procesar_pagos()

        # Sidebar
        with st.sidebar:
            doctor_seleccionado = st.selectbox(
                "Seleccionar Doctor",
                options=["Todos"] + self.doctores
            )

            col1, col2 = st.columns(2)
            with col1:
                fecha_min = self.df['fecha'].min().date() if 'fecha' in self.df.columns and not self.df.empty else datetime.now().date()
                fecha_inicio = st.date_input("Fecha inicio", value=fecha_min)
            with col2:
                fecha_max = self.df['fecha'].max().date() if 'fecha' in self.df.columns and not self.df.empty else datetime.now().date()
                fecha_fin = st.date_input("Fecha fin", value=fecha_max)

            if st.button("🔄 Recargar Datos", use_container_width=True):
                with st.spinner('Recargando datos desde Google Sheets...'):
                    if self.cargar_datos_google_sheets():
                        self.procesar_pagos()
                        st.success("Datos recargados correctamente")
                    else:
                        st.error("Error al recargar los datos")

        # Aplicar filtros
        df_filtrado = self.filtrar_por_fecha(
            pd.to_datetime(fecha_inicio),
            pd.to_datetime(fecha_fin)
        )
        if doctor_seleccionado != "Todos" and 'doctor_a_pagar' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['doctor_a_pagar'] == doctor_seleccionado]

        # Métricas principales
        metricas = self.calcular_metricas_totales()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Ingresos Totales</h3>
                <h2 class="positive-value">${metricas.get('total_ingresos', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Pagos a Doctores</h3>
                <h2 class="negative-value">${metricas.get('total_pagos_doctores', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Rentabilidad</h3>
                <h2 class="positive-value">{metricas.get('total_rentabilidad', 0):.2f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Procedimientos</h3>
                <h2>{metricas.get('total_procedimientos', 0)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Segunda fila de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Pagos a Referidores</h3>
                <h2 class="negative-value">${metricas.get('total_pagos_referidores', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Retenciones</h3>
                <h2 class="positive-value">${metricas.get('total_retenciones', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Gastos Laboratorio</h3>
                <h2 class="negative-value">${metricas.get('total_laboratorio', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Cargo ARS</h3>
                <h2 class="negative-value">${metricas.get('total_cargo_ars', 0):,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)

        # Pestañas para diferentes vistas
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Resumen", "👨‍⚕️ Doctores", "📈 Gráficos", "🔍 Transacciones", "🖨️ Reportes"])

        with tab1:
            st.markdown('<div class="section-header">📊 Resumen General</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Distribución de Gastos**")
                gastos = {
                    'Pagos Doctores': metricas.get('total_pagos_doctores', 0),
                    'Pagos Referidores': metricas.get('total_pagos_referidores', 0),
                    'Gastos Laboratorio': metricas.get('total_laboratorio', 0),
                    'Retenciones': metricas.get('total_retenciones', 0),
                    'Cargo ARS': metricas.get('total_cargo_ars', 0)
                }
                fig_gastos = px.pie(
                    values=list(gastos.values()),
                    names=list(gastos.keys()),
                    title="Distribución de Gastos",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_gastos.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_gastos, use_container_width=True)
            
            with col2:
                st.write("**Evolución de Ingresos vs Gastos**")
                if 'fecha' in self.df.columns:
                    try:
                        diarios = self.df.groupby('fecha').agg({
                            'pago_total_paciente': 'sum',
                            'pago_doctor': 'sum',
                            'pago_referidor': 'sum'
                        }).reset_index()

                        fig_evolucion = go.Figure()
                        fig_evolucion.add_trace(go.Scatter(
                            x=diarios['fecha'], 
                            y=diarios['pago_total_paciente'], 
                            mode='lines', 
                            name='Ingresos',
                            line=dict(color='#007aff', width=3)
                        ))
                        fig_evolucion.add_trace(go.Scatter(
                            x=diarios['fecha'], 
                            y=diarios['pago_doctor'], 
                            mode='lines', 
                            name='Pagos Doctores',
                            line=dict(color='#ff9500', width=3)
                        ))
                        fig_evolucion.add_trace(go.Scatter(
                            x=diarios['fecha'], 
                            y=diarios['pago_referidor'], 
                            mode='lines', 
                            name='Pagos Referidores',
                            line=dict(color='#34c759', width=3)
                        ))

                        fig_evolucion.update_layout(
                            title="Evolución Diaria de Ingresos y Gastos",
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#1d1d1f')
                        )
                        st.plotly_chart(fig_evolucion, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creando gráfico de evolución: {str(e)}")

        with tab2:
            st.markdown('<div class="section-header">👨‍⚕️ Pagos por Doctor</div>', unsafe_allow_html=True)
            
            pagos_doctor = self.obtener_pagos_por_doctor()
            
            if not pagos_doctor.empty:
                fig_barras = px.bar(
                    pagos_doctor.head(10),
                    x='Doctor',
                    y='Total a Pagar',
                    title="Top 10 Doctores por Monto a Pagar",
                    color='Total a Pagar',
                    color_continuous_scale='Blues'
                )
                fig_barras.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_barras, use_container_width=True)
                
                st.dataframe(
                    pagos_doctor.style.format({
                        'Total a Pagar': '${:,.2f}',
                        'Total Retenido': '${:,.2f}',
                        'Ingreso Clínica': '${:,.2f}',
                        'Rentabilidad % Promedio': '{:.2f}%',
                        'Promedio por Procedimiento': '${:,.2f}'
                    }),
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("No hay datos de pagos por doctor")
            
            st.markdown('<div class="section-header">🔄 Pagos a Referidores</div>', unsafe_allow_html=True)
            pagos_referidor = self.obtener_pagos_por_referidor()
            
            if not pagos_referidor.empty:
                st.dataframe(
                    pagos_referidor.style.format({
                        'Total a Pagar': '${:,.2f}',
                        'Monto Total Referidos': '${:,.2f}',
                        'Porcentaje Pagado': '{:.2f}%'
                    }),
                    use_container_width=True
                )
                st.info("💡 Los pagos a referidores se calculan como el 10% del monto total pagado por el paciente")
            else:
                st.info("No hay datos de pagos a referidores")

        with tab3:
            st.markdown('<div class="section-header">📈 Análisis Gráfico</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'procedimiento' in self.df.columns:
                    try:
                        rentabilidad_procedimiento = self.df.groupby('procedimiento').agg({
                            'rentabilidad': 'mean',
                            'paciente': 'count'
                        }).reset_index()

                        rentabilidad_procedimiento = rentabilidad_procedimiento[rentabilidad_procedimiento['paciente'] >= 3]

                        if len(rentabilidad_procedimiento) > 0:
                            fig_rentabilidad = px.bar(
                                rentabilidad_procedimiento.sort_values('rentabilidad', ascending=False).head(10),
                                x='procedimiento',
                                y='rentabilidad',
                                title="Top 10 Procedimientos más Rentables",
                                color='rentabilidad',
                                color_continuous_scale='Greens'
                            )
                            fig_rentabilidad.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig_rentabilidad, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creando gráfico de rentabilidad: {str(e)}")
            
            with col2:
                if 'cobra_por_porcentaje' in self.df.columns:
                    try:
                        tipo_pago_counts = self.df['cobra_por_porcentaje'].value_counts()
                        fig_tipo_pago = px.pie(
                            values=tipo_pago_counts.values,
                            names=tipo_pago_counts.index,
                            title="Distribución de Tipo de Pago",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_tipo_pago.update_traces(textposition='inside', textinfo='percent+label')
                        fig_tipo_pago.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_tipo_pago, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error creando gráfico de tipos de pago: {str(e)}")

        with tab4:
            st.markdown('<div class="section-header">🔍 Detalle de Transacciones</div>', unsafe_allow_html=True)

            columnas_mostrar = [
                'fecha', 'paciente', 'procedimiento', 'paciente_asegurado',
                'pago_por_seguro', 'pago_privado', 'pago_total_paciente',
                'paciente_refido', 'laboratorio', 'gastos',
                'doctor_a_pagar', 'cobra_por_porcentaje', '%_de_pago',
                'monto_a_pagar_por_tarifario', 'cargo_por_ars',
                'descuento_lab', 'descuento_gastos', 'retencion_10',
                'costes', 'pago_doctor', 'pago_referidor',
                'ingreso_clinica', 'retencion', 'monto_final_pago', 'rentabilidad'
            ]

            columnas_disponibles = [col for col in columnas_mostrar if col in df_filtrado.columns]

            st.dataframe(
                df_filtrado[columnas_disponibles].style.format({
                    'pago_por_seguro': '${:,.2f}',
                    'pago_privado': '${:,.2f}',
                    'pago_total_paciente': '${:,.2f}',
                    'laboratorio': '${:,.2f}',
                    'gastos': '${:,.2f}',
                    'monto_a_pagar_por_tarifario': '${:,.2f}',
                    'cargo_por_ars': '${:,.2f}',
                    'descuento_lab': '${:,.2f}',
                    'descuento_gastos': '${:,.2f}',
                    'retencion_10': '${:,.2f}',
                    'costes': '${:,.2f}',
                    'pago_doctor': '${:,.2f}',
                    'pago_referidor': '${:,.2f}',
                    'ingreso_clinica': '${:,.2f}',
                    'retencion': '${:,.2f}',
                    'monto_final_pago': '${:,.2f}',
                    'rentabilidad': '{:.2f}%'
                }),
                use_container_width=True,
                height=400
            )

            csv = df_filtrado[columnas_disponibles].to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos (CSV)",
                data=csv,
                file_name="pagos_doctores.csv",
                mime="text/csv",
                use_container_width=True
            )

        with tab5:
            st.markdown('<div class="section-header">📊 Reportes de Pagos por Doctor</div>', unsafe_allow_html=True)
            
            # Filtros específicos para el reporte
            col1, col2, col3 = st.columns(3)
            with col1:
                doctor_reporte = st.selectbox(
                    "Seleccionar Doctor para Reporte",
                    options=["Todos"] + self.doctores,
                    key="doctor_reporte"
                )
            
            with col2:
                fecha_inicio_reporte = st.date_input(
                    "Fecha inicio reporte",
                    value=fecha_inicio,
                    key="fecha_inicio_reporte"
                )
            
            with col3:
                fecha_fin_reporte = st.date_input(
                    "Fecha fin reporte", 
                    value=fecha_fin,
                    key="fecha_fin_reporte"
                )
            
            # Generar reporte para impresión
            html_reporte = self.generar_reporte_impresion(
                doctor_reporte,
                pd.to_datetime(fecha_inicio_reporte),
                pd.to_datetime(fecha_fin_reporte)
            )
            
            if html_reporte:
                # Vista previa del reporte
                st.markdown("### 📋 Vista Previa del Reporte")
                st.components.v1.html(html_reporte, height=800, scrolling=True)
                
                # Botones de descarga
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📄 Descargar Reporte (HTML)",
                        data=html_reporte,
                        file_name=f"reporte_{doctor_reporte}_{fecha_inicio_reporte}_a_{fecha_fin_reporte}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                
                with col2:
                    st.download_button(
                        label="📊 Descargar para Imprimir",
                        data=html_reporte,
                        file_name=f"reporte_{doctor_reporte}_{fecha_inicio_reporte}_a_{fecha_fin_reporte}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                
                st.info("""
                **💡 Para imprimir:**
                1. Descarga el reporte en HTML
                2. Abre el archivo descargado
                3. Usa la opción de imprimir de tu navegador (Ctrl+P)
                4. Ajusta la configuración de impresión a hoja 8 1/2 x 11
                """)
                
            else:
                st.info("No hay datos para generar el reporte con los filtros seleccionados")

# Ejecutar la aplicación
if __name__ == "__main__":
    dashboard = DashboardPagos()
    dashboard.mostrar_dashboard()