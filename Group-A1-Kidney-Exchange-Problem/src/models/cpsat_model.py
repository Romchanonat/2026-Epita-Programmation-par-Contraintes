import time
from ortools.sat.python import cp_model
from .base import BaseSolver, KEPSolution 

class CPSatSolver(BaseSolver):
    """
    Solveur CP-SAT focalisé sur l'optimisation des cycles.
    Le problème est modélisé comme un Exact Cover / Set Packing.
    """

    def solve(self) -> KEPSolution:
        start_time = time.perf_counter()
        
        model = cp_model.CpModel()
        
        # 1. Variables de décision
        # Pour chaque cycle possible, on crée une variable booléenne (0 ou 1)
        # selection_vars[i] == 1 signifie que le cycle i est choisi pour la transplantation
        selection_vars = [model.NewBoolVar(f'cycle_{i}') for i in range(len(self.cycles))]
            
        # 2. Contraintes d'unicité (Disjoint Sets)
        # Un patient ne peut être présent que dans UN SEUL cycle sélectionné.
        node_to_vars = {}
        for i, cycle in enumerate(self.cycles):
            for node in cycle:
                if node not in node_to_vars:
                    node_to_vars[node] = []
                node_to_vars[node].append(selection_vars[i])
        
        for node, vars_list in node_to_vars.items():
            # Somme des sélections pour ce nœud <= 1
            model.Add(sum(vars_list) <= 1)
            
        # 3. Objectif : Maximiser le nombre de transplantations
        # On peut pondérer ici par len(cycle) ou par un score d'urgence
        total_transplants_expr = sum(selection_vars[i] * len(self.cycles[i]) 
                                    for i in range(len(self.cycles)))
        
        model.Maximize(total_transplants_expr)
        
        # 4. Résolution
        solver = cp_model.CpSolver()
        # Optionnel : Limiter le temps de calcul si le graphe est énorme
        # solver.parameters.max_time_in_seconds = 60.0 
        
        status = solver.Solve(model)
        
        # 5. Construction de la solution
        selected_cycles = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for i, var in enumerate(selection_vars):
                if solver.Value(var):
                    selected_cycles.append(self.cycles[i])
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Calcul des stats finales
        total_tx = sum(len(c) for c in selected_cycles)
        
        return KEPSolution(
            cycles=selected_cycles,
            chains=[],  # empty, no chains in this model
            total_transplants=total_tx,
            total_weight=float(total_tx),
            solve_time_ms=duration_ms,
            solver_name="CP-SAT"
        )