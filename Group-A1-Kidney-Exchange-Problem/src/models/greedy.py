import time
from typing import List

from models.base import BaseSolver, KEPSolution


class GreedySolver(BaseSolver):
    """Heuristique gloutonne pour le Kidney Exchange Problem."""

    def __init__(self, kep_graph):
        super().__init__(kep_graph)

    def solve(self) -> KEPSolution:
        start_time = time.time()

        G = self.graph.graph

        # Score des cycles
        scored_cycles = []
        for cycle in self.cycles:
            weight = self._cycle_weight(cycle, G)
            scored_cycles.append((cycle, weight))

        # Trier par poids décroissant
        scored_cycles.sort(key=lambda x: x[1], reverse=True)

        # Sélection gloutonne de cycles disjoints
        selected_cycles: List[List[int]] = []
        used_nodes = set()

        for cycle, weight in scored_cycles:
            if any(node in used_nodes for node in cycle):
                continue

            selected_cycles.append(cycle)
            used_nodes.update(cycle)

        # Chaînes altruistes (simple greedy DFS)
        chains = self._build_greedy_chains(used_nodes)

        # Calcul des métriques
        total_transplants = sum(len(c) for c in selected_cycles) + sum(len(ch) for ch in chains)
        total_weight = sum(self._cycle_weight(c, G) for c in selected_cycles) \
                     + sum(self._chain_weight(ch, G) for ch in chains)

        solve_time_ms = (time.time() - start_time) * 1000

        return KEPSolution(
            cycles=selected_cycles,
            chains=chains,
            total_transplants=total_transplants,
            total_weight=total_weight,
            solve_time_ms=solve_time_ms,
            solver_name="Greedy"
        )

    def _cycle_weight(self, cycle, G):
        weight = 0.0
        for i in range(len(cycle)):
            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]
            weight += G[u][v].get("weight", 1.0)
        return weight

    def _chain_weight(self, chain, G):
        weight = 0.0
        for i in range(len(chain) - 1):
            u, v = chain[i], chain[i + 1]
            weight += G[u][v].get("weight", 1.0)
        return weight

    def _build_greedy_chains(self, used_nodes):
        """
        Construit des chaînes à partir des donneurs altruistes.
        Approche simple : DFS greedy en maximisant le poids local.
        """
        G = self.graph.graph
        chains = []

        # Identifier les nœuds altruistes
        altruists = [
            pair.id for pair in self.graph.pairs
            if getattr(pair, "is_altruistic", False)
        ]

        for start in altruists:
            if start in used_nodes:
                continue

            chain = [start]
            current = start

            while True:
                # voisins possibles non utilisés
                candidates = [
                    j for j in G.successors(current)
                    if j not in used_nodes and j not in chain
                ]

                if not candidates:
                    break

                # choisir le meilleur successeur (greedy)
                best_next = max(
                    candidates,
                    key=lambda j: G[current][j].get("weight", 1.0)
                )

                chain.append(best_next)
                used_nodes.add(best_next)
                current = best_next

            if len(chain) > 1:
                used_nodes.update(chain)
                chains.append(chain)

        return chains