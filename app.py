"""
Sales Analytics Pro - VERSIÓN SIMPLE 100% FUNCIONAL
"""
from flask import Flask, request, render_template_string, redirect, url_for, flash
import pandas as pd
import secrets
from datetime import datetime
import numpy as np
import io

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ============================================
# SPLASH SCREEN - SIMPLE
# ============================================
SPLASH_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="2;url=/main">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .splash { text-align: center; }
        h1 { font-size: 48px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="splash">
        <h1>📊 SALES ANALYTICS</h1>
        <p>Cargando...</p>
    </div>
</body>
</html>
'''

# ============================================
# PÁGINA PRINCIPAL - SIMPLE
# ============================================
INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Cargar Archivo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            max-width: 500px;
            width: 100%;
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .upload-area {
            border: 2px dashed #667eea;
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
            cursor: pointer;
        }
        .upload-area:hover { background: #f8f9fa; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            display: inline-block;
            margin-top: 20px;
        }
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
        <p>Sube tu archivo de ventas</p>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data" action="/upload">
            <div class="upload-area" onclick="document.getElementById('file').click()">
                <p style="font-size: 48px; margin: 0;">📁</p>
                <p>Haz clic para seleccionar archivo</p>
                <input type="file" name="file" id="file" style="display: none;" accept=".csv,.xlsx,.xls" required>
            </div>
            <button type="submit" class="btn">Procesar Archivo</button>
        </form>
        
        <p style="margin-top: 20px;">
            <a href="/sample" style="color: #667eea;">Usar datos de ejemplo</a>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Formatos: CSV, Excel
        </p>
    </div>
    
    <script>
        document.getElementById('file').onchange = function() {
            this.form.submit();
        };
    </script>
</body>
</html>
'''

# ============================================
# DASHBOARD - SIMPLE
# ============================================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - {{ filename }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
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
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .menu {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        .menu-item {
            padding: 10px 20px;
            border-radius: 20px;
            text-decoration: none;
            color: #666;
            background: #f0f0f0;
        }
        .menu-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f0f0f0;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="brand">📊 SALES ANALYTICS</span>
            <div>
                <span style="margin-right: 15px; color: #666;">{{ filename }}</span>
                <a href="/main" class="btn">+ Nuevo</a>
            </div>
        </div>
        
        <div class="metrics">
            {% for metric in metrics %}
            <div class="metric-card">
                <div style="color: #999; font-size: 12px;">{{ metric.label }}</div>
                <div class="metric-value">{{ metric.value }}</div>
                <div style="color: #666; font-size: 12px;">{{ metric.sub }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="menu">
            <a href="/dashboard/{{ session_id }}/resumen" class="menu-item {% if viz == 'resumen' %}active{% endif %}">📊 Resumen</a>
            <a href="/dashboard/{{ session_id }}/datos" class="menu-item {% if viz == 'datos' %}active{% endif %}">📋 Datos</a>
        </div>
        
        <div class="content">
            <h2 style="margin-top: 0; color: #333;">{{ viz_title }}</h2>
            <div style="overflow-x: auto;">
                {{ viz_content|safe }}
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            {{ timestamp }}
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
# FUNCIONES SIMPLES
# ============================================

def procesar_dataframe(df):
    """Procesa el dataframe y extrae métricas básicas"""
    metrics = []
    
    # Métrica 1: Total registros
    metrics.append({
        'label': '📊 Registros',
        'value': f'{len(df):,}',
        'sub': f'{len(df.columns)} columnas'
    })
    
    # Buscar columna numérica para ventas
    ventas_col = None
    for col in df.columns:
        if any(x in str(col).lower() for x in ['venta', 'sales', 'total', 'precio', 'price']):
            ventas_col = col
            break
    
    if ventas_col:
        try:
            df[ventas_col] = pd.to_numeric(df[ventas_col], errors='coerce')
            total = df[ventas_col].sum()
            metrics.append({
                'label': '💰 Ventas',
                'value': f'${total:,.0f}' if not pd.isna(total) else '$0',
                'sub': 'Totales'
            })
        except:
            metrics.append({
                'label': '💰 Ventas',
                'value': 'N/A',
                'sub': 'No detectable'
            })
    else:
        metrics.append({
            'label': '💰 Ventas',
            'value': 'N/A',
            'sub': 'Columna no encontrada'
        })
    
    # Buscar columna de productos
    for col in df.columns:
        if any(x in str(col).lower() for x in ['producto', 'product', 'item']):
            try:
                n_productos = df[col].nunique()
                metrics.append({
                    'label': '🏷️ Productos',
                    'value': f'{n_productos:,}',
                    'sub': 'Únicos'
                })
                break
            except:
                pass
    else:
        metrics.append({
            'label': '🏷️ Productos',
            'value': 'N/A',
            'sub': 'No detectable'
        })
    
    # Siempre tener 4 métricas
    while len(metrics) < 4:
        metrics.append({
            'label': '📊 Info',
            'value': '-',
            'sub': ''
        })
    
    return metrics[:4]

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
    """Datos de ejemplo"""
    try:
        # Crear datos simples
        data = {
            'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'Producto': ['Laptop', 'Mouse', 'Teclado', 'Monitor', 'Laptop'],
            'Ventas': [1200, 25, 80, 350, 1200],
            'Cantidad': [1, 5, 2, 1, 1],
            'Cliente': ['A', 'B', 'A', 'C', 'D']
        }
        df = pd.DataFrame(data)
        
        session_id = secrets.token_hex(8)
        metrics = procesar_dataframe(df)
        
        sessions[session_id] = {
            'df': df,
            'filename': 'datos_ejemplo.csv',
            'metrics': metrics,
            'rows': len(df)
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No se seleccionó archivo', 'error')
        return redirect(url_for('main'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Archivo vacío', 'error')
        return redirect(url_for('main'))
    
    try:
        # Leer archivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            flash('Formato no soportado', 'error')
            return redirect(url_for('main'))
        
        # Limpiar datos
        df.columns = [str(col).strip() for col in df.columns]
        
        # Crear sesión
        session_id = secrets.token_hex(8)
        metrics = procesar_dataframe(df)
        
        sessions[session_id] = {
            'df': df,
            'filename': file.filename,
            'metrics': metrics,
            'rows': len(df)
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main'))

@app.route('/dashboard/<session_id>/<viz_type>')
def dashboard(session_id, viz_type):
    if session_id not in sessions:
        return redirect(url_for('main'))
    
    session_data = sessions[session_id]
    df = session_data['df']
    
    if viz_type == 'resumen':
        viz_title = '📊 Vista previa de datos'
        viz_content = f'''
        <div style="overflow-x: auto;">
            {df.head(10).to_html(index=False)}
        </div>
        <p style="color: #666; margin-top: 10px;">
            Mostrando 10 de {len(df)} registros
        </p>
        '''
    else:
        viz_title = '📋 Todos los datos'
        viz_content = f'''
        <div style="overflow-x: auto;">
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
# INICIAR
# ============================================
if __name__ == '__main__':
    print("="*50)
    print("📊 SALES ANALYTICS - VERSIÓN SIMPLE")
    print("="*50)
    print("🌐 http://localhost:5000")
    print("📁 Datos de ejemplo: http://localhost:5000/sample")
    print("="*50)
    
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
