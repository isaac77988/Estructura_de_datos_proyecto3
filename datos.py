"""
datos.py - Persistencia, catálogos, formatos y modelos de portafolio.
Soporta CDT, Bonos, TES, Acciones con historial/comisiones y Dividendos.
"""
import json
import os
import re
from datetime import date, timedelta
from tkinter import messagebox

ARCHIVO = "datos_portafolio.json"

CATALOGO_ACCIONES = [
    ("KO", "Coca-Cola", "Consumo"),
    ("PEP", "PepsiCo", "Consumo"),
    ("NKE", "Nike", "Consumo"),
    ("MCD", "McDonald's", "Consumo"),
    ("AAPL", "Apple", "Tecnología"),
    ("MSFT", "Microsoft", "Tecnología"),
    ("GOOGL", "Alphabet (Google)", "Tecnología"),
    ("AMZN", "Amazon", "Tecnología"),
    ("NVDA", "NVIDIA", "Tecnología"),
    ("TSLA", "Tesla", "Tecnología"),
    ("JPM", "JPMorgan Chase", "Finanzas"),
    ("V", "Visa", "Finanzas"),
    ("XOM", "ExxonMobil", "Energía"),
    ("JNJ", "Johnson & Johnson", "Salud"),
    ("T", "AT&T", "Telecom"),
    ("EC", "Ecopetrol (Colombia)", "Colombia"),
    ("CIB", "Bancolombia (Colombia)", "Colombia"),
    ("SPY", "ETF S&P 500", "ETF"),
    ("QQQ", "ETF Nasdaq 100", "ETF"),
]

OPCIONES_ACCIONES = sorted(f"{nombre} ({simbolo})" for simbolo, nombre, _ in CATALOGO_ACCIONES)
NOMBRES_ACCIONES = {simbolo: nombre for simbolo, nombre, _ in CATALOGO_ACCIONES}


def extraer_simbolo(texto):
    texto = str(texto).strip()
    m = re.search(r"\(([^()]+)\)\s*$", texto)
    return (m.group(1) if m else texto).strip().upper()


def nombre_accion(simbolo):
    nombre = NOMBRES_ACCIONES.get(simbolo)
    return f"{nombre} ({simbolo})" if nombre else simbolo


class GestorPortafolio:
    """Clase principal para la gestión y persistencia del portafolio financiero."""

    def __init__(self, archivo=ARCHIVO):
        self.archivo = archivo
        self.datos = self.cargar()

    def datos_vacios(self):
        return {
            "saldo": 0.0,
            "cdts": [],
            "bonos": [],
            "tes": [],
            "acciones": {},          # Historial de operaciones o tenencia agregada
            "transacciones": [],     # Registro detallado de compras/ventas con comisiones
            "dividendos": [],        # Registro de dividendos recibidos
            "movimientos": [],
        }

    def cargar(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                base = self.datos_vacios()
                base.update(datos)
                return base
            except (json.JSONDecodeError, OSError):
                messagebox.showwarning("Aviso", "No se pudo leer el archivo de datos. Se inicia vacío.")
        return self.datos_vacios()

    def guardar(self):
        with open(self.archivo, "w", encoding="utf-8") as f:
            json.dump(self.datos, f, indent=2, ensure_ascii=False)


# Instancia global de persistencia
gestor_portafolio = GestorPortafolio()


def cargar():
    return gestor_portafolio.cargar()


def guardar(datos):
    gestor_portafolio.datos = datos
    gestor_portafolio.guardar()


def datos_vacios():
    return gestor_portafolio.datos_vacios()


# ----------------------------------------------------------------------
# Formato de Números (Estándar Colombiano)
# ----------------------------------------------------------------------
def leer_numero(texto, nombre="Valor", permitir_cero=False):
    t = str(texto).strip().replace("$", "").replace(" ", "")
    if "." in t and "," in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".") if t.count(",") == 1 else t.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        n = float(t)
    except ValueError:
        raise ValueError(f"{nombre} debe ser un número.")
    if n < 0 or (n == 0 and not permitir_cero):
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return n


def num(x, dec=2):
    x = round(float(x), dec)
    if x == 0:
        x = 0.0
    s = f"{abs(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"-{s}" if x < 0 else s


def moneda(x):
    s = num(x)
    return f"-$ {s[1:]}" if s.startswith("-") else f"$ {s}"


def pct(x, signo=True):
    s = num(x, 2)
    if signo and x > 0 and not s.startswith("-"):
        s = "+" + s
    return f"{s}%"


# ----------------------------------------------------------------------
# Cálculos de Activos de Renta Fija
# ----------------------------------------------------------------------
def valor_actual_cdt(c, hoy=None):
    hoy = hoy or date.today()
    inicio = date.fromisoformat(c["vence"]) - timedelta(days=c["plazo"])
    dias = min(max((hoy - inicio).days, 0), c["plazo"])
    return c["monto"] * (1 + c["tasa"] / 100) ** (dias / 365)


def valor_actual_bono(b, hoy=None):
    hoy = hoy or date.today()
    total = 30 * b["plazo"]
    inicio = date.fromisoformat(b["vence"]) - timedelta(days=total)
    dias = min(max((hoy - inicio).days, 0), total)
    return b["monto"] + (b["final"] - b["monto"]) * dias / total


def valor_actual_tes(t, hoy=None):
    """Valoración contractual y de mercado estimada para TES (Títulos de Deuda Pública)."""
    hoy = hoy or date.today()
    total_dias = (date.fromisoformat(t["vence"]) - date.fromisoformat(t["emision"])).days
    if total_dias <= 0:
        return t["monto"]
    transcurridos = min(max((hoy - date.fromisoformat(t["emision"])).days, 0), total_dias)
    # Acumulación lineal o compuesta del cupón anual
    return t["monto"] * (1 + (t["tasa"] / 100) * (transcurridos / 365))