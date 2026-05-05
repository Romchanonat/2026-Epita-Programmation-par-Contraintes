"""
Test du solveur PLNE pour le KEP.
Lancer depuis la racine du projet : python test_plne.py
"""
import sys
sys.path.insert(0, 'src')

from core.graph import KEPGraph, Pair, Patient, Donor
from core.compatibility import CompatibilityChecker
from data.generator import generate_instance
from models.PLNE import PLNESolver


def build_kep(n_pairs: int = 12, seed: int = 7, add_ndd: bool = True) -> KEPGraph:
    """Construit un KEPGraph à partir de paires générées aléatoirement."""
    raw = generate_instance(n_pairs, seed=seed)
    kep = KEPGraph(max_cycle_size=3)

    for r in raw:
        donor = Donor(
            id=r['id'],
            blood_type=r['donor']['blood_type'],
            hla_antigens=r['donor']['hla'],
        )
        patient = Patient(
            id=r['id'],
            blood_type=r['patient']['blood_type'],
            pra=r['patient']['pra'],
            hla_antibodies=r['patient']['antibodies'],
            time_on_dialysis=r['patient']['dialysis_months'],
        )
        kep.add_pair(Pair(id=r['id'], patient=patient, donor=donor))

    # Construire les arcs entre paires normales
    checker = CompatibilityChecker()
    kep.build_compatibility_arcs(checker)

    # Ajouter un donneur altruiste (NDD) si demandé
    if add_ndd:
        ndd_donor = Donor(id=99, blood_type='O', hla_antigens=[])
        ndd_pair = Pair(id=99, patient=None, donor=ndd_donor, is_altruistic=True)
        kep.pairs.append(ndd_pair)
        kep.graph.add_node(99, pair=ndd_pair)
        for pair in kep.pairs:
            if pair.is_altruistic:
                continue
            w = checker.check(ndd_donor, pair.patient)
            if w > 0:
                kep.graph.add_edge(99, pair.id, weight=w)

    return kep


def test_basic():
    """Le solveur tourne sans erreur et retourne une solution cohérente."""
    print("=== Test basique ===")
    kep = build_kep(n_pairs=12, seed=7)
    solver = PLNESolver(kep)
    sol = solver.solve()
    sol.summary()

    assert sol.n_transplants >= 0
    assert sol.objective_value >= 0
    print("✓ Solution valide\n")


def test_no_double_assignment():
    """Aucune paire n'apparaît dans deux cycles/chaînes à la fois."""
    print("=== Test : pas de double affectation ===")
    kep = build_kep(n_pairs=20, seed=42)
    solver = PLNESolver(kep)
    sol = solver.solve()

    seen = set()
    for cycle in sol.cycles:
        for node in cycle:
            assert node not in seen, f"Nœud {node} affecté deux fois !"
            seen.add(node)
    for chain in sol.chains:
        for node in chain[1:]:   # on ignore le NDD (index 0)
            assert node not in seen, f"Nœud {node} affecté deux fois !"
            seen.add(node)

    print(f"✓ Aucun doublon sur {len(seen)} nœuds assignés\n")


def test_empty_graph():
    """Le solveur gère proprement un graphe sans arcs (aucun échange possible)."""
    print("=== Test : graphe vide ===")
    kep = KEPGraph(max_cycle_size=3)
    donor   = Donor(id=0, blood_type='AB', hla_antigens=['A1'])
    patient = Patient(id=0, blood_type='O', pra=0.9,
                      hla_antibodies=['A1'], time_on_dialysis=12)
    kep.add_pair(Pair(id=0, patient=patient, donor=donor))
    # Pas d'arcs → pas de cycles

    solver = PLNESolver(kep)
    sol = solver.solve()

    assert sol.n_transplants == 0
    assert sol.cycles == []
    print("✓ Graphe vide géré correctement\n")


if __name__ == "__main__":
    test_basic()
    test_no_double_assignment()
    test_empty_graph()
    print("Tous les tests sont passés ✓")