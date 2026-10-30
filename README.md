# Portafolio Bancario

Aplicación de escritorio en Python (tkinter) que simula un portafolio bancario: cuenta de ahorros, CDT, bonos, compra y venta de acciones, divisas, resumen con gráficas e historial de movimientos.

> Proyecto educativo: todas las operaciones son simuladas.

## Características

- Menú interactivo (barra de menú y pestañas) con interfaz gráfica.
- **Cuenta:** depósitos y retiros.
- **CDT:** apertura con monto, plazo y tasa E.A.; liquidación al vencimiento o anticipada.
- **Bonos:** compra y redención.
- **Acciones:** compra y venta con precio real y gráfica histórica (API de Yahoo Finance).
- **Divisas:** tasas de cambio con gráfica (API open.er-api.com).
- **Resumen:** patrimonio total y gráfica de distribución del portafolio.
- **Movimientos:** historial de operaciones.
- Toda la información se guarda en `datos_portafolio.json`.

## Requisitos

- Python 3.9 o superior (tkinter viene incluido en Windows y macOS).
- En Linux, instalar tkinter: `sudo apt install python3-tk`
- Conexión a internet para las gráficas de acciones y divisas.

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO

# 2. (Opcional) Crear un entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python portafolio_bancario.py
```

En Mac/Linux usa `python3` en lugar de `python`.

## Uso rápido

1. Ve a la pestaña **Cuenta** y deposita dinero.
2. Abre un CDT, compra un bono o compra acciones (por ejemplo `AAPL`).
3. Revisa el **Resumen** y los **Movimientos**.

## Tecnologías

Python, tkinter, matplotlib, requests.
