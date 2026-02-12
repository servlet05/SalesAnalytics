"""
Sales Analytics Pro - Versión Corregida
=======================================
Aplicación web para análisis de ventas
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

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ============================================
# SPLASH SCREEN
# ============================================
SPLASH_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics Pro</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .splash {
            text-align: center;
            animation: fadeIn 0.8s ease forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        h1 { font-size: 48px; margin-bottom: 16px; }
        .progress {
            width: 200px;
            height: 4px;
            background: rgba(255,255,255,0.2);
            margin: 30px auto;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-bar {
            width: 100%;
            height: 100%;
            background: white;
            animation: progress 2s linear forwards;
        }
        @keyframes progress {
            from { width: 0%; }
            to { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="splash">
        <h1>📊 SALES ANALYTICS PRO</h1>
        <p style="font-size: 20px; opacity: 0.9;">Análisis inteligente de ventas</p>
        <div class="progress">
            <div class="progress-bar"></div>
        </div>
        <p style="margin-top: 20px;">inicializando...</p>
    </div>
    <script>
        setTimeout(() => { window.location.href = "/main"; }, 2000);
    </script>
</body>
</html>
'''

# ============================================
# PÁGINA PRINCIPAL
# ============================================
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics Pro - Cargar Archivo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 600px;
            width: 100%;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f3f0ff;
        }
        .upload-icon {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 10px;
        }
        .file-input {
            display: none;
        }
        .file-label {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            display: inline-block;
            margin-top: 20px;
            border: none;
            font-size: 16px;
        }
        .formats {
            margin-top: 20px;
            color: #999;
            font-size: 14px;
        }
        .loading {
            display: none;
            margin-top: 20px;
            color: #667eea;
        }
        .error {
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Sales Analytics Pro</h1>
        <p class="subtitle">Sube tu archivo de ventas para análisis instantáneo</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="error" style="display: block; background: {{ '#ff4444' if category == 'error' else '#00C851' }};">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data" action="/upload" id="uploadForm">
            <div class="upload-area" onclick="document.getElementById('file').click()">
                <div class="upload-icon">📁</div>
                <p style="color: #333;">Arrastra tu archivo o haz clic aquí</p>
                <input type="file" name="file" id="file" class="file-input" accept=".csv,.xlsx,.xls,.json" required>
                <label for="file" class="file-label">Seleccionar archivo</label>
                <div class="formats">
                    Formatos soportados: CSV, Excel, JSON
                </div>
            </div>
            <div class="loading" id="loading">
                ⚙️ Procesando archivo...
            </div>
        </form>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p style="font-size: 14px;">
                <a href="/sample" style="color: #667eea; text-decoration: none;">📊 Probar con datos de ejemplo</a>
            </p>
        </div>
    </div>
    
    <script>
        document.getElementById('file').addEventListener('change', function() {
            if (this.files.length > 0) {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('uploadForm').submit();
            }
        });
    </script>
</body>
</html>
'''

# ============================================
# DASHBOARD TEMPLATE
# ============================================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - {{ filename }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .file-info {
            background: #f8f9fa;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            color: #666;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 14px;
            margin-left: 15px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .metric-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }
        .metric-sub {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .menu {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .menu-item {
            padding: 10px 20px;
            border-radius: 20px;
            text-decoration: none;
            color: #666;
            background: #f8f9fa;
            transition: all 0.3s;
        }
        .menu-item:hover, .menu-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .viz-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .viz-title {
            font-size: 20px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        .table-wrapper {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="brand">📊 SALES ANALYTICS PRO</span>
            <div>
                <span class="file-info">{{ filename }} · {{ rows }} registros</span>
                <a href="/main" class="btn">Nuevo análisis</a>
            </div>
        </div>
        
        <div class="metrics">
            {% for metric in metrics %}
            <div class="metric-card">
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-value">{{ metric.value }}</div>
                {% if metric.sub %}
                <div class="metric-sub">{{ metric.sub }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <div class="menu">
            <a href="/dashboard/{{ session_id }}/resumen" class="menu-item {% if viz == 'resumen' %}active{% endif %}">📊 Dashboard</a>
            <a href="/dashboard/{{ session_id }}/ventas_tiempo" class="menu-item {% if viz == 'ventas_tiempo' %}active{% endif %}">📈 Ventas por Tiempo</a>
            <a href="/dashboard/{{ session_id }}/top_productos" class="menu-item {% if viz == 'top_productos' %}active{% endif %}">🏆 Top Productos</a>
            <a href="/dashboard/{{ session_id }}/ventas_categoria" class="menu-item {% if viz == 'ventas_categoria' %}active{% endif %}">📦 Por Categoría</a>
            <a href="/dashboard/{{ session_id }}/ventas_region" class="menu-item {% if viz == 'ventas_region' %}active{% endif %}">🌍 Por Región</a>
            <a href="/dashboard/{{ session_id }}/clientes" class="menu-item {% if viz == 'clientes' %}active{% endif %}">👥 Clientes</a>
            <a href="/dashboard/{{ session_id }}/datos" class="menu-item {% if viz == 'datos' %}active{% endif %}">📋 Ver Datos</a>
        </div>
        
        <div class="viz-container">
            <div class="viz-title">{{ viz_title }}</div>
            <div class="viz-content">
                {{ viz_content|safe }}
            </div>
        </div>
        
        <div class="footer">
            Sales Analytics Pro · {{ timestamp }}
        </div>
    </div>
</body>
</html>
'''

# ============================================
# ALMACENAMIENTO EN MEMORIA
# ============================================
sessions = {}

# ============================================
# FUNCIONES DE ANÁLISIS
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
    
    # Buscar columna de ventas
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['venta', 'sales', 'total', 'monto', 'amount', 'price', 'precio', 'revenue']):
            cols['ventas'] = col
            break
    
    # Si no encuentra, tomar la primera columna numérica
    if not cols['ventas']:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cols['ventas'] = numeric_cols[0]
    
    # Buscar columna de fecha
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['fecha', 'date', 'tiempo', 'time', 'dia', 'mes', 'year']):
            cols['fecha'] = col
            break
    
    # Buscar columna de producto
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['producto', 'product', 'item', 'articulo', 'nombre']):
            cols['producto'] = col
            break
    
    # Buscar columna de cliente
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['cliente', 'customer', 'buyer', 'comprador']):
            cols['cliente'] = col
            break
    
    # Buscar columna de región
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['region', 'pais', 'country', 'ciudad', 'city', 'estado', 'state']):
            cols['region'] = col
            break
    
    # Buscar columna de cantidad
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['cantidad', 'quantity', 'qty', 'unidades']):
            cols['cantidad'] = col
            break
    
    return cols

def obtener_metricas(df, cols_detectadas):
    """Calcula métricas básicas"""
    metrics = []
    
    # Total de registros
    metrics.append({
        'label': '📊 Total Registros',
        'value': f'{len(df):,}',
        'sub': f'{len(df.columns)} columnas'
    })
    
    # Ventas totales
    if cols_detectadas['ventas']:
        try:
            total_ventas = df[cols_detectadas['ventas']].sum()
            avg_ventas = df[cols_detectadas['ventas']].mean()
            metrics.append({
                'label': '💰 Ventas Totales',
                'value': f'${total_ventas:,.0f}',
                'sub': f'Promedio: ${avg_ventas:,.0f}'
            })
        except:
            pass
    
    # Productos únicos
    if cols_detectadas['producto']:
        try:
            n_productos = df[cols_detectadas['producto']].nunique()
            metrics.append({
                'label': '🏷️ Productos',
                'value': f'{n_productos:,}',
                'sub': 'únicos'
            })
        except:
            pass
    
    # Clientes únicos
    if cols_detectadas['cliente']:
        try:
            n_clientes = df[cols_detectadas['cliente']].nunique()
            metrics.append({
                'label': '👥 Clientes',
                'value': f'{n_clientes:,}',
                'sub': 'únicos'
            })
        except:
            pass
    
    return metrics[:4]

def generar_grafico_ventas_tiempo(df, cols_detectadas):
    """Genera gráfico de ventas por tiempo"""
    if not cols_detectadas['fecha'] or not cols_detectadas['ventas']:
        return None
    
    try:
        df_temp = df.copy()
        df_temp[cols_detectadas['fecha']] = pd.to_datetime(df_temp[cols_detectadas['fecha']])
        df_temp['fecha_simple'] = df_temp[cols_detectadas['fecha']].dt.date
        
        ventas_diarias = df_temp.groupby('fecha_simple')[cols_detectadas['ventas']].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ventas_diarias['fecha_simple'],
            y=ventas_diarias[cols_detectadas['ventas']],
            mode='lines+markers',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='📈 Ventas en el Tiempo',
            xaxis_title='Fecha',
            yaxis_title='Ventas ($)',
            template='plotly_white',
            height=500
        )
        
        return fig
    except:
        return None

def generar_grafico_top_productos(df, cols_detectadas):
    """Genera gráfico de top productos"""
    if not cols_detectadas['producto'] or not cols_detectadas['ventas']:
        return None
    
    try:
        top = df.groupby(cols_detectadas['producto'])[cols_detectadas['ventas']].sum().nlargest(10).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top[cols_detectadas['producto']],
            x=top[cols_detectadas['ventas']],
            orientation='h',
            marker_color='#764ba2',
            text=top[cols_detectadas['ventas']],
            texttemplate='$%{x:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🏆 Top 10 Productos',
            xaxis_title='Ventas ($)',
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=150)
        )
        
        return fig
    except:
        return None

def generar_grafico_ventas_region(df, cols_detectadas):
    """Genera gráfico de ventas por región"""
    if not cols_detectadas['region'] or not cols_detectadas['ventas']:
        return None
    
    try:
        regiones = df.groupby(cols_detectadas['region'])[cols_detectadas['ventas']].sum().reset_index()
        regiones = regiones.sort_values(cols_detectadas['ventas'], ascending=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=regiones[cols_detectadas['region']],
            x=regiones[cols_detectadas['ventas']],
            orientation='h',
            marker_color='#f39c12',
            text=regiones[cols_detectadas['ventas']],
            texttemplate='$%{x:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🌍 Ventas por Región',
            xaxis_title='Ventas ($)',
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=150)
        )
        
        return fig
    except:
        return None

def generar_grafico_top_clientes(df, cols_detectadas):
    """Genera gráfico de top clientes"""
    if not cols_detectadas['cliente'] or not cols_detectadas['ventas']:
        return None
    
    try:
        top = df.groupby(cols_detectadas['cliente'])[cols_detectadas['ventas']].sum().nlargest(10).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top[cols_detectadas['cliente']].astype(str),
            y=top[cols_detectadas['ventas']],
            marker_color='#2ecc71',
            text=top[cols_detectadas['ventas']],
            texttemplate='$%{y:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='👥 Top 10 Clientes',
            xaxis_title='Cliente',
            yaxis_title='Ventas ($)',
            template='plotly_white',
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    except:
        return None

def generar_dashboard_resumen(df, cols_detectadas):
    """Genera dashboard resumen"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Distribución de Ventas', 'Top Productos', 'Ventas por Región', 'Top Clientes'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Gráfico 1: Distribución (si hay categorías)
    if cols_detectadas['producto'] and cols_detectadas['ventas']:
        try:
            dist = df.groupby(cols_detectadas['producto'])[cols_detectadas['ventas']].sum().nlargest(5)
            fig.add_trace(
                go.Pie(labels=dist.index, values=dist.values, hole=0.4),
                row=1, col=1
            )
        except:
            pass
    
    # Gráfico 2: Top productos
    if cols_detectadas['producto'] and cols_detectadas['ventas']:
        try:
            top = df.groupby(cols_detectadas['producto'])[cols_detectadas['ventas']].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=top.values, y=top.index, orientation='h', marker_color='#764ba2'),
                row=1, col=2
            )
        except:
            pass
    
    # Gráfico 3: Ventas por región
    if cols_detectadas['region'] and cols_detectadas['ventas']:
        try:
            region = df.groupby(cols_detectadas['region'])[cols_detectadas['ventas']].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=region.index, y=region.values, marker_color='#f39c12'),
                row=2, col=1
            )
        except:
            pass
    
    # Gráfico 4: Top clientes
    if cols_detectadas['cliente'] and cols_detectadas['ventas']:
        try:
            clientes = df.groupby(cols_detectadas['cliente'])[cols_detectadas['ventas']].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=clientes.index.astype(str), y=clientes.values, marker_color='#2ecc71'),
                row=2, col=2
            )
        except:
            pass
    
    fig.update_layout(height=700, template='plotly_white', showlegend=False)
    return fig

# ============================================
# RUTAS
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
        
        session_id = secrets.token_hex(8)
        cols_detectadas = detectar_columnas_ventas(df)
        
        sessions[session_id] = {
            'df': df,
            'filename': 'datos_ejemplo.csv',
            'cols_detectadas': cols_detectadas,
            'metrics': obtener_metricas(df, cols_detectadas),
            'rows': len(df),
            'columns': len(df.columns),
            'nulos': df.isnull().sum().sum()
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
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
        # Leer archivo
        if file.filename.lower().endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif file.filename.lower().endswith('.json'):
            df = pd.read_json(file)
        else:
            flash('Formato no soportado. Usa CSV, Excel o JSON', 'error')
            return redirect(url_for('main'))
        
        # Validar
        if len(df) == 0:
            flash('El archivo está vacío', 'error')
            return redirect(url_for('main'))
        
        # Limpiar nombres de columnas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Detectar columnas
        cols_detectadas = detectar_columnas_ventas(df)
        
        # Crear sesión
        session_id = secrets.token_hex(8)
        sessions[session_id] = {
            'df': df,
            'filename': file.filename,
            'cols_detectadas': cols_detectadas,
            'metrics': obtener_metricas(df, cols_detectadas),
            'rows': len(df),
            'columns': len(df.columns),
            'nulos': df.isnull().sum().sum()
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'error')
        return redirect(url_for('main'))

@app.route('/dashboard/<session_id>/<viz_type>')
def dashboard(session_id, viz_type):
    if session_id not in sessions:
        return redirect(url_for('main'))
    
    session_data = sessions[session_id]
    df = session_data['df']
    cols_detectadas = session_data['cols_detectadas']
    
    # Generar visualización según tipo
    viz_content = ''
    viz_title = ''
    
    if viz_type == 'resumen':
        fig = generar_dashboard_resumen(df, cols_detectadas)
        viz_title = '📊 Dashboard Resumen'
    elif viz_type == 'ventas_tiempo':
        fig = generar_grafico_ventas_tiempo(df, cols_detectadas)
        viz_title = '📈 Evolución de Ventas'
    elif viz_type == 'top_productos':
        fig = generar_grafico_top_productos(df, cols_detectadas)
        viz_title = '🏆 Top Productos'
    elif viz_type == 'ventas_categoria':
        fig = generar_grafico_top_productos(df, cols_detectadas)  # Reutilizamos
        viz_title = '📦 Ventas por Producto'
    elif viz_type == 'ventas_region':
        fig = generar_grafico_ventas_region(df, cols_detectadas)
        viz_title = '🌍 Ventas por Región'
    elif viz_type == 'clientes':
        fig = generar_grafico_top_clientes(df, cols_detectadas)
        viz_title = '👥 Top Clientes'
    elif viz_type == 'datos':
        viz_title = '📋 Vista de Datos'
        viz_content = f'''
        <div class="table-wrapper">
            {df.head(50).to_html(classes='table', border=0, index=False)}
        </div>
        <p style="text-align: center; margin-top: 20px; color: #666;">
            Mostrando 50 de {len(df)} registros
        </p>
        '''
    
    if viz_type != 'datos':
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
        else:
            viz_content = '''
            <div style="text-align: center; padding: 50px;">
                <h3 style="color: #666;">📊 No hay datos suficientes para esta visualización</h3>
                <p style="color: #999;">El archivo no contiene las columnas necesarias</p>
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

# ============================================
# INICIAR APLICACIÓN
# ============================================
if __name__ == '__main__':
    print("="*60)
    print("📊 SALES ANALYTICS PRO - VERSIÓN CORREGIDA")
    print("="*60)
    print("🚀 Servidor: http://localhost:5000")
    print("📁 Datos de ejemplo: http://localhost:5000/sample")
    print("="*60)
    
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
