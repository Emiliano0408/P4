from automata_core import State, Automaton

def preprocess_regex(expression):
    """Inserta operadores de concatenación explícitos (.) y valida sintaxis básica."""
    if not expression:
        raise ValueError("La expresión regular está vacía (Posición: 0).")
    
    output = []
    operators = {'+', '*'}
    binary_ops = {'+'}
    
    for i in range(len(expression)):
        c1 = expression[i]
        output.append(c1)
        
        if i + 1 < len(expression):
            c2 = expression[i + 1]
            
            # Validar caracteres no permitidos
            if not (c1.isalnum() or c1 in {'+', '*', '(', ')', 'λ', '∅'}):
                raise ValueError(f"Símbolo no reconocido '{c1}' en la posición {i}.")
            
            # Reglas para concatenación implícita
            if (c1 not in binary_ops and c1 != '(') and (c2 != ')' and c2 not in operators and c2 != '+'):
                output.append('.')
            elif c1 == '*' and (c2 != ')' and c2 not in operators and c2 != '+'):
                output.append('.')
            elif c1 == ')' and (c2 == '(' or (c2 != ')' and c2 not in operators and c2 != '+')):
                output.append('.')
                
    last_c = expression[-1]
    if not (last_c.isalnum() or last_c in {'*', ')', 'λ', '∅'}):
        raise ValueError(f"Símbolo no reconocido '{last_c}' en la posición {len(expression)-1}.")
        
    return "".join(output)

def infix_to_postfix(expression):
    """Convierte la expresión infija a postfija respetando precedencias y reportando posición del error[cite: 1, 2]."""
    precedence = {'*': 3, '.': 2, '+': 1}
    output = []
    stack = []
    
    processed = preprocess_regex(expression)
    
    for idx, char in enumerate(expression):
        if char.isalnum() or char in {'λ', '∅'}:
            output.append(char)
        elif char == '(':
            stack.append((char, idx))
        elif char == ')':
            found_opening = False
            while stack:
                top, top_idx = stack.pop()
                if top == '(':
                    found_opening = True
                    break
                output.append(top)
            if not found_opening:
                raise ValueError(f"Error de sintaxis: Paréntesis de cierre ')' sin apertura en la posición {idx}.")
        elif char in precedence:
            while stack and stack[-1][0] != '(' and precedence.get(stack[-1][0], 0) >= precedence[char]:
                output.append(stack.pop()[0])
            stack.append((char, idx))
        else:
            raise ValueError(f"Error de sintaxis: Carácter inválido '{char}' en la posición {idx}.")
            
    while stack:
        top, top_idx = stack.pop()
        if top == '(':
            raise ValueError(f"Error de sintaxis: Paréntesis de apertura '(' sin cerrar en la posición {top_idx}.")
        output.append(top)
        
    return output

def build_thompson(postfix):
   def build_thompson_with_steps(postfix):
    """
    Construye el AFN-λ paso a paso, devolviendo el autómata final 
    y un registro detallado de cada autómata parcial generado.
    """
    stack = []
    steps = [] # Historial de autómatas parciales
    
    for idx, token in enumerate(postfix):
        if token.isalnum() or token in {'λ', '∅'}:
            start = State()
            accept = State(is_accept=True)
            sym = None if token in {'λ', '∅'} and token != '∅' else token
            
            if token != '∅':
                start.add_transition(sym, accept)
            
            nfa_part = Automaton({start, accept}, start, {sym} if sym else set())
            stack.append(nfa_part)
            
            steps.append({
                "paso": len(steps) + 1,
                "accion": f"Crear autómata básico para el símbolo '{token}'",
                "estados": len(nfa_part.states),
                "alfabeto": list(nfa_part.alphabet)
            })
            
        elif token == '.': # Concatenación
            if len(stack) < 2:
                raise ValueError("Error de sintaxis en concatenación.")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            
            nfa1.accept_state.is_accept = False
            nfa1.accept_state.add_transition(None, nfa2.start_state)
            
            combined_states = nfa1.states | nfa2.states
            combined_alphabet = nfa1.alphabet | nfa2.alphabet | {None}
            nfa_res = Automaton(combined_states, nfa1.start_state, combined_alphabet)
            nfa_res.accept_state = nfa2.accept_state
            nfa_res.accept_state.is_accept = True
            
            stack.append(nfa_res)
            steps.append({
                "paso": len(steps) + 1,
                "accion": "Aplicar construcción de Concatenación (.)",
                "estados": len(nfa_res.states),
                "alfabeto": list(nfa_res.alphabet)
            })
            
        elif token == '+': # Unión
            if len(stack) < 2:
                raise ValueError("Error de sintaxis en unión.")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            
            start = State()
            accept = State(is_accept=True)
            
            nfa1.accept_state.is_accept = False
            nfa2.accept_state.is_accept = False
            
            start.add_transition(None, nfa1.start_state)
            start.add_transition(None, nfa2.start_state)
            nfa1.accept_state.add_transition(None, accept)
            nfa2.accept_state.add_transition(None, accept)
            
            combined_states = nfa1.states | nfa2.states | {start, accept}
            combined_alphabet = nfa1.alphabet | nfa2.alphabet | {None}
            nfa_res = Automaton(combined_states, start, combined_alphabet)
            nfa_res.accept_state = accept
            
            stack.append(nfa_res)
            steps.append({
                "paso": len(steps) + 1,
                "accion": "Aplicar construcción de Unión (+)",
                "estados": len(nfa_res.states),
                "alfabeto": list(nfa_res.alphabet)
            })
            
        elif token == '*': # Cerradura de Kleene
            if len(stack) < 1:
                raise ValueError("Error de sintaxis en cerradura de Kleene.")
            nfa = stack.pop()
            
            start = State()
            accept = State(is_accept=True)
            
            nfa.accept_state.is_accept = False
            
            start.add_transition(None, nfa.start_state)
            start.add_transition(None, accept)
            nfa.accept_state.add_transition(None, nfa.start_state)
            nfa.accept_state.add_transition(None, accept)
            
            combined_states = nfa.states | {start, accept}
            combined_alphabet = nfa.alphabet | {None}
            nfa_res = Automaton(combined_states, start, combined_alphabet)
            nfa_res.accept_state = accept
            
            stack.append(nfa_res)
            steps.append({
                "paso": len(steps) + 1,
                "accion": "Aplicar Cerradura de Kleene (*)",
                "estados": len(nfa_res.states),
                "alfabeto": list(nfa_res.alphabet)
            })
            
    if len(stack) != 1:
        raise ValueError("Expresión regular mal formada.")
        
    final_nfa = stack.pop()
    final_nfa.accept_state.is_accept = True
    return final_nfa, steps
    # Asegurar que el estado final guarde la bandera de aceptación correctamente
    final_nfa.accept_state.is_accept = True
    return final_nfa