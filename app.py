"""
Sales Analytics Pro - Versión con Debug
=======================================
"""

from flask import Flask, request, render_template_string, redirect, url_for, session, flash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import secrets
from datetime import datetime
import os
import numpy as np
import io
import traceback  # <--- AGREGAR ESTO

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['DEBUG'] = True  # <--- AGREGAR ESTO

# ============================================
# SPLASH SCREEN
# ============================================
SPLASH_HTML = '''...'''  # (mantén el mismo código)

# ============================================
# PÁGINA PRINCIPAL
# ============================================
INDEX_HTML = '''...'''  # (mantén el mismo código)

# ============================================
# DASHBOARD TEMPLATE
# ============================================
DASHBOARD_HTML = '''...'''  # (mantén el mismo código)

# ============================================
# ALMACENAMIENTO EN MEMORIA
# ============================================
sessions = {}

# ============================================
# FUNCIONES DE ANÁLISIS - VERSIÓN CORREGIDA
# ============================================

def detectar_columnas_ventas(df):
    """Detecta columnas importantes en el DataFrame"""
    cols = {
        'ventas': None,
        'fecha': None,
        'producto': None,
        'cliente': None,
        'region': None,
        'cantidad': None
    }
    
    print("=== DETECTANDO COLUMNAS ===")
    print(f"Columnas disponibles: {list(df.columns)}")
    
    # Buscar columna de ventas
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['venta', 'sales', 'total', 'monto', 'amount', 'price', 'precio', 'revenue']):
            cols['ventas'] = col
            print(f"✓ Columna de ventas detectada: {col}")
            break
    
    # Si no encuentra, tomar la primera columna numérica
    if not cols['ventas']:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cols['ventas'] = numeric_cols[0]
            print(f"✓ Usando primera columna numérica como ventas: {cols['ventas']}")
    
    # Buscar columna de fecha
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['fecha', 'date', 'tiempo', 'time', 'dia', 'mes', 'year']):
            cols['fecha'] = col
            print(f"✓ Columna de fecha detectada: {col}")
            break
    
    return cols

def obtener_metricas(df, cols_detectadas):
    """Calcula métricas básicas"""
    metrics = []
    
    try:
        # Total de registros
        metrics.append({
            'label': '📊 Total Registros',
            'value': f'{len(df):,}',
            'sub': f'{len(df.columns)} columnas'
        })
        
        # Ventas totales
        if cols_detectadas['ventas'] and cols_detectadas['ventas'] in df.columns:
            ventas_col = cols_detectadas['ventas']
            # Asegurar que sea numérico
            df[ventas_col] = pd.to_numeric(df[ventas_col], errors='coerce')
            total_ventas = df[ventas_col].sum()
            avg_ventas = df[ventas_col].mean()
            metrics.append({
                'label': '💰 Ventas Totales',
                'value': f'${total_ventas:,.0f}' if not pd.isna(total_ventas) else '$0',
                'sub': f'Promedio: ${avg_ventas:,.0f}' if not pd.isna(avg_ventas) else '$0'
            })
        
        # Productos únicos
        if cols_detectadas['producto'] and cols_detectadas['producto'] in df.columns:
            n_productos = df[cols_detectadas['producto']].nunique()
            metrics.append({
                'label': '🏷️ Productos',
                'value': f'{n_productos:,}',
                'sub': 'únicos'
            })
        
        # Clientes únicos
        if cols_detectadas['cliente'] and cols_detectadas['cliente'] in df.columns:
            n_clientes = df[cols_detectadas['cliente']].nunique()
            metrics.append({
                'label': '👥 Clientes',
                'value': f'{n_clientes:,}',
                'sub': 'únicos'
            })
            
    except Exception as e:
        print(f"Error en obtener_metricas: {e}")
    
    # Asegurar que siempre tengamos 4 métricas
    while len(metrics) < 4:
        metrics.append({
            'label': '📊 Información',
            'value': 'Cargando...',
            'sub': ''
        })
    
    return metrics[:4]

# ============================================
# RUTAS - VERSIÓN CORREGIDA
# ============================================

@app.route('/')
def splash():
    return render_template_string(SPLASH_HTML)

@app.route('/main')
def main():
    return render_template_string(INDEX_HTML)

@app.route('/sample')
def sample():
    """Carga datos de ejemplo"""
    try:
        print("=== CARGANDO DATOS DE EJEMPLO ===")
        
        # Crear datos de ejemplo
        np.random.seed(42)
        n = 100
        
        df = pd.DataFrame({
            'Fecha': pd.date_range(start='2024-01-01', periods=n, freq='D'),
            'Producto': np.random.choice(['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Teclado', 'Mouse'], n),
            'Categoría': np.random.choice(['Electrónica', 'Computación', 'Accesorios'], n),
            'Ventas': np.random.uniform(100, 2000, n).round(2),
            'Cantidad': np.random.randint(1, 10, n),
            'Cliente': np.random.choice(['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D', 'Particular'], n),
            'Región': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste', 'Centro'], n)
        })
        
        print(f"DataFrame creado: {df.shape}")
        print(f"Columnas: {list(df.columns)}")
        
        session_id = secrets.token_hex(8)
        cols_detectadas = detectar_columnas_ventas(df)
        metrics = obtener_metricas(df, cols_detectadas)
        
        sessions[session_id] = {
            'df': df,
            'filename': 'datos_ejemplo.csv',
            'cols_detectadas': cols_detectadas,
            'metrics': metrics,
            'rows': len(df),
            'columns': len(df.columns),
            'nulos': int(df.isnull().sum().sum())
        }
        
        print(f"✓ Sesión creada: {session_id}")
        print(f"✓ Métricas: {metrics}")
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        print(f"❌ ERROR en sample: {e}")
        traceback.print_exc()
        flash(f'Error al cargar datos de ejemplo: {str(e)}', 'error')
        return redirect(url_for('main'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('main'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nombre de archivo vacío', 'error')
        return redirect(url_for('main'))
    
    try:
        print(f"=== PROCESANDO ARCHIVO: {file.filename} ===")
        
        # Leer archivo
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file)
            print("✓ Archivo CSV leído")
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
            print("✓ Archivo Excel leído")
        elif file.filename.lower().endswith('.json'):
            df = pd.read_json(file)
            print("✓ Archivo JSON leído")
        else:
            flash('Formato no soportado. Usa CSV, Excel o JSON', 'error')
            return redirect(url_for('main'))
        
        print(f"✓ DataFrame shape: {df.shape}")
        print(f"✓ Columnas: {list(df.columns)}")
        
        # Validar
        if len(df) == 0:
            flash('El archivo está vacío', 'error')
            return redirect(url_for('main'))
        
        # Limpiar nombres de columnas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Detectar columnas
        cols_detectadas = detectar_columnas_ventas(df)
        metrics = obtener_metricas(df, cols_detectadas)
        
        # Crear sesión
        session_id = secrets.token_hex(8)
        sessions[session_id] = {
            'df': df,
            'filename': file.filename,
            'cols_detectadas': cols_detectadas,
            'metrics': metrics,
            'rows': len(df),
            'columns': len(df.columns),
            'nulos': int(df.isnull().sum().sum())
        }
        
        print(f"✓ Sesión creada: {session_id}")
        print(f"✓ Redirigiendo a dashboard...")
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        print(f"❌ ERROR en upload: {e}")
        traceback.print_exc()
        flash(f'Error al procesar el archivo: {str(e)}', 'error')
        return redirect(url_for('main'))

@app.route('/dashboard/<session_id>/<viz_type>')
def dashboard(session_id, viz_type):
    if session_id not in sessions:
        print(f"❌ Sesión no encontrada: {session_id}")
        return redirect(url_for('main'))
    
    try:
        session_data = sessions[session_id]
        df = session_data['df']
        cols_detectadas = session_data['cols_detectadas']
        
        print(f"=== DASHBOARD: {viz_type} ===")
        print(f"Sesión: {session_id}")
        print(f"Archivo: {session_data['filename']}")
        
        # Generar visualización según tipo
        viz_content = ''
        viz_title = ''
        
        if viz_type == 'resumen':
            viz_title = '📊 Dashboard Resumen'
            viz_content = '''
            <div style="text-align: center; padding: 50px;">
                <h3 style="color: #666;">📊 Visualización en desarrollo</h3>
                <p style="color: #999;">Próximamente: dashboard interactivo</p>
            </div>
            '''
        elif viz_type == 'datos':
            viz_title = '📋 Vista de Datos'
            viz_content = f'''
            <div class="table-wrapper">
                {df.head(20).to_html(classes='table', border=0, index=False)}
            </div>
            <p style="text-align: center; margin-top: 20px; color: #666;">
                Mostrando 20 de {len(df)} registros
            </p>
            '''
        else:
            viz_title = '📊 Visualización'
            viz_content = '''
            <div style="text-align: center; padding: 50px;">
                <h3 style="color: #666;">📊 Visualización no disponible</h3>
                <p style="color: #999;">Esta funcionalidad estará disponible pronto</p>
            </div>
            '''
        
        return render_template_string(
            DASHBOARD_HTML,
            session_id=session_id,
            filename=session_data['filename'],
            rows=session_data['rows'],
            metrics=session_data['metrics'],
            viz=viz_type,
            viz_title=viz_title,
            viz_content=viz_content,
            timestamp=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
    except Exception as e:
        print(f"❌ ERROR en dashboard: {e}")
        traceback.print_exc()
        flash(f'Error al mostrar dashboard: {str(e)}', 'error')
        return redirect(url_for('main'))

# ============================================
# INICIAR APLICACIÓN
# ============================================
if __name__ == '__main__':
    print("="*60)
    print("📊 SALES ANALYTICS PRO - MODO DEBUG")
    print("="*60)
    print("🚀 Servidor: http://localhost:5000")
    print("📁 Datos de ejemplo: http://localhost:5000/sample")
    print("⚠️  Los errores se mostrarán en la terminal")
    print("="*60)
    
    # Abrir navegador
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    # Ejecutar en modo debug
    app.run(host='0.0.0.0', port=5000, debug=True)
