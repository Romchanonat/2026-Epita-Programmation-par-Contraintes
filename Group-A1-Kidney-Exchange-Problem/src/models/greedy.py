from __future__ import annotations

from src.core.graph import KEPGraph
from src.models.base import KidneyExchangeSolver, SolverResult


class GreedySolver(KidneyExchangeSolver):
    """
    Heuristique gloutonne pour le KEP.

    Paramètres :
        graph           : Graphe KEP.
        max_cycle_size  : Taille max des cycles.
        strategy        : Critère de sélection 'weight', 'size' ou 'density'.
        use_chains      : Inclure les chaînes altruistes.
    """

    STRATEGIES = ("weight", "size", "density")

    def __init__(
        self,
        graph: KEPGraph,
        max_cycle_size: int = 3,
        strategy: str = "weight",
        use_chains: bool = True,
    ):
        super().__init__(graph, max_cycle_size)
        if strategy not in self.STRATEGIES:
            raise ValueError(f"strategy doit être parmi {self.STRATEGIES}.")
        self.strategy = strategy
        self.use_chains = use_chains

    @property
    def name(self) -> str:
        return f"Greedy ({self.strategy})"

    def solve(self, time_limit: float = 60.0) -> SolverResult:
        """
        Lance l'heuristique gloutonne.

        Note : time_limit n'est pas utilisé (l'algo est quasi-instantané),
        mais l'argument est conservé pour respecter l'interface commune.
        """
        t0 = self._start_timer()
        G = self.graph

        # Énumérer toutes les options (cycles + chaînes)
        candidates = self._build_candidates()

        if not candidates:
            return self._no_solution("INFEASIBLE", self._elapsed(t0))

        # Trier selon la stratégie choisie (ordre décroissant)
        candidates.sort(key=self._priority_key, reverse=True)

        # Sélection gloutonne
        selected_cycles: list[list[int]] = []
        selected_chains: list[list[int]] = []
        used_pairs: set[int] = set()
        total_weight = 0.0

        for candidate in candidates:
            kind = candidate["kind"]
            nodes = candidate["nodes"]

            # Vérifier la disjonction
            if any(n in used_pairs for n in nodes):
                continue

            # Accepter ce cycle/chaîne
            used_pairs.update(nodes)
            total_weight += candidate["weight"]

            if kind == "cycle":
                selected_cycles.append(candidate["path"])
            else:
                selected_chains.append(candidate["path"])

        elapsed = self._elapsed(t0)
        return self._make_result(
            status="FEASIBLE",
            cycles=selected_cycles,
            chains=selected_chains,
            objective_value=total_weight,
            wall_time=elapsed,
            strategy=self.strategy,
            n_candidates_evaluated=len(candidates),
        )

    # Construction des candidats

    def _build_candidates(self) -> list[dict]:
        """
        Construit la liste de tous les cycles et chaînes valides
        avec leurs métadonnées de priorité.
        """
        G = self.graph
        ndd_ids = {p.id for p in G.pairs if p.is_altruistic}
        candidates = []

        # Cycles
        for cycle in G.get_valid_cycles():
            w = G.cycle_weight(cycle)
            candidates.append({
                "kind": "cycle",
                "path": cycle,
                "nodes": set(cycle),
                "weight": w,
                "size": len(cycle),
            })

        # Chaînes (si activées)
        if self.use_chains:
            for chain in G.get_valid_chains():
                w = G.chain_weight(chain)
                # Les nœuds "occupés" d'une chaîne sont les paires régulières
                # (pas le NDD lui-même — mais on le bloque quand même)
                nodes_in_chain = set(chain)   # inclut le NDD
                patients_in_chain = set(chain[1:])   # paires régulières seulement
                candidates.append({
                    "kind": "chain",
                    "path": chain,
                    "nodes": nodes_in_chain,
                    "weight": w,
                    "size": len(chain) - 1,   # transplants réalisés (hors NDD)
                })

        return candidates

    def _priority_key(self, candidate: dict) -> float:
        """Retourne la clé de priorité selon la stratégie."""
        if self.strategy == "weight":
            return candidate["weight"]
        elif self.strategy == "size":
            # Tiebreak par poids pour les cycles de même taille
            return candidate["size"] + candidate["weight"] * 1e-6
        elif self.strategy == "density":
            size = max(1, candidate["size"])
            return candidate["weight"] / size
        return 0.0
