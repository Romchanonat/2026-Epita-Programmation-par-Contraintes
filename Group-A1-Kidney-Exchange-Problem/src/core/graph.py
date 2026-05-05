from dataclasses import dataclass, field
from typing import Optional
import networkx as nx

@dataclass
class Donor:
    id: int
    blood_type: str
    hla_antigens: list[str]

@dataclass
class Patient:
    id: int
    blood_type: str
    pra: float
    hla_antibodies: list[str]
    time_on_dialysis: int

@dataclass
class Pair:
    """Une paire patient-donneur incompatible."""
    id: int
    patient: Patient
    donor: Donor
    is_altruistic: bool = False  # NDD : donneur sans patient

class KEPGraph:
    def __init__(self, max_cycle_size: int = 3):
        self.pairs: list[Pair] = []
        self.graph = nx.DiGraph()
        self.max_cycle_size = max_cycle_size

    def add_pair(self, pair: Pair):
        self.pairs.append(pair)
        self.graph.add_node(pair.id, pair=pair)

    def build_compatibility_arcs(self, compatibility_checker):
        """Construit les arcs selon les règles de compatibilité."""
        for i in self.pairs:
            for j in self.pairs:
                if i.id == j.id:
                    continue
                weight = compatibility_checker.check(i.donor, j.patient)
                if weight > 0:
                    self.graph.add_edge(i.id, j.id, weight=weight)

    def get_valid_cycles(self) -> list[list[int]]:
        """Énumère tous les cycles simples de taille <= max_cycle_size."""
        cycles = []
        for cycle in nx.simple_cycles(self.graph, length_bound=self.max_cycle_size):
            if 2 <= len(cycle) <= self.max_cycle_size:
                cycles.append(cycle)
        return cycles
    
    def get_valid_chains(self) -> list[list[int]]:
        """Énumère toutes les chaînes possibles à partir des NDD."""
        chains = []
        # 1. Identifier tous les altruistes (NDD)
        altruist_nodes = [
            n for n, data in self.graph.nodes(data=True) 
            if data['pair'].is_altruistic
        ]
        
        # 2. Identifier tous les autres nœuds (cibles potentielles)
        all_nodes = set(self.graph.nodes)

        for source in altruist_nodes:
            # On cherche les chemins vers n'importe quel autre nœud
            targets = all_nodes - {source}
            # On utilise all_simple_paths avec une liste de targets
            paths = nx.all_simple_paths(
                self.graph, 
                source=source, 
                target=targets, 
                cutoff=self.max_cycle_size
            )
            chains.extend(paths)
            
        return chains