import xml.etree.ElementTree as ET

class State:
    def __init__(self, name=None, is_accept=False):
        # Generar nombre único automático si no se provee
        global _state_counter
        if '_state_counter' not in globals():
            _state_counter = 0
            
        if name is None:
            self.name = f"q{_state_counter}"
            _state_counter += 1
        else:
            self.name = str(name)
            
        self.is_accept = is_accept
        self.transitions = {} # {simbolo: [estado_destino1, estado_destino2, ...]}

    def add_transition(self, symbol, target_state):
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        if target_state not in self.transitions[symbol]:
            self.transitions[symbol].append(target_state)

    def __repr__(self):
        return f"State({self.name}, accept={self.is_accept})"


class Automaton:
    def __init__(self, states, start_state, alphabet, accept_state=None):
        self.states = states
        self.start_state = start_state
        self.alphabet = alphabet
        
        if accept_state is not None:
            self.accept_state = accept_state
        else:
            accepts = [s for s in states if s.is_accept]
            self.accept_state = accepts[0] if accepts else None

    @classmethod
    def import_from_jff(cls, filepath):
        """Importa un autómata desde un archivo XML (.jff) de JFLAP."""
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        states_map = {}
        states_set = set()
        start_state = None
        
        # 1. Leer estados
        for state_elem in root.findall(".//state"):
            s_id = state_elem.get("id")
            s_name = state_elem.get("name", f"q{s_id}")
            
            # Verificar si es de aceptación
            is_accept = state_elem.find("final") is not None
            
            state_obj = State(name=s_name, is_accept=is_accept)
            states_map[s_id] = state_obj
            states_set.add(state_obj)
            
            # Verificar si es inicial
            if state_elem.find("initial") is not None:
                start_state = state_obj

        if not start_state and states_set:
            start_state = list(states_set)[0]

        alphabet = set()

        # 2. Leer transiciones
        for trans_elem in root.findall(".//transition"):
            from_id = trans_elem.find("from").text
            to_id = trans_elem.find("to").text
            read_elem = trans_elem.find("read")
            
            symbol = read_elem.text if read_elem is not None and read_elem.text is not None else None
            
            if symbol == "" or symbol is None:
                symbol = None # Transición lambda
            else:
                alphabet.add(symbol)
                
            if from_id in states_map and to_id in states_map:
                states_map[from_id].add_transition(symbol, states_map[to_id])

        return cls(states_set, start_state, alphabet)

    def export_to_jff(self, filepath):
        """Exporta el autómata actual a formato .jff (JFLAP)."""
        root = ET.Element("structure")
        type_elem = ET.SubElement(root, "type")
        type_elem.text = "fa"
        automaton_elem = ET.SubElement(root, "automaton")
        
        state_to_id = {s: i for i, s in enumerate(self.states)}
        
        for s, s_id in state_to_id.items():
            state_el = ET.SubElement(automaton_elem, "state", id=str(s_id), name=s.name)
            if s == self.start_state:
                ET.SubElement(state_el, "initial")
            if s.is_accept:
                ET.SubElement(state_el, "final")
                
        for s, s_id in state_to_id.items():
            for symbol, targets in s.transitions.items():
                for t in targets:
                    t_id = state_to_id[t]
                    trans_el = ET.SubElement(automaton_elem, "transition")
                    ET.SubElement(trans_el, "from").text = str(s_id)
                    ET.SubElement(trans_el, "to").text = str(t_id)
                    read_el = ET.SubElement(trans_el, "read")
                    read_el.text = "" if symbol is None else str(symbol)
                    
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def get_lambda_closure(state_set):
        """Calcula la cerradura λ (lambda-closure) de un conjunto de estados."""
        closure = set(state_set)
        stack = list(state_set)
        
        while stack:
            current = stack.pop()
            if None in current.transitions:
                for neighbor in current.transitions[None]:
                    if neighbor not in closure:
                        closure.add(neighbor)
                        stack.append(neighbor)
        return closure

    @classmethod
    def remove_lambda_transitions(cls, nfa):
        """Elimina las transiciones λ de un AFN obteniendo un AFN equivalente."""
        new_states = {}
        for s in nfa.states:
            new_states[s] = State(name=s.name, is_accept=s.is_accept)
            
        for s in nfa.states:
            closure = cls.get_lambda_closure({s})
            is_accept = any(st.is_accept for st in closure)
            new_states[s].is_accept = is_accept
            
        alphabet = nfa.alphabet - {None}
        
        for s in nfa.states:
            closure = cls.get_lambda_closure({s})
            for symbol in alphabet:
                reachable = set()
                for st in closure:
                    if symbol in st.transitions:
                        for target in st.transitions[symbol]:
                            reachable.update(cls.get_lambda_closure({target}))
                
                for target_st in reachable:
                    new_states[s].add_transition(symbol, new_states[target_st])
                    
        start_closure = cls.get_lambda_closure({nfa.start_state})
        new_start = new_states[nfa.start_state]
        
        states_set = set(new_states.values())
        return cls(states_set, new_start, alphabet)

    @classmethod
    def subset_construction(cls, nfa):
        """Convierte un AFN en un AFD usando el algoritmo de construcción de subconjuntos."""
        alphabet = nfa.alphabet
        start_closure = frozenset(cls.get_lambda_closure({nfa.start_state}))
        
        dfa_states_map = {start_closure: State(name=f"S_{0}", is_accept=any(s.is_accept for s in start_closure))}
        unmarked = [start_closure]
        
        dfa_states = {dfa_states_map[start_closure]}
        dfa_start = dfa_states_map[start_closure]
        
        counter = 1
        while unmarked:
            current_closure = unmarked.pop()
            current_dfa_state = dfa_states_map[current_closure]
            
            for symbol in alphabet:
                move_set = set()
                for s in current_closure:
                    if symbol in s.transitions:
                        move_set.update(s.transitions[symbol])
                
                if not move_set:
                    continue
                    
                target_closure = frozenset(cls.get_lambda_closure(move_set))
                
                if target_closure not in dfa_states_map:
                    is_acc = any(s.is_accept for s in target_closure)
                    new_state = State(name=f"S_{counter}", is_accept=is_acc)
                    counter += 1
                    dfa_states_map[target_closure] = new_state
                    dfa_states.add(new_state)
                    unmarked.append(target_closure)
                    
                current_dfa_state.add_transition(symbol, dfa_states_map[target_closure])
                
        return cls(dfa_states, dfa_start, alphabet)

    @classmethod
    def minimize_dfa(cls, dfa):
        """Minimiza un AFD usando el algoritmo de partición de equivalencia (Hopcroft / Moore)."""
        states = list(dfa.states)
        alphabet = dfa.alphabet
        
        accepting = {s for s in states if s.is_accept}
        non_accepting = {s for s in states if not s.is_accept}
        
        partitions = []
        if accepting:
            partitions.append(accepting)
        if non_accepting:
            partitions.append(non_accepting)
            
        while True:
            new_partitions = []
            for group in partitions:
                subgroups = {}
                for s in group:
                    signature = tuple(
                        next((i for i, p in enumerate(partitions) if any(t in p for t in s.transitions.get(sym, []))), -1)
                        for sym in sorted(alphabet)
                    )
                    if signature not in subgroups:
                        subgroups[signature] = set()
                    subgroups[signature].add(s)
                new_partitions.extend(subgroups.values())
                
            if len(new_partitions) == len(partitions):
                break
            partitions = new_partitions
            
        state_to_group = {}
        for i, group in enumerate(partitions):
            for s in group:
                state_to_group[s] = i
                
        new_states_map = {}
        for i, group in enumerate(partitions):
            rep = list(group)[0]
            new_states_map[i] = State(name=f"M_{i}", is_accept=rep.is_accept)
            
        new_states = set(new_states_map.values())
        new_start = new_states_map[state_to_group[dfa.start_state]]
        
        for i, group in enumerate(partitions):
            rep = list(group)[0]
            current_new = new_states_map[i]
            for sym, targets in rep.transitions.items():
                if targets:
                    target_group_idx = state_to_group[targets[0]]
                    current_new.add_transition(sym, new_states_map[target_group_idx])
                    
        return cls(new_states, new_start, alphabet)

    def verificar_determinismo(self):
        """
        Verifica si el autómata es determinista (AFD).
        Si no lo es, retorna (False, estado_fallido, simbolo_fallido).
        Si lo es, retorna (True, None, None).
        """
        for s in self.states:
            if None in s.transitions and s.transitions[None]:
                return False, s.name, "λ (transición vacía)"
            
            seen_symbols = set()
            for symbol, targets in s.transitions.items():
                if len(targets) > 1:
                    return False, s.name, symbol
                if symbol in seen_symbols:
                    return False, s.name, symbol
                seen_symbols.add(symbol)
                
        return True, None, None

    def eliminacion_estados_paso_a_paso(self):
        """
        Aplica el método de eliminación de estados (GNFA) para obtener la expresión regular,
        registrando el autómata generalizado después de eliminar cada estado.
        """
        is_dfa, estado_err, simb_err = self.verificar_determinismo()
        if not is_dfa:
            raise ValueError(f"El autómata no es determinista. Falla en el estado '{estado_err}' con el símbolo '{simb_err}'.")

        q_start = State(name="q_start")
        q_accept = State(name="q_accept", is_accept=True)
        
        trans = {}
        all_states = list(self.states)
        
        for s in all_states:
            for symbol, targets in s.transitions.items():
                for t in targets:
                    pair = (s, t)
                    sym_str = str(symbol) if symbol is not None else "λ"
                    if pair in trans:
                        trans[pair] += f"+{sym_str}"
                    else:
                        trans[pair] = sym_str

        trans[(q_start, self.start_state)] = "λ"

        for s in all_states:
            if s.is_accept:
                pair = (s, q_accept)
                if pair in trans:
                    trans[pair] += "+λ"
                else:
                    trans[pair] = "λ"

        states_to_eliminate = list(all_states)
        steps = []

        steps.append({
            "paso": 0,
            "estado_eliminado": "Ninguno (GNFA Inicial)",
            "transiciones": {f"{k[0].name} -> {k[1].name}": v for k, v in trans.items()}
        })

        for idx, q_k in enumerate(states_to_eliminate):
            predecesores = [s for s in list(trans.keys()) if s[1] == q_k and s[0] != q_k]
            sucesores = [s for s in list(trans.keys()) if s[0] == q_k and s[1] != q_k]
            
            loop_kk = trans.get((q_k, q_k), None)

            for pred in predecesores:
                q_i = pred[0]
                r_ik = trans[(q_i, q_k)]

                for suc in sucesores:
                    q_j = suc[1]
                    r_kj = trans[(q_k, q_j)]

                    parts = []
                    if (q_i, q_j) in trans:
                        parts.append(trans[(q_i, q_j)])
                    
                    middle = ""
                    if loop_kk and loop_kk != "λ":
                        middle += f"({loop_kk})*"
                    
                    r_ik_clean = "" if r_ik == "λ" else r_ik
                    r_kj_clean = "" if r_kj == "λ" else r_kj
                    
                    if r_ik_clean and r_kj_clean:
                        path = f"({r_ik_clean}){middle}({r_kj_clean})" if ("+" in r_ik or "+" in r_kj) else f"{r_ik_clean}{middle}{r_kj_clean}"
                    elif r_ik_clean:
                        path = f"({r_ik_clean}){middle}" if "+" in r_ik else f"{r_ik_clean}{middle}"
                    elif r_kj_clean:
                        path = f"{middle}({r_kj_clean})" if "+" in r_kj else f"{middle}{r_kj_clean}"
                    else:
                        path = middle if middle else "λ"

                    parts.append(path)
                    
                    trans[(q_i, q_j)] = "+".join(parts) if len(parts) > 1 else parts[0]

            keys_to_remove = [k for k in trans.keys() if k[0] == q_k or k[1] == q_k]
            for k in keys_to_remove:
                del trans[k]

            steps.append({
                "paso": idx + 1,
                "estado_eliminado": q_k.name,
                "transiciones": {f"{k[0].name} -> {k[1].name}": v for k, v in trans.items()}
            })

        final_regex = trans.get((q_start, q_accept), "∅")
        return final_regex, steps