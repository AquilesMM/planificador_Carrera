"""
gui.py
------
Interfaz gráfica (Tkinter) de "Planificá tu Carrera".

Se apoya en:
  - database.py -> lee/escribe MySQL
  - logica.py   -> calcula habilitaciones, impacto futuro y alternativas

La ventana está organizada en pestañas (ttk.Notebook):
  1. Plan de estudios
  2. Situación académica (cargar/editar estados)
  3. Qué puedo cursar / Qué no puedo cursar
  4. Finales pendientes y materias a recursar
  5. Impacto futuro
  6. Alternativas de planificación
  7. Caso de Martín / Resumen
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from database import (
    ConexionBD, obtener_plan_de_estudios, obtener_correlatividades,
    obtener_estudiantes, obtener_o_crear_estudiante, obtener_situacion_academica,
    guardar_estado_asignatura,
)
from logica import PlanDeCarrera

ESTADOS = ["no_cursada", "regular", "no_regularizada", "aprobada"]
COLOR_ESTADO = {
    "aprobada": "#c8f0c8",
    "regular": "#fff2b2",
    "no_regularizada": "#f7c6c6",
    "no_cursada": "#eeeeee",
}


def _etiqueta(a) -> str:
    """Nombre para mostrar en listas, con código y marca de electiva/integradora."""
    extra = []
    if a.es_electiva:
        extra.append("electiva")
    if a.es_integradora:
        extra.append("integradora")
    sufijo = f" [{', '.join(extra)}]" if extra else ""
    return f"N°{a.codigo} — {a.nombre}{sufijo}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Planificá tu Carrera — Ingeniería en Sistemas de Información")
        self.geometry("1100x700")

        self.bd = ConexionBD()
        self.id_estudiante: int | None = None
        self.plan: PlanDeCarrera | None = None

        self._construir_barra_superior()
        self._construir_notebook()

        self._cargar_lista_estudiantes()

    # -------------------------------------------------------------
    # Barra superior: selección de estudiante
    # -------------------------------------------------------------
    def _construir_barra_superior(self):
        barra = ttk.Frame(self, padding=8)
        barra.pack(fill="x")

        ttk.Label(barra, text="Estudiante:").pack(side="left")
        self.combo_estudiante = ttk.Combobox(barra, state="readonly", width=30)
        self.combo_estudiante.pack(side="left", padx=6)
        self.combo_estudiante.bind("<<ComboboxSelected>>", self._on_seleccionar_estudiante)

        ttk.Button(barra, text="Nuevo estudiante", command=self._nuevo_estudiante).pack(side="left", padx=4)
        ttk.Button(barra, text="Cargar caso de Martín", command=self._cargar_caso_martin).pack(side="left", padx=4)
        ttk.Button(barra, text="Actualizar", command=self.refrescar_todo).pack(side="left", padx=4)

        self.lbl_avance = ttk.Label(barra, text="", font=("", 10, "bold"))
        self.lbl_avance.pack(side="right")

    def _construir_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_plan = ttk.Frame(self.nb)
        self.tab_situacion = ttk.Frame(self.nb)
        self.tab_habilitadas = ttk.Frame(self.nb)
        self.tab_finales = ttk.Frame(self.nb)
        self.tab_impacto = ttk.Frame(self.nb)
        self.tab_alternativas = ttk.Frame(self.nb)
        self.tab_resumen = ttk.Frame(self.nb)

        self.nb.add(self.tab_plan, text="Plan de estudios")
        self.nb.add(self.tab_situacion, text="Situación académica")
        self.nb.add(self.tab_habilitadas, text="Qué puedo / no puedo cursar")
        self.nb.add(self.tab_finales, text="Finales y recursada")
        self.nb.add(self.tab_impacto, text="Impacto futuro")
        self.nb.add(self.tab_alternativas, text="Alternativas")
        self.nb.add(self.tab_resumen, text="Resumen del caso")

        self._construir_tab_plan()
        self._construir_tab_situacion()
        self._construir_tab_habilitadas()
        self._construir_tab_finales()
        self._construir_tab_impacto()
        self._construir_tab_alternativas()
        self._construir_tab_resumen()

    # -------------------------------------------------------------
    # Carga inicial de estudiantes
    # -------------------------------------------------------------
    def _cargar_lista_estudiantes(self):
        try:
            estudiantes = obtener_estudiantes(self.bd)
        except Exception as e:
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a MySQL.\n\n"
                f"Revisá la configuración en app/database.py (DB_CONFIG) "
                f"y que la base 'planifica_tu_carrera' exista "
                f"(ejecutá db/schema.sql).\n\nDetalle: {e}",
            )
            return
        self._estudiantes = {e["nombre"]: e["id_estudiante"] for e in estudiantes}
        self.combo_estudiante["values"] = list(self._estudiantes.keys())
        if estudiantes:
            self.combo_estudiante.current(0)
            self._on_seleccionar_estudiante()

    def _on_seleccionar_estudiante(self, *_):
        nombre = self.combo_estudiante.get()
        if not nombre:
            return
        self.id_estudiante = self._estudiantes[nombre]
        self.refrescar_todo()

    def _nuevo_estudiante(self):
        nombre = simpledialog.askstring("Nuevo estudiante", "Nombre del estudiante:")
        if not nombre:
            return
        id_est = obtener_o_crear_estudiante(self.bd, nombre.strip())
        self._cargar_lista_estudiantes()
        self.combo_estudiante.set(nombre.strip())
        self.id_estudiante = id_est
        self.refrescar_todo()

    def _cargar_caso_martin(self):
        if "Martín" not in self._estudiantes:
            messagebox.showinfo(
                "Caso de Martín",
                "No se encontró a 'Martín' en la base. Ejecutá db/schema.sql "
                "completo: ese script ya carga su situación académica.",
            )
            return
        self.combo_estudiante.set("Martín")
        self._on_seleccionar_estudiante()
        self.nb.select(self.tab_resumen)

    # -------------------------------------------------------------
    # Refresco general
    # -------------------------------------------------------------
    def refrescar_todo(self):
        if self.id_estudiante is None:
            return
        try:
            asignaturas = obtener_plan_de_estudios(self.bd)
            correlatividades = obtener_correlatividades(self.bd)
            situacion = obtener_situacion_academica(self.bd, self.id_estudiante)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos.\n{e}")
            return

        self.plan = PlanDeCarrera(asignaturas, correlatividades, situacion)

        self._refrescar_tab_plan()
        self._refrescar_tab_situacion()
        self._refrescar_tab_habilitadas()
        self._refrescar_tab_finales()
        self._refrescar_tab_impacto_selector()
        self._refrescar_tab_alternativas()
        self._refrescar_tab_resumen()

        avance = self.plan.avance_general()
        self.lbl_avance.config(
            text=f"Avance: {avance['aprobadas']}/{avance['total_materias']} "
                 f"aprobadas ({avance['porcentaje_aprobado']}%)"
        )

    # -------------------------------------------------------------
    # Tab 1: Plan de estudios
    # -------------------------------------------------------------
    def _construir_tab_plan(self):
        cols = ("codigo", "nivel", "nombre", "horas", "estado")
        self.tree_plan = ttk.Treeview(self.tab_plan, columns=cols, show="headings", height=22)
        anchos = (60, 60, 420, 70, 160)
        titulos = ("N°", "Nivel", "Asignatura", "Hs.", "Estado")
        for c, w, t in zip(cols, anchos, titulos):
            self.tree_plan.heading(c, text=t)
            self.tree_plan.column(c, width=w, anchor="w")
        self.tree_plan.pack(fill="both", expand=True, padx=6, pady=6)
        for estado, color in COLOR_ESTADO.items():
            self.tree_plan.tag_configure(estado, background=color)

    def _refrescar_tab_plan(self):
        self.tree_plan.delete(*self.tree_plan.get_children())
        for nivel, materias in self.plan.por_nivel().items():
            for a in materias:
                nombre = a.nombre + (" (Integradora)" if a.es_integradora else "")
                nombre += " [Electiva]" if a.es_electiva else ""
                self.tree_plan.insert(
                    "", "end",
                    values=(a.codigo, a.nivel, nombre, a.horas or "-", a.estado.replace("_", " ")),
                    tags=(a.estado,),
                )

    # -------------------------------------------------------------
    # Tab 2: Situación académica (editable)
    # -------------------------------------------------------------
    def _construir_tab_situacion(self):
        info = ttk.Label(
            self.tab_situacion,
            text="Doble clic sobre una fila para cambiar el estado de esa asignatura.",
            font=("", 9, "italic"),
        )
        info.pack(anchor="w", padx=6, pady=(6, 0))

        cols = ("codigo", "nivel", "nombre", "estado")
        self.tree_situacion = ttk.Treeview(self.tab_situacion, columns=cols, show="headings", height=22)
        anchos = (60, 60, 460, 160)
        titulos = ("N°", "Nivel", "Asignatura", "Estado")
        for c, w, t in zip(cols, anchos, titulos):
            self.tree_situacion.heading(c, text=t)
            self.tree_situacion.column(c, width=w, anchor="w")
        self.tree_situacion.pack(fill="both", expand=True, padx=6, pady=6)
        for estado, color in COLOR_ESTADO.items():
            self.tree_situacion.tag_configure(estado, background=color)
        self.tree_situacion.bind("<Double-1>", self._editar_estado)

    def _refrescar_tab_situacion(self):
        self.tree_situacion.delete(*self.tree_situacion.get_children())
        for nivel, materias in self.plan.por_nivel().items():
            for a in materias:
                self.tree_situacion.insert(
                    "", "end", iid=str(a.id),
                    values=(a.codigo, a.nivel, a.nombre, a.estado.replace("_", " ")),
                    tags=(a.estado,),
                )

    def _editar_estado(self, event):
        item = self.tree_situacion.identify_row(event.y)
        if not item:
            return
        id_asignatura = int(item)
        nombre = self.plan.asignaturas[id_asignatura].nombre
        actual = self.plan.asignaturas[id_asignatura].estado

        ventana = tk.Toplevel(self)
        ventana.title(nombre)
        ttk.Label(ventana, text=f"Nuevo estado para:\n{nombre}").pack(padx=12, pady=8)
        combo = ttk.Combobox(ventana, values=ESTADOS, state="readonly")
        combo.set(actual)
        combo.pack(padx=12, pady=4)

        def guardar():
            nuevo_estado = combo.get()
            guardar_estado_asignatura(self.bd, self.id_estudiante, id_asignatura, nuevo_estado)
            ventana.destroy()
            self.refrescar_todo()

        ttk.Button(ventana, text="Guardar", command=guardar).pack(pady=8)

    # -------------------------------------------------------------
    # Tab 3: Habilitadas / No habilitadas
    # -------------------------------------------------------------
    def _construir_tab_habilitadas(self):
        frame = ttk.Frame(self.tab_habilitadas)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        izq = ttk.LabelFrame(frame, text="✅ Puede cursar")
        izq.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.list_habilitadas = tk.Listbox(izq)
        self.list_habilitadas.pack(fill="both", expand=True, padx=4, pady=4)

        der = ttk.LabelFrame(frame, text="🚫 No puede cursar (motivo)")
        der.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.list_no_habilitadas = tk.Listbox(der)
        self.list_no_habilitadas.pack(fill="both", expand=True, padx=4, pady=4)

    def _refrescar_tab_habilitadas(self):
        self.list_habilitadas.delete(0, "end")
        for a in self.plan.materias_habilitadas():
            self.list_habilitadas.insert("end", f"Nivel {a.nivel} — {_etiqueta(a)}")

        self.list_no_habilitadas.delete(0, "end")
        for a, bloqueos in self.plan.materias_no_habilitadas():
            motivos = "; ".join(
                f"necesita {b.nombre_requisito} {b.estado_requerido} "
                f"(actual: {b.estado_actual.replace('_', ' ')})"
                for b in bloqueos
            )
            self.list_no_habilitadas.insert("end", f"Nivel {a.nivel} — {a.nombre}: {motivos}")

    # -------------------------------------------------------------
    # Tab 4: Finales pendientes / a recursar
    # -------------------------------------------------------------
    def _construir_tab_finales(self):
        frame = ttk.Frame(self.tab_finales)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        izq = ttk.LabelFrame(frame, text="📝 Finales pendientes (regularizadas)")
        izq.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.list_finales = tk.Listbox(izq)
        self.list_finales.pack(fill="both", expand=True, padx=4, pady=4)

        der = ttk.LabelFrame(frame, text="🔁 A recursar (no regularizadas)")
        der.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.list_recursar = tk.Listbox(der)
        self.list_recursar.pack(fill="both", expand=True, padx=4, pady=4)

    def _refrescar_tab_finales(self):
        self.list_finales.delete(0, "end")
        for a in self.plan.materias_con_final_pendiente():
            self.list_finales.insert("end", f"Nivel {a.nivel} — {a.nombre}")

        self.list_recursar.delete(0, "end")
        for a in self.plan.materias_a_recursar():
            self.list_recursar.insert("end", f"Nivel {a.nivel} — {a.nombre}")

    # -------------------------------------------------------------
    # Tab 5: Impacto futuro
    # -------------------------------------------------------------
    def _construir_tab_impacto(self):
        top = ttk.Frame(self.tab_impacto)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Ver impacto futuro de:").pack(side="left")
        self.combo_impacto = ttk.Combobox(top, state="readonly", width=55)
        self.combo_impacto.pack(side="left", padx=6)
        ttk.Button(top, text="Ver impacto", command=self._mostrar_impacto).pack(side="left")

        self.list_impacto = tk.Listbox(self.tab_impacto)
        self.list_impacto.pack(fill="both", expand=True, padx=6, pady=6)

    def _refrescar_tab_impacto_selector(self):
        pendientes = self.plan.materias_a_recursar() + self.plan.materias_con_final_pendiente()
        self._map_impacto = {f"{a.nombre} ({a.estado.replace('_',' ')})": a.id for a in pendientes}
        self.combo_impacto["values"] = list(self._map_impacto.keys())
        self.list_impacto.delete(0, "end")
        if self.combo_impacto["values"]:
            self.combo_impacto.current(0)
            self._mostrar_impacto()

    def _mostrar_impacto(self):
        etiqueta = self.combo_impacto.get()
        self.list_impacto.delete(0, "end")
        if not etiqueta:
            return
        id_asignatura = self._map_impacto[etiqueta]
        afectadas = self.plan.impacto_futuro(id_asignatura)
        if not afectadas:
            self.list_impacto.insert("end", "No condiciona el cursado de ninguna otra asignatura.")
        for a in afectadas:
            self.list_impacto.insert("end", f"Nivel {a.nivel} — {a.nombre}")

    # -------------------------------------------------------------
    # Tab 6: Alternativas de planificación
    # -------------------------------------------------------------
    def _construir_tab_alternativas(self):
        self.txt_alternativas = tk.Text(self.tab_alternativas, wrap="word")
        self.txt_alternativas.pack(fill="both", expand=True, padx=6, pady=6)
        self.txt_alternativas.tag_configure("titulo", font=("", 11, "bold"))

    def _refrescar_tab_alternativas(self):
        self.txt_alternativas.config(state="normal")
        self.txt_alternativas.delete("1.0", "end")
        for alt in self.plan.generar_alternativas():
            self.txt_alternativas.insert("end", alt["titulo"] + "\n", "titulo")
            self.txt_alternativas.insert("end", alt["descripcion"] + "\n\n")
            for accion in alt["acciones"]:
                self.txt_alternativas.insert("end", f"   • {accion}\n")
            self.txt_alternativas.insert("end", f"\n   Ventaja: {alt['ventaja']}\n")
            self.txt_alternativas.insert("end", f"   Desventaja: {alt['desventaja']}\n")
            self.txt_alternativas.insert("end", "\n" + "-" * 90 + "\n\n")
        self.txt_alternativas.config(state="disabled")

    # -------------------------------------------------------------
    # Tab 7: Resumen del caso (responde el cuestionario del PDF)
    # -------------------------------------------------------------
    def _construir_tab_resumen(self):
        self.txt_resumen = tk.Text(self.tab_resumen, wrap="word")
        self.txt_resumen.pack(fill="both", expand=True, padx=6, pady=6)
        self.txt_resumen.tag_configure("pregunta", font=("", 10, "bold"))

    def _refrescar_tab_resumen(self):
        self.txt_resumen.config(state="normal")
        self.txt_resumen.delete("1.0", "end")
        r = self.plan.responder_cuestionario()
        t = self.txt_resumen

        t.insert("end", "1) ¿Qué asignaturas puede cursar?\n", "pregunta")
        for a in r["1_puede_cursar"]:
            t.insert("end", f"   • {a.nombre} (Nivel {a.nivel})\n")

        t.insert("end", "\n2) ¿Qué asignaturas NO puede cursar y por qué?\n", "pregunta")
        for a, bloqueos in r["2_no_puede_cursar"]:
            motivos = "; ".join(f"{b.nombre_requisito} debe estar {b.estado_requerido}" for b in bloqueos)
            t.insert("end", f"   • {a.nombre}: {motivos}\n")

        t.insert("end", "\n3) Consecuencias de no haber regularizado:\n", "pregunta")
        for m in r["3_consecuencias_no_regularizada"]["materias"]:
            t.insert("end", f"   • {m.nombre} obliga a recursar.\n")
        afectadas = r["3_consecuencias_no_regularizada"]["impacto"]
        if afectadas:
            t.insert("end", "   Esto además retrasa: " +
                      ", ".join(sorted(set(a.nombre for a in afectadas))) + "\n")

        t.insert("end", "\n4) ¿Qué final conviene priorizar?\n", "pregunta")
        top_final = r["4_final_a_priorizar"]
        if top_final:
            impacto = len(self.plan.impacto_futuro(top_final.id))
            t.insert("end", f"   • {top_final.nombre}, porque condiciona {impacto} "
                             f"asignatura/s futura/s (el mayor impacto entre los pendientes).\n")
        for a in r["4_ranking_finales"]:
            t.insert("end", f"      - {a.nombre}: destraba {len(self.plan.impacto_futuro(a.id))}\n")

        t.insert("end", "\n5) Asignaturas de niveles posteriores que podrían verse afectadas:\n", "pregunta")
        for nombre_origen, afectadas in r["5_materias_futuras_afectadas"].items():
            nombres = ", ".join(a.nombre for a in afectadas) if afectadas else "(ninguna)"
            t.insert("end", f"   • Por {nombre_origen}: {nombres}\n")

        t.insert("end", "\n6) Alternativas de planificación: ver pestaña 'Alternativas'.\n", "pregunta")

        t.insert("end", "\n7) Avance general de la carrera:\n", "pregunta")
        avance = r["7_avance_general"]
        t.insert("end", f"   • {avance['aprobadas']} de {avance['total_materias']} materias "
                         f"aprobadas ({avance['porcentaje_aprobado']}%). "
                         f"{avance['regulares_con_final_pendiente']} con final pendiente.\n")

        t.config(state="disabled")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
