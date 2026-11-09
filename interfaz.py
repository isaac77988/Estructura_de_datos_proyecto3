"""
interfaz.py - Interfaz gráfica (tkinter + matplotlib).
Incluye pestañas de Resumen, Cuenta, CDT, Bonos, TES, Acciones, Dividendos, Divisas, Rendimiento, Simulación y Movimientos.
"""
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from api import api_accion_cop, api_tasas_cop
from datos import (
    ARCHIVO,
    OPCIONES_ACCIONES,
    cargar,
    datos_vacios,
    extraer_simbolo,
    guardar,
    leer_numero,
    moneda,
    nombre_accion,
    num,
    pct,
    valor_actual_bono,
    valor_actual_cdt,
    valor_actual_tes,
)

BG = "#F3F6FB"
PRIMARIO = "#0D47A1"
ACENTO = "#1E88E5"
VERDE = "#2E7D32"
ROJO = "#C62828"
NARANJA = "#EF6C00"
MORADO = "#7B1FA2"
TEAL = "#00897B"
TEXTO = "#1F2933"
FILA_PAR = "#FFFFFF"
FILA_IMPAR = "#EAF1FB"

TABS = ["Resumen", "Cuenta", "CDT", "Bonos", "TES", "Acciones", "Dividendos", "Divisas", "Rendimiento", "Simulación", "Movimientos"]

DIVISAS = [
    ("USD", "Dólar estadounidense"),
    ("EUR", "Euro"),
    ("GBP", "Libra esterlina"),
    ("CHF", "Franco suizo"),
    ("CAD", "Dólar canadiense"),
    ("MXN", "Peso mexicano"),
    ("BRL", "Real brasileño"),
    ("PEN", "Sol peruano"),
    ("JPY", "Yen japonés"),
]
COLORES_DIVISAS = [ACENTO, MORADO, NARANJA, ROJO, TEAL, VERDE, "#F9A825", "#5D4037", "#455A64"]


def cantidad_txt(c):
    s = num(c, 4)
    return s.rstrip("0").rstrip(",") if "," in s else s


def eje_cop(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0)))


class App(tk.Tk):
    PERIODOS = {
        "1 mes": "1mo",
        "3 meses": "3mo",
        "6 meses": "6mo",
        "1 año": "1y",
        "2 años": "2y",
        "5 años": "5y",
        "10 años": "10y",
    }

    def __init__(self):
        super().__init__()
        self.title("Portafolio Bancario e Inversiones")
        self.geometry("1220x800")
        self.minsize(1050, 700)
        self.configure(bg=BG)
        self.datos = cargar()
        self.valores_mercado = {}

        self._estilos()
        self._crear_menu()
        self._encabezado()

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8, 10))
        self.tabs = {}
        for nombre in TABS:
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=f"  {nombre}  ")
            self.tabs[nombre] = frame

        self._ui_resumen()
        self._ui_cuenta()
        self._ui_cdt()
        self._ui_bonos()
        self._ui_tes()
        self._ui_acciones()
        self._ui_dividendos()
        self._ui_divisas()
        self._ui_rendimiento()
        self._ui_simulacion()
        self._ui_movimientos()
        self.refrescar()

    def _estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXTO, font=("Segoe UI", 10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXTO)
        s.configure("TLabelframe", background=BG, bordercolor=ACENTO)
        s.configure("TLabelframe.Label", background=BG, foreground=PRIMARIO, font=("Segoe UI", 10, "bold"))
        s.configure("TEntry", fieldbackground="white", padding=4)
        s.configure("TCombobox", fieldbackground="white", padding=4)
        s.map("TCombobox", fieldbackground=[("readonly", "white")])

        s.configure("TNotebook", background="#DCE6F5", borderwidth=0, tabmargins=(6, 6, 6, 0))
        s.configure("TNotebook.Tab", padding=(10, 6), background="#C3D4EC", foreground=PRIMARIO,
                    font=("Segoe UI", 9, "bold"))
        s.map("TNotebook.Tab", background=[("selected", ACENTO), ("active", "#9CC2EE")], foreground=[("selected", "white")])

        for nombre, color, hover in [
            ("Accent", ACENTO, "#1565C0"),
            ("Success", VERDE, "#1B5E20"),
            ("Danger", ROJO, "#8E0000"),
            ("Warn", NARANJA, "#E65100"),
        ]:
            s.configure(f"{nombre}.TButton", background=color, foreground="white",
                        font=("Segoe UI", 9, "bold"), padding=(10, 6), borderwidth=0, focusthickness=0)
            s.map(f"{nombre}.TButton", background=[("active", hover), ("pressed", hover)], foreground=[("active", "white")])

        s.configure("Treeview", rowheight=26, background="white", fieldbackground="white", foreground=TEXTO, bordercolor="#B0C4DE")
        s.configure("Treeview.Heading", background=PRIMARIO, foreground="white", font=("Segoe UI", 9, "bold"), padding=6, relief="flat")

    def _boton(self, master, texto, comando, estilo="Accent"):
        return ttk.Button(master, text=texto, command=comando, style=f"{estilo}.TButton", cursor="hand2")

    def _tabla(self, master, columnas, encabezados, anchos, altura=10, expandir=True):
        marco = ttk.Frame(master)
        tree = ttk.Treeview(marco, columns=columnas, show="headings", height=altura)
        for c, t, w in zip(columnas, encabezados, anchos):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="center")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=barra.set)
        tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        marco.pack(fill="both" if expandir else "x", expand=expandir, padx=10, pady=4)
        tree.tag_configure("par", background=FILA_PAR)
        tree.tag_configure("impar", background=FILA_IMPAR)
        tree.tag_configure("vencido", background="#E8F5E9", foreground="#1B5E20")
        tree.tag_configure("ganancia", background="#E8F5E9", foreground="#1B5E20")
        tree.tag_configure("perdida", background="#FDECEA", foreground="#B71C1C")
        tree.tag_configure("neutro", background=FILA_PAR)
        tree.tag_configure("pos", foreground=VERDE)
        tree.tag_configure("neg", foreground=ROJO)
        tree.tag_configure("total", background=PRIMARIO, foreground="white", font=("Segoe UI", 10, "bold"))
        return tree

    @staticmethod
    def _fila(tree, valores, i, iid=None, tag=None):
        tags = (tag,) if tag else (("par",) if i % 2 == 0 else ("impar",))
        tree.insert("", "end", iid=iid, values=valores, tags=tags)

    def _grafica(self, master, tamano=(6, 4)):
        fig = Figure(figsize=tamano, dpi=100, facecolor=BG)
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)
        return fig, canvas

    def _combo_acciones(self, master, inicial="", ancho=30):
        combo = ttk.Combobox(master, values=OPCIONES_ACCIONES, width=ancho)
        if inicial:
            combo.set(inicial)

        def filtrar(evento):
            if evento.keysym in ("Up", "Down", "Left", "Right", "Return", "Escape", "Tab"):
                return
            txt = combo.get().strip().lower()
            combo["values"] = [o for o in OPCIONES_ACCIONES if txt in o.lower()] if txt else OPCIONES_ACCIONES

        combo.bind("<KeyRelease>", filtrar)
        return combo

    def _crear_menu(self):
        barra = tk.Menu(self)
        m_archivo = tk.Menu(barra, tearoff=0)
        m_archivo.add_command(label="Guardar", command=self._guardar_manual)
        m_archivo.add_command(label="Borrar todos los datos", command=self._borrar_todo)
        m_archivo.add_separator()
        m_archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=m_archivo)
        self.config(menu=barra)

    def _encabezado(self):
        h = tk.Frame(self, bg=PRIMARIO)
        h.pack(fill="x")
        izq = tk.Frame(h, bg=PRIMARIO)
        izq.pack(side="left", padx=18, pady=10)
        tk.Label(izq, text="Portafolio Bancario e Inversiones", bg=PRIMARIO, fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(izq, text="CDT  |  Bonos  |  TES  |  Acciones  |  Dividendos      Valores en pesos colombianos (COP)", bg=PRIMARIO, fg="#BBDEFB", font=("Segoe UI", 9)).pack(anchor="w")
        der = tk.Frame(h, bg=PRIMARIO)
        der.pack(side="right", padx=18)
        tk.Label(der, text="Patrimonio total", bg=PRIMARIO, fg="#BBDEFB", font=("Segoe UI", 9)).pack(anchor="e")
        self.lbl_header_total = tk.Label(der, text="", bg=PRIMARIO, fg="#FFD54F", font=("Segoe UI", 16, "bold"))
        self.lbl_header_total.pack(anchor="e")
        tk.Frame(self, bg=ACENTO, height=4).pack(fill="x")

    def _guardar_manual(self):
        guardar(self.datos)
        messagebox.showinfo("Guardado", f"Datos guardados en {ARCHIVO}")

    def _borrar_todo(self):
        if messagebox.askyesno("Confirmar", "¿Borrar TODOS los datos del portafolio?"):
            self.datos = datos_vacios()
            guardar(self.datos)
            self.refrescar()

    def registrar(self, tipo, detalle, monto):
        self.datos["movimientos"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": tipo,
            "detalle": detalle,
            "monto": monto
        })

    # --- RESUMEN ---
    def _ui_resumen(self):
        tab = self.tabs["Resumen"]
        fila = ttk.Frame(tab)
        fila.pack(fill="x", padx=10, pady=(12, 4))
        self.tarjetas = {}
        for col, (nombre, color) in enumerate([
            ("Efectivo", ACENTO), ("CDT", MORADO), ("Bonos", NARANJA), ("TES", TEAL), ("Acciones", VERDE), ("Total", "#263238"),
        ]):
            marco = tk.Frame(fila, bg=color, padx=10, pady=8)
            marco.grid(row=0, column=col, sticky="nsew", padx=4)
            fila.columnconfigure(col, weight=1, uniform="tarjetas")
            tk.Label(marco, text=nombre if nombre != "Total" else "PATRIMONIO", bg=color, fg="white", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            valor = tk.Label(marco, text="", bg=color, fg="white", font=("Segoe UI", 12, "bold"))
            valor.pack(anchor="w")
            self.tarjetas[nombre] = valor

        barra = ttk.Frame(tab)
        barra.pack(fill="x", padx=10, pady=6)
        self._boton(barra, "Actualizar precios de mercado", self.actualizar_mercado).pack(side="left", padx=5)
        self.fig_res, self.canvas_res = self._grafica(tab, (6, 3.5))

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
                self.valores_mercado[s] = api_accion_cop(s, "5d")["precio"]
            except Exception as e:
                errores.append(f"{s}: {e}")
        self.config(cursor="")
        self.refrescar()
        if errores:
            messagebox.showwarning("Aviso", "\n".join(errores))

    def refrescar_resumen(self):
        d = self.datos
        efectivo = d["saldo"]
        cdt = sum(valor_actual_cdt(c) for c in d["cdts"])
        bonos = sum(valor_actual_bono(b) for b in d["bonos"])
        tes = sum(valor_actual_tes(t) for t in d.get("tes", []))
        acc = self.valor_acciones()
        total = efectivo + cdt + bonos + tes + acc

        for nombre, valor in [("Efectivo", efectivo), ("CDT", cdt), ("Bonos", bonos), ("TES", tes), ("Acciones", acc), ("Total", total)]:
            if nombre in self.tarjetas:
                self.tarjetas[nombre].config(text=moneda(valor))
        self.lbl_header_total.config(text=moneda(total))

        self.fig_res.clear()
        ax = self.fig_res.add_subplot(111)
        partes = [("Efectivo", efectivo, ACENTO), ("CDT", cdt, MORADO), ("Bonos", bonos, NARANJA), ("TES", tes, TEAL), ("Acciones", acc, VERDE)]
        partes = [p for p in partes if p[1] > 0]
        if partes:
            ax.pie([p[1] for p in partes], labels=[p[0] for p in partes], colors=[p[2] for p in partes],
                   autopct=lambda v: f"{v:.1f}%".replace(".", ","), startangle=90,
                   wedgeprops={"edgecolor": "white", "linewidth": 2}, textprops={"fontsize": 9})
            ax.set_title("Distribución del Portafolio (COP)", color=PRIMARIO, fontweight="bold")
        else:
            ax.text(0.5, 0.5, "Sin datos en el portafolio", ha="center", va="center", fontsize=11, color="#546E7A")
            ax.axis("off")
        self.canvas_res.draw()

    # --- CUENTA ---
    def _ui_cuenta(self):
        tab = self.tabs["Cuenta"]
        tarjeta = tk.Frame(tab, bg="#E3F2FD", padx=30, pady=20, highlightbackground=ACENTO, highlightthickness=2)
        tarjeta.pack(padx=20, pady=20, anchor="n")
        tk.Label(tarjeta, text="Cuenta de Ahorros (COP)", bg="#E3F2FD", fg=PRIMARIO, font=("Segoe UI", 12, "bold")).pack()
        self.lbl_saldo = tk.Label(tarjeta, text="", bg="#E3F2FD", fg=VERDE, font=("Segoe UI", 24, "bold"))
        self.lbl_saldo.pack(pady=(6, 14))
        fila = tk.Frame(tarjeta, bg="#E3F2FD")
        fila.pack()
        tk.Label(fila, text="Monto en pesos:", bg="#E3F2FD").pack(side="left", padx=6)
        self.e_monto_cuenta = ttk.Entry(fila, width=20)
        self.e_monto_cuenta.pack(side="left", padx=6)
        botones = tk.Frame(tarjeta, bg="#E3F2FD")
        botones.pack(pady=(14, 4))
        self._boton(botones, "Depositar", self.depositar, "Success").pack(side="left", padx=8)
        self._boton(botones, "Retirar", self.retirar, "Danger").pack(side="left", padx=8)

    def depositar(self):
        try:
            m = leer_numero(self.e_monto_cuenta.get(), "El monto")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        self.datos["saldo"] += m
        self.registrar("Depósito", "Cuenta de ahorros", m)
        self.e_monto_cuenta.delete(0, "end")
        guardar(self.datos)
        self.refrescar()

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
        guardar(self.datos)
        self.refrescar()

    # --- CDT ---
    def _ui_cdt(self):
        tab = self.tabs["CDT"]
        f = ttk.LabelFrame(tab, text="Abrir Nuevo CDT")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Monto (COP):").grid(row=0, column=0, padx=5, pady=8)
        self.e_cdt_monto = ttk.Entry(f, width=16)
        self.e_cdt_monto.grid(row=0, column=1)
        ttk.Label(f, text="Plazo (días):").grid(row=0, column=2, padx=5)
        self.c_cdt_plazo = ttk.Combobox(f, values=[90, 180, 360, 540], width=8)
        self.c_cdt_plazo.set(180)
        self.c_cdt_plazo.grid(row=0, column=3)
        ttk.Label(f, text="Tasa E.A. (%):").grid(row=0, column=4, padx=5)
        self.e_cdt_tasa = ttk.Entry(f, width=8)
        self.e_cdt_tasa.insert(0, "10.0")
        self.e_cdt_tasa.grid(row=0, column=5)
        self._boton(f, "Abrir CDT", self.abrir_cdt, "Accent").grid(row=0, column=6, padx=10)

        cols = ("monto", "tasa", "plazo", "vence", "actual", "final", "estado")
        self.tree_cdt = self._tabla(tab, cols, ["Capital (COP)", "Tasa EA", "Plazo", "Vencimiento", "Valor actual", "Valor final", "Estado"], [130, 70, 80, 100, 130, 140, 80], altura=10)
        self._boton(tab, "Liquidar CDT seleccionado", self.liquidar_cdt, "Warn").pack(pady=6)

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
        self.datos["cdts"].append({
            "monto": monto, "tasa": tasa, "plazo": plazo,
            "vence": (date.today() + timedelta(days=plazo)).isoformat(),
            "final": round(final, 2)
        })
        self.registrar("CDT", f"Apertura CDT {plazo} días al {num(tasa)}% EA", -monto)
        self.e_cdt_monto.delete(0, "end")
        guardar(self.datos)
        self.refrescar()

    def liquidar_cdt(self):
        sel = self.tree_cdt.selection()
        if not sel:
            return messagebox.showinfo("Info", "Selecciona un CDT.")
        i = int(sel[0])
        c = self.datos["cdts"][i]
        vencido = date.today() >= date.fromisoformat(c["vence"])
        pago = c["final"] if vencido else c["monto"]
        self.datos["saldo"] += pago
        self.datos["cdts"].pop(i)
        self.registrar("CDT", "Liquidación CDT", pago)
        guardar(self.datos)
        self.refrescar()

    # --- BONOS ---
    def _ui_bonos(self):
        tab = self.tabs["Bonos"]
        f = ttk.LabelFrame(tab, text="Comprar Bono Corporativo")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Emisor:").grid(row=0, column=0, padx=5, pady=8)
        self.e_bono_nombre = ttk.Entry(f, width=15)
        self.e_bono_nombre.grid(row=0, column=1)
        ttk.Label(f, text="Monto:").grid(row=0, column=2, padx=5)
        self.e_bono_monto = ttk.Entry(f, width=14)
        self.e_bono_monto.grid(row=0, column=3)
        ttk.Label(f, text="Tasa %:").grid(row=0, column=4, padx=5)
        self.e_bono_tasa = ttk.Entry(f, width=6)
        self.e_bono_tasa.insert(0, "11")
        self.e_bono_tasa.grid(row=0, column=5)
        ttk.Label(f, text="Plazo m:").grid(row=0, column=6, padx=5)
        self.e_bono_plazo = ttk.Entry(f, width=6)
        self.e_bono_plazo.insert(0, "24")
        self.e_bono_plazo.grid(row=0, column=7)
        self._boton(f, "Comprar", self.comprar_bono, "Accent").grid(row=0, column=8, padx=10)

        cols = ("nombre", "monto", "tasa", "plazo", "vence", "actual", "final")
        self.tree_bonos = self._tabla(tab, cols, ["Emisor", "Capital", "Tasa anual", "Plazo m", "Vencimiento", "Valor actual", "Valor final"], [130, 130, 70, 80, 100, 130, 140], altura=10)
        self._boton(tab, "Redimir bono seleccionado", self.redimir_bono, "Warn").pack(pady=6)

    def comprar_bono(self):
        nombre = self.e_bono_nombre.get().strip() or "Bono Corp"
        try:
            monto = leer_numero(self.e_bono_monto.get(), "El monto")
            tasa = leer_numero(self.e_bono_tasa.get(), "La tasa")
            meses = int(leer_numero(self.e_bono_plazo.get(), "El plazo"))
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        if monto > self.datos["saldo"]:
            return messagebox.showerror("Error", "Saldo insuficiente.")
        self.datos["saldo"] -= monto
        self.datos["bonos"].append({
            "nombre": nombre, "monto": monto, "tasa": tasa, "plazo": meses,
            "vence": (date.today() + timedelta(days=30 * meses)).isoformat(),
            "final": round(monto * (1 + tasa / 100 * meses / 12), 2)
        })
        self.registrar("Bono", f"Compra {nombre}", -monto)
        guardar(self.datos)
        self.refrescar()

    def redimir_bono(self):
        sel = self.tree_bonos.selection()
        if not sel:
            return messagebox.showinfo("Info", "Selecciona un bono.")
        i = int(sel[0])
        b = self.datos["bonos"][i]
        pago = b["final"] if date.today() >= date.fromisoformat(b["vence"]) else b["monto"]
        self.datos["saldo"] += pago
        self.datos["bonos"].pop(i)
        self.registrar("Bono", f"Redención {b['nombre']}", pago)
        guardar(self.datos)
        self.refrescar()

    # --- TES (Títulos de Deuda Pública) ---
    def _ui_tes(self):
        tab = self.tabs["TES"]
        f = ttk.LabelFrame(tab, text="Adquirir TES (Títulos de Deuda Pública)")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Tipo:").grid(row=0, column=0, padx=5, pady=8)
        self.c_tes_tipo = ttk.Combobox(f, values=["TES Tasa Fija COP", "TES UVR"], width=16, state="readonly")
        self.c_tes_tipo.set("TES Tasa Fija COP")
        self.c_tes_tipo.grid(row=0, column=1)
        ttk.Label(f, text="Monto:").grid(row=0, column=2, padx=5)
        self.e_tes_monto = ttk.Entry(f, width=14)
        self.e_tes_monto.grid(row=0, column=3)
        ttk.Label(f, text="Cupón %:").grid(row=0, column=4, padx=5)
        self.e_tes_tasa = ttk.Entry(f, width=6)
        self.e_tes_tasa.insert(0, "9.5")
        self.e_tes_tasa.grid(row=0, column=5)
        ttk.Label(f, text="Plazo años:").grid(row=0, column=6, padx=5)
        self.e_tes_anos = ttk.Entry(f, width=6)
        self.e_tes_anos.insert(0, "3")
        self.e_tes_anos.grid(row=0, column=7)
        self._boton(f, "Invertir TES", self.comprar_tes, "Accent").grid(row=0, column=8, padx=10)

        cols = ("tipo", "monto", "tasa", "emision", "vence", "actual")
        self.tree_tes = self._tabla(tab, cols, ["Tipo TES", "Capital", "Cupón anual", "Emisión", "Vencimiento", "Valor actual"], [150, 140, 80, 100, 100, 150], altura=10)
        self._boton(tab, "Redimir TES seleccionado", self.redimir_tes, "Warn").pack(pady=6)

    def comprar_tes(self):
        tipo = self.c_tes_tipo.get()
        try:
            monto = leer_numero(self.e_tes_monto.get(), "El monto")
            tasa = leer_numero(self.e_tes_tasa.get(), "La tasa")
            anos = int(leer_numero(self.e_tes_anos.get(), "El plazo en años"))
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        if monto > self.datos["saldo"]:
            return messagebox.showerror("Error", "Saldo insuficiente.")
        hoy = date.today()
        vence = hoy + timedelta(days=int(anos * 365))
        self.datos["saldo"] -= monto
        if "tes" not in self.datos:
            self.datos["tes"] = []
        self.datos["tes"].append({
            "tipo": tipo, "monto": monto, "tasa": tasa,
            "emision": hoy.isoformat(), "vence": vence.isoformat()
        })
        self.registrar("TES", f"Compra {tipo} al {num(tasa)}%", -monto)
        guardar(self.datos)
        self.refrescar()

    def redimir_tes(self):
        sel = self.tree_tes.selection()
        if not sel:
            return messagebox.showinfo("Info", "Selecciona un TES.")
        i = int(sel[0])
        t = self.datos["tes"][i]
        pago = valor_actual_tes(t)
        self.datos["saldo"] += pago
        self.datos["tes"].pop(i)
        self.registrar("TES", f"Redención {t['tipo']}", pago)
        guardar(self.datos)
        self.refrescar()

    # --- ACCIONES ---
    def _ui_acciones(self):
        tab = self.tabs["Acciones"]
        f = ttk.LabelFrame(tab, text="Operación de Acciones (con Comisión de Bróker)")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Empresa:").grid(row=0, column=0, padx=5, pady=8)
        self.cb_accion = self._combo_acciones(f, "Coca-Cola (KO)", 25)
        self.cb_accion.grid(row=0, column=1)
        ttk.Label(f, text="Cantidad:").grid(row=0, column=2, padx=5)
        self.e_cantidad = ttk.Entry(f, width=8)
        self.e_cantidad.insert(0, "1")
        self.e_cantidad.grid(row=0, column=3)
        ttk.Label(f, text="Comisión (COP):").grid(row=0, column=4, padx=5)
        self.e_comision = ttk.Entry(f, width=10)
        self.e_comision.insert(0, "0")
        self.e_comision.grid(row=0, column=5)

        btns = ttk.Frame(f)
        btns.grid(row=0, column=6, padx=10)
        self._boton(btns, "Consultar", self.consultar_accion, "Accent").pack(side="left", padx=2)
        self._boton(btns, "Comprar", lambda: self.operar_accion("compra"), "Success").pack(side="left", padx=2)
        self._boton(btns, "Vender", lambda: self.operar_accion("venta"), "Danger").pack(side="left", padx=2)

        self.lbl_precio = ttk.Label(f, text="Selecciona una empresa y consulta su precio en mercado.", foreground=PRIMARIO, font=("Segoe UI", 9, "bold"))
        self.lbl_precio.grid(row=1, column=0, columnspan=7, sticky="w", padx=6, pady=(0, 6))

        cols = ("accion", "cantidad", "costo", "mercado", "ganancia")
        self.tree_acc = self._tabla(tab, cols, ["Empresa", "Cantidad", "Costo total (con comisión)", "Valor mercado", "Ganancia / Pérdida"], [210, 80, 160, 160, 160], altura=6, expandir=False)
        self.fig_acc, self.canvas_acc = self._grafica(tab, (6, 3.2))

    def consultar_accion(self):
        simbolo = extraer_simbolo(self.cb_accion.get())
        if not simbolo:
            messagebox.showerror("Error", "Selecciona una empresa.")
            return None
        self.config(cursor="watch")
        self.update()
        try:
            r = api_accion_cop(simbolo)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Error", f"No se pudo consultar {simbolo}:\n{e}")
            return None
        self.config(cursor="")
        self.valores_mercado[simbolo] = r["precio"]
        self.lbl_precio.config(text=f"{nombre_accion(simbolo)}: {moneda(r['precio'])} COP")

        self.fig_acc.clear()
        ax = self.fig_acc.add_subplot(111)
        fechas = [f for f, _ in r["serie"]]
        valores = [v for _, v in r["serie"]]
        ax.plot(fechas, valores, color=ACENTO, linewidth=2)
        ax.set_title(f"{nombre_accion(simbolo)} - 3 Meses (COP)", color=PRIMARIO, fontweight="bold")
        eje_cop(ax)
        ax.grid(alpha=0.3)
        self.fig_acc.autofmt_xdate()
        self.canvas_acc.draw()
        return simbolo, r["precio"]

    def operar_accion(self, tipo):
        try:
            cant = leer_numero(self.e_cantidad.get(), "La cantidad")
            comision = leer_numero(self.e_comision.get(), "La comisión", permitir_cero=True)
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        res = self.consultar_accion()
        if not res:
            return
        simbolo, precio = res
        bruto = cant * precio
        total = bruto + comision if tipo == "compra" else bruto - comision

        acc = self.datos["acciones"]
        if tipo == "compra":
            if total > self.datos["saldo"]:
                return messagebox.showerror("Error", f"Saldo insuficiente. Requieres {moneda(total)}.")
            self.datos["saldo"] -= total
            a = acc.setdefault(simbolo, {"cantidad": 0.0, "costo_total": 0.0})
            a["cantidad"] += cant
            a["costo_total"] += total
            self.registrar("Acción", f"Compra {cantidad_txt(cant)} x {simbolo} (Comisión: {moneda(comision)})", -total)
        else:
            a = acc.get(simbolo)
            if not a or a["cantidad"] < cant:
                return messagebox.showerror("Error", "No posees suficientes acciones.")
            costo_unit = a["costo_total"] / a["cantidad"]
            a["cantidad"] -= cant
            a["costo_total"] -= costo_unit * cant
            if a["cantidad"] <= 1e-9:
                del acc[simbolo]
            self.datos["saldo"] += total
            self.registrar("Acción", f"Venta {cantidad_txt(cant)} x {simbolo} (Comisión: {moneda(comision)})", total)
        
        if "transacciones" not in self.datos:
            self.datos["transacciones"] = []
        self.datos["transacciones"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": tipo.upper(), "simbolo": simbolo, "cantidad": cant,
            "precio_unitario": precio, "comision": comision, "total": total
        })
        guardar(self.datos)
        self.refrescar()

    # --- DIVIDENDOS ---
    def _ui_dividendos(self):
        tab = self.tabs["Dividendos"]
        f = ttk.LabelFrame(tab, text="Registrar Dividendo Recibido")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Empresa:").grid(row=0, column=0, padx=5, pady=8)
        self.cb_div_accion = self._combo_acciones(f, "Coca-Cola (KO)", 25)
        self.cb_div_accion.grid(row=0, column=1)
        ttk.Label(f, text="Valor Neto (COP):").grid(row=0, column=2, padx=5)
        self.e_div_monto = ttk.Entry(f, width=16)
        self.e_div_monto.grid(row=0, column=3)
        self._boton(f, "Registrar Dividendo", self.registrar_dividendo, "Success").grid(row=0, column=4, padx=10)

        cols = ("fecha", "accion", "monto")
        self.tree_div = self._tabla(tab, cols, ["Fecha", "Empresa", "Valor Neto (COP)"], [150, 250, 180], altura=12)

    def registrar_dividendo(self):
        simbolo = extraer_simbolo(self.cb_div_accion.get())
        try:
            monto = leer_numero(self.e_div_monto.get(), "El dividendo")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        self.datos["saldo"] += monto
        if "dividendos" not in self.datos:
            self.datos["dividendos"] = []
        fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.datos["dividendos"].append({"fecha": fecha_str, "simbolo": simbolo, "monto": monto})
        self.registrar("Dividendo", f"Ingreso dividendo {simbolo}", monto)
        self.e_div_monto.delete(0, "end")
        guardar(self.datos)
        self.refrescar()

    # --- DIVISAS ---
    def _ui_divisas(self):
        tab = self.tabs["Divisas"]
        f = ttk.Frame(tab)
        f.pack(fill="x", padx=10, pady=10)
        self._boton(f, "Consultar Tasas", self.consultar_divisas, "Accent").pack(side="left")
        self.lbl_divisas = ttk.Label(f, text="Valor de cada moneda extranjera en pesos colombianos.", foreground=PRIMARIO, font=("Segoe UI", 9, "bold"))
        self.lbl_divisas.pack(side="left", padx=12)
        self.tree_divisas = self._tabla(tab, ("moneda", "nombre", "valor"), ["Moneda", "Nombre", "Vale en COP"], [90, 240, 200], altura=9, expandir=False)
        self.fig_div, self.canvas_div = self._grafica(tab, (6, 3))

    def consultar_divisas(self):
        try:
            tasas = api_tasas_cop()
        except Exception as e:
            return messagebox.showerror("Error", str(e))
        self.lbl_divisas.config(text=f"1 USD = {moneda(tasas['USD'])} COP")
        self.tree_divisas.delete(*self.tree_divisas.get_children())
        for i, (cod, nombre) in enumerate(DIVISAS):
            self._fila(self.tree_divisas, (cod, nombre, moneda(tasas[cod])), i)

        self.fig_div.clear()
        ax = self.fig_div.add_subplot(111)
        codigos = [c for c, _ in DIVISAS]
        valores = [tasas[c] for c in codigos]
        ax.bar(codigos, valores, color=COLORES_DIVISAS)
        ax.set_title("Equivalencia Divisas en COP", color=PRIMARIO, fontweight="bold")
        eje_cop(ax)
        ax.grid(axis="y", alpha=0.3)
        self.canvas_div.draw()

    # --- RENDIMIENTO ---
    def _ui_rendimiento(self):
        tab = self.tabs["Rendimiento"]
        barra = ttk.Frame(tab)
        barra.pack(fill="x", padx=10, pady=8)
        self._boton(barra, "Actualizar Rendimiento", self.actualizar_mercado, "Accent").pack(side="left")

        self.lbl_rend_total = tk.Label(tab, text="", font=("Segoe UI", 11, "bold"), fg="white", bg="#546E7A", pady=8)
        self.lbl_rend_total.pack(fill="x", padx=10, pady=4)

        cols = ("producto", "tipo", "invertido", "actual", "ganancia", "rend", "detalle")
        self.tree_rend = self._tabla(tab, cols, ["Producto", "Tipo", "Invertido", "Valor actual", "Ganancia", "Rentabilidad", "Detalle"], [160, 70, 130, 140, 140, 90, 220], altura=9, expandir=False)
        self.fig_rend, self.canvas_rend = self._grafica(tab, (6, 2.5))

    def refrescar_rendimiento(self):
        d = self.datos
        filas = []
        for i, c in enumerate(d["cdts"], 1):
            filas.append((f"CDT {i}", "CDT", c["monto"], valor_actual_cdt(c), f"{num(c['tasa'])}% EA"))
        for b in d["bonos"]:
            filas.append((b["nombre"], "Bono", b["monto"], valor_actual_bono(b), f"{num(b['tasa'])}% anual"))
        for t in d.get("tes", []):
            filas.append((t["tipo"], "TES", t["monto"], valor_actual_tes(t), f"Cupón {num(t['tasa'])}%"))
        for s, a in d["acciones"].items():
            p = self.valores_mercado.get(s)
            actual = a["cantidad"] * p if p else None
            filas.append((nombre_accion(s), "Acción", a["costo_total"], actual, f"{cantidad_txt(a['cantidad'])} un."))

        self.tree_rend.delete(*self.tree_rend.get_children())
        tot_inv = tot_act = 0.0
        nombres, rends = [], []
        for producto, tipo, inv, act, detalle in filas:
            if act is None:
                self._fila(self.tree_rend, (producto, tipo, moneda(inv), "—", "—", "—", detalle), 0, tag="neutro")
            else:
                gan = act - inv
                rend = gan / inv * 100 if inv > 0 else 0.0
                tot_inv += inv
                tot_act += act
                nombres.append(producto)
                rends.append(rend)
                tag = "ganancia" if gan > 0 else "perdida" if gan < 0 else "neutro"
                self._fila(self.tree_rend, (producto, tipo, moneda(inv), moneda(act), moneda(gan), pct(rend), detalle), 0, tag=tag)

        if filas and tot_inv > 0:
            gan_t = tot_act - tot_inv
            rend_t = gan_t / tot_inv * 100
            self._fila(self.tree_rend, ("TOTAL", "", moneda(tot_inv), moneda(tot_act), moneda(gan_t), pct(rend_t), ""), 0, tag="total")
            self.lbl_rend_total.config(bg=VERDE if gan_t >= 0 else ROJO, text=f"Invertido: {moneda(tot_inv)} | Actual: {moneda(tot_act)} | Ganancia: {moneda(gan_t)} ({pct(rend_t)})")
        else:
            self.lbl_rend_total.config(bg="#546E7A", text="Sin inversiones registradas.")

        self.fig_rend.clear()
        ax = self.fig_rend.add_subplot(111)
        if rends:
            ax.barh(nombres, rends, color=[VERDE if r >= 0 else ROJO for r in rends])
            ax.axvline(0, color="gray", linewidth=1)
            ax.set_title("Rentabilidad por Producto (%)", color=PRIMARIO, fontweight="bold")
            ax.grid(axis="x", alpha=0.3)
            ax.invert_yaxis()
            self.fig_rend.tight_layout()
        else:
            ax.axis("off")
        self.canvas_rend.draw()

    # --- SIMULACIÓN ---
    def _ui_simulacion(self):
        tab = self.tabs["Simulación"]
        f = ttk.LabelFrame(tab, text="Simulador Histórico de Inversión")
        f.pack(fill="x", padx=10, pady=10)
        ttk.Label(f, text="Empresa:").grid(row=0, column=0, padx=5, pady=8)
        self.cb_sim = self._combo_acciones(f, "Apple (AAPL)", 25)
        self.cb_sim.grid(row=0, column=1)
        ttk.Label(f, text="Monto:").grid(row=0, column=2, padx=5)
        self.e_sim_monto = ttk.Entry(f, width=12)
        self.e_sim_monto.insert(0, "5000000")
        self.e_sim_monto.grid(row=0, column=3)
        ttk.Label(f, text="Periodo:").grid(row=0, column=4, padx=5)
        self.c_sim_periodo = ttk.Combobox(f, values=list(self.PERIODOS), width=8, state="readonly")
        self.c_sim_periodo.set("1 año")
        self.c_sim_periodo.grid(row=0, column=5)
        self._boton(f, "Simular", self.simular, "Accent").grid(row=0, column=6, padx=10)

        self.lbl_sim = ttk.Label(tab, text="", font=("Segoe UI", 9, "bold"), justify="left")
        self.lbl_sim.pack(anchor="w", padx=12, pady=4)
        self.fig_sim, self.canvas_sim = self._grafica(tab, (6, 3.2))

    def simular(self):
        simbolo = extraer_simbolo(self.cb_sim.get())
        try:
            monto = leer_numero(self.e_sim_monto.get(), "El monto")
        except ValueError as e:
            return messagebox.showerror("Error", str(e))
        periodo = self.PERIODOS[self.c_sim_periodo.get()]

        self.config(cursor="watch")
        self.update()
        try:
            serie = api_accion_cop(simbolo, periodo)["serie"]
        except Exception as e:
            self.config(cursor="")
            return messagebox.showerror("Error", str(e))
        self.config(cursor="")

        fechas = [f for f, _ in serie]
        precios = [p for _, p in serie]
        acciones = monto / precios[0]
        valores = [acciones * p for p in precios]
        final = valores[-1]
        ganancia = final - monto
        rend = ganancia / monto * 100

        self.lbl_sim.config(foreground=VERDE if ganancia >= 0 else ROJO,
            text=f"Simulación {nombre_accion(simbolo)} ({self.c_sim_periodo.get()}): Invertido {moneda(monto)} -> Valor hoy {moneda(final)} | Resultado: {moneda(ganancia)} ({pct(rend)})")

        self.fig_sim.clear()
        ax = self.fig_sim.add_subplot(111)
        ax.plot(fechas, valores, color=ACENTO, linewidth=2)
        ax.axhline(monto, color="gray", linestyle=":")
        ax.set_title("Evolución de Simulación Histórica (COP)", color=PRIMARIO, fontweight="bold")
        eje_cop(ax)
        ax.grid(alpha=0.3)
        self.fig_sim.autofmt_xdate()
        self.canvas_sim.draw()

    # --- MOVIMIENTOS ---
    def _ui_movimientos(self):
        cols = ("fecha", "tipo", "detalle", "monto")
        self.tree_mov = self._tabla(self.tabs["Movimientos"], cols, ["Fecha", "Tipo", "Detalle", "Monto (COP)"], [140, 100, 520, 160], altura=16)

    def refrescar(self):
        d = self.datos
        self.lbl_saldo.config(text=moneda(d["saldo"]))

        self.tree_cdt.delete(*self.tree_cdt.get_children())
        for i, c in enumerate(d["cdts"]):
            vencido = date.today() >= date.fromisoformat(c["vence"])
            self._fila(self.tree_cdt, (moneda(c["monto"]), f"{num(c['tasa'])}%", c["plazo"], c["vence"], moneda(valor_actual_cdt(c)), moneda(c["final"]), "Vencido" if vencido else "Vigente"), i, tag="vencido" if vencido else None)

        self.tree_bonos.delete(*self.tree_bonos.get_children())
        for i, b in enumerate(d["bonos"]):
            self._fila(self.tree_bonos, (b["nombre"], moneda(b["monto"]), f"{num(b['tasa'])}%", b["plazo"], b["vence"], moneda(valor_actual_bono(b)), moneda(b["final"])), i)

        if "tes" in d:
            self.tree_tes.delete(*self.tree_tes.get_children())
            for i, t in enumerate(d["tes"]):
                self._fila(self.tree_tes, (t["tipo"], moneda(t["monto"]), f"{num(t['tasa'])}%", t["emision"], t["vence"], moneda(valor_actual_tes(t))), i)

        self.tree_acc.delete(*self.tree_acc.get_children())
        for i, (s, a) in enumerate(d["acciones"].items()):
            p = self.valores_mercado.get(s)
            if p:
                mercado = a["cantidad"] * p
                gan = mercado - a["costo_total"]
                self._fila(self.tree_acc, (nombre_accion(s), cantidad_txt(a["cantidad"]), moneda(a["costo_total"]), moneda(mercado), f"{moneda(gan)} ({pct(gan/a['costo_total']*100 if a['costo_total'] else 0)})"), i, tag="ganancia" if gan > 0 else "perdida")
            else:
                self._fila(self.tree_acc, (nombre_accion(s), cantidad_txt(a["cantidad"]), moneda(a["costo_total"]), "—", "—"), i)

        if "dividendos" in d:
            self.tree_div.delete(*self.tree_div.get_children())
            for i, div in enumerate(reversed(d["dividendos"])):
                self._fila(self.tree_div, (div["fecha"], nombre_accion(div["simbolo"]), moneda(div["monto"])), i)

        self.tree_mov.delete(*self.tree_mov.get_children())
        for i, m in enumerate(reversed(d["movimientos"])):
            self._fila(self.tree_mov, (m["fecha"], m["tipo"], m["detalle"], moneda(m["monto"])), i, tag="pos" if m["monto"] >= 0 else "neg")

        self.refrescar_rendimiento()
        self.refrescar_resumen()
