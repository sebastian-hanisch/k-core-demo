"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kco_constants as C
from kco_evaluation import de


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, bottom=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=bottom), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def node_size(n):
    return 10 if n <= 60 else 8 if n <= 150 else 6 if n <= 260 else 5


def build_network(inst, core, removed=frozenset(), height=520):
    """Netz mit festen Positionen; noch nicht entfernte Knoten nach Kernzahl gefärbt, entfernte grau und hohl. Gleicher Maßstab auf beiden Achsen
    (scaleanchor mit autorange, Rand über zwei unsichtbare Eckmarker)."""
    n = inst.n
    alive_x, alive_y, gone_x, gone_y = [], [], [], []
    for u in range(n):
        for v in inst.adj[u]:
            if u < v:
                target = gone_x if (u in removed or v in removed) else alive_x
                targety = gone_y if (u in removed or v in removed) else alive_y
                target += [inst.pos[u][0], inst.pos[v][0], None]
                targety += [inst.pos[u][1], inst.pos[v][1], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=gone_x, y=gone_y, mode="lines", line=dict(color="rgba(150,150,150,0.12)", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=alive_x, y=alive_y, mode="lines", line=dict(color=C.COLOR_EDGE, width=1), hoverinfo="skip", showlegend=False))
    deg = [len(a) for a in inst.adj]

    def hover(v):
        name = str(inst.labels[v]) if inst.labels else f"Knoten {v}"
        role = f" ({inst.groups[v]})" if inst.groups else ""
        return f"{name}{role}: Grad {deg[v]}, Kernzahl {core[v]}"

    alive = [v for v in range(n) if v not in removed]
    gone = [v for v in range(n) if v in removed]
    size = node_size(n)
    if gone:
        fig.add_trace(go.Scatter(x=[inst.pos[v][0] for v in gone], y=[inst.pos[v][1] for v in gone], mode="markers",
                                 marker=dict(size=size, color="rgba(0,0,0,0)", line=dict(color=C.COLOR_REMOVED, width=1.2)),
                                 hovertext=[hover(v) for v in gone], hoverinfo="text", showlegend=False))
    top = max(core) if core else 0
    fig.add_trace(go.Scatter(
        x=[inst.pos[v][0] for v in alive], y=[inst.pos[v][1] for v in alive], mode="markers+text" if n <= 12 else "markers",
        text=[str(inst.labels[v]) if inst.labels else str(v) for v in alive] if n <= 12 else None, textposition="top center",
        marker=dict(size=size, color=[core[v] for v in alive], colorscale=C.SHELL_SCALE, cmin=0, cmax=max(top, 1),
                    line=dict(color="rgba(40,40,40,0.55)", width=0.6),
                    colorbar=dict(title=dict(text="Kernzahl", side="top"), nticks=4, thickness=12, len=0.6)),
        hovertext=[hover(v) for v in alive], hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[-0.04, 1.04], y=[-0.04, 1.04], mode="markers", marker=dict(size=1, color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, autorange=True)
    fig.update_yaxes(visible=False, autorange=True, scaleanchor="x", scaleratio=1)
    return _base(fig, height=height)


def build_remaining(log, n):
    """Verbleibende Knoten über die Durchläufe des naiven Schälens (Stufen: ein Punkt je Durchlauf, Beschriftung k und Durchlauf)."""
    xs = list(range(len(log) + 1))
    left = [n]
    for ev in log:
        left.append(left[-1] - len(ev.entfernt))
    fig = go.Figure(go.Scatter(x=xs, y=left, mode="lines+markers", line=dict(color=C.COLOR_LINE, width=3, shape="hv"),
                               hovertext=["Start"] + [f"k = {ev.k}, Durchlauf {ev.durchlauf}: {len(ev.entfernt)} fallen" for ev in log], hoverinfo="text"))
    fig.update_xaxes(title_text="Durchlauf", nticks=6, tickformat="d")
    fig.update_yaxes(title_text="verbleibende Knoten", rangemode="tozero")
    return _base(fig, height=260, bottom=40)


def build_core_vs_degree(deg, core):
    """Blasendiagramm: Grad gegen Kernzahl, Blasengröße = Zahl der Knoten mit diesem Paar; Diagonale = Kernzahl gleich Grad."""
    counts = {}
    for d, c in zip(deg, core):
        counts[(d, c)] = counts.get((d, c), 0) + 1
    pairs = sorted(counts)
    top = max(max(deg, default=1), 1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color="rgba(150,150,150,0.8)", dash="dash"), hoverinfo="skip", name="Kernzahl = Grad"))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pairs], y=[p[1] for p in pairs], mode="markers",
        marker=dict(size=[8 + 4 * counts[p] ** 0.5 for p in pairs], color=C.COLOR_LINE, opacity=0.7, line=dict(color="white", width=0.5)),
        hovertext=[f"Grad {p[0]}, Kernzahl {p[1]}: {counts[p]} Knoten" for p in pairs], hoverinfo="text", name="Knoten (Größe = Anzahl)"))
    fig.update_xaxes(title_text="Grad")
    fig.update_yaxes(title_text="Kernzahl")
    return _base(fig, height=340, bottom=40)


def build_steps(rows):
    """Faktor naiv / Bucket je Netztyp und Größe (logarithmische Achse); der ungünstige Pfad ragt heraus."""
    sizes = sorted({r["n"] for r in rows})
    types = list(dict.fromkeys(r["netztyp"] for r in rows))
    shades = ["#9ecae1", "#4c78a8", "#1f3b5c"]
    fig = go.Figure()
    for i, n in enumerate(sizes):
        ys = [next(r["factor"] for r in rows if r["netztyp"] == t and r["n"] == n) for t in types]
        fig.add_trace(go.Bar(x=types, y=ys, name=f"n = {n}", marker_color=shades[i % len(shades)],
                             hovertemplate="%{x}, n = " + str(n) + ": %{y:.1f}-fach<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Schritte naiv ÷ Schritte Bucket", type="log")
    return _base(fig, height=340, bottom=40)


def build_spread_rho(r):
    """Rangkorrelation von Maß und Ausbreitungskraft; ein konstantes Maß (Rangkorrelation nicht definiert) steht als 0 mit Beschriftung „konstant“."""
    names = list(C.MEASURES)
    vals = [0.0 if r.rho[m] is None else r.rho[m] for m in names]
    colors = [C.COLOR_BUCKET if m == "Kernzahl" else C.COLOR_LINE for m in names]
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=colors, text=["konstant" if r.rho[m] is None else de(r.rho[m], 2) for m in names],
                           textposition="outside", hovertemplate="%{x}: %{text}<extra></extra>"))
    fig.update_yaxes(title_text="Rangkorrelation mit der Ausbreitungskraft", range=[min(-0.1, min(vals) - 0.1), 1.15])
    return _base(fig, height=320, bottom=30)


def build_spread_top(r):
    """Mittlere Ausbreitungskraft der besten 5 % nach jedem Maß, dazu die Auswahl nach den Messläufen (auf einer Hälfte gewählt, auf der anderen bewertet) und die Zufallswahl."""
    names = list(C.MEASURES)
    fig = go.Figure(go.Bar(x=names, y=[r.top[m] for m in names], marker_color=[C.COLOR_BUCKET if m == "Kernzahl" else C.COLOR_LINE for m in names],
                           text=[de(r.top[m]) for m in names], textposition="outside", hovertemplate="%{x}: %{y:.1f}<extra></extra>", name="Auswahl nach Maß"))
    fig.add_trace(go.Scatter(x=names, y=[r.oracle] * len(names), mode="lines", line=dict(color=C.COLOR_ORACLE, dash="dash", width=2),
                             name=f"Auswahl nach Messläufen ({de(r.oracle)})", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=names, y=[r.random] * len(names), mode="lines", line=dict(color=C.COLOR_RANDOM, dash="dot", width=2),
                             name=f"Zufallswahl ({de(r.random)})", hoverinfo="skip"))
    fig.update_yaxes(title_text="mittlere Endgröße der gewählten Starter", rangemode="tozero")
    return _base(fig, height=380, bottom=90)
