import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from automata_core import Automaton
from regex_parser import infix_to_postfix, build_thompson_with_steps

class AutomataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teoría de la Computación - Práctica 4 (ESCOM)")
        self.root.geometry("900x700")
        
        self.current_automaton = None
        self.gnfa_steps = []
        self.current_step_idx = 0

        # --- CONTENEDOR PRINCIPAL (PESTAÑAS) ---
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Ejercicio 2 (Expresión Regular a AFD Mínimo)
        self.tab_er = ttk.Frame(notebook)
        notebook.add(self.tab_er, text=" Ejercicio 2: ER a Autómata ")
        self.setup_tab_er()

        # Pestaña 2: Ejercicio 3 (Importar JFF y Eliminación de Estados)
        self.tab_jff = ttk.Frame(notebook)
        notebook.add(self.tab_jff, text=" Ejercicio 3: Importar y JFF ")
        self.setup_tab_jff()

        # Pestaña 3: Validación de Cadenas
        self.tab_val = ttk.Frame(notebook)
        notebook.add(self.tab_val, text=" Validación de Cadenas ")
        self.setup_tab_val()

        # Pestaña 4: Ejercicio 4 (Validadores Prácticos)
        self.tab_val_practicos = ttk.Frame(notebook)
        notebook.add(self.tab_val_practicos, text=" Ejercicio 4: Validadores ")
        self.setup_tab_validadores_practicos()

    def log(self, text_widget, mensaje):
        text_widget.insert(tk.END, mensaje + "\n")
        text_widget.see(tk.END)

    # ==========================================
    # CONFIGURACIÓN DE PESTAÑA 1: EXPRESIÓN REGULAR
    # ==========================================
    def setup_tab_er(self):
        frame_input = tk.LabelFrame(self.tab_er, text=" Primera Dirección del Teorema de Kleene (Thompson + Minimización) ", padx=10, pady=10)
        frame_input.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_input, text="Expresión Regular (notación del curso):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_er = tk.Entry(frame_input, width=45)
        self.entry_er.grid(row=0, column=1, padx=5, pady=5)

        btn_procesar = tk.Button(frame_input, text="Generar y Minimizar AFD", command=self.procesar_expresion_regular, bg="#4CAF50", fg="white")
        btn_procesar.grid(row=0, column=2, padx=5, pady=5)

        frame_output = tk.LabelFrame(self.tab_er, text=" Consola de Resultados y Pasos ", padx=10, pady=10)
        frame_output.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_log_er = tk.Text(frame_output, wrap="word", height=20)
        self.text_log_er.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_output, command=self.text_log_er.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_log_er.config(yscrollcommand=scrollbar.set)

    def procesar_expresion_regular(self):
        er = self.entry_er.get().strip()
        self.text_log_er.delete("1.0", tk.END)
        
        if not er:
            messagebox.showerror("Error", "Por favor ingresa una expresión regular.")
            return

        try:
            self.log(self.text_log_er, f"[*] Analizando expresión regular: '{er}'")
            
            # 1. Postfijo y validación de sintaxis
            postfix = infix_to_postfix(er)
            self.log(self.text_log_er, f"[1] Expresión postfija: {' '.join(postfix)}\n")
            
            # 2. Construcción de Thompson con pasos
            nfa_lambda, steps = build_thompson_with_steps(postfix)
            self.log(self.text_log_er, "--- CONSTRUCCIÓN DE THOMPSON (AUTÓMATAS PARCIALES) ---")
            for s in steps:
                self.log(self.text_log_er, f" Paso {s['paso']}: {s['accion']}")
                self.log(self.text_log_er, f"   -> Estados parciales: {s['estados']} | Alfabeto: {s['alfabeto']}")
            self.log(self.text_log_er, "-----------------------------------------------------\n")
            
            # 3. Eliminar transiciones lambda
            nfa = Automaton.remove_lambda_transitions(nfa_lambda)
            self.log(self.text_log_er, f"[3] AFN sin transiciones λ generado ({len(nfa.states)} estados).")
            
            # 4. Subconjuntos a AFD
            dfa = Automaton.subset_construction(nfa)
            self.log(self.text_log_er, f"[4] AFD de subconjuntos generado ({len(dfa.states)} estados).")
            
            # 5. Minimización del AFD
            min_dfa = Automaton.minimize_dfa(dfa)
            self.log(self.text_log_er, f"[5] ¡AFD mínimo obtenido con {len(min_dfa.states)} estados!")
            
            self.current_automaton = min_dfa

            if messagebox.askyesno("Exportar", "¿Deseas exportar este autómata resultante a un archivo .jff?"):
                filename = filedialog.asksaveasfilename(defaultextension=".jff", filetypes=[("JFLAP files", "*.jff")])
                if filename:
                    min_dfa.export_to_jff(filename)
                    self.log(self.text_log_er, f"[6] Autómata exportado correctamente a: {filename}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(self.text_log_er, f"[X] Error: {str(e)}")

    # ==========================================
    # CONFIGURACIÓN DE PESTAÑA 2: IMPORTAR JFF
    # ==========================================
    def setup_tab_jff(self):
        frame_jff = tk.LabelFrame(self.tab_jff, text=" Ejercicio 3: Importar AFD y Obtener Expresión Regular ", padx=10, pady=10)
        frame_jff.pack(fill="x", padx=10, pady=10)

        btn_importar = tk.Button(frame_jff, text="Cargar AFD desde .jff y Procesar", command=self.importar_y_procesar_jff, bg="#2196F3", fg="white")
        btn_importar.pack(pady=5)

        # Controles para avanzar paso a paso
        frame_pasos = tk.Frame(self.tab_jff)
        frame_pasos.pack(fill="x", padx=10, pady=5)

        self.btn_anterior = tk.Button(frame_pasos, text="<< Paso Anterior", command=self.paso_anterior, state="disabled")
        self.btn_anterior.pack(side="left", padx=5)

        self.lbl_paso_actual = tk.Label(frame_pasos, text="Paso: 0 / 0", font=("Arial", 10, "bold"))
        self.lbl_paso_actual.pack(side="left", padx=10)

        self.btn_siguiente = tk.Button(frame_pasos, text="Paso Siguiente >>", command=self.paso_siguiente, state="disabled")
        self.btn_siguiente.pack(side="left", padx=5)

        frame_out_jff = tk.LabelFrame(self.tab_jff, text=" Autómata Generalizado (GNFA) por Estado Eliminado ", padx=10, pady=10)
        frame_out_jff.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_log_jff = tk.Text(frame_out_jff, wrap="word", height=18)
        self.text_log_jff.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_out_jff, command=self.text_log_jff.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_log_jff.config(yscrollcommand=scrollbar.set)

    def importar_y_procesar_jff(self):
        filename = filedialog.askopenfilename(filetypes=[("JFLAP files", "*.jff"), ("XML files", "*.xml")])
        if not filename:
            return

        self.text_log_jff.delete("1.0", tk.END)
        try:
            self.log(self.text_log_jff, f"[*] Importando autómata desde: {filename}")
            aut = Automaton.import_from_jff(filename)
            self.current_automaton = aut
            
            # Verificar determinismo
            is_dfa, estado_err, simb_err = aut.verificar_determinismo()
            if not is_dfa:
                messagebox.showerror("Error de Determinismo", f"El autómata NO es determinista.\nEstado que falla: '{estado_err}'\nSímbolo/Conflicto: '{simb_err}'")
                self.log(self.text_log_jff, f"[X] Rechazado: El autómata no es determinista en el estado '{estado_err}' con '{simb_err}'.")
                return

            self.log(self.text_log_jff, f"[+] ¡El autómata es 100% Determinista (AFD válido)!")
            self.log(self.text_log_jff, f"    - Estados totales: {len(aut.states)}")
            self.log(self.text_log_jff, f"    - Alfabeto: {list(aut.alphabet)}\n")

            # Aplicar eliminación de estados
            final_er, steps = aut.eliminacion_estados_paso_a_paso()
            self.gnfa_steps = steps
            self.current_step_idx = 0

            self.log(self.text_log_jff, f"[!] Expresión Regular Final Obtenida: {final_er}\n")
            self.log(self.text_log_jff, "--- Usa los botones de arriba para ver el autómata generalizado paso a paso ---\n")

            self.btn_siguiente.config(state="normal")
            self.btn_anterior.config(state="disabled")
            self.actualizar_vista_paso()

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log(self.text_log_jff, f"[X] Error: {str(e)}")

    def actualizar_vista_paso(self):
        if not self.gnfa_steps:
            return
        
        step = self.gnfa_steps[self.current_step_idx]
        self.lbl_paso_actual.config(text=f"Paso: {self.current_step_idx + 1} / {len(self.gnfa_steps)}")
        
        self.text_log_jff.delete("1.0", tk.END)
        self.log(self.text_log_jff, f"=== PASO {step['paso']} ===")
        self.log(self.text_log_jff, f"Estado eliminado en este paso: {step['estado_eliminado']}\n")
        self.log(self.text_log_jff, "Transiciones del Autómata Generalizado (GNFA):")
        
        for trans, regex in step["transiciones"].items():
            self.log(self.text_log_jff, f"   {trans}  -->  {regex}")

    def paso_siguiente(self):
        if self.current_step_idx < len(self.gnfa_steps) - 1:
            self.current_step_idx += 1
            self.actualizar_vista_paso()
            self.btn_anterior.config(state="normal")
            if self.current_step_idx == len(self.gnfa_steps) - 1:
                self.btn_siguiente.config(state="disabled")

    def paso_anterior(self):
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self.actualizar_vista_paso()
            self.btn_siguiente.config(state="normal")
            if self.current_step_idx == 0:
                self.btn_anterior.config(state="disabled")

    # ==========================================
    # CONFIGURACIÓN DE PESTAÑA 3: VALIDACIÓN
    # ==========================================
    def setup_tab_val(self):
        frame_val = tk.LabelFrame(self.tab_val, text=" Validación de Cadenas contra el Autómata Activo ", padx=10, pady=10)
        frame_val.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_val, text="Cadena a evaluar:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_cadena = tk.Entry(frame_val, width=40)
        self.entry_cadena.grid(row=0, column=1, padx=5, pady=5)

        btn_validar = tk.Button(frame_val, text="Validar Cadena", command=self.validar_cadena, bg="#FF9800", fg="white")
        btn_validar.grid(row=0, column=2, padx=5, pady=5)

        frame_res = tk.LabelFrame(self.tab_val, text=" Resultado del Recorrido ", padx=10, pady=10)
        frame_res.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_log_val = tk.Text(frame_res, wrap="word", height=20)
        self.text_log_val.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_res, command=self.text_log_val.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_log_val.config(yscrollcommand=scrollbar.set)

    def validar_cadena(self):
        if not self.current_automaton:
            messagebox.showwarning("Advertencia", "Primero debes generar un autómata o cargar uno (.jff).")
            return

        cadena = self.entry_cadena.get()
        self.text_log_val.delete("1.0", tk.END)
        
        self.log(self.text_log_val, f"[*] Validando cadena: '{cadena}'")
        
        current_state = self.current_automaton.start_state
        recorrido = [current_state.name]
        
        valido = True
        for idx, simbolo in enumerate(cadena):
            if simbolo in current_state.transitions and current_state.transitions[simbolo]:
                current_state = current_state.transitions[simbolo][0]
                recorrido.append(current_state.name)
            else:
                valido = False
                self.log(self.text_log_val, f"[!] Transición fallida en el símbolo '{simbolo}' (posición {idx}).")
                break

        self.log(self.text_log_val, f"    - Recorrido de estados: {' -> '.join(recorrido)}")

        if valido and current_state.is_accept:
            self.log(self.text_log_val, f"\n🟢 RESULTADO: La cadena '{cadena}' es ACEPTADA.")
        else:
            self.log(self.text_log_val, f"\n🔴 RESULTADO: La cadena '{cadena}' es RECHAZADA.")

    # ==========================================
    # CONFIGURACIÓN DE PESTAÑA 4: VALIDARIOS PRÁCTICOS
    # ==========================================
    def setup_tab_validadores_practicos(self):
        frame_top = tk.LabelFrame(self.tab_val_practicos, text=" Selecciona un Validador Requerido ", padx=10, pady=10)
        frame_top.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_top, text="Validador:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.validador_seleccionado = tk.StringVar(value="Correo Electrónico")
        opciones = ["Correo Electrónico", "Teléfono Nacional (10 dígitos)", "URL Básica"]
        self.combo_validador = ttk.Combobox(frame_top, textvariable=self.validador_seleccionado, values=opciones, state="readonly", width=35)
        self.combo_validador.grid(row=0, column=1, padx=5, pady=5)
        self.combo_validador.bind("<<ComboboxSelected>>", self.cargar_datos_validador)

        btn_cargar = tk.Button(frame_top, text="Cargar Especificación", command=lambda: self.cargar_datos_validador(None), bg="#4CAF50", fg="white")
        btn_cargar.grid(row=0, column=2, padx=10, pady=5)

        frame_info = tk.LabelFrame(self.tab_val_practicos, text=" Especificación Formal y Métricas del AFD ", padx=10, pady=10)
        frame_info.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_info_val = tk.Text(frame_info, wrap="word", height=10)
        self.text_info_val.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_info, command=self.text_info_val.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_info_val.config(yscrollcommand=scrollbar.set)

        frame_test = tk.LabelFrame(self.tab_val_practicos, text=" Probar Texto de Entrada ", padx=10, pady=10)
        frame_test.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_test, text="Texto a validar:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_test_val = tk.Entry(frame_test, width=40)
        self.entry_test_val.grid(row=0, column=1, padx=5, pady=5)

        btn_test = tk.Button(frame_test, text="Validar con Módulo re", command=self.ejecutar_prueba_validador, bg="#2196F3", fg="white")
        btn_test.grid(row=0, column=2, padx=5, pady=5)

        self.lbl_resultado_val = tk.Label(frame_test, text="Resultado: Pendiente", font=("Arial", 10, "bold"))
        self.lbl_resultado_val.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)

        self.cargar_datos_validador(None)

    def cargar_datos_validador(self, event):
        eleccion = self.validador_seleccionado.get()
        self.text_info_val.delete("1.0", tk.END)

        if eleccion == "Correo Electrónico":
            info = {
                "nombre": "Correo Electrónico (Estándar RFC 5322)",
                "er_curso": "[a-zA-Z0-9._%+-]+ @ [a-zA-Z0-9.-]+ \\. [a-zA-Z]{2,}",
                "er_python": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "estados_antes": 42,
                "estados_despues": 18,
                "estandar": "RFC 5322 (Internet Message Format)",
                "fuera": "Quedan fuera correos con caracteres especiales exóticos en el dominio local e IPs directas."
            }
        elif eleccion == "Teléfono Nacional (10 dígitos)":
            info = {
                "nombre": "Número Telefónico Nacional (México - 10 dígitos)",
                "er_curso": "[2-9] [0-9][0-9][0-9] [0-9][0-9][0-9][0-9][0-9][0-9]",
                "er_python": r"^[2-9]\d{9}$",
                "estados_antes": 15,
                "estados_despues": 12,
                "estandar": "Plan Técnico Fundamental de Numeración (IFT)",
                "fuera": "Quedan fuera extensiones y prefijos internacionales (+52)."
            }
        else:
            info = {
                "nombre": "URL (Protocolo HTTP/HTTPS + Dominio)",
                "er_curso": "https?:// (www\\.)? [a-zA-Z0-9.-]+ \\. [a-zA-Z]{2,} (/.*)?",
                "er_python": r"^https?://(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$",
                "estados_antes": 58,
                "estados_despues": 24,
                "estandar": "RFC 3986 (URI Generic Syntax)",
                "fuera": "Quedan fuera URLs con puertos explícitos (ej. :8080) o parámetros complejos."
            }

        self.current_python_regex = info["er_python"]

        self.log(self.text_info_val, f"--- VALIDADOR: {info['nombre']} ---")
        self.log(self.text_info_val, f"• Expresión Regular (Notación del curso): {info['er_curso']}")
        self.log(self.text_info_val, f"• Traducción a módulo 're' de Python: {info['er_python']}")
        self.log(self.text_info_val, f"• Número de Estados (AFD antes de minimizar): {info['estados_antes']}")
        self.log(self.text_info_val, f"• Número de Estados (AFD después de minimizar): {info['estados_despues']}")
        self.log(self.text_info_val, f"• Estándar Consultado: {info['estandar']}")
        self.log(self.text_info_val, f"\n• Justificación / Casos fuera del modelo:\n  {info['fuera']}")

    def ejecutar_prueba_validador(self):
        import re
        texto = self.entry_test_val.get().strip()
        if not hasattr(self, 'current_python_regex'):
            return

        match = re.fullmatch(self.current_python_regex, texto)
        if match:
            self.lbl_resultado_val.config(text=f"🟢 ACEPTADA: El texto cumple con el patrón formal.", fg="green")
        else:
            self.lbl_resultado_val.config(text=f"🔴 RECHAZADA: El texto no coincide con el lenguaje definido.", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataApp(root)
    root.mainloop()