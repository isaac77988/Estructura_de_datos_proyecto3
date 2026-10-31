import json
import os
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import matplotlib
import requests
import yfinance as yf

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

ARCHIVO = "datos_portafolio.json"


# ----------------------------------------------------------------------
# Persistencia
# ----------------------------------------------------------------------
def datos_vacios():
    return {"saldo": 0.0, "cdts": [], "bonos": [], "acciones": {}, "movimientos": []}


def cargar():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                datos = json.load(f)
            base = datos_vacios()
            base.update(datos)
            return base
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Aviso", "No se pudo leer el archivo de datos. Se inicia vacío.")
    return datos_vacios()


def guardar(datos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


# ----------------------------------------------------------------------
# APIs
# ----------------------------------------------------------------------
def api_historico_accion(simbolo, rango="3mo"):
    """Devuelve (precio_actual, [(fecha, cierre), ...]) desde Yahoo Finance."""
    ticker = yf.Ticker(simbolo)
    hist = ticker.history(period=rango, interval="1d")
    if hist is None or hist.empty:
        raise ValueError("Símbolo no encontrado o sin datos")
    serie = []
    for fecha, cierre in hist["Close"].dropna().items():
        if getattr(fecha, "tzinfo", None) is not None:
            fecha = fecha.tz_localize(None)
        serie.append((fecha.to_pydatetime(), float(cierre)))
    if not serie:
        raise ValueError("Sin datos de precios")
    precio = serie[-1][1]
    try:
        ultimo = ticker.fast_info["last_price"]
        if ultimo and ultimo > 0:
            precio = float(ultimo)
    except Exception:  # noqa: BLE001
        pass  # se usa el último cierre
    return precio, serie


def api_tasas_usd():
    r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
    r.raise_for_status()
    return r.json()["rates"]


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def leer_numero(texto, nombre="Valor", permitir_cero=False):
    try:
        n = float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{nombre} debe ser un número.")
    if n < 0 or (n == 0 and not permitir_cero):
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return n


def moneda(x):
    return f"${x:,.2f}"


# ----------------------------------------------------------------------
# Aplicación
# ----------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Portafolio Bancario")
        self.geometry("1000x680")
        self.datos = cargar()
        self.valores_mercado = {}  # símbolo -> último precio consultado

        self._crear_menu()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_resumen = ttk.Frame(self.nb)
        self.tab_cuenta = ttk.Frame(self.nb)
        self.tab_cdt = ttk.Frame(self.nb)
        self.tab_bonos = ttk.Frame(self.nb)
        self.tab_acciones = ttk.Frame(self.nb)
        self.tab_divisas = ttk.Frame(self.nb)
        self.tab_mov = ttk.Frame(self.nb)
        for tab, nombre in [
            (self.tab_resumen, "Resumen"),
            (self.tab_cuenta, "Cuenta"),
            (self.tab_cdt, "CDT"),
            (self.tab_bonos, "Bonos"),
            (self.tab_acciones, "Acciones"),
            (self.tab_divisas, "Divisas"),
            (self.tab_mov, "Movimientos"),
        ]:
            self.nb.add(tab, text=nombre)

        self._ui_resumen()
        self._ui_cuenta()
        self._ui_cdt()
        self._ui_bonos()
        self._ui_acciones()
        self._ui_divisas()
        self._ui_movimientos()
        self.refrescar()

    # ------------------------------------------------------------ menú
    def _crear_menu(self):
        barra = tk.Menu(self)
        m_archivo = tk.Menu(barra, tearoff=0)
        m_archivo.add_command(label="Guardar", command=self._guardar_manual)
        m_archivo.add_command(label="Borrar todos los datos", command=self._borrar_todo)
        m_archivo.add_separator()
        m_archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=m_archivo)

        m_serv = tk.Menu(barra, tearoff=0)
        for i, nombre in enumerate(["Resumen", "Cuenta", "CDT", "Bonos", "Acciones", "Divisas", "Movimientos"]):
            m_serv.add_command(label=nombre, command=lambda i=i: self.nb.select(i))
        barra.add_cascade(label="Servicios", menu=m_serv)

        m_ayuda = tk.Menu(barra, tearoff=0)
        m_ayuda.add_command(
            label="Acerca de",
            command=lambda: messagebox.showinfo(
                "Acerca de", "Portafolio bancario educativo.\nLas operaciones son simuladas."
            ),
        )
        barra.add_cascade(label="Ayuda", menu=m_ayuda)
        self.config(menu=barra)

    def _guardar_manual(self):
        guardar(self.datos)
        messagebox.showinfo("Guardado", f"Datos guardados en {ARCHIVO}")

    def _borrar_todo(self):
        if messagebox.askyesno("Confirmar", "¿Borrar TODOS los datos del portafolio?"):
            self.datos = datos_vacios()
            self.guardar_y_refrescar()

    def guardar_y_refrescar(self):
        guardar(self.datos)
        self.refrescar()

    def registrar(self, tipo, detalle, monto):
        self.datos["movimientos"].append(
            {"fecha": datetime.now().strftime("%Y-%m-%d %H:%M"), "tipo": tipo, "detalle": detalle, "monto": monto}
        )

    # ------------------------------------------------------------ resumen
    def _ui_resumen(self):
        top = ttk.Frame(self.tab_resumen)
        top.pack(fill="x", padx=10, pady=10)
        self.lbl_resumen = ttk.Label(top, text="", font=("Segoe UI", 11), justify="left")
        self.lbl_resumen.pack(side="left")
        ttk.Button(top, text="Actualizar precios de mercado", command=self.actualizar_mercado).pack(side="right")

        self.fig_res = Figure(figsize=(6, 4), dpi=100)
        self.canvas_res = FigureCanvasTkAgg(self.fig_res, master=self.tab_resumen)
        self.canvas_res.get_tk_widget().pack(fill="both", expand=True)

    def valor_acciones(self):
        total = 0.0
        for s, a in self.datos["acciones"].items():
            precio = self.valores_mercado.get(s)
            total += a["cantidad"] * precio if precio else a["costo_total"]
        return total

    def actualizar_mercado(self):
        if not self.datos["acciones"]:
            messagebox.showinfo("Info", "No tienes acciones registradas.")
            return
        self.config(cursor="watch")
        self.update()
        errores = []
        for s in self.datos["acciones"]:
            try:
                self.valores_mercado[s], _ = api_historico_accion(s, "5d")
            except Exception as e:  # noqa: BLE001
                errores.append(f"{s}: {e}")
        self.config(cursor="")
        self.refrescar()
        if errores:
            messagebox.showwarning("Algunos precios fallaron", "\n".join(errores))

    def refrescar_resumen(self):
        d = self.datos
        cdt = sum(c["monto"] for c in d["cdts"])
        bonos = sum(b["monto"] for b in d["bonos"])
        acc = self.valor_acciones()
        total = d["saldo"] + cdt + bonos + acc
        self.lbl_resumen.config(
            text=(
                f"Saldo disponible:  {moneda(d['saldo'])}\n"
                f"CDT (capital):     {moneda(cdt)}\n"
                f"Bonos (capital):   {moneda(bonos)}\n"
                f"Acciones:          {moneda(acc)}\n"
                f"PATRIMONIO TOTAL:  {moneda(total)}"
            )
        )
        self.fig_res.clear()
        ax = self.fig_res.add_subplot(111)
        partes = [("Efectivo", d["saldo"]), ("CDT", cdt), ("Bonos", bonos), ("Acciones", acc)]
        partes = [(n, v) for n, v in partes if v > 0]
        if partes:
            ax.pie([v for _, v in partes], labels=[n for n, _ in partes], autopct="%1.1f%%", startangle=90)
            ax.set_title("Distribución del portafolio")
        else:
            ax.text(0.5, 0.5, "Aún no hay datos.\nComienza depositando en la pestaña Cuenta.", ha="center", va="center")
            ax.axis("off")
        self.canvas_res.draw()

    # ------------------------------------------------------------ cuenta
    def _ui_cuenta(self):
        f = ttk.LabelFrame(self.tab_cuenta, text="Cuenta de ahorros")
        f.pack(padx=20, pady=20, anchor="n")
        self.lbl_saldo = ttk.Label(f, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_saldo.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        ttk.Label(f, text="Monto:").grid(row=1, column=0, padx=5, pady=5)
        self.e_monto_cuenta = ttk.Entry(f)
        self.e_monto_cuenta.grid(row=1, column=1, padx=5)
        ttk.Button(f, text="Depositar", command=self.depositar).grid(row=2, column=0, pady=10, padx=5)
        ttk.Button(f, text="Retirar", command=self.retirar).grid(row=2, column=1, pady=10, padx=5)

    def depositar(self):
        try:
            m = leer_numero(self.e_monto_cuenta.get(), "El monto")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        self.datos["saldo"] += m
        self.registrar("Depósito", "Cuenta de ahorros", m)
        self.e_monto_cuenta.delete(0, "end")
        self.guardar_y_refrescar()

    def retirar(self):
        try:
            m = leer_numero(self.e_monto_cuenta.get(), "El monto")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        if m > self.datos["saldo"]:
            return messagebox.showerror("Error", "Saldo insuficiente.")
        self.datos["saldo"] -= m
        self.registrar("Retiro", "Cuenta de ahorros", -m)
        self.e_monto_cuenta.delete(0, "end")
        self.guardar_y_refrescar()

    # ------------------------------------------------------------ CDT
    def _ui_cdt(self):
        f = ttk.LabelFrame(self.tab_cdt, text="Abrir nuevo CDT")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Monto:").grid(row=0, column=0, padx=5, pady=5)
        self.e_cdt_monto = ttk.Entry(f, width=15)
        self.e_cdt_monto.grid(row=0, column=1)
        ttk.Label(f, text="Plazo (días):").grid(row=0, column=2, padx=5)
        self.c_cdt_plazo = ttk.Combobox(f, values=[90, 180, 360, 540], width=8)
        self.c_cdt_plazo.set(180)
        self.c_cdt_plazo.grid(row=0, column=3)
        ttk.Label(f, text="Tasa E.A. (%):").grid(row=0, column=4, padx=5)
        self.e_cdt_tasa = ttk.Entry(f, width=8)
        self.e_cdt_tasa.insert(0, "9.5")
        self.e_cdt_tasa.grid(row=0, column=5)
        ttk.Button(f, text="Abrir CDT", command=self.abrir_cdt).grid(row=0, column=6, padx=10)

        cols = ("monto", "tasa", "plazo", "vence", "final", "estado")
        self.tree_cdt = ttk.Treeview(self.tab_cdt, columns=cols, show="headings", height=12)
        for c, t in zip(cols, ["Capital", "Tasa EA %", "Plazo (días)", "Vencimiento", "Valor final", "Estado"]):
            self.tree_cdt.heading(c, text=t)
            self.tree_cdt.column(c, width=130, anchor="center")
        self.tree_cdt.pack(fill="both", expand=True, padx=10)
        ttk.Button(self.tab_cdt, text="Liquidar CDT seleccionado", command=self.liquidar_cdt).pack(pady=8)

    def abrir_cdt(self):
        try:
            monto = leer_numero(self.e_cdt_monto.get(), "El monto")
            plazo = int(leer_numero(self.c_cdt_plazo.get(), "El plazo"))
            tasa = leer_numero(self.e_cdt_tasa.get(), "La tasa")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        if monto > self.datos["saldo"]:
            return messagebox.showerror("Error", "Saldo insuficiente en la cuenta.")
        final = monto * (1 + tasa / 100) ** (plazo / 365)
        self.datos["saldo"] -= monto
        self.datos["cdts"].append(
            {
                "monto": monto,
                "tasa": tasa,
                "plazo": plazo,
                "vence": (date.today() + timedelta(days=plazo)).isoformat(),
                "final": round(final, 2),
            }
        )
        self.registrar("CDT", f"Apertura a {plazo} días al {tasa}% EA", -monto)
        self.guardar_y_refrescar()

    def liquidar_cdt(self):
        sel = self.tree_cdt.selection()
        if not sel:
            return messagebox.showinfo("Info", "Selecciona un CDT.")
        i = int(sel[0])
        c = self.datos["cdts"][i]
        vencido = date.today() >= date.fromisoformat(c["vence"])
        if vencido:
            pago = c["final"]
        else:
            if not messagebox.askyesno(
                "Cancelación anticipada",
                "El CDT aún no vence. Si lo cancelas solo recibirás el capital, sin rendimientos. ¿Continuar?",
            ):
                return
            pago = c["monto"]
        self.datos["saldo"] += pago
        self.datos["cdts"].pop(i)
        self.registrar("CDT", "Liquidación" + ("" if vencido else " anticipada"), pago)
        self.guardar_y_refrescar()

    # ------------------------------------------------------------ Bonos
    def _ui_bonos(self):
        f = ttk.LabelFrame(self.tab_bonos, text="Comprar bono")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Nombre/emisor:").grid(row=0, column=0, padx=5, pady=5)
        self.e_bono_nombre = ttk.Entry(f, width=18)
        self.e_bono_nombre.grid(row=0, column=1)
        ttk.Label(f, text="Monto:").grid(row=0, column=2, padx=5)
        self.e_bono_monto = ttk.Entry(f, width=12)
        self.e_bono_monto.grid(row=0, column=3)
        ttk.Label(f, text="Tasa anual (%):").grid(row=0, column=4, padx=5)
        self.e_bono_tasa = ttk.Entry(f, width=8)
        self.e_bono_tasa.insert(0, "11")
        self.e_bono_tasa.grid(row=0, column=5)
        ttk.Label(f, text="Plazo (meses):").grid(row=0, column=6, padx=5)
        self.e_bono_plazo = ttk.Entry(f, width=6)
        self.e_bono_plazo.insert(0, "24")
        self.e_bono_plazo.grid(row=0, column=7)
        ttk.Button(f, text="Comprar", command=self.comprar_bono).grid(row=0, column=8, padx=10)

        cols = ("nombre", "monto", "tasa", "plazo", "vence", "final")
        self.tree_bonos = ttk.Treeview(self.tab_bonos, columns=cols, show="headings", height=12)
        for c, t in zip(cols, ["Emisor", "Capital", "Tasa %", "Plazo (meses)", "Vencimiento", "Valor al vencimiento"]):
            self.tree_bonos.heading(c, text=t)
            self.tree_bonos.column(c, width=130, anchor="center")
        self.tree_bonos.pack(fill="both", expand=True, padx=10)
        ttk.Button(self.tab_bonos, text="Redimir bono seleccionado", command=self.redimir_bono).pack(pady=8)

    def comprar_bono(self):
        nombre = self.e_bono_nombre.get().strip() or "Bono"
        try:
            monto = leer_numero(self.e_bono_monto.get(), "El monto")
            tasa = leer_numero(self.e_bono_tasa.get(), "La tasa")
            meses = int(leer_numero(self.e_bono_plazo.get(), "El plazo"))
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        if monto > self.datos["saldo"]:
            return messagebox.showerror("Error", "Saldo insuficiente en la cuenta.")
        self.datos["saldo"] -= monto
        self.datos["bonos"].append(
            {
                "nombre": nombre,
                "monto": monto,
                "tasa": tasa,
                "plazo": meses,
                "vence": (date.today() + timedelta(days=30 * meses)).isoformat(),
                "final": round(monto * (1 + tasa / 100 * meses / 12), 2),
            }
        )
        self.registrar("Bono", f"Compra {nombre} al {tasa}% a {meses} meses", -monto)
        self.guardar_y_refrescar()

    def redimir_bono(self):
        sel = self.tree_bonos.selection()
        if not sel:
            return messagebox.showinfo("Info", "Selecciona un bono.")
        i = int(sel[0])
        b = self.datos["bonos"][i]
        if date.today() >= date.fromisoformat(b["vence"]):
            pago = b["final"]
        else:
            if not messagebox.askyesno(
                "Venta anticipada",
                "El bono aún no vence. Se venderá con descuento (solo recibirás el capital). ¿Continuar?",
            ):
                return
            pago = b["monto"]
        self.datos["saldo"] += pago
        self.datos["bonos"].pop(i)
        self.registrar("Bono", f"Redención {b['nombre']}", pago)
        self.guardar_y_refrescar()

    # ------------------------------------------------------------ Acciones
    def _ui_acciones(self):
        f = ttk.LabelFrame(self.tab_acciones, text="Compra y venta de acciones")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Símbolo (ej. AAPL, MSFT, TSLA):").grid(row=0, column=0, padx=5, pady=5)
        self.e_simbolo = ttk.Entry(f, width=10)
        self.e_simbolo.grid(row=0, column=1)
        ttk.Label(f, text="Cantidad:").grid(row=0, column=2, padx=5)
        self.e_cantidad = ttk.Entry(f, width=8)
        self.e_cantidad.insert(0, "1")
        self.e_cantidad.grid(row=0, column=3)
        ttk.Button(f, text="Consultar y graficar", command=self.consultar_accion).grid(row=0, column=4, padx=5)
        ttk.Button(f, text="Comprar", command=lambda: self.operar_accion("compra")).grid(row=0, column=5, padx=5)
        ttk.Button(f, text="Vender", command=lambda: self.operar_accion("venta")).grid(row=0, column=6, padx=5)
        self.lbl_precio = ttk.Label(f, text="Precio: —")
        self.lbl_precio.grid(row=1, column=0, columnspan=7, sticky="w", padx=5)

        cuerpo = ttk.Frame(self.tab_acciones)
        cuerpo.pack(fill="both", expand=True, padx=10)
        cols = ("simbolo", "cantidad", "costo", "mercado")
        self.tree_acc = ttk.Treeview(cuerpo, columns=cols, show="headings", height=8)
        for c, t in zip(cols, ["Símbolo", "Cantidad", "Costo total", "Valor de mercado"]):
            self.tree_acc.heading(c, text=t)
            self.tree_acc.column(c, width=110, anchor="center")
        self.tree_acc.pack(side="left", fill="y")
        self.fig_acc = Figure(figsize=(5, 3.5), dpi=100)
        self.canvas_acc = FigureCanvasTkAgg(self.fig_acc, master=cuerpo)
        self.canvas_acc.get_tk_widget().pack(side="left", fill="both", expand=True)

    def consultar_accion(self, silencioso=False):
        simbolo = self.e_simbolo.get().strip().upper()
        if not simbolo:
            messagebox.showerror("Error", "Escribe un símbolo.")
            return None
        self.config(cursor="watch")
        self.update()
        try:
            precio, serie = api_historico_accion(simbolo)
        except Exception as e:  # noqa: BLE001
            self.config(cursor="")
            messagebox.showerror("Error de API", f"No se pudo consultar {simbolo}:\n{e}")
            return None
        self.config(cursor="")
        self.valores_mercado[simbolo] = precio
        self.lbl_precio.config(text=f"Precio actual de {simbolo}: {moneda(precio)} USD")
        self.fig_acc.clear()
        ax = self.fig_acc.add_subplot(111)
        ax.plot([f for f, _ in serie], [c for _, c in serie], color="tab:blue")
        ax.set_title(f"{simbolo} - últimos 3 meses (API Yahoo Finance)")
        ax.set_ylabel("Cierre (USD)")
        ax.grid(alpha=0.3)
        self.fig_acc.autofmt_xdate()
        self.canvas_acc.draw()
        return simbolo, precio

    def operar_accion(self, tipo):
        try:
            cant = leer_numero(self.e_cantidad.get(), "La cantidad")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        res = self.consultar_accion()
        if not res:
            return
        simbolo, precio = res
        total = cant * precio
        acc = self.datos["acciones"]
        if tipo == "compra":
            if total > self.datos["saldo"]:
                return messagebox.showerror(
                    "Error", f"Saldo insuficiente. Necesitas {moneda(total)}."
                )
            self.datos["saldo"] -= total
            a = acc.setdefault(simbolo, {"cantidad": 0.0, "costo_total": 0.0})
            a["cantidad"] += cant
            a["costo_total"] += total
            self.registrar("Acción", f"Compra {cant:g} x {simbolo} @ {precio:,.2f}", -total)
        else:
            a = acc.get(simbolo)
            if not a or a["cantidad"] < cant:
                return messagebox.showerror("Error", "No tienes suficientes acciones para vender.")
            costo_unit = a["costo_total"] / a["cantidad"]
            a["cantidad"] -= cant
            a["costo_total"] -= costo_unit * cant
            if a["cantidad"] <= 1e-9:
                del acc[simbolo]
            self.datos["saldo"] += total
            self.registrar("Acción", f"Venta {cant:g} x {simbolo} @ {precio:,.2f}", total)
        self.guardar_y_refrescar()

    # ------------------------------------------------------------ Divisas
    def _ui_divisas(self):
        f = ttk.Frame(self.tab_divisas)
        f.pack(fill="x", padx=10, pady=10)
        ttk.Button(f, text="Consultar tasas de cambio (API)", command=self.consultar_divisas).pack(side="left")
        self.lbl_divisas = ttk.Label(f, text="")
        self.lbl_divisas.pack(side="left", padx=15)
        self.fig_div = Figure(figsize=(6, 4), dpi=100)
        self.canvas_div = FigureCanvasTkAgg(self.fig_div, master=self.tab_divisas)
        self.canvas_div.get_tk_widget().pack(fill="both", expand=True)

    def consultar_divisas(self):
        self.config(cursor="watch")
        self.update()
        try:
            tasas = api_tasas_usd()
        except Exception as e:  # noqa: BLE001
            self.config(cursor="")
            return messagebox.showerror("Error de API", str(e))
        self.config(cursor="")
        monedas = ["EUR", "GBP", "MXN", "BRL", "COP"]
        self.lbl_divisas.config(text=f"1 USD = {tasas['COP']:,.2f} COP")
        # Se grafica el valor de 1 USD en cada moneda, normalizado en escala log por la diferencia de magnitudes
        self.fig_div.clear()
        ax = self.fig_div.add_subplot(111)
        valores = [tasas[m] for m in monedas]
        ax.bar(monedas, valores, color="tab:green")
        ax.set_yscale("log")
        ax.set_title("Valor de 1 USD en otras monedas (escala log)")
        for i, v in enumerate(valores):
            ax.text(i, v, f"{v:,.2f}", ha="center", va="bottom")
        self.canvas_div.draw()

    # ------------------------------------------------------------ Movimientos
    def _ui_movimientos(self):
        cols = ("fecha", "tipo", "detalle", "monto")
        self.tree_mov = ttk.Treeview(self.tab_mov, columns=cols, show="headings")
        for c, t, w in zip(cols, ["Fecha", "Tipo", "Detalle", "Monto"], [140, 100, 420, 140]):
            self.tree_mov.heading(c, text=t)
            self.tree_mov.column(c, width=w, anchor="center")
        self.tree_mov.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------------------------------------------------------ refrescar
    def refrescar(self):
        d = self.datos
        self.lbl_saldo.config(text=f"Saldo disponible: {moneda(d['saldo'])}")

        self.tree_cdt.delete(*self.tree_cdt.get_children())
        for i, c in enumerate(d["cdts"]):
            estado = "Vencido" if date.today() >= date.fromisoformat(c["vence"]) else "Vigente"
            self.tree_cdt.insert(
                "", "end", iid=str(i),
                values=(moneda(c["monto"]), c["tasa"], c["plazo"], c["vence"], moneda(c["final"]), estado),
            )

        self.tree_bonos.delete(*self.tree_bonos.get_children())
        for i, b in enumerate(d["bonos"]):
            self.tree_bonos.insert(
                "", "end", iid=str(i),
                values=(b["nombre"], moneda(b["monto"]), b["tasa"], b["plazo"], b["vence"], moneda(b["final"])),
            )

        self.tree_acc.delete(*self.tree_acc.get_children())
        for s, a in d["acciones"].items():
            p = self.valores_mercado.get(s)
            mercado = moneda(a["cantidad"] * p) if p else "—"
            self.tree_acc.insert("", "end", values=(s, f"{a['cantidad']:g}", moneda(a["costo_total"]), mercado))

        self.tree_mov.delete(*self.tree_mov.get_children())
        for m in reversed(d["movimientos"]):
            self.tree_mov.insert("", "end", values=(m["fecha"], m["tipo"], m["detalle"], moneda(m["monto"])))

        self.refrescar_resumen()


if __name__ == "__main__":
    App().mainloop()
