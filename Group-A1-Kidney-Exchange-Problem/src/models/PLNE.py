import itertools
from dataclasses import dataclass, field
from typing import Optional
import pulp
import networkx as nx
import time
 
from models.base import BaseSolver, KEPSolution
from core.graph import KEPGraph

class PLNESolver(BaseSolver):
    """
    Solver PLNE for Kidney Exchange Problem
    """

    def __init__(self, kep_graph: KEPGraph, max_chain_length: int = 3):

        super().__init__(kep_graph)
        self.max_chain_length = max_chain_length
        self.chains = self._enumerate_chains()

    def _enumerate_chains(self) -> list[list[int]]:
        """
        Enumerate all the simple chains starting from a NDD (altruistic donnor)
        """

        chains = []
        ndd_ids = [p.id for p in self.graph.pairs if p.is_altruistic]

        for ndd in ndd_ids:
            stack = [[ndd]]
            while stack:
                path = stack.pop()
                last = path[-1]
                if len(path >= 2):
                    chains.append(path[:])
                if len(path) <= self.max_chain_length:
                    for _, neighboor in self.graph.graph.out_edges(last):
                        if neighboor not in path:
                            stack.append(path + [neighboor])

        return chains
    

    def _cycle_weigths(self, cycle: list[int]) -> float:
        """
        Sums the weights of the edges of the cycle
        """

        total = 0.0
        n = len(cycle)
        for i in range(n):
            u = cycle[i]
            v = cycle[(i + 1) % n]
            data = self.graph.graph.get_edge_data(u, v)
            total += data["weight"] if data else 0.0
        
        return total
    

    def _chain_weight(self, chain: list[int]) -> float:
        """
        sums the weights of the edges of the chain
        """
        
        total = 0.0
        for i in range(len(chain) - 1):
            u, v = chain[i], chain[i + 1]
            data = self.graph.graph.get_edge_data(u, v)
            total += data["weight"] if data else 0.0
        
        return total
    

    def _cycle_transplants(self, cycle: list[int]) -> int:
        """
        returns the number of transplants of the cyle
        """

        return len(cycle)
    

    def _chain_transplants(self, chain: list[int]) -> int:
        """
        returns the number of transplants of the cyle
        """

        return len(chain) - 1


    def solve(self) -> KEPSolution:
        t0 = time.time()

        prob = pulp.LpProblem("KEP_PLNE", pulp.LpMaximize)

        x = {
            i : pulp.LpVariable(f"x_c{i}", cat="Binary")
            for i in range(len(self.cycles))
        }

        y = {
            j: pulp.LpVariable(f"y_ch{j}", cat="Binary")
            for j in range(len(self.chains))
        }

        prob += pulp.lpSum(
            self._cycle_weight(self.cycles[i]) * x[i]
            for i in range(len(self.cycles))
        ) + pulp.lpSum(
            self._chain_weight(self.chains[j]) * y[j]
            for j in range(len(self.chains))
        )

        non_ndd_ids = [p.id for p in self.graph.pairs if not p.is_altruistic]

        for node in non_ndd_ids:
            cycle_vars = [
                x[i]
                for i, c in enumerate(self.cycles)
                if node in c
            ]

            chain_vars = [
                y[j]
                for j, ch in enumerate(self.chains)
                if node in ch[1:]
            ]

            if cycle_vars or chain_vars:
                prob += pulp.lpSum(cycle_vars + chain_vars) <= 1, f"cover_{node}"

        ndd_ids = [p.id for p in self.graph.pairs if p.is_altruistic]
        for ndd in ndd_ids:
                
            chain_vars = [y[j] for j, ch in enumerate(self.chains) if ch[0] == ndd]
            if chain_vars:
                prob += pulp.lpSum(chain_vars) <= 1, f"ndd_{ndd}"

        solver = pulp.PULP_CBC_CMD(msg=0)
        prob.solve(solver)

        solve_time_ms = (time.time() - t0) * 1000

        selected_cycles = [
            self.cycles[i]
            for i in range(len(self.cycles))
            if pulp.value(x[i]) is not None and pulp.value(x[i]) > 0.5
        ]

        selected_chains = [
            self.chains[j]
            for j in range(len(self.chains))
            if pulp.value(y[j]) is not None and pulp.value(y[j]) > 0.5
        ]

        total_weight = sum(self._cycle_weight(c) for c in selected_chains) + \
                        (self._chain_weight(ch) for ch in selected_chains)
        
        total_transplants = sum(self._cycle_transplants(c) for c in selected_chains) + \
                            sum(self._chain_transplants(ch) for ch in selected_chains)
        

        return KEPSolution(
            cycles=selected_cycles,
            chains=selected_chains,
            total_transplants=total_transplants,
            total_weight=total_weight,
            solve_time_ms=solve_time_ms,
            solver_name="PLNE",
        )