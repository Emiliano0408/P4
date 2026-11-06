import xml.etree.ElementTree as ET

class State:
    _id_counter = 0
    def __init__(self, name=None, is_accept=False):
        self.name = name if name is not None else str(State._id_counter)
        State._id_counter += 1
        self.is_accept = is_accept
        self.transitions = {}  # símbolo -> lista de estados destino (None representa la transición λ)

    def add_transition(self, symbol, state):
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        if state not in self.transitions[symbol]:
            self.transitions[symbol].append(state)

class Automaton:
    def __init__(self, states, start_state, alphabet):
        self.states = states
        self.start_state = start_state
        self.alphabet = alphabet

    @staticmethod
    def lambda_closure(states_set):
        """Calcula la cerradura λ para un conjunto de estados[cite: 4]."""
        closure = set(states_set)
        stack = list(states_set)
        while stack:
            current = stack.pop()
            if None in current.transitions:
                for target in current.transitions[None]:
                    if target not in closure:
                        closure.add(target)
                        stack.append(target)
        return frozenset(closure)

    @classmethod
    def remove_lambda_transitions(cls, nfa):
        """Transforma un AFN-λ en un AFN sin transiciones λ[cite: 4]."""
        new_states = {}
        
        for s in nfa.states:
            new_states[s] = State(name=s.name, is_accept=s.is_accept)

        for s in nfa.states:
            closure = cls.lambda_closure({s})
            is_accept = any(st.is_accept for st in closure)
            new_states[s].is_accept = is_accept

            for symbol in nfa.alphabet:
                if symbol is None:
                    continue
                reachable = set()
                for st in closure:
                    if symbol in st.transitions:
                        for target in st.transitions[symbol]:
                            reachable.update(cls.lambda_closure({target}))
                
                for target in reachable:
                    new_states[s].add_transition(symbol, new_states[target])

        new_start = new_states[nfa.start_state]
        all_new_states = set(new_states.values())
        clean_alphabet = nfa.alphabet - {None}
        return Automaton(all_new_states, new_start, clean_alphabet)

    @classmethod
    def subset_construction(cls, nfa):
        """Transforma un AFN en un AFD equivalente mediante construcción de subconjuntos[cite: 4]."""
        alphabet = nfa.alphabet - {None}
        start_closure = cls.lambda_closure({nfa.start_state})
        
        mapping = {}
        start_dfa_state = State(name="s0", is_accept=any(s.is_accept for s in start_closure))
        mapping[start_closure] = start_dfa_state
        
        dfa_states = {start_dfa_state}
        unmarked = [start_closure]
        processed = set()

        while unmarked:
            current_subset = unmarked.pop(0)
            if current_subset in processed:
                continue
            processed.add(current_subset)
            current_dfa_state = mapping[current_subset]

            for symbol in alphabet:
                move_result = set()
                for s in current_subset:
                    if symbol in s.transitions:
                        move_result.update(s.transitions[symbol])
                
                if not move_result:
                    continue
                
                closure_result = cls.lambda_closure(move_result)
                
                if closure_result not in mapping:
                    is_acc = any(s.is_accept for s in closure_result)
                    new_state = State(name=f"s_{len(mapping)}", is_accept=is_acc)
                    mapping[closure_result] = new_state
                    dfa_states.add(new_state)
                    unmarked.append(closure_result)
                
                current_dfa_state.add_transition(symbol, mapping[closure_result])

        return Automaton(dfa_states, start_dfa_state, alphabet)

    @classmethod
    def minimize_dfa(cls, dfa):
        """Minimiza un AFD mediante el método de partición por equivalencia[cite: 4]."""
        # 1. Eliminar estados inaccesibles
        reachable = set()
        queue = [dfa.start_state]
        while queue:
            curr = queue.pop(0)
            if curr not in reachable:
                reachable.add(curr)
                for targets in curr.transitions.values():
                    for t in targets:
                        if t not in reachable:
                            queue.append(t)
                            
        states = list(reachable)
        accepting = {s for s in states if s.is_accept}
        non_accepting = {s for s in states if not s.is_accept}
        
        partitions = [non_accepting, accepting]
        partitions = [p for p in partitions if p]

        while True:
            new_partitions = []
            for group in partitions:
                subgroups = {}
                for s in group:
                    signature = []
                    for symbol in sorted(dfa.alphabet):
                        target = s.transitions.get(symbol, [None])[0]
                        target_group_idx = -1
                        if target is not None:
                            for idx, p in enumerate(partitions):
                                if target in p:
                                    target_group_idx = idx
                                    break
                        signature.append((symbol, target_group_idx))
                    sig_tuple = tuple(signature)
                    if sig_tuple not in subgroups:
                        subgroups[sig_tuple] = set()
                    subgroups[sig_tuple].add(s)
                new_partitions.extend(subgroups.values())
            
            if len(new_partitions) == len(partitions):
                break
            partitions = new_partitions

        state_mapping = {}
        new_states_set = set()
        new_start = None

        for idx, group in enumerate(partitions):
            is_acc = any(s.is_accept for s in group)
            rep_state = State(name=f"M_{idx}", is_accept=is_acc)
            for s in group:
                state_mapping[s] = rep_state
            new_states_set.add(rep_state)
            if dfa.start_state in group:
                new_start = rep_state

        for group in partitions:
            sample_state = list(group)[0]
            rep_state = state_mapping[sample_state]
            for symbol, targets in sample_state.transitions.items():
                if targets:
                    target_rep = state_mapping[targets[0]]
                    rep_state.add_transition(symbol, target_rep)

        return Automaton(new_states_set, new_start, dfa.alphabet)

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

    def export_to_jff(self, filename):
        """Exporta el autómata a formato XML (.jff) compatible con JFLAP[cite: 20]."""
        root = ET.Element("structure")
        ET.SubElement(root, "type").text = "fa"
        automaton_elem = ET.SubElement(root, "automaton")

        state_to_id = {s: i for i, s in enumerate(self.states)}

        for s, i in state_to_id.items():
            state_elem = ET.SubElement(automaton_elem, "state", id=str(i), name=s.name)
            ET.SubElement(state_elem, "x").text = str(100 + (i * 50) % 500)
            ET.SubElement(state_elem, "y").text = str(100 + (i * 75) % 400)
            if s == self.start_state:
                ET.SubElement(state_elem, "initial")
            if s.is_accept:
                ET.SubElement(state_elem, "final")

        for s, i in state_to_id.items():
            for symbol, targets in s.transitions.items():
                for target in targets:
                    trans_elem = ET.SubElement(automaton_elem, "transition")
                    ET.SubElement(trans_elem, "from").text = str(i)
                    ET.SubElement(trans_elem, "to").text = str(state_to_id[target])
                    ET.SubElement(trans_elem, "read").text = symbol if symbol is not None else ""

        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    @classmethod
    
    def import_from_jff(cls, filename):
        """Importa un autómata desde un archivo .jff de JFLAP[cite: 20]."""
        tree = ET.parse(filename)
        root = tree.getroot()
        automaton_node = root.find("automaton")

        states_map = {}
        alphabet = set()
        start_state = None

        # Leer estados
        for state_elem in automaton_node.findall("state"):
            s_id = state_elem.get("id")
            s_name = state_elem.get("name", s_id)
            is_final = state_elem.find("final") is not None
            is_initial = state_elem.find("initial") is not None

            st = State(name=s_name, is_accept=is_final)
            states_map[s_id] = st
            if is_initial:
                start_state = st

        # Leer transiciones
        for trans_elem in automaton_node.findall("transition"):
            from_id = trans_elem.find("from").text
            to_id = trans_elem.find("to").text
            read_elem = trans_elem.find("read")
            symbol = read_elem.text if read_elem is not None and read_elem.text is not None else None

            if symbol != "":
                alphabet.add(symbol)
            else:
                symbol = None # Transición lambda

            if from_id in states_map and to_id in states_map:
                states_map[from_id].add_transition(symbol, states_map[to_id])

        return cls(set(states_map.values()), start_state, alphabet)