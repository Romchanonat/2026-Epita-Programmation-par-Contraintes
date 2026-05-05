import time
from ortools.sat.python import cp_model
from .base import KidneyExchangeSolver, SolverResult

class CPSatSolver(KidneyExchangeSolver):
    """
    Solveur CP-SAT capable de gérer uniquement les cycles 
    ou les cycles + chaînes altruistes.
    """

    def solve(self, time_limit: float = 60.0) -> SolverResult:
        """Méthode principale de l'interface."""
        if self.altruist_enabled:
            return self._solve_with_altruists(time_limit)
        else:
            return self._solve_cycles_only(time_limit)

    def _solve_cycles_only(self, time_limit: float) -> SolverResult:
        """Logique standard sans donneurs altruistes."""
        start_time = self._start_timer()
        all_cycles = self.graph.get_valid_cycles()
        
        if not all_cycles:
            return self._no_solution("INFEASIBLE", self._elapsed(start_time))

        model = cp_model.CpModel()
        cycle_vars = [model.NewBoolVar(f'cycle_{i}') for i in range(len(all_cycles))]
        
        # Contraintes d'unicité
        node_to_vars = {}
        for i, cycle in enumerate(all_cycles):
            for node in cycle:
                node_to_vars.setdefault(node, []).append(cycle_vars[i])
        
        for vars_list in node_to_vars.values():
            model.Add(sum(vars_list) <= 1)
            
        # Objectif
        model.Maximize(sum(cycle_vars[i] * len(all_cycles[i]) for i in range(len(all_cycles))))
        
        # Résolution
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)
        
        return self._wrap_results(solver, status, all_cycles, [], start_time)

    def _solve_with_altruists(self, time_limit: float) -> SolverResult:
        """Logique étendue incluant les chaînes."""
        start_time = self._start_timer()
        
        all_cycles = self.graph.get_valid_cycles()
        # On peut autoriser les chaînes à être un peu plus longues que les cycles
        all_chains = self.graph.get_valid_chains()
        
        model = cp_model.CpModel()
        cycle_vars = [model.NewBoolVar(f'cycle_{i}') for i in range(len(all_cycles))]
        chain_vars = [model.NewBoolVar(f'chain_{j}') for j in range(len(all_chains))]
        
        node_to_vars = {}
        # Patients dans les cycles
        for i, cycle in enumerate(all_cycles):
            for node in cycle:
                node_to_vars.setdefault(node, []).append(cycle_vars[i])
        # Patients et altruistes dans les chaînes
        for j, chain in enumerate(all_chains):
            for node in chain:
                node_to_vars.setdefault(node, []).append(chain_vars[j])
        
        for vars_list in node_to_vars.values():
            model.Add(sum(vars_list) <= 1)
            
        # Objectif : cycles (taille k) + chaînes (taille k-1 transplantations)
        obj = sum(cycle_vars[i] * len(all_cycles[i]) for i in range(len(all_cycles)))
        obj += sum(chain_vars[j] * (len(all_chains[j]) - 1) for j in range(len(all_chains)))
        model.Maximize(obj)
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)
        
        # Extraction
        sel_cycles = [all_cycles[i] for i, v in enumerate(cycle_vars) if solver.Value(v)] if status in (3, 4) else []
        sel_chains = [all_chains[j] for j, v in enumerate(chain_vars) if solver.Value(v)] if status in (3, 4) else []
        
        return self._wrap_results(solver, status, sel_cycles, sel_chains, start_time)

    def _wrap_results(self, solver, status, cycles, chains, start_time) -> SolverResult:
        """Utilitaire pour formater la sortie OR-Tools vers SolverResult."""
        ort_map = {cp_model.OPTIMAL: "OPTIMAL", cp_model.FEASIBLE: "FEASIBLE", 
                   cp_model.INFEASIBLE: "INFEASIBLE", cp_model.UNKNOWN: "TIMEOUT"}
        
        res_status = ort_map.get(status, "ERROR")
        if res_status in ("INFEASIBLE", "ERROR"):
            return self._no_solution(res_status, self._elapsed(start_time))
            
        return self._make_result(
            status=res_status,
            cycles=cycles,
            chains=chains,
            objective_value=solver.ObjectiveValue(),
            wall_time=self._elapsed(start_time)
        )