# Solver result

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Optional

from core.graph import KEPGraph

# Si KEPGraph est défini dans un autre fichier, n'oublie pas de l'importer :
# from your_module import KEPGraph

@dataclass
class KEPSolution:
    cycles: list[list[int]]         # cycles sélectionnés
    chains: list[list[int]]         # chaînes altruistes sélectionnées
    total_transplants: int          # nombre total de transplantations
    total_weight: float             # poids total (urgence + PRA)
    solve_time_ms: float            # temps de résolution en ms
    solver_name: str                # "CP-SAT" | "PLNE" | "Greedy"

    def summary(self):
        print(f"\n{'='*40}")
        print(f"Solveur        : {self.solver_name}")
        print(f"Transplants    : {self.total_transplants}")
        print(f"Poids total    : {self.total_weight:.4f}")
        print(f"Temps          : {self.solve_time_ms:.1f} ms")
        print(f"Cycles         : {self.cycles}")
        print(f"Chaînes        : {self.chains}")
        print(f"{'='*40}\n")

# ─────────────────────────────────────────
# INTERFACE COMMUNE DES SOLVEURS
# ─────────────────────────────────────────

class BaseSolver(ABC):
    """Interface que chaque solveur doit implémenter."""

    def __init__(self, kep_graph: KEPGraph):
        self.graph    = kep_graph
        self.cycles   = kep_graph.get_valid_cycles()

    @abstractmethod
    def solve(self) -> KEPSolution:
        """Lance la résolution et retourne une KEPSolution."""
        ...