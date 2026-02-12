"""
Sales Analytics Pro
==================
Aplicación web para análisis inteligente de ventas.
Construida con Flask, Pandas y Plotly.

Autor: servlet05
Licencia: MIT
GitHub: https://github.com/servlet05/SalesAnalytics
"""

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_file
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import json
from datetime import datetime, timedelta
import secrets
import os
import logging
from functools import wraps
import hashlib
import uuid
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# ============================================
# BASE DE DATOS EN MEMORIA (sesiones)
# ============================================
sessions_data = {}

# ============================================
# DECORADORES PERSONALIZADOS
# ============================================
def require_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = kwargs.get('session_id')
        if not session_id or session_id not in sessions_data:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# CLASE DETECTOR DE COLUMNAS DE VENTAS
# ============================================
class SalesColumnDetector:
    """Detecta automáticamente columnas de ventas sin importar el nombre"""
    
    # Patrones para diferentes tipos de columnas
    PATTERNS = {
        'date': [
            r'date', r'fecha', r'time', r'order_date', r'ship_date', 
            r'created_at', r'timestamp', r'dia', r'mes', r'año', r'year'
        ],
        'sales': [
            r'sale', r'venta', r'revenue', r'ingreso', r'total', r'amount',
            r'price', r'precio', r'cost', r'income', r'importe', r'sales'
        ],
        'quantity': [
            r'quantity', r'cantidad', r'qty', r'units', r'unidades',
            r'count', r'num', r'number', r'order_quantity'
        ],
        'profit': [
            r'profit', r'ganancia', r'margin', r'margen', r'benefit',
            r'utilidad', r'earnings', r'net'
        ],
        'product': [
            r'product', r'item', r'article', r'producto', r'name',
            r'description', r'categoria', r'category', r'marca', r'brand'
        ],
        'customer': [
            r'customer', r'cliente', r'buyer', r'comprador', r'user',
            r'account', r'contact', r'email'
        ],
        'region': [
            r'region', r'country', r'city', r'state', r'province',
            r'pais', r'ciudad', r'location', r'zona', r'area'
        ],
        'discount': [
            r'discount', r'descuento', r'offer', r'promo', r'promotion',
            r'rebate', r'off'
        ],
        'shipping': [
            r'ship', r'envi', r'delivery', r'entrega', r'courier',
            r'transport', r'mode', r'method'
        ]
    }
    
    @classmethod
    def detect_columns(cls, df):
        """Detecta todos los tipos de columnas en el DataFrame"""
        detected = {
            'date': [],
            'sales': [],
            'quantity': [],
            'profit': [],
            'product': [],
            'customer': [],
            'region': [],
            'discount': [],
            'shipping': [],
            'other_numeric': [],
            'other_categorical': []
        }
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Detectar por patrones
            for col_type, patterns in cls.PATTERNS.items():
                for pattern in patterns:
                    if pattern in col_lower or col_lower.startswith(pattern):
                        detected[col_type].append(col)
                        break
            
            # Clasificar por tipo de dato si no fue detectado
            if col not in [item for sublist in detected.values() for item in sublist]:
                if pd.api.types.is_numeric_dtype(df[col]):
                    if 'int' in str(df[col].dtype) and df[col].max() < 1000:
                        detected['quantity'].append(col)
                    else:
                        detected['other_numeric'].append(col)
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    detected['date'].append(col)
                else:
                    detected['other_categorical'].append(col)
        
        return detected

# ============================================
# CLASE ANALIZADOR DE VENTAS
# ============================================
class SalesAnalyzer:
    """Realiza análisis completos de ventas"""
    
    def __init__(self, df, detected_columns):
        self.df = df
        self.cols = detected_columns
        self.prepare_data()
    
    def prepare_data(self):
        """Prepara los datos para análisis"""
        # Convertir fechas
        for date_col in self.cols['date']:
            try:
                self.df[date_col] = pd.to_datetime(self.df[date_col])
            except:
                pass
        
        # Asegurar columnas numéricas
        for num_col in self.cols['sales'] + self.cols['quantity'] + self.cols['profit'] + self.cols['discount']:
            try:
                self.df[num_col] = pd.to_numeric(self.df[num_col], errors='coerce')
            except:
                pass
        
        # Crear columna de fecha si no existe
        if not self.cols['date']:
            self.df['Fecha_Analisis'] = datetime.now()
            self.cols['date'] = ['Fecha_Analisis']
    
    def get_sales_column(self):
        """Obtiene la mejor columna de ventas disponible"""
        if self.cols['sales']:
            return self.cols['sales'][0]
        elif self.cols['profit']:
            return self.cols['profit'][0]
        elif self.cols['quantity']:
            return self.cols['quantity'][0]
        else:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            return numeric_cols[0] if len(numeric_cols) > 0 else None
    
    def get_basic_metrics(self):
        """Calcula métricas básicas de ventas"""
        metrics = []
        sales_col = self.get_sales_column()
        
        # Total de ventas
        if sales_col:
            total_sales = self.df[sales_col].sum()
            avg_sales = self.df[sales_col].mean()
            metrics.append({
                'label': '💰 Ventas Totales',
                'value': f'${total_sales:,.0f}',
                'sub': f'Promedio: ${avg_sales:,.0f}'
            })
        
        # Cantidad de transacciones
        metrics.append({
            'label': '📊 Transacciones',
            'value': f'{len(self.df):,}',
            'sub': f'{len(self.df.columns)} columnas'
        })
        
        # Productos únicos
        if self.cols['product']:
            unique_products = self.df[self.cols['product'][0]].nunique()
            metrics.append({
                'label': '🏷️ Productos',
                'value': f'{unique_products:,}',
                'sub': 'Únicos'
            })
        
        # Clientes únicos
        if self.cols['customer']:
            unique_customers = self.df[self.cols['customer'][0]].nunique()
            metrics.append({
                'label': '👥 Clientes',
                'value': f'{unique_customers:,}',
                'sub': 'Activos'
            })
        
        # Cantidad de productos vendidos
        if self.cols['quantity']:
            total_quantity = self.df[self.cols['quantity'][0]].sum()
            metrics.append({
                'label': '📦 Unidades',
                'value': f'{total_quantity:,.0f}',
                'sub': 'Vendidas'
            })
        
        return metrics[:4]  # Máximo 4 métricas
    
    def sales_over_time(self):
        """Ventas a través del tiempo"""
        sales_col = self.get_sales_column()
        if not sales_col or not self.cols['date']:
            return None
        
        date_col = self.cols['date'][0]
        
        # Agrupar por fecha
        daily_sales = self.df.groupby(self.df[date_col].dt.date)[sales_col].sum().reset_index()
        daily_sales.columns = ['Fecha', 'Ventas']
        
        fig = go.Figure()
        
        # Línea de ventas
        fig.add_trace(go.Scatter(
            x=daily_sales['Fecha'],
            y=daily_sales['Ventas'],
            mode='lines+markers',
            name='Ventas',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6, color='#2E86AB')
        ))
        
        # Línea de tendencia
        z = np.polyfit(range(len(daily_sales)), daily_sales['Ventas'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=daily_sales['Fecha'],
            y=p(range(len(daily_sales))),
            mode='lines',
            name='Tendencia',
            line=dict(color='#A23B72', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title='📈 Evolución de Ventas',
            xaxis_title='Fecha',
            yaxis_title='Ventas ($)',
            template='plotly_white',
            hovermode='x unified',
            height=500,
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig
    
    def top_products(self, n=10):
        """Top productos más vendidos"""
        if not self.cols['product']:
            return None
        
        product_col = self.cols['product'][0]
        sales_col = self.get_sales_column()
        
        if sales_col:
            # Por ventas
            top_products = self.df.groupby(product_col)[sales_col].sum().nlargest(n).reset_index()
            value_col = 'Ventas'
            title = f'🏆 Top {n} Productos por Ventas'
            x_title = 'Ventas ($)'
        elif self.cols['quantity']:
            # Por cantidad
            top_products = self.df.groupby(product_col)[self.cols['quantity'][0]].sum().nlargest(n).reset_index()
            value_col = 'Cantidad'
            title = f'🏆 Top {n} Productos por Unidades'
            x_title = 'Cantidad Vendida'
        else:
            # Por frecuencia
            top_products = self.df[product_col].value_counts().head(n).reset_index()
            top_products.columns = [product_col, 'Frecuencia']
            value_col = 'Frecuencia'
            title = f'🏆 Top {n} Productos más Frecuentes'
            x_title = 'Frecuencia'
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top_products[product_col],
            x=top_products[value_col],
            orientation='h',
            marker_color='#2E86AB',
            text=top_products[value_col],
            texttemplate='%{x:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=150, r=40, t=60, b=40)
        )
        
        return fig
    
    def sales_by_category(self):
        """Ventas por categoría/producto"""
        if not self.cols['product'] or len(self.cols['product']) < 1:
            return None
        
        product_col = self.cols['product'][0]
        sales_col = self.get_sales_column()
        
        if not sales_col:
            return None
        
        category_sales = self.df.groupby(product_col)[sales_col].sum().nlargest(8).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=category_sales[product_col],
            values=category_sales[sales_col],
            hole=0.4,
            marker_colors=px.colors.qualitative.Set3,
            textinfo='label+percent',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🥧 Distribución de Ventas por Producto',
            template='plotly_white',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def sales_by_region(self):
        """Ventas por región/ubicación"""
        if not self.cols['region']:
            return None
        
        region_col = self.cols['region'][0]
        sales_col = self.get_sales_column()
        
        if not sales_col:
            return None
        
        region_sales = self.df.groupby(region_col)[sales_col].sum().reset_index()
        region_sales = region_sales.sort_values(sales_col, ascending=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=region_sales[region_col],
            x=region_sales[sales_col],
            orientation='h',
            marker_color='#A23B72',
            text=region_sales[sales_col],
            texttemplate='$%{x:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🌍 Ventas por Región',
            xaxis_title='Ventas ($)',
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=150, r=40, t=60, b=40)
        )
        
        return fig
    
    def customer_segments(self):
        """Análisis de segmentos de clientes"""
        if not self.cols['customer']:
            return None
        
        customer_col = self.cols['customer'][0]
        sales_col = self.get_sales_column()
        
        if not sales_col:
            return None
        
        # Top clientes
        top_customers = self.df.groupby(customer_col)[sales_col].sum().nlargest(10).reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_customers[customer_col].astype(str),
            y=top_customers[sales_col],
            marker_color='#F18F01',
            text=top_customers[sales_col],
            texttemplate='$%{y:,.0f}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='👥 Top 10 Clientes por Ventas',
            xaxis_title='Cliente',
            yaxis_title='Ventas ($)',
            template='plotly_white',
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def discount_analysis(self):
        """Análisis de descuentos"""
        if not self.cols['discount'] or not self.cols['sales']:
            return None
        
        discount_col = self.cols['discount'][0]
        sales_col = self.cols['sales'][0]
        
        # Crear rangos de descuento
        df_temp = self.df.copy()
        df_temp['Rango_Descuento'] = pd.cut(
            df_temp[discount_col],
            bins=[0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 1],
            labels=['0-5%', '5-10%', '10-15%', '15-20%', '20-25%', '25-30%', '30%+']
        )
        
        discount_effect = df_temp.groupby('Rango_Descuento')[sales_col].agg(['sum', 'count']).reset_index()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Ventas por Rango de Descuento', 'Cantidad de Transacciones'),
            vertical_spacing=0.15
        )
        
        fig.add_trace(
            go.Bar(x=discount_effect['Rango_Descuento'], y=discount_effect['sum'],
                   name='Ventas', marker_color='#2E86AB'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=discount_effect['Rango_Descuento'], y=discount_effect['count'],
                   name='Transacciones', marker_color='#F18F01'),
            row=2, col=1
        )
        
        fig.update_layout(
            title='🏷️ Análisis de Descuentos',
            template='plotly_white',
            height=600,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Rango de Descuento", row=2, col=1)
        fig.update_yaxes(title_text="Ventas ($)", row=1, col=1)
        fig.update_yaxes(title_text="Número de Transacciones", row=2, col=1)
        
        return fig
    
    def shipping_analysis(self):
        """Análisis de métodos de envío"""
        if not self.cols['shipping']:
            return None
        
        shipping_col = self.cols['shipping'][0]
        shipping_counts = self.df[shipping_col].value_counts().reset_index()
        shipping_counts.columns = ['Método', 'Cantidad']
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=shipping_counts['Método'],
            values=shipping_counts['Cantidad'],
            hole=0.4,
            marker_colors=px.colors.qualitative.Pastel,
            textinfo='label+percent',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='🚚 Métodos de Envío',
            template='plotly_white',
            height=500,
            showlegend=True
        )
        
        return fig
    
    def profit_analysis(self):
        """Análisis de ganancias"""
        if not self.cols['profit'] or not self.cols['sales']:
            return None
        
        profit_col = self.cols['profit'][0]
        sales_col = self.cols['sales'][0]
        
        # Calcular margen
        df_temp = self.df.copy()
        df_temp['Margen'] = (df_temp[profit_col] / df_temp[sales_col] * 100)
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Ganancias vs Ventas', 'Distribución de Márgenes'),
            specs=[[{'type': 'scatter'}, {'type': 'histogram'}]]
        )
        
        fig.add_trace(
            go.Scatter(x=df_temp[sales_col], y=df_temp[profit_col],
                      mode='markers', marker=dict(color='#2E86AB', size=8),
                      name='Transacciones'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Histogram(x=df_temp['Margen'], nbinsx=20,
                        marker_color='#A23B72', name='Margen'),
            row=1, col=2
        )
        
        fig.update_layout(
            title='💰 Análisis de Rentabilidad',
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Ventas ($)", row=1, col=1)
        fig.update_yaxes(title_text="Ganancias ($)", row=1, col=1)
        fig.update_xaxes(title_text="Margen (%)", row=1, col=2)
        fig.update_yaxes(title_text="Frecuencia", row=1, col=2)
        
        return fig
    
    def sales_summary(self):
        """Dashboard resumen con múltiples gráficas"""
        sales_col = self.get_sales_column()
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Ventas por Producto', 'Distribución de Ventas',
                          'Ventas por Región', 'Top Clientes'),
            specs=[[{'type': 'bar'}, {'type': 'pie'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        # Ventas por producto (top 5)
        if self.cols['product'] and sales_col:
            product_sales = self.df.groupby(self.cols['product'][0])[sales_col].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=product_sales.values, y=product_sales.index, orientation='h',
                      marker_color='#2E86AB', showlegend=False),
                row=1, col=1
            )
        
        # Distribución de ventas (si hay categorías)
        if len(self.cols['product']) > 0 and sales_col:
            dist_sales = self.df.groupby(self.cols['product'][0])[sales_col].sum().nlargest(4)
            fig.add_trace(
                go.Pie(labels=dist_sales.index, values=dist_sales.values,
                      hole=0.4, showlegend=False),
                row=1, col=2
            )
        
        # Ventas por región
        if self.cols['region'] and sales_col:
            region_sales = self.df.groupby(self.cols['region'][0])[sales_col].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=region_sales.index, y=region_sales.values,
                      marker_color='#A23B72', showlegend=False),
                row=2, col=1
            )
        
        # Top clientes
        if self.cols['customer'] and sales_col:
            customer_sales = self.df.groupby(self.cols['customer'][0])[sales_col].sum().nlargest(5)
            fig.add_trace(
                go.Bar(x=customer_sales.index.astype(str), y=customer_sales.values,
                      marker_color='#F18F01', showlegend=False),
                row=2, col=2
            )
        
        fig.update_layout(
            title='📊 Dashboard Resumen de Ventas',
            template='plotly_white',
            height=700,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Ventas ($)", row=1, col=1)
        fig.update_xaxes(title_text="Región", row=2, col=1)
        fig.update_xaxes(title_text="Cliente", row=2, col=2)
        
        return fig

# ============================================
# GENERADOR DE PLANTILLAS HTML
# ============================================
def create_templates():
    """Crea los archivos de plantilla HTML si no existen"""
    
    # Splash template
    splash_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics Pro · Iniciando</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
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
            max-width: 600px;
            opacity: 0;
            animation: fadeIn 0.8s ease forwards;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-20px); }
        }
        
        .splash.fade-out {
            animation: fadeOut 0.8s ease forwards;
        }
        
        .icon {
            font-size: 90px;
            margin-bottom: 32px;
            display: inline-block;
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        h1 {
            font-size: 64px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            font-size: 24px;
            font-weight: 350;
            margin-bottom: 24px;
            line-height: 1.4;
            opacity: 0.9;
        }
        
        .divider {
            width: 80px;
            height: 3px;
            background: white;
            margin: 32px auto;
            border-radius: 3px;
            opacity: 0.6;
        }
        
        .tech {
            font-size: 16px;
            opacity: 0.8;
            margin-bottom: 48px;
            font-family: monospace;
            letter-spacing: 2px;
        }
        
        .progress-container {
            width: 240px;
            margin: 0 auto;
        }
        
        .progress {
            width: 100%;
            height: 4px;
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-bar {
            width: 0%;
            height: 100%;
            background: white;
            animation: progress 4s ease-in-out forwards;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            20% { width: 30%; }
            50% { width: 70%; }
            80% { width: 90%; }
            100% { width: 100%; }
        }
        
        .status {
            margin-top: 20px;
            opacity: 0.9;
            font-size: 15px;
            animation: pulse 2s ease infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 1; }
        }
        
        .footer {
            margin-top: 60px;
            opacity: 0.6;
            font-size: 13px;
        }
        
        .github-corner {
            position: fixed;
            top: 0;
            right: 0;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <a href="https://github.com/tuusuario/sales-analytics-pro" class="github-corner" target="_blank">
        <svg width="80" height="80" viewBox="0 0 250 250" style="fill:white; color:linear-gradient(135deg, #667eea 0%, #764ba2 100%); position: absolute; top: 0; right: 0; border: 0;">
            <path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path>
            <path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path>
            <path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path>
        </svg>
    </a>
    
    <div class="splash" id="splash">
        <div class="icon">📈</div>
        <h1>SALES ANALYTICS PRO</h1>
        <div class="subtitle">
            Análisis inteligente de ventas<br>
            Potencia tu negocio con datos
        </div>
        <div class="divider"></div>
        <div class="tech">✦ flask · pandas · plotly ✦</div>
        
        <div class="progress-container">
            <div class="progress">
                <div class="progress-bar"></div>
            </div>
        </div>
        <div class="status" id="status">inicializando sistema...</div>
        
        <div class="footer">
            <span>⚡ 100% Python · Código Abierto · MIT License ⚡</span>
        </div>
    </div>
    
    <script>
        const statusMessages = [
            "cargando módulos de análisis...",
            "preparando detectores de ventas...",
            "iniciando visualizaciones...",
            "sistema listo para analizar datos..."
        ];
        
        let i = 0;
        const statusEl = document.getElementById('status');
        
        const interval = setInterval(() => {
            if (i < statusMessages.length) {
                statusEl.textContent = statusMessages[i];
                i++;
            }
        }, 1000);
        
        setTimeout(() => {
            clearInterval(interval);
            statusEl.textContent = "✨ ¡Listo! Redirigiendo... ✨";
            
            const splash = document.getElementById('splash');
            splash.classList.add('fade-out');
            
            setTimeout(() => {
                window.location.href = "/";
            }, 800);
        }, 4500);
    </script>
</body>
</html>
    '''
    
    # Index template
    index_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics Pro · Cargar Datos</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #2d3436;
            line-height: 1.5;
            min-height: 100vh;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        
        .brand {
            text-align: center;
            margin-bottom: 50px;
        }
        
        .brand h1 {
            font-size: 52px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .brand p {
            font-size: 20px;
            color: #636e72;
            font-weight: 350;
        }
        
        .upload-card {
            background: white;
            border-radius: 30px;
            padding: 50px 40px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .upload-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 50px rgba(102,126,234,0.2);
        }
        
        .upload-icon {
            font-size: 64px;
            color: #667eea;
            margin-bottom: 24px;
        }
        
        .file-input {
            display: none;
        }
        
        .file-label {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 18px;
            font-weight: 600;
            padding: 16px 48px;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            letter-spacing: -0.01em;
            box-shadow: 0 10px 20px rgba(102,126,234,0.3);
        }
        
        .file-label:hover {
            transform: scale(1.05);
            box-shadow: 0 15px 30px rgba(102,126,234,0.4);
        }
        
        .formats {
            margin-top: 30px;
            display: flex;
            justify-content: center;
            gap: 15px;
            color: #636e72;
            font-size: 14px;
            flex-wrap: wrap;
        }
        
        .formats span {
            padding: 8px 20px;
            background: #f1f3f5;
            border-radius: 50px;
            border: 1px solid #dfe6e9;
            font-weight: 500;
        }
        
        .loading {
            display: none;
            margin-top: 40px;
            color: #667eea;
            font-size: 18px;
            font-weight: 500;
        }
        
        .loading::after {
            content: "...";
            animation: dots 1.5s steps(4, end) infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: "."; }
            40% { content: ".."; }
            60%, 100% { content: "..."; }
        }
        
        .features {
            display: flex;
            justify-content: space-around;
            margin-top: 50px;
            width: 100%;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .feature {
            background: white;
            padding: 20px;
            border-radius: 20px;
            flex: 1;
            min-width: 150px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .feature-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .feature h3 {
            font-size: 16px;
            color: #2d3436;
            margin-bottom: 5px;
        }
        
        .feature p {
            font-size: 13px;
            color: #636e72;
        }
        
        .footer {
            margin-top: 60px;
            color: #636e72;
            font-size: 13px;
            text-align: center;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        
        .error-message {
            background: #ff6b6b;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">
            <h1>📈 SALES ANALYTICS PRO</h1>
            <p>Sube tu archivo de ventas · Análisis instantáneo</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="error-message" style="display: block; background: {{ '#ff6b6b' if category == 'error' else '#51cf66' }};">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post" enctype="multipart/form-data" action="/upload" id="uploadForm">
            <div class="upload-card">
                <div class="upload-icon">📊</div>
                <input type="file" name="file" id="file" class="file-input" accept=".csv,.xlsx,.xls,.json" required>
                <label for="file" class="file-label">📁 Seleccionar archivo</label>
                <div class="formats">
                    <span>CSV</span>
                    <span>Excel (.xlsx, .xls)</span>
                    <span>JSON</span>
                </div>
                <div class="loading" id="loading">Procesando archivo</div>
            </div>
        </form>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🔍</div>
                <h3>Detección inteligente</h3>
                <p>Auto-detecta ventas, productos, clientes</p>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <h3>15+ visualizaciones</h3>
                <p>Gráficas interactivas automáticas</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>Tiempo real</h3>
                <p>Análisis instantáneo sin configuración</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔒</div>
                <h3>100% local</h3>
                <p>Tus datos no salen de tu computadora</p>
            </div>
        </div>
        
        <div class="footer">
            <p>✨ <strong>Sales Analytics Pro</strong> · Análisis inteligente de ventas · MIT License</p>
            <p style="margin-top: 10px;">
                <a href="https://github.com/tuusuario/sales-analytics-pro" target="_blank">GitHub</a> · 
                <a href="#" onclick="window.location.href='/sample'">Probar con datos de ejemplo</a>
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
    
    # Dashboard template
    dashboard_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sales Analytics Pro · {{ filename }}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f8f9fa;
            color: #2d3436;
            line-height: 1.5;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px 24px;
        }
        
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px 30px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.03);
            border: 1px solid #e9ecef;
        }
        
        .brand {
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .file-badge {
            background: #f1f3f5;
            padding: 10px 24px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 500;
            color: #495057;
            border: 1px solid #dee2e6;
        }
        
        .btn-new {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 28px;
            border-radius: 50px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            box-shadow: 0 5px 15px rgba(102,126,234,0.3);
        }
        
        .btn-new:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102,126,234,0.4);
        }
        
        .dashboard-header {
            margin-bottom: 30px;
        }
        
        .dashboard-header h1 {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 10px;
            color: #2d3436;
        }
        
        .dashboard-header p {
            font-size: 16px;
            color: #636e72;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 20px;
            border: 1px solid #e9ecef;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.05);
        }
        
        .metric-label {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #868e96;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 36px;
            font-weight: 700;
            color: #2d3436;
            margin-bottom: 8px;
        }
        
        .metric-sub {
            font-size: 14px;
            color: #868e96;
        }
        
        .menu-section {
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
        }
        
        .menu-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .menu-title h2 {
            font-size: 20px;
            font-weight: 600;
            color: #2d3436;
        }
        
        .menu-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }
        
        .menu-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 12px 24px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 500;
            color: #495057;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-block;
        }
        
        .menu-item:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
            transform: translateY(-2px);
        }
        
        .menu-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
        }
        
        .viz-container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid #e9ecef;
            box-shadow: 0 5px 20px rgba(0,0,0,0.02);
        }
        
        .viz-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .viz-header h3 {
            font-size: 22px;
            font-weight: 600;
            color: #2d3436;
        }
        
        .viz-content {
            width: 100%;
            min-height: 500px;
        }
        
        .table-wrapper {
            overflow-x: auto;
            margin-top: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        th {
            text-align: left;
            padding: 16px 12px;
            background: #f8f9fa;
            color: #2d3436;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }
        
        td {
            padding: 14px 12px;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
        }
        
        tr:hover td {
            background: #f8f9fa;
        }
        
        .insights-box {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe9db 100%);
            border-radius: 15px;
            padding: 20px 25px;
            margin-top: 30px;
            border-left: 4px solid #fd7e14;
        }
        
        .insights-title {
            font-weight: 600;
            color: #e67e22;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .insights-content {
            color: #2d3436;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #868e96;
            font-size: 13px;
        }
        
        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 20px 16px;
            }
            .dashboard-header h1 {
                font-size: 28px;
            }
            .navbar {
                flex-direction: column;
                gap: 15px;
            }
        }
        
        .export-btn {
            background: white;
            border: 1px solid #dee2e6;
            padding: 10px 20px;
            border-radius: 50px;
            font-size: 13px;
            color: #495057;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .export-btn:hover {
            background: #f8f9fa;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="navbar">
            <span class="brand">📊 SALES ANALYTICS PRO</span>
            <div class="file-info">
                <span class="file-badge">
                    📁 {{ filename }} · {{ rows }} registros · {{ columnas }} columnas
                </span>
                <a href="/" class="btn-new">+ Nuevo análisis</a>
            </div>
        </div>
        
        <div class="dashboard-header">
            <h1>{{ tipo }}</h1>
            <p>🎯 {{ nulos }} valores nulos · Detección automática completada</p>
        </div>
        
        <div class="metrics-grid">
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
        
        <div class="menu-section">
            <div class="menu-title">
                <span style="font-size: 28px;">🎯</span>
                <h2>Visualizaciones disponibles</h2>
            </div>
            <div class="menu-grid">
                <a href="/dashboard/{{ session_id }}/resumen" class="menu-item {% if viz == 'resumen' %}active{% endif %}">
                    📊 Dashboard General
                </a>
                <a href="/dashboard/{{ session_id }}/ventas_tiempo" class="menu-item {% if viz == 'ventas_tiempo' %}active{% endif %}">
                    📈 Ventas en el Tiempo
                </a>
                <a href="/dashboard/{{ session_id }}/top_productos" class="menu-item {% if viz == 'top_productos' %}active{% endif %}">
                    🏆 Top Productos
                </a>
                <a href="/dashboard/{{ session_id }}/ventas_categoria" class="menu-item {% if viz == 'ventas_categoria' %}active{% endif %}">
                    📦 Ventas por Categoría
                </a>
                <a href="/dashboard/{{ session_id }}/ventas_region" class="menu-item {% if viz == 'ventas_region' %}active{% endif %}">
                    🌍 Ventas por Región
                </a>
                <a href="/dashboard/{{ session_id }}/clientes" class="menu-item {% if viz == 'clientes' %}active{% endif %}">
                    👥 Top Clientes
                </a>
                <a href="/dashboard/{{ session_id }}/descuentos" class="menu-item {% if viz == 'descuentos' %}active{% endif %}">
                    🏷️ Análisis de Descuentos
                </a>
                <a href="/dashboard/{{ session_id }}/envios" class="menu-item {% if viz == 'envios' %}active{% endif %}">
                    🚚 Métodos de Envío
                </a>
                <a href="/dashboard/{{ session_id }}/rentabilidad" class="menu-item {% if viz == 'rentabilidad' %}active{% endif %}">
                    💰 Análisis de Rentabilidad
                </a>
                <a href="/dashboard/{{ session_id }}/datos" class="menu-item {% if viz == 'datos' %}active{% endif %}">
                    📋 Ver Datos
                </a>
            </div>
        </div>
        
        <div class="viz-container">
            <div class="viz-header">
                <div>
                    <h3>{{ viz_title }}</h3>
                    <p style="color: #868e96; font-size: 14px; margin-top: 5px;">{{ viz_desc }}</p>
                </div>
                <div>
                    <button class="export-btn" onclick="window.print()">
                        🖨️ Exportar
                    </button>
                </div>
            </div>
            <div class="viz-content">
                {{ viz_content|safe }}
            </div>
            
            {% if insights %}
            <div class="insights-box">
                <div class="insights-title">💡 Insights detectados</div>
                <div class="insights-content">{{ insights }}</div>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p><strong>Sales Analytics Pro</strong> · Análisis inteligente de ventas · MIT License</p>
            <p style="margin-top: 10px;">
                ⚡ Procesado en {{ processing_time }}s · {{ timestamp }}
            </p>
        </div>
    </div>
</body>
</html>
    '''
    
    # Guardar templates
    with open('templates/splash.html', 'w', encoding='utf-8') as f:
        f.write(splash_template)
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

# ============================================
# RUTAS DE LA APLICACIÓN
# ============================================

@app.route('/splash')
def splash():
    """Muestra el splash screen"""
    return render_template('splash.html')

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/sample')
def sample_data():
    """Carga datos de ejemplo"""
    try:
        # Crear datos de ejemplo
        np.random.seed(42)
        n = 1000
        
        sample_df = pd.DataFrame({
            'Fecha': pd.date_range(start='2023-01-01', periods=n, freq='D'),
            'Producto': np.random.choice(['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Teclado', 'Mouse'], n),
            'Categoría': np.random.choice(['Electrónica', 'Computación', 'Accesorios'], n),
            'Ventas': np.random.uniform(100, 2000, n).round(2),
            'Cantidad': np.random.randint(1, 10, n),
            'Cliente': np.random.choice(['Empresa A', 'Empresa B', 'Empresa C', 'Particular'], n),
            'Región': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste', 'Centro'], n),
            'Descuento': np.random.choice([0, 0.05, 0.1, 0.15, 0.2], n, p=[0.5, 0.2, 0.15, 0.1, 0.05]),
            'Método_Envío': np.random.choice(['Estándar', 'Express', 'Same Day'], n),
            'Ganancia': np.random.uniform(20, 500, n).round(2)
        })
        
        session_id = secrets.token_hex(8)
        
        # Detectar columnas
        detector = SalesColumnDetector()
        detected_cols = detector.detect_columns(sample_df)
        
        # Analizar datos
        analyzer = SalesAnalyzer(sample_df.copy(), detected_cols)
        
        # Guardar en sesión
        sessions_data[session_id] = {
            'df': sample_df,
            'filename': 'datos_ejemplo_ventas.csv',
            'detected_cols': detected_cols,
            'analyzer': analyzer,
            'metrics': analyzer.get_basic_metrics(),
            'tipo': '📊 Datos de Ejemplo - Ventas',
            'rows': len(sample_df),
            'columns': len(sample_df.columns),
            'nulos': sample_df.isnull().sum().sum(),
            'timestamp': datetime.now().isoformat()
        }
        
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except Exception as e:
        logger.error(f"Error creando datos de ejemplo: {str(e)}")
        from flask import flash
        flash('Error al cargar datos de ejemplo', 'error')
        return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    """Procesa el archivo subido"""
    if 'file' not in request.files:
        from flask import flash
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nombre de archivo vacío', 'error')
        return redirect(url_for('index'))
    
    try:
        # Leer archivo según extensión
        filename = file.filename.lower()
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8')
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
        elif filename.endswith('.json'):
            df = pd.read_json(file)
        else:
            flash('Formato no soportado. Usa CSV, Excel o JSON', 'error')
            return redirect(url_for('index'))
        
        # Validar datos mínimos
        if len(df) == 0:
            flash('El archivo está vacío', 'error')
            return redirect(url_for('index'))
        
        if len(df.columns) == 0:
            flash('El archivo no tiene columnas', 'error')
            return redirect(url_for('index'))
        
        # Limpiar nombres de columnas
        df.columns = [str(col).strip() for col in df.columns]
        
        # Crear sesión
        session_id = secrets.token_hex(8)
        
        # Detectar columnas
        detector = SalesColumnDetector()
        detected_cols = detector.detect_columns(df)
        
        # Analizar datos
        analyzer = SalesAnalyzer(df.copy(), detected_cols)
        
        # Determinar tipo de datos
        if detected_cols['sales']:
            tipo = '💰 Análisis de Ventas'
        elif detected_cols['profit']:
            tipo = '💵 Análisis Financiero'
        elif detected_cols['quantity']:
            tipo = '📦 Análisis de Inventario'
        else:
            tipo = '📊 Datos Generales'
        
        # Guardar en sesión
        sessions_data[session_id] = {
            'df': df,
            'filename': file.filename,
            'detected_cols': detected_cols,
            'analyzer': analyzer,
            'metrics': analyzer.get_basic_metrics(),
            'tipo': tipo,
            'rows': len(df),
            'columns': len(df.columns),
            'nulos': df.isnull().sum().sum(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Archivo procesado exitosamente: {file.filename}")
        return redirect(f'/dashboard/{session_id}/resumen')
        
    except pd.errors.EmptyDataError:
        flash('El archivo está vacío o corrupto', 'error')
        return redirect(url_for('index'))
    except pd.errors.ParserError:
        flash('Error al parsear el archivo. Verifica el formato', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        flash(f'Error al procesar el archivo: {str(e)[:100]}', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard/<session_id>/<viz_type>')
@require_session
def dashboard(session_id, viz_type):
    """Muestra el dashboard con visualizaciones"""
    start_time = time.time()
    
    # Obtener datos de sesión
    session_data = sessions_data[session_id]
    df = session_data['df']
    analyzer = session_data['analyzer']
    detected_cols = session_data['detected_cols']
    
    # Generar visualización según tipo
    viz_content = ''
    viz_title = ''
    viz_desc = ''
    insights = ''
    
    if viz_type == 'resumen':
        fig = analyzer.sales_summary()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '📊 Dashboard Ejecutivo de Ventas'
            viz_desc = 'Vista general del rendimiento de ventas'
            insights = generate_insights(df, analyzer, detected_cols)
        else:
            viz_content = error_message('No se pudo generar el dashboard resumen')
    
    elif viz_type == 'ventas_tiempo':
        fig = analyzer.sales_over_time()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '📈 Evolución de Ventas en el Tiempo'
            viz_desc = 'Análisis de tendencias y estacionalidad'
            insights = time_insights(df, analyzer, detected_cols)
        else:
            viz_content = error_message('No se encontraron columnas de fecha o ventas')
    
    elif viz_type == 'top_productos':
        fig = analyzer.top_products()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '🏆 Ranking de Productos'
            viz_desc = 'Productos con mejor rendimiento'
            insights = product_insights(df, analyzer, detected_cols)
        else:
            viz_content = error_message('No se encontraron columnas de productos')
    
    elif viz_type == 'ventas_categoria':
        fig = analyzer.sales_by_category()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '📦 Distribución de Ventas por Categoría'
            viz_desc = 'Participación de cada categoría en ventas totales'
        else:
            viz_content = error_message('No se encontraron categorías de productos')
    
    elif viz_type == 'ventas_region':
        fig = analyzer.sales_by_region()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '🌍 Ventas por Región'
            viz_desc = 'Rendimiento por ubicación geográfica'
        else:
            viz_content = error_message('No se encontraron columnas de región')
    
    elif viz_type == 'clientes':
        fig = analyzer.customer_segments()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '👥 Top Clientes'
            viz_desc = 'Clientes con mayores compras'
            insights = customer_insights(df, analyzer, detected_cols)
        else:
            viz_content = error_message('No se encontraron columnas de clientes')
    
    elif viz_type == 'descuentos':
        fig = analyzer.discount_analysis()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '🏷️ Análisis de Descuentos'
            viz_desc = 'Impacto de descuentos en ventas'
        else:
            viz_content = error_message('No se encontraron columnas de descuentos')
    
    elif viz_type == 'envios':
        fig = analyzer.shipping_analysis()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '🚚 Métodos de Envío'
            viz_desc = 'Preferencias de envío de clientes'
        else:
            viz_content = error_message('No se encontraron métodos de envío')
    
    elif viz_type == 'rentabilidad':
        fig = analyzer.profit_analysis()
        if fig:
            viz_content = fig.to_html(full_html=False, include_plotlyjs=False)
            viz_title = '💰 Análisis de Rentabilidad'
            viz_desc = 'Relación entre ventas y ganancias'
        else:
            viz_content = error_message('No se encontraron columnas de ganancias')
    
    elif viz_type == 'datos':
        # Mostrar tabla de datos
        viz_content = render_table(df.head(100))
        viz_title = f'📋 Vista previa de datos: {session_data["filename"]}'
        viz_desc = f'Mostrando 100 de {len(df)} registros'
    
    else:
        viz_content = error_message('Visualización no encontrada')
    
    processing_time = round(time.time() - start_time, 2)
    
    return render_template(
        'dashboard.html',
        session_id=session_id,
        filename=session_data['filename'],
        tipo=session_data['tipo'],
        rows=session_data['rows'],
        columnas=session_data['columns'],
        nulos=session_data['nulos'],
        metrics=session_data['metrics'],
        viz=viz_type,
        viz_title=viz_title,
        viz_desc=viz_desc,
        viz_content=viz_content,
        insights=insights,
        processing_time=processing_time,
        timestamp=datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def error_message(message):
    """Genera mensaje de error formateado"""
    return f'''
    <div style="text-align: center; padding: 50px;">
        <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
        <h3 style="color: #ff6b6b; margin-bottom: 15px;">{message}</h3>
        <p style="color: #868e96;">Intenta con otra visualización o sube otro archivo</p>
    </div>
    '''

def render_table(df, max_rows=100):
    """Genera tabla HTML formateada"""
    html = '<div class="table-wrapper"><table>'
    
    # Header
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead>'
    
    # Body
    html += '<tbody>'
    for _, row in df.head(max_rows).iterrows():
        html += '<tr>'
        for val in row:
            if pd.isna(val):
                html += '<td><span style="color: #adb5bd;">NULL</span></td>'
            else:
                html += f'<td>{str(val)[:50]}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    
    if len(df) > max_rows:
        html += f'<p style="text-align: center; margin-top: 20px; color: #868e96;">Mostrando {max_rows} de {len(df)} registros</p>'
    
    return html

def generate_insights(df, analyzer, cols):
    """Genera insights automáticos de ventas"""
    insights = []
    sales_col = analyzer.get_sales_column()
    
    if sales_col:
        total_sales = df[sales_col].sum()
        avg_sales = df[sales_col].mean()
        insights.append(f"💰 Ventas totales: ${total_sales:,.0f} | Promedio por transacción: ${avg_sales:,.2f}")
    
    if cols['product'] and sales_col:
        top_product = df.groupby(cols['product'][0])[sales_col].sum().nlargest(1)
        if len(top_product) > 0:
            insights.append(f"🏆 Producto estrella: {top_product.index[0]} (${top_product.values[0]:,.0f})")
    
    if cols['customer'] and sales_col:
        top_customer = df.groupby(cols['customer'][0])[sales_col].sum().nlargest(1)
        if len(top_customer) > 0:
            insights.append(f"👥 Mejor cliente: {top_customer.index[0]} (${top_customer.values[0]:,.0f})")
    
    if cols['region'] and sales_col:
        top_region = df.groupby(cols['region'][0])[sales_col].sum().nlargest(1)
        if len(top_region) > 0:
            insights.append(f"🌍 Región destacada: {top_region.index[0]} (${top_region.values[0]:,.0f})")
    
    if cols['quantity']:
        total_units = df[cols['quantity'][0]].sum()
        insights.append(f"📦 Unidades vendidas: {total_units:,.0f}")
    
    return '<br>'.join(insights) if insights else 'No se detectaron insights automáticos'

def time_insights(df, analyzer, cols):
    """Insights específicos de tiempo"""
    insights = []
    
    if cols['date'] and analyzer.get_sales_column():
        date_col = cols['date'][0]
        sales_col = analyzer.get_sales_column()
        
        df_dates = df.copy()
        df_dates[date_col] = pd.to_datetime(df_dates[date_col])
        
        # Mejor mes
        df_dates['mes'] = df_dates[date_col].dt.month_name()
        best_month = df_dates.groupby('mes')[sales_col].sum().nlargest(1)
        if len(best_month) > 0:
            insights.append(f"📅 Mejor mes: {best_month.index[0]} (${best_month.values[0]:,.0f})")
        
        # Mejor día de la semana
        df_dates['dia'] = df_dates[date_col].dt.day_name()
        best_day = df_dates.groupby('dia')[sales_col].sum().nlargest(1)
        if len(best_day) > 0:
            insights.append(f"📆 Mejor día: {best_day.index[0]} (${best_day.values[0]:,.0f})")
    
    return '<br>'.join(insights) if insights else 'No se detectaron insights temporales'

def product_insights(df, analyzer, cols):
    """Insights específicos de productos"""
    insights = []
    
    if cols['product'] and analyzer.get_sales_column():
        product_col = cols['product'][0]
        sales_col = analyzer.get_sales_column()
        
        # Productos únicos
        unique_products = df[product_col].nunique()
        insights.append(f"🏷️ Total productos únicos: {unique_products}")
        
        if cols['quantity']:
            qty_col = cols['quantity'][0]
            top_qty = df.groupby(product_col)[qty_col].sum().nlargest(1)
            if len(top_qty) > 0:
                insights.append(f"📊 Producto más vendido (unidades): {top_qty.index[0]} ({top_qty.values[0]:,.0f} unidades)")
    
    return '<br>'.join(insights) if insights else 'No se detectaron insights de productos'

def customer_insights(df, analyzer, cols):
    """Insights específicos de clientes"""
    insights = []
    
    if cols['customer'] and analyzer.get_sales_column():
        customer_col = cols['customer'][0]
        sales_col = analyzer.get_sales_column()
        
        unique_customers = df[customer_col].nunique()
        insights.append(f"👥 Total clientes únicos: {unique_customers}")
        
        # Ticket promedio por cliente
        customer_avg = df.groupby(customer_col)[sales_col].mean().mean()
        insights.append(f"💵 Ticket promedio por cliente: ${customer_avg:,.2f}")
    
    return '<br>'.join(insights) if insights else 'No se detectaron insights de clientes'

# ============================================
# LIMPIEZA DE SESIONES ANTIGUAS
# ============================================
def cleanup_old_sessions():
    """Elimina sesiones inactivas (>1 hora)"""
    current_time = datetime.now()
    to_delete = []
    
    for session_id, session_data in sessions_data.items():
        if 'timestamp' in session_data:
            session_time = datetime.fromisoformat(session_data['timestamp'])
            if (current_time - session_time).total_seconds() > 3600:
                to_delete.append(session_id)
    
    for session_id in to_delete:
        del sessions_data[session_id]
    
    logger.info(f"Limpieza: {len(to_delete)} sesiones eliminadas")

# ============================================
# INICIALIZACIÓN Y EJECUCIÓN
# ============================================
def create_sample_data():
    """Crea archivo de ejemplo si no existe"""
    sample_path = 'examples/sample_sales_data.csv'
    os.makedirs('examples', exist_ok=True)
    
    if not os.path.exists(sample_path):
        np.random.seed(42)
        n = 500
        
        sample_df = pd.DataFrame({
            'Fecha': pd.date_range(start='2023-01-01', periods=n, freq='D'),
            'Producto': np.random.choice(['Laptop Pro', 'Smartphone X', 'Tablet Air', 'Monitor 4K', 'Teclado Mecánico', 'Mouse Inalámbrico'], n),
            'Categoría': np.random.choice(['Electrónica', 'Computación', 'Accesorios'], n),
            'Ventas': np.random.uniform(100, 2500, n).round(2),
            'Cantidad': np.random.randint(1, 15, n),
            'Cliente': np.random.choice(['TechCorp', 'Innovate Inc', 'Global Solutions', 'Digital Store', 'Consumer Direct'], n),
            'Región': np.random.choice(['Norteamérica', 'Europa', 'Asia Pacífico', 'Latam', 'Oriente Medio'], n),
            'Descuento': np.random.choice([0, 0.05, 0.1, 0.15, 0.2, 0.25], n, p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05]),
            'Método_Envío': np.random.choice(['Estándar', 'Express', 'Same Day', 'Económico'], n),
            'Ganancia': np.random.uniform(20, 600, n).round(2)
        })
        
        sample_df.to_csv(sample_path, index=False)
        logger.info(f"Datos de ejemplo creados en {sample_path}")

if __name__ == '__main__':
    # Crear templates
    create_templates()
    
    # Crear datos de ejemplo
    create_sample_data()
    
    # Banner de inicio
    print("="*80)
    print("📈 SALES ANALYTICS PRO v1.0")
    print("="*80)
    print("🚀 Sistema de análisis inteligente de ventas")
    print("📊 Flask + Pandas + Plotly")
    print("🔍 Detector automático de columnas de ventas")
    print("⚡ 15+ visualizaciones interactivas")
    print("💡 Insights automáticos")
    print("="*80)
    print("📍 Servidor: http://localhost:5000")
    print("📍 Datos de ejemplo: http://localhost:5000/sample")
    print("="*80)
    print("📁 Creado por: Tu Nombre")
    print("📄 Licencia: MIT")
    print("🐙 GitHub: https://github.com/tuusuario/sales-analytics-pro")
    print("="*80)
    
    # Limpiar sesiones antiguas al iniciar
    cleanup_old_sessions()
    
    # Iniciar aplicación
    import webbrowser
    webbrowser.open('http://localhost:5000/splash')
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
