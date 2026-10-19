"""Kennzahlen, Verdikt-Logik und Sweeps der k-Core-Demo. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung."""

from dataclasses import dataclass
from statistics import median

import kco_algorithm as A
import kco_constants as C
from kco_scenario import Instance, make_instance


def de(x, digits=1) -> str:
    """Dezimalzahl mit Komma (deutsche Texte)."""
    return f"{x:.{digits}f}".replace(".", ",")


@dataclass(frozen=True)
class Settings:
    netztyp: str = C.T_RANDOM
    n: int = C.DEFAULT_N
    c: int = C.DEFAULT_C
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    bucket: A.BucketResult
    naive: A.NaiveResult
    shells: dict           # Kernzahl -> Zahl der Knoten
    degeneracy: int
    omega: object          # Cliquenzahl oder None (Aufruflimit)
    rho: object            # Rangkorrelation Grad-Kernzahl oder None (eine Seite konstant)
    share_equal: float     # Anteil der Knoten mit Kernzahl == Grad
    valid: bool            # Kernzahlen gültig und beide Verfahren stimmen überein

    @property
    def core(self):
        return self.bucket.core


def share_core_equals_degree(core, deg) -> float:
    return sum(1 for c, d in zip(core, deg) if c == d) / len(core) if core else 0.0


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.netztyp, settings.n, settings.c, settings.seed)
    A.check_graph(inst.adj)
    bucket = A.core_numbers_bucket(inst.adj)
    naive = A.core_numbers_naive(inst.adj)
    deg = A.degrees(inst.adj)
    valid = bucket.core == naive.core and A.validate_core_numbers(inst.adj, bucket.core)
    return Analysis(inst, bucket, naive, A.shell_sizes(bucket.core), A.degeneracy(bucket.core), A.max_clique_size(inst.adj),
                    A.rank_correlation(deg, list(bucket.core)), share_core_equals_degree(bucket.core, deg), valid)


def naive_factor(a: Analysis) -> float:
    """Schritte des naiven Schälens geteilt durch die des Bucket-Algorithmus (beide zählen Elementarschritte; 0 Schritte: Faktor 1)."""
    return a.naive.steps / a.bucket.steps if a.bucket.steps else 1.0


def top_core_count(a: Analysis) -> int:
    """Zahl der Knoten im höchsten Kern (Schale der höchsten Kernzahl)."""
    return a.shells[a.degeneracy] if a.shells else 0


# --- E1: Schritte ----------------------------------------------------------------------------------------------------------------------------------

STEP_NETS = (
    (C.T_RANDOM, C.DEFAULT_C),
    (C.T_BA, C.DEFAULT_C),
    (C.T_GRID, 4),
    (C.T_PATH, C.DEFAULT_C),
)


def sweep_steps(sizes=C.STEP_SIZES, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Bucket gegen naives Schälen über die Netzgröße: Median der Schritte und des Faktors über die festen Instanzen SWEEP_SEEDS
    (Gitter und Pfad sind deterministisch)."""
    rows = []
    for typ, c in STEP_NETS:
        used = seeds if typ in (C.T_RANDOM, C.T_BA) else seeds[:1]
        for n in sizes:
            results = [analyse_steps_only(typ, n, c, s) for s in used]
            rows.append({
                "netztyp": typ, "n": n,
                "bucket": median(r[0] for r in results), "naive": median(r[1] for r in results),
                "factor": median(r[1] / r[0] for r in results), "passes": median(r[2] for r in results),
            })
    return rows


def analyse_steps_only(typ, n, c, seed):
    """(Bucket-Schritte, naive Schritte, naive Durchläufe) ohne Cliquenzahl und Korrelationen (die Schritt-Sweeps brauchen nur die Zähler)."""
    inst = make_instance(typ, n, c, seed, layout=False)
    b = A.core_numbers_bucket(inst.adj)
    nv = A.core_numbers_naive(inst.adj)
    assert b.core == nv.core
    return b.steps, nv.steps, nv.passes


def verdict_steps(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E1: typischer Faktor auf Zufall, skalenfrei und Gitter gegen den Faktor im ungünstigen Pfad, jeweils bei der größten Größe."""
    n_max = max(r["n"] for r in rows)
    last = {r["netztyp"]: r for r in rows if r["n"] == n_max}
    typical = [last[t]["factor"] for t in (C.T_RANDOM, C.T_BA, C.T_GRID) if t in last]
    path = last.get(C.T_PATH)
    if path is None or not typical:
        return "info", "Für dieses Verdikt fehlen Netztypen."
    return "info", (
        f"Bei n = {n_max} braucht das naive Schälen auf Zufalls-, skalenfreien und Gitter-Netzen das {de(min(typical))}- bis {de(max(typical))}-fache der Schritte "
        f"des Bucket-Algorithmus. Im ungünstig nummerierten Pfad ist es das **{path['factor']:.0f}-fache** ({path['passes']:.0f} Durchläufe): "
        "der Faktor wächst dort mit n, weil jeder Durchlauf nur die zwei Enden entfernt."
    )


# --- E2: Kernzahl gegen Grad über die Netztypen --------------------------------------------------------------------------------------------------


def sweep_types(settings: Settings) -> list[dict]:
    """Eine Zeile je erzeugtem Netztyp bei gleichem n, c und Seed: Schalen, höchster Kern, Anteil darin, Rangkorrelation Grad-Kernzahl, Cliquenschranke."""
    rows = []
    for typ in C.GENERATED_TYPES:
        a = analyse(Settings(typ, settings.n, settings.c, settings.seed))
        rows.append({
            "netztyp": typ, "n": a.inst.n, "m": a.inst.m, "schalen": len(a.shells), "degeneracy": a.degeneracy,
            "im_hoechsten_kern": top_core_count(a), "rho": a.rho, "gleich": a.share_equal, "omega": a.omega,
            "luecke": None if a.omega is None else a.degeneracy + 1 - a.omega,
        })
    return rows


def verdict_types(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E2: auf wie vielen Netztypen ist die Kernzahl konstant (eine Schale, keine Information)?"""
    constant = [r["netztyp"] for r in rows if r["schalen"] == 1]
    if not constant:
        return "success", f"In allen {len(rows)} Netztypen gibt es mehrere Schalen: die Kernzahl unterscheidet Knoten."
    return "warning", (
        f"In **{len(constant)} von {len(rows)}** Netztypen liegen alle Knoten in einer einzigen Schale ({', '.join(constant)}): "
        "dort ist die Kernzahl konstant und trägt keine Information."
    )


# --- Hauptverdikt (Kernfrage) ----------------------------------------------------------------------------------------------------------------------


def verdict_information(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage: trägt die Kernzahl in diesem Netz Information, die der Grad nicht schon hat?"""
    if len(a.shells) <= 1:
        k = next(iter(a.shells)) if a.shells else 0
        return "warning", f"Alle {a.inst.n} Knoten haben dieselbe Kernzahl {k}: die Kernzahl trägt hier **keine Information**, der Grad unterscheidet die Knoten, die Kernzahl nicht."
    if a.rho is None:
        return "info", "Die Grade sind alle gleich: die Kernzahl lässt sich nicht gegen den Grad vergleichen."
    if a.rho >= 0.95:
        return "info", (
            f"Kernzahl und Grad ordnen die Knoten fast gleich (Rangkorrelation {de(a.rho, 3)}; bei {100 * a.share_equal:.0f} % der Knoten ist die Kernzahl gleich dem Grad): "
            "die Kernzahl bringt hier kaum etwas Neues."
        )
    return "success", (
        f"Die Kernzahl ordnet die Knoten anders als der Grad (Rangkorrelation {de(a.rho, 3)}; nur bei {100 * a.share_equal:.0f} % der Knoten ist sie gleich dem Grad): "
        f"{len(a.shells)} Schalen, der höchste Kern ({a.degeneracy}-Kern) enthält {top_core_count(a)} von {a.inst.n} Knoten."
    )


# --- E3: Ausbreitung -----------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpreadExperiment:
    beta: float
    beta_c: object
    runs: int
    k: int
    mean_power: float
    reliability: object
    rho: dict          # Maß -> Rangkorrelation mit der Ausbreitungskraft (None: Maß konstant)
    top: dict          # Maß -> mittlere Ausbreitungskraft der besten 5 % nach diesem Maß (bewertet auf der Gegenhälfte)
    oracle: float      # beste Auswahl, auf einer Hälfte der Läufe gewählt und auf der anderen bewertet
    random: float      # Mittelwert aller Knoten (Zufallswahl), Gegenhälfte


def measures_of(adj, core) -> dict:
    return {"Grad": A.degrees(adj), "Kernzahl": list(core), "Betweenness": A.betweenness(adj), "PageRank": A.pagerank(adj), "Closeness": A.closeness(adj)}


def spread_experiment(settings: Settings, beta_factor: float, runs: int) -> SpreadExperiment | None:
    """Ausbreitungskraft jedes Knotens als Einzelstarter (SIR) gegen fünf Maße. None, wenn das Netz keine Kanten hat."""
    a = analyse(settings)
    adj = a.inst.adj
    beta_c = A.mean_field_threshold(adj, C.MU)
    if beta_c is None:
        return None
    beta = min(1.0, beta_factor * beta_c)
    res = A.sir_spread_power(adj, beta, C.MU, runs, C.SPREAD_SEED)
    n = a.inst.n
    k = max(5, round(C.TOP_FRACTION * n)) if n >= 5 else n
    k = min(k, n)
    meas = measures_of(adj, a.core)
    rho = {name: A.rank_correlation(vals, list(res.power)) for name, vals in meas.items()}
    top = {name: A.topk_expected(vals, res.half_b, k) for name, vals in meas.items()}
    return SpreadExperiment(beta, beta_c, res.runs, k, sum(res.power) / n, res.reliability, rho, top,
                            A.honest_oracle(res.half_a, res.half_b, k), sum(res.half_b) / n)


def verdict_spread(r: SpreadExperiment) -> tuple[str, str]:
    """Verdikt zu E3: wo steht die Kernzahl unter den fünf Maßen, und was erreichen die besten 5 % nach jedem Maß gegen Zufall und Messauswahl?"""
    defined = {m: v for m, v in r.rho.items() if v is not None}
    rel = "unbestimmt" if r.reliability is None else de(r.reliability, 2)
    best = max(defined, key=defined.get) if defined else None
    best_top = max(r.top, key=r.top.get)
    tail = (f"Zuverlässigkeit der Messung: {rel}. Zum Vergleich: Zufallswahl {de(r.random)}, Auswahl nach den Messläufen {de(r.oracle)} "
            "(selbst verrauscht, ein gutes Maß kann sie übertreffen).")
    if r.rho["Kernzahl"] is None:
        return "warning", (
            f"Die Kernzahl ist in diesem Netz konstant und sagt über die Ausbreitung **nichts**: ihre Auswahl entspricht der Zufallswahl ({de(r.top['Kernzahl'])}). "
            f"Beste Rangkorrelation: {best} ({de(defined[best], 2)}); die besten {r.k} Starter nach {best_top} erreichen im Mittel {de(r.top[best_top])} Knoten. " + tail
        )
    rank = sorted(defined, key=defined.get, reverse=True).index("Kernzahl") + 1
    kind = "success" if best == "Kernzahl" else "info"
    return kind, (
        f"Die Kernzahl hat die Rangkorrelation {de(r.rho['Kernzahl'], 2)} mit der Ausbreitungskraft (Platz {rank} von {len(defined)}; der Grad {de(r.rho['Grad'], 2)}, "
        f"am besten {best} mit {de(defined[best], 2)}). Die besten {r.k} Starter nach Kernzahl erreichen im Mittel {de(r.top['Kernzahl'])} Knoten, nach Grad {de(r.top['Grad'])}, "
        f"am besten {best_top} mit {de(r.top[best_top])}. " + tail
    )
