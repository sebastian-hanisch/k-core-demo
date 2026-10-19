"""Kern: k-Kern-Zerlegung (Bucket-Algorithmus und naives Schälen), Vergleichsmaße, SIR-Ausbreitung, Rangkorrelation und Top-k-Auswahl.

Alle Einheiten sind eigene Funktionen ohne versteckten Zustand; Netze sind einfache ungerichtete Graphen als Liste sortierter Nachbarlisten
(`adj[v]`, Knoten 0 bis n - 1, keine Schleifen, keine Mehrfachkanten). Zufall nur über `random.Random` mit übergebenem Seed.
"""

import math
import random
from collections import deque
from dataclasses import dataclass


# --- Prüfer ---------------------------------------------------------------------------------------------------------------------------------------


def check_graph(adj) -> None:
    """Unabhängiger Prüfer: Knoten 0 bis n - 1, symmetrisch, keine Schleifen, keine Mehrfachkanten, Nachbarlisten sortiert."""
    n = len(adj)
    for v, nb in enumerate(adj):
        if list(nb) != sorted(set(nb)):
            raise ValueError(f"Nachbarliste von {v} ist nicht sortiert oder hat Doppelte")
        for u in nb:
            if not 0 <= u < n or u == v:
                raise ValueError(f"Kante {v}-{u} ungültig")
            if v not in adj[u]:
                raise ValueError(f"Kante {v}-{u} nicht symmetrisch")


def validate_core_numbers(adj, core) -> bool:
    """Gültigkeit (nicht Maximalität): für jedes v hat v mindestens core[v] Nachbarn mit Kernzahl >= core[v], und core[v] <= Grad.
    Damit hat jede Menge {core >= k} den Mindestgrad k. Die Maximalität sichert der Vergleich der beiden unabhängigen Verfahren."""
    for v, nb in enumerate(adj):
        if core[v] > len(nb):
            return False
        if sum(1 for u in nb if core[u] >= core[v]) < core[v]:
            return False
    return True


# --- Bucket-Algorithmus (Batagelj und Zaveršnik) ----------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class BucketResult:
    core: tuple
    steps: int      # genau 2n + 2m: n für die Bins, n für die Positionen, 2m für die Kantenprüfungen
    order: tuple    # Entfernungsreihenfolge = Degeneracy-Ordnung


def core_numbers_bucket(adj) -> BucketResult:
    """Kernzahlen in O(n + m): Knoten nach Grad in Buckets sortiert, jeder Knoten wird einmal entfernt, jede Kante zweimal geprüft."""
    n = len(adj)
    if n == 0:
        return BucketResult((), 0, ())
    deg = [len(a) for a in adj]
    maxd = max(deg)
    steps = 0
    bins = [0] * (maxd + 2)
    for d in deg:
        bins[d] += 1
        steps += 1
    start = 0
    for d in range(maxd + 1):
        num = bins[d]
        bins[d] = start
        start += num
    pos = [0] * n
    vert = [0] * n
    for v in range(n):
        pos[v] = bins[deg[v]]
        vert[pos[v]] = v
        bins[deg[v]] += 1
        steps += 1
    for d in range(maxd, 0, -1):
        bins[d] = bins[d - 1]
    bins[0] = 0
    core = list(deg)
    for i in range(n):
        v = vert[i]
        for u in adj[v]:
            steps += 1
            if core[u] > core[v]:
                du = core[u]
                pu = pos[u]
                pw = bins[du]
                w = vert[pw]
                if u != w:
                    pos[u], pos[w] = pw, pu
                    vert[pu], vert[pw] = w, u
                bins[du] += 1
                core[u] -= 1
    return BucketResult(tuple(core), steps, tuple(vert))


# --- Naives Schälen (Definition) -------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PeelEvent:
    k: int            # aktuelle Schwelle: entfernt werden Knoten mit Restgrad < k
    durchlauf: int    # Nummer des Durchlaufs innerhalb dieser Schwelle (ab 1)
    entfernt: tuple   # in diesem Durchlauf entfernte Knoten, in der Reihenfolge ihrer Entfernung


@dataclass(frozen=True)
class NaiveResult:
    core: tuple
    steps: int        # Gradprüfungen (Summe der Restknotenzahlen je Durchlauf) plus 2m Gradabzüge
    passes: int
    log: tuple        # PeelEvent je Durchlauf


def core_numbers_naive(adj) -> NaiveResult:
    """Definition: für k = 1, 2, ...: wiederholt alle Knoten mit Restgrad < k entfernen, bis in einem Durchlauf nichts mehr fällt.
    Ein Knoten, der bei Schwelle k fällt, hat die Kernzahl k - 1. Jeder Durchlauf geht die Restknoten in aufsteigender Nummer durch."""
    n = len(adj)
    deg = [len(a) for a in adj]
    alive = set(range(n))
    core = [0] * n
    steps = 0
    passes = 0
    log = []
    k = 0
    while alive:
        k += 1
        durchlauf = 0
        changed = True
        while changed and alive:
            changed = False
            passes += 1
            durchlauf += 1
            removed = []
            for v in sorted(alive):
                steps += 1
                if deg[v] < k:
                    alive.discard(v)
                    core[v] = k - 1
                    removed.append(v)
                    for u in adj[v]:
                        steps += 1
                        if u in alive:
                            deg[u] -= 1
                    changed = True
            log.append(PeelEvent(k, durchlauf, tuple(removed)))
    return NaiveResult(tuple(core), steps, passes, tuple(log))


def removed_after(log, step) -> frozenset:
    """Menge der Knoten, die nach den ersten `step` Durchläufen des Schälens entfernt sind (step = 0: keiner)."""
    gone = set()
    for ev in log[:step]:
        gone.update(ev.entfernt)
    return frozenset(gone)


# --- Kennzahlen der Zerlegung ----------------------------------------------------------------------------------------------------------------------


def k_core_nodes(core, k) -> list:
    """Knoten des k-Kerns: alle Knoten mit Kernzahl >= k."""
    return [v for v, c in enumerate(core) if c >= k]


def shell_sizes(core) -> dict:
    """Kernzahl -> Zahl der Knoten mit genau dieser Kernzahl (die Schale), aufsteigend nach Kernzahl."""
    sizes = {}
    for c in core:
        sizes[c] = sizes.get(c, 0) + 1
    return dict(sorted(sizes.items()))


def degeneracy(core) -> int:
    return max(core, default=0)


def clique_upper_bound(core) -> int:
    """Obere Schranke der Cliquenzahl: Degeneracy + 1 (eine Clique der Größe s liegt im (s - 1)-Kern)."""
    return degeneracy(core) + 1


class _CliqueLimit(Exception):
    pass


def max_clique_size(adj, call_limit=2_000_000):
    """Cliquenzahl ω: Bron-Kerbosch mit Pivot und Schranke |R| + |P| <= beste Größe. None, wenn das Aufruflimit überschritten wird."""
    n = len(adj)
    if n == 0:
        return 0
    nbrs = [set(a) for a in adj]
    best = [1]
    calls = [0]

    def rec(r, p, x):
        calls[0] += 1
        if calls[0] > call_limit:
            raise _CliqueLimit
        if not p and not x:
            best[0] = max(best[0], r)
            return
        if r + len(p) <= best[0]:
            return
        pivot = max(p | x, key=lambda u: (len(nbrs[u] & p), -u))
        for v in sorted(p - nbrs[pivot]):
            rec(r + 1, p & nbrs[v], x & nbrs[v])
            p = p - {v}
            x = x | {v}

    try:
        rec(0, set(range(n)), set())
    except _CliqueLimit:
        return None
    return best[0]


# --- Vergleichsmaße -------------------------------------------------------------------------------------------------------------------------------


def degrees(adj) -> list:
    return [len(a) for a in adj]


def _bfs_distances(adj, s) -> list:
    dist = [-1] * len(adj)
    dist[s] = 0
    queue = deque([s])
    while queue:
        v = queue.popleft()
        for u in adj[v]:
            if dist[u] < 0:
                dist[u] = dist[v] + 1
                queue.append(u)
    return dist


def closeness(adj) -> list:
    """Nähe: (r / Summe der Abstände) * (r / (n - 1)) mit r = Zahl der erreichbaren anderen Knoten (Wasserman-Faust, wie networkx)."""
    n = len(adj)
    if n <= 1:
        return [0.0] * n
    out = []
    for s in range(n):
        reach = [d for d in _bfs_distances(adj, s) if d > 0]
        total = sum(reach)
        out.append(0.0 if total == 0 else (len(reach) / total) * (len(reach) / (n - 1)))
    return out


def betweenness(adj) -> list:
    """Betweenness nach Brandes (ungewichtet, ungerichtet, nicht normiert: jedes Knotenpaar einmal gezählt)."""
    n = len(adj)
    cb = [0.0] * n
    for s in range(n):
        stack = []
        pred = [[] for _ in range(n)]
        sigma = [0] * n
        sigma[s] = 1
        dist = [-1] * n
        dist[s] = 0
        queue = deque([s])
        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = [0.0] * n
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    return [x / 2 for x in cb]


def pagerank(adj, damping=0.85, iterations=500, tol=1e-12) -> list:
    """PageRank (ungerichtet: jede Kante in beide Richtungen), Knoten ohne Kante verteilen ihren Rang gleichmäßig."""
    n = len(adj)
    if n == 0:
        return []
    p = [1.0 / n] * n
    for _ in range(iterations):
        dangling = sum(p[v] for v in range(n) if not adj[v])
        base = (1 - damping) / n + damping * dangling / n
        new = [base] * n
        for v in range(n):
            if adj[v]:
                share = damping * p[v] / len(adj[v])
                for u in adj[v]:
                    new[u] += share
        if sum(abs(new[i] - p[i]) for i in range(n)) < tol:
            return new
        p = new
    return p


# --- Rangkorrelation und Top-k -----------------------------------------------------------------------------------------------------------------------


def average_ranks(values) -> list:
    """Ränge ab 1; bei Gleichstand der Mittelwert der belegten Ränge (wie scipy.stats.rankdata, Methode 'average')."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for t in range(i, j + 1):
            ranks[order[t]] = r
        i = j + 1
    return ranks


def rank_correlation(x, y):
    """Spearman-Rangkorrelation (Pearson der mittleren Ränge); None, wenn eine Seite konstant ist oder weniger als zwei Werte vorliegen."""
    n = len(x)
    if n < 2 or len(y) != n:
        return None
    rx, ry = average_ranks(x), average_ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return sxy / math.sqrt(sxx * syy)


def topk_expected(values, score, k) -> float:
    """Mittlerer Wert von `score` über die k besten Knoten nach `values`; Gleichstände werden im Erwartungswert über zufällige Auflösung gemittelt."""
    groups = {}
    for v, val in enumerate(values):
        groups.setdefault(val, []).append(v)
    remaining = k
    total = 0.0
    for val in sorted(groups, reverse=True):
        if remaining <= 0:
            break
        group = groups[val]
        take = min(remaining, len(group))
        total += take * (sum(score[v] for v in group) / len(group))
        remaining -= take
    return total / k


def honest_oracle(half_a, half_b, k) -> float:
    """Bestes Erreichbare ohne Eigenlob: die k besten Knoten nach Hälfte A der Läufe, bewertet auf Hälfte B (Gleichstände: kleinere Nummer zuerst)."""
    order = sorted(range(len(half_a)), key=lambda v: (-half_a[v], v))[:k]
    return sum(half_b[v] for v in order) / k


# --- SIR-Ausbreitung (Regel wie in kaskaden-demo) -------------------------------------------------------------------------------------------------


def sir_final_size(adj, beta, mu, seed, patient_zero, max_steps=200) -> int:
    """Endgröße eines SIR-Laufs (Zahl der je angesteckten Knoten inkl. Patient Null). Diskrete Zeit, synchron: jeder Infizierte steckt jeden gesunden
    Nachbarn unabhängig mit Wahrscheinlichkeit beta an, danach genest jeder Infizierte (Zustand vor dem Schritt) mit Wahrscheinlichkeit mu."""
    n = len(adj)
    rng = random.Random(int(seed) * 1_000_003 + 6421)
    rnd = rng.random
    state = [0] * n
    state[patient_zero] = 1
    infected = [patient_zero]
    ever = 1
    for _ in range(int(max_steps)):
        if not infected:
            break
        current = sorted(infected)
        new = set()
        for v in current:
            for u in adj[v]:
                if state[u] == 0 and u not in new and rnd() < beta:
                    new.add(u)
        recovered = [v for v in current if rnd() < mu]
        for u in new:
            state[u] = 1
        for v in recovered:
            state[v] = 2
        infected = [v for v in current if state[v] == 1] + list(new)
        ever += len(new)
    return ever


@dataclass(frozen=True)
class SpreadResult:
    power: tuple          # erwartete Endgröße je Startknoten (Mittel beider Hälften)
    half_a: tuple         # Mittel der Läufe mit gerader Nummer
    half_b: tuple         # Mittel der Läufe mit ungerader Nummer
    reliability: object   # Rangkorrelation der beiden Hälften (None, wenn konstant)
    runs: int


def sir_spread_power(adj, beta, mu, runs, seed) -> SpreadResult:
    """Ausbreitungskraft jedes Knotens als Einzelstarter: Mittel der Endgröße über `runs` Läufe (auf eine gerade Zahl aufgerundet; zwei Hälften)."""
    runs = runs + (runs % 2)
    n = len(adj)
    sums = [[0.0] * n, [0.0] * n]
    for v in range(n):
        for r in range(runs):
            sums[r % 2][v] += sir_final_size(adj, beta, mu, int(seed) * 1_000_000_007 + v * 100_003 + r, v)
    half = runs // 2
    a = tuple(s / half for s in sums[0])
    b = tuple(s / half for s in sums[1])
    return SpreadResult(tuple((x + y) / 2 for x, y in zip(a, b)), a, b, rank_correlation(a, b), runs)


def mean_field_threshold(adj, mu):
    """β_c = μ·⟨k⟩/⟨k²⟩ (heterogene Mean-Field-Näherung); None, wenn ⟨k²⟩ = 0. Nur Orientierung: in endlichen Netzen liegt die echte Schwelle höher."""
    n = len(adj)
    if n == 0:
        return None
    deg = degrees(adj)
    k2 = sum(d * d for d in deg) / n
    if k2 <= 0:
        return None
    return mu * (sum(deg) / n) / k2
