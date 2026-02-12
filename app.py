"""
SALES ANALYTICS - VERSIÓN CON GRÁFICAS
Plotly funcionando 100%
"""

from flask import Flask, request, render_template_string, redirect, url_for, flash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import secrets
from datetime import datetime
import numpy as np
import io
import traceback

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ============================================
# HTML TEMPLATES
# ============================================
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            font-size: 36px;
        }
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            margin: 30px 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            background: #f8f9fa;
            border-color: #764ba2;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn:hover { transform: scale(1.05); }
        .error {
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Sales Analytics</h1>
        <p style="color: #666;">Sube tu archivo de ventas (CSV o Excel)</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data" action="/upload" id="uploadForm">
            <div class="upload-area" onclick="document.getElementById('file').click()">
                <div style="font-size: 48px; margin-bottom: 10px;">📁</div>
                <p style="color: #667eea; font-weight: bold;">Haz clic para seleccionar archivo</p>
                <p style="color: #999; font-size: 14px; margin-top: 10px;">CSV, Excel (XLSX, XLS)</p>
                <input type="file" name="file" id="file" accept=".csv,.xlsx,.xls" style="display: none;" required>
            </div>
            <button type="submit" class="btn">Procesar Archivo</button>
        </form>
        
        <p style="text-align: center; margin-top: 20px;">
            <a href="/sample" style="color: #667eea; text-decoration: none;">📊 Usar datos de ejemplo</a>
        </p>
    </div>
    
    <script>
        document.getElementById('file').addEventListener('change', function() {
            document.getElementById('uploadForm').submit();
        });
    </script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - {{ filename }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            border-radius: 15px;
            padding: 20px 30px;
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
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            text-decoration: none;
            font-size: 14px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
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
        .menu {
            background: white;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .menu-item {
            padding: 10px 20px;
            border-radius: 25px;
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
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .viz-title {
            font-size: 20px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
        }
        .viz-content {
            width: 100%;
            min-height: 500px;
        }
        .table-wrapper {
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="brand">📊 SALES ANALYTICS</span>
            <div>
                <span style="margin-right: 15px; color: #666;">{{ filename }} · {{ rows }} registros</span>
                <a href="/main" class="btn">+ Nuevo análisis</a>
            </div>
        </div>
        
        <div class="metrics">
            {% for metric in metrics %}
            <div class="metric-card">
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-value">{{ metric.value }}</div>
                <div style="color: #666; font-size: 12px; margin-top: 5px;">{{ metric.sub }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="menu">
            <a href="/dashboard/{{ session_id }}/resumen" class="menu-item {% if viz == 'resumen' %}active{% endif %}">📊 Dashboard</a>
            <a href="/dashboard/{{ session_id }}/ventas_tiempo" class="menu-item {% if viz == 'ventas_tiempo' %}active{% endif %}">📈 Ventas por Tiempo</a>
            <a href="/dashboard/{{ session_id }}/top_productos" class="menu-item {% if viz == 'top_productos' %}active{% endif %}">🏆 Top Productos</a>
            <a href="/dashboard/{{ session_id }}/ventas_region" class="menu-item {% if viz == 'ventas_region' %}active{% endif %}">🌍 Ventas por Región</a>
            <a href="/dashboard/{{ session_id }}/datos" class="menu-item {% if viz == 'datos' %}active{% endif %}">📋 Ver Datos</a>
        </div>
        
        <div class="viz-container">
            <div class="viz-title">{{ viz_title }}</div>
            <div class="viz-content">
                {{ viz_content|safe }}
            </div>
        </div>
        
        <div class="footer">
            Sales Analytics · {{ timestamp }}
        </div>
    </div>
</body>
</html>
'''

# ============================================
# ALMACENAMIENTO
# ============================================
sessions = {}

# ============================================
# FUNCIONES DE ANÁLISIS
# ============================================

def detectar_columnas(df):
    """Detecta columnas importantes"""
    cols = {
        'ventas': None,
        'fecha': None,
        'producto': None,
        'region': None
    }
    
    # Buscar ventas
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['venta', 'sales', 'total', 'monto', 'price', 'precio', 'revenue']):
            cols['ventas'] = col
            break
    
    if not cols['ventas']:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cols['ventas'] = numeric_cols[0]
    
    # Buscar fecha
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['fecha', 'date', 'tiempo', 'time']):
            cols['fecha'] = col
            break
    
    # Buscar producto
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['producto', 'product', 'item', 'articulo']):
            cols['producto'] = col
            break
    
    # Buscar región
    for col in df.columns:
        col_lower = str(col).lower()
        if any(x in col_lower for x in ['region', 'pais', 'country', 'ciudad', 'city']):
            cols['region'] = col
            break
    
    return cols

def calcular_metricas(df, cols):
    """Calcula métricas básicas"""
    metrics = []
    
    # Total registros
    metrics.append({
        'label': '📊 Registros',
        'value': f'{len(df):,}',
        'sub': f'{len(df.columns)} columnas'
    })
    
    # Ventas totales
    if cols['ventas'] and cols['ventas'] in df.columns:
        try:
            df[cols['ventas']] = pd.to_numeric(df[cols['ventas']], errors='coerce')
            total = df[cols['ventas']].sum()
            avg = df[cols['ventas']].mean()
            metrics.append({
                'label': '💰 Ventas Totales',
                'value': f'${total:,.0f}' if not pd.isna(total) else '$0',
                'sub': f'Promedio: ${avg:,.0f}' if not pd.isna(avg) else '$0'
            })
        except:
            metrics.append({'label': '💰 Ventas', 'value': 'N/A', 'sub': 'Error cálculo'})
    else:
        metrics.append({'label': '💰 Ventas', 'value': 'N/A', 'sub': 'No detectada'})
    
    # Productos
    if cols['producto'] and cols['producto'] in df.columns:
        try:
            n_productos = df[cols['producto']].nunique()
            metrics.append({
                'label': '🏷️ Productos',
                'value': f'{n_productos:,}',
                'sub': 'Únicos'
            })
        except:
            metrics.append({'label': '🏷️ Productos', 'value': 'N/A', 'sub': 'Error'})
    else:
        metrics.append({'label': '🏷️ Productos', 'value': 'N/A', 'sub': 'No detectada'})
    
    # Regiones
    if cols['region'] and cols['region'] in df.columns:
        try:
            n_regiones = df[cols['region']].nunique()
            metrics.append({
                'label': '🌍 Regiones',
                'value': f'{n_regiones:,}',
                'sub': 'Ubicaciones'
            })
        except:
            metrics.append({'label': '🌍 Regiones', 'value': 'N/A', 'sub': 'Error'})
    else:
        metrics.append({'label': '🌍 Regiones', 'value': 'N/A', 'sub': 'No detectada'})
    
    return metrics[:4]

def grafico_ventas_tiempo(df, cols):
    """Gráfico de ventas en el tiempo"""
    if not cols['fecha'] or not cols['ventas']:
        return None
    
    try:
        df_temp = df.copy()
        df_temp[cols['fecha']] = pd.to_datetime(df_temp[cols['fecha']])
        df_temp['fecha_simple'] = df_temp[cols['fecha']].dt.date
        ventas = df_temp.groupby('fecha_simple')[cols['ventas']].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ventas['fecha_simple'],
            y=ventas[cols['ventas']],
            mode='lines+markers',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title='📈 Ventas en el Tiempo',
            xaxis_title='Fecha',
            yaxis_title='Ventas ($)',
            template='plotly_white',
            height=500
        )
        return fig.to_html(full_html=False, include_plotlyjs=False)
    except:
        return None

def grafico_top_productos(df, cols):
    """Gráfico de top productos"""
    if not cols['producto'] or not cols['ventas']:
        return None
    
    try:
        top = df.groupby(cols['producto'])[cols['ventas']].sum().nlargest(10).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top[cols['producto']],
            x=top[cols['ventas']],
            orientation='h',
            marker_color='#764ba2',
            text=top[cols['ventas']],
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
        return fig.to_html(full_html=False, include_plotlyjs=False)
    except:
        return None

def grafico_ventas_region(df, cols):
    """Gráfico de ventas por región"""
    if not cols['region'] or not cols['ventas']:
        return None
    
    try:
        regiones = df.groupby(cols['region'])[cols['ventas']].sum().reset_index()
        regiones = regiones.sort_values(cols['ventas'], ascending=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=regiones[cols['region']],
            x=regiones[cols['ventas']],
            orientation='h',
            marker_color='#f39c12',
            text=regiones[cols['ventas']],
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
        return fig.to_html(full_html=False, include_plotlyjs=False)
    except:
        return None

# ============================================
# RUTAS
# ============================================

@app.route('/')
def index():
    return redirect(url_for('main'))

@app.route('/main')
def main():
    return render_template_string(INDEX_HTML)

@app.route('/sample')
def sample():
    try:
        # Datos de ejemplo
        df = pd.DataFrame({
            'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'Producto': ['Laptop', 'Mouse', 'Teclado', 'Monitor', 'Laptop'],
            'Ventas': [1200, 25, 80, 350, 1200],
            'Región': ['Norte', 'Sur', 'Norte', 'Este', 'Oeste']
        })
        
        session_id = secrets.token_hex(8)
        cols = detectar_columnas(df)
        metrics = calcular_metricas(df, cols)
        
        sessions[session_id] = {
            'df': df,
            'filename': 'ejemplo_ventas.csv',
            'cols': cols,
            'metrics': metrics,
            'rows': len(df)
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
    except Exception as e:
        print(f"Error sample: {e}")
        traceback.print_exc()
        flash(f'Error: {str(e)}')
        return redirect(url_for('main'))

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            flash('No hay archivo')
            return redirect(url_for('main'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Archivo vacío')
            return redirect(url_for('main'))
        
        # Leer archivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Formato no soportado. Usa CSV o Excel')
            return redirect(url_for('main'))
        
        # Limpiar columnas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Detectar columnas y calcular métricas
        cols = detectar_columnas(df)
        metrics = calcular_metricas(df, cols)
        
        # Crear sesión
        session_id = secrets.token_hex(8)
        sessions[session_id] = {
            'df': df,
            'filename': file.filename,
            'cols': cols,
            'metrics': metrics,
            'rows': len(df)
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        print(f"Error upload: {e}")
        traceback.print_exc()
        flash(f'Error: {str(e)}')
        return redirect(url_for('main'))

@app.route('/dashboard/<session_id>/<viz_type>')
def dashboard(session_id, viz_type):
    if session_id not in sessions:
        return redirect(url_for('main'))
    
    session_data = sessions[session_id]
    df = session_data['df']
    cols = session_data['cols']
    
    # Generar visualización
    if viz_type == 'resumen':
        viz_title = '📊 Dashboard Resumen'
        # Mostrar tabla y métricas
        viz_content = f'''
        <div style="margin-bottom: 30px;">
            <h3>Vista previa de datos</h3>
            <div class="table-wrapper">
                {df.head(10).to_html(index=False)}
            </div>
        </div>
        '''
        # Intentar agregar gráficos si existen
        fig1 = grafico_top_productos(df, cols)
        fig2 = grafico_ventas_region(df, cols)
        
        if fig1 or fig2:
            viz_content += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">'
            if fig1:
                viz_content += f'<div>{fig1}</div>'
            if fig2:
                viz_content += f'<div>{fig2}</div>'
            viz_content += '</div>'
    
    elif viz_type == 'ventas_tiempo':
        viz_title = '📈 Ventas por Tiempo'
        fig = grafico_ventas_tiempo(df, cols)
        viz_content = fig if fig else '<p style="color: #666; text-align: center;">No hay datos de fecha o ventas</p>'
    
    elif viz_type == 'top_productos':
        viz_title = '🏆 Top Productos'
        fig = grafico_top_productos(df, cols)
        viz_content = fig if fig else '<p style="color: #666; text-align: center;">No hay datos de productos o ventas</p>'
    
    elif viz_type == 'ventas_region':
        viz_title = '🌍 Ventas por Región'
        fig = grafico_ventas_region(df, cols)
        viz_content = fig if fig else '<p style="color: #666; text-align: center;">No hay datos de región o ventas</p>'
    
    else:  # datos
        viz_title = '📋 Todos los Datos'
        viz_content = f'''
        <div class="table-wrapper">
            {df.to_html(index=False)}
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
# EJECUTAR
# ============================================
if __name__ == '__main__':
    print("="*60)
    print("📊 SALES ANALYTICS - CON GRÁFICAS ACTIVADAS")
    print("="*60)
    print("🚀 Servidor: http://localhost:5000")
    print("📁 Datos ejemplo: http://localhost:5000/sample")
    print("📈 Gráficas: Plotly activado")
    print("="*60)
    
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
