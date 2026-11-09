"""
api.py - Consultas a servicios externos y gestión de cotizaciones.
Todos los valores se entregan en pesos colombianos (COP).
"""
from bisect import bisect_right
import requests
import yfinance as yf


class ClienteAPI:
    """Cliente para la gestión de tasas de cambio y cotizaciones de mercado."""

    def __init__(self):
        self._cache_tasas_usd = None
        self._cache_dolar = {}
        self._cache_acciones = {}

    def obtener_tasas_usd(self):
        """Obtiene las tasas de cambio desde la API externa o caché."""
        if self._cache_tasas_usd:
            return self._cache_tasas_usd
        try:
            r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
            r.raise_for_status()
            self._cache_tasas_usd = r.json()["rates"]
            return self._cache_tasas_usd
        except Exception as e:
            raise RuntimeError(f"Error al consultar tasas USD: {e}")

    def obtener_tasas_cop(self):
        """Devuelve un diccionario con el valor en pesos colombianos (COP) de 1 unidad de cada moneda."""
        tasas = self.obtener_tasas_usd()
        cop = tasas.get("COP", 1.0)
        return {m: cop / v for m, v in tasas.items() if v}

    def _serie_cierres(self, hist):
        """Convierte el histórico de yfinance en una lista limpia de tuplas (fecha, cierre)."""
        serie = []
        for fecha, cierre in hist["Close"].dropna().items():
            if getattr(fecha, "tzinfo", None) is not None:
                fecha = fecha.tz_localize(None)
            serie.append((fecha.to_pydatetime(), float(cierre)))
        return serie

    def _serie_dolar(self, rango):
        """Obtiene el histórico del dólar en pesos (COP=X) con soporte de caché por sesión."""
        if rango in self._cache_dolar:
            return self._cache_dolar[rango]
        try:
            hist = yf.Ticker("COP=X").history(period=rango, interval="1d")
            serie = [(f.date(), c) for f, c in self._serie_cierres(hist)]
            if serie:
                self._cache_dolar[rango] = serie
            return serie
        except Exception:
            return []

    def obtener_trm(self):
        """Devuelve la tasa representativa del mercado (TRM) actual en pesos colombianos."""
        serie = self._serie_dolar("5d")
        if serie and serie[-1][1] > 0:
            return serie[-1][1]
        tasas = self.obtener_tasas_usd()
        return float(tasas.get("COP", 4000.0))

    def consultar_accion_cop(self, simbolo, rango="3mo"):
        """Consulta una acción mediante yfinance, aplicando la conversión histórica o actual a COP."""
        cache_key = f"{simbolo}_{rango}"
        if cache_key in self._cache_acciones:
            return self._cache_acciones[cache_key]

        ticker = yf.Ticker(simbolo)
        hist = ticker.history(period=rango, interval="1d")
        if hist is None or hist.empty:
            raise ValueError(f"Símbolo no encontrado o sin datos: {simbolo}")
        
        serie = self._serie_cierres(hist)
        if not serie:
            raise ValueError("Sin datos de precios válidos para la serie")

        precio = serie[-1][1]
        moneda_orig = "USD"
        try:
            ultimo = ticker.fast_info.get("last_price")
            if ultimo and ultimo > 0:
                precio = float(ultimo)
        except Exception:
            pass

        try:
            moneda_orig = str(ticker.fast_info.get("currency") or "USD").upper()
        except Exception:
            pass

        if moneda_orig == "COP":
            resultado = {
                "precio": precio,
                "serie": serie,
                "precio_usd": precio,
                "moneda": "COP",
                "trm": 1.0,
            }
            self._cache_acciones[cache_key] = resultado
            return resultado

        if moneda_orig == "USD":
            dolar = self._serie_dolar(rango)
            factor_actual = dolar[-1][1] if dolar else self.obtener_trm()
            if dolar:
                fechas_fx = [d for d, _ in dolar]
                serie_cop = []
                for f, c in serie:
                    i = bisect_right(fechas_fx, f.date()) - 1
                    tasa = dolar[i][1] if i >= 0 else dolar[0][1]
                    serie_cop.append((f, c * tasa))
            else:
                serie_cop = [(f, c * factor_actual) for f, c in serie]
        else:
            tasas_cop = self.obtener_tasas_cop()
            factor_actual = tasas_cop.get(moneda_orig, self.obtener_trm())
            serie_cop = [(f, c * factor_actual) for f, c in serie]

        resultado = {
            "precio": precio * factor_actual,
            "serie": serie_cop,
            "precio_usd": precio,
            "moneda": moneda_orig,
            "trm": factor_actual,
        }
        self._cache_acciones[cache_key] = resultado
        return resultado


_cliente_global = ClienteAPI()


def api_tasas_usd():
    return _cliente_global.obtener_tasas_usd()


def api_tasas_cop():
    return _cliente_global.obtener_tasas_cop()


def api_trm():
    return _cliente_global.obtener_trm()


def api_accion_cop(simbolo, rango="3mo"):
    return _cliente_global.consultar_accion_cop(simbolo, rango)
