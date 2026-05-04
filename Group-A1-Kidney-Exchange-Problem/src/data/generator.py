import random
import json
BLOOD_TYPE_COMPATIBILITY = {
    'O-':  ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+':  ['O+', 'A+', 'B+', 'AB+'],
    'A-':  ['A-', 'A+', 'AB-', 'AB+'],
    'A+':  ['A+', 'AB+'],
    'B-':  ['B-', 'B+', 'AB-', 'AB+'],
    'B+':  ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+'],
}
BLOOD_TYPES = ['O', 'A', 'B', 'AB']
BLOOD_FREQ = [0.44, 0.42, 0.10, 0.04]  # fréquences réelles
HLA_POOL = [f'{l}{n}' for l in ['A','B','DR'] for n in range(1, 20)]

def generate_instance(n_pairs, seed=42, pra_high_ratio=0.15):
    """
    Génère n_pairs paires patient-donneur incompatibles.
    pra_high_ratio : proportion de patients très sensibilisés (PRA > 0.8)
    """
    random.seed(seed)
    pairs = []

    for i in range(n_pairs):
        # Générer une paire garantie incompatible
        while True:
            donor_bt   = random.choices(BLOOD_TYPES, BLOOD_FREQ)[0]
            patient_bt = random.choices(BLOOD_TYPES, BLOOD_FREQ)[0]
            donor_hla  = random.sample(HLA_POOL, 6)

            # PRA élevé pour une fraction des patients
            if random.random() < pra_high_ratio:
                pra = random.uniform(0.8, 1.0)
                n_antibodies = random.randint(8, 15)
            else:
                pra = random.uniform(0.0, 0.5)
                n_antibodies = random.randint(0, 4)

            patient_antibodies = random.sample(HLA_POOL, n_antibodies)

            # Vérifier l'incompatibilité
            blood_incompatible = (
                patient_bt not in BLOOD_TYPE_COMPATIBILITY[donor_bt]
            )
            hla_incompatible = any(
                ab in donor_hla for ab in patient_antibodies
            )

            if blood_incompatible or hla_incompatible:
                break  # Paire valide (incompatible)

        pairs.append({
            'id': i,
            'donor': {'blood_type': donor_bt, 'hla': donor_hla},
            'patient': {
                'blood_type': patient_bt,
                'pra': round(pra, 2),
                'antibodies': patient_antibodies,
                'dialysis_months': random.randint(1, 120)
            }
        })

    return pairs