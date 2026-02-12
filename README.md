# 📈 Sales Analytics 

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-orange.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-red.svg)

**Sales Analytics Pro** es una aplicación web profesional para el análisis inteligente de datos de ventas. Detecta automáticamente columnas de ventas, productos, clientes, regiones y más, generando visualizaciones interactivas sin necesidad de configuración.

![Dashboard Preview](docs/screenshots/dashboard.png)

## ✨ Características

### 🎯 Detección Automática
- **Columnas de ventas**: Detecta ventas, ingresos, precios sin importar el nombre
- **Productos**: Identifica columnas de productos, categorías, descripciones
- **Clientes**: Reconoce datos de clientes, compradores, cuentas
- **Regiones**: Detecta ubicaciones geográficas automáticamente
- **Fechas**: Identifica columnas temporales para análisis de tendencias

### 📊 Visualizaciones Interactivas
- **Dashboard Ejecutivo**: Vista general con múltiples métricas
- **Ventas en el Tiempo**: Evolución y tendencias
- **Top Productos**: Ranking por ventas y unidades
- **Análisis por Región**: Rendimiento geográfico
- **Segmentación de Clientes**: Identificación de mejores clientes
- **Análisis de Descuentos**: Impacto en ventas
- **Métodos de Envío**: Preferencias logísticas
- **Rentabilidad**: Relación ventas-ganancias

### 💡 Insights Automáticos
- Productos estrella
- Mejores clientes
- Regiones destacadas
- Patrones temporales
- Recomendaciones accionables

### 🔒 Seguridad y Privacidad
- **100% Local**: Tus datos nunca salen de tu computadora
- **Sin Base de Datos**: Todo en memoria, se elimina al cerrar
- **Sesiones Temporales**: Datos disponibles solo durante el análisis

## 🚀 Instalación Rápida

### Opción 1: Clonar repositorio

```bash
# Clonar el repositorio
git clone https://github.com/tuusuario/sales-analytics-pro.git
cd sales-analytics-pro

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py
