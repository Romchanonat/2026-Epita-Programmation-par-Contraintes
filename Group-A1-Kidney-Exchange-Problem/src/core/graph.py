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
        self.max_chain_length = max_cycle_size

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
        for cycle in nx.simple_cycles(self.graph):
            if 2 <= len(cycle) <= self.max_cycle_size:
                cycles.append(cycle)
        return cycles
    
    def get_valid_chains(self) -> list[list[int]]:
        """
        Énumère les chaînes altruistes de longueur dans [1, max_chain_length].

        Une chaîne commence par un NDD et suit des arcs de compatibilité
        sans repasser par un nœud déjà visité.

        Returns:
            Liste de chaînes, chaque chaîne = [ndd_id, pair1, pair2, ...]
        """
        if self.max_chain_length == 0:
            return []

        ndd_nodes = [p.id for p in self.pairs if p.is_altruistic]
        chains = []

        for ndd_id in ndd_nodes:
            self._dfs_chains(
                current=ndd_id,
                path=[ndd_id],
                visited={ndd_id},
                chains=chains,
            )
        return chains

    def _dfs_chains(
        self,
        current: int,
        path: list[int],
        visited: set[int],
        chains: list[list[int]],
    ) -> None:
        """DFS pour construire les chaînes depuis un NDD."""
        # Enregistrer la chaîne courante si elle contient au moins 1 paire régulière
        if len(path) >= 2:
            chains.append(list(path))

        # Arrêter si on atteint la longueur max
        if len(path) - 1 >= self.max_chain_length:
            return

        for neighbor in self.graph.successors(current):
            if neighbor not in visited and not self._pair_index[neighbor].is_altruistic:
                visited.add(neighbor)
                path.append(neighbor)
                self._dfs_chains(neighbor, path, visited, chains)
                path.pop()
                visited.discard(neighbor)

    def get_pair(self, pair_id: int) -> Pair:
        """Retourne la paire associée à un identifiant."""
        return self._pair_index[pair_id]

    def arc_weight(self, i: int, j: int) -> float:
        """Retourne le poids de l'arc (i → j), 0 si inexistant."""
        return self.graph[i][j].get("weight", 0.0) if self.graph.has_edge(i, j) else 0.0

    def cycle_weight(self, cycle: list[int]) -> float:
        """Retourne le poids total d'un cycle (somme des arcs)."""
        return sum(
            self.arc_weight(cycle[k], cycle[(k + 1) % len(cycle)])
            for k in range(len(cycle))
        )

    def chain_weight(self, chain: list[int]) -> float:
        """Retourne le poids total d'une chaîne (somme des arcs)."""
        return sum(
            self.arc_weight(chain[k], chain[k + 1])
            for k in range(len(chain) - 1)
        )
