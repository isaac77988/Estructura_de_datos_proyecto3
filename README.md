\# Portafolio Bancario e Inversiones



Aplicación de escritorio desarrollada en Python (tkinter + matplotlib) para el seguimiento, monitoreo y evaluación del desempeño de un portafolio de inversiones compuesto por activos de renta fija (CDT, bonos corporativos, TES) y renta variable (acciones internacionales y locales, ETFs), incorporando gestión de comisiones de bróker y dividendos.



> Proyecto académico educativo: simulaciones financieras y cotizaciones de mercado en tiempo real.



\## Características Principales



\- \*\*Moneda Única (COP):\*\* Todos los cálculos, valores patrimoniales y transacciones se presentan en pesos colombianos con formato local (`$ 1.234.567,89`).

\- \*\*Cuenta de Ahorros:\*\* Depósitos y retiros de efectivo con registro histórico de movimientos.

\- \*\*Renta Fija:\*\* Gestión de CDT, bonos corporativos y Títulos de Deuda Pública (\*\*TES\*\* en tasa fija y UVR) con valoración contractual e intereses causados.

\- \*\*Renta Variable (Acciones):\*\* Catálogo de más de 20 empresas y ETFs con precios de mercado en tiempo real mediante `yfinance`, considerando comisiones de bróker e historial de transacciones.

\- \*\*Dividendos:\*\* Módulo dedicado para el registro de ingresos por dividendos netos recibidos.

\- \*\*Divisas y TRM:\*\* Consulta de tipos de cambio internacionales respaldados por `open.er-api.com`.

\- \*\*Rendimiento y Simulación:\*\* Análisis acumulado de rentabilidad por producto y simulador histórico de inversión a largo plazo.



\## Requisitos del Sistema



\- Python 3.9 o superior.

\- Conexión a internet activa para actualización de precios bursátiles y divisas.



\## Instalación y Ejecución



```bash

\# 1. Clonar el repositorio

git clone \[https://github.com/TU\_USUARIO/TU\_REPOSITORIO.git](https://github.com/TU\_USUARIO/TU\_REPOSITORIO.git)

cd TU\_REPOSITORIO



\# 2. Crear y activar entorno virtual

python -m venv venv

\# Windows:

venv\\Scripts\\activate

\# Mac / Linux:

source venv/bin/activate



\# 3. Instalar dependencias

pip install -r requirements.txt



\# 4. Ejecutar la aplicación

python main.py

