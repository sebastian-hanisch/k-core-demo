"""k-Core: Kernzahl und Schälen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück der Reihe „Netzwerkanalyse“: die k-Kern-Zerlegung (naives Schälen und Bucket-Algorithmus), Kernzahl gegen Grad und die Frage,
was die Ausbreitung eines Einzelstarters wirklich vorhersagt. Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import kco_algorithm as A
import kco_constants as C
from kco_evaluation import (
    Settings,
    de,
    analyse,
    naive_factor,
    spread_experiment,
    sweep_steps,
    sweep_types,
    top_core_count,
    verdict_information,
    verdict_spread,
    verdict_steps,
    verdict_types,
)
from kco_layout import dunkles_design, kopf_css
from kco_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kco_scenario import link_stand
from kco_visualization import (
    build_core_vs_degree,
    build_network,
    build_remaining,
    build_spread_rho,
    build_spread_top,
    build_steps,
)

st.set_page_config(page_title="k-Core – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _steps():
    return sweep_steps()


@st.cache_data(show_spinner=False)
def _types(settings):
    return sweep_types(settings)


@st.cache_data(show_spinner=False)
def _spread(settings, beta_factor, runs):
    return spread_experiment(settings, beta_factor, runs)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kco_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 k-Core: Kernzahl und Schälen")
st.markdown(
    """
**Erstes Stück** der Reihe „Netzwerkanalyse“, die erste Demo im Struktur-Arm. Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **ein** Verfahren an einem wachsenden Beispiel: einem Netz von Subunternehmern und Lieferanten (synthetisch; dazu das echte Link-Netz dieser Website). Beim **Schälen** werden wiederholt alle Knoten mit weniger als *k* Nachbarn entfernt; was bleibt, ist der **k-Kern**, und die **Kernzahl** eines Knotens ist das größte *k*, in dessen Kern er liegt. In der [Demo zur größten Clique](https://sebastianhanisch-max-clique-demo.streamlit.app/) war die Kernzahl nur ein Werkzeug; hier ist sie das Thema.

Die Kernfrage: **Wann trägt die Kernzahl Information, die der Grad nicht schon hat, und was sagt die Ausbreitung wirklich voraus?**

Weiter unten: drei Experimente (**🔬**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Schälen", expanded=True):
    st.markdown(
        """
1. **Naives Schälen (die Definition):** Setze *k* = 1. Entferne alle Knoten, die im Restnetz weniger als *k* Nachbarn haben; wer dabei fällt, bekommt die **Kernzahl** *k* − 1.
2. Jede Entfernung senkt den Grad der Nachbarn, also gehe das Restnetz erneut durch, bis in einem **Durchlauf** nichts mehr fällt. Das Übrige ist der *k*-Kern. Dann *k* um eins erhöhen.
3. **Bucket-Algorithmus (Batagelj und Zaveršnik):** statt jedes Mal alle Knoten zu prüfen, hält er die Knoten nach Grad in Fächern und entfernt immer einen mit kleinstem Rest-Grad. Jede Kante wird zweimal angesehen: genau **2n + 2m** Schritte.
4. **Warum das funktioniert:** Ein Knoten kann nur im *k*-Kern bleiben, wenn mindestens *k* seiner Nachbarn ebenfalls bleiben. Fällt einer, sinkt der Grad der Nachbarn, und die Entfernung setzt sich wie ein Dominostein fort. Der Bucket-Algorithmus nutzt das: er muss nach einer Entfernung nur die Nachbarn des Entfernten neu einsortieren.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Netz zu teilen.")

load_permalink_settings()
init_session_state_defaults()
st.session_state.setdefault("peel_step", 0)

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    typ = st.selectbox("Netztyp", C.ALL_TYPES, key="netztyp_select", help="Welches Netz erzeugt oder geladen wird. Handbeispiel, Gegenbeispiel Pfad und Link-Netz sind feste Netze.")
    n_fixed = typ in C.N_FIXED_TYPES
    c_fixed = typ in C.C_FIXED_TYPES
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", disabled=n_fixed, help="Zahl der Knoten (beim Gitter auf ein Quadrat gerundet).")
    c = st.slider("Verbindungen je Knoten c", *bounds("c_slider"), key="c_slider", disabled=c_fixed, help="Was c bedeutet, hängt vom Netztyp ab (siehe darunter).")
    st.caption(C.C_MEANING[typ] if typ in C.C_MEANING else "Dieses Netz ist fest: n, c und Zufalls-Seed wirken hier nicht." if n_fixed else "Dieses Netz ist fest: c und Zufalls-Seed wirken hier nicht, n gibt die Länge des Pfads.")
    seed = st.number_input("Zufalls-Seed des Netzes", *bounds("seed_input"), key="seed_input", step=1, disabled=typ in C.FIXED_TYPES)
    st.button("🎲 Neues Netz würfeln", width="stretch", on_click=randomize_seed, disabled=typ in C.FIXED_TYPES)

sync_query_params({"netztyp_select": typ, "n_slider": int(n), "c_slider": int(c), "seed_input": int(seed)})

settings = Settings(typ, int(n), int(c), int(seed))
a = _analysis(settings)
if not a.valid:
    st.error("Interner Fehler: Bucket-Algorithmus und naives Schälen liefern verschiedene Kernzahlen oder die Kernzahlen sind ungültig. Bitte melden.")
if typ == C.T_LINK:
    st.info(f"Das echte Link-Netz von sebastianhanisch.net, Schnappschuss vom {link_stand()} (ungerichtet zusammengefasst): 50 Seiten und 300 Demos. Die Zahlen gelten für diesen Stand, nicht für die heutige Website.")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Netz und sein Schälen")
m1, m2, m3 = st.columns(3)
m1.metric("Knoten / Kanten", f"{a.inst.n} / {a.inst.m}")
m2.metric("Höchste Kernzahl (Degeneracy)", a.degeneracy)
m3.metric("Schalen", len(a.shells))
m4, m5, m6 = st.columns(3)
m4.metric("Knoten im höchsten Kern", f"{top_core_count(a)} ({100 * top_core_count(a) / a.inst.n:.0f} %)")
m5.metric("Schritte Bucket-Algorithmus", a.bucket.steps, delta=f"naiv: {a.naive.steps} Schritte ({de(naive_factor(a))}-fach)", delta_color="off")
m6.metric("Cliquenzahl ω ≤ Degeneracy + 1", "nicht berechnet" if a.omega is None else f"{a.omega} ≤ {a.degeneracy + 1}")

log = a.naive.log
st.session_state["peel_step"] = min(int(st.session_state.get("peel_step", 0)), len(log))
col_net, col_side = st.columns([3, 2])
with col_net:
    step = st.slider("Durchlauf des naiven Schälens", 0, len(log), key="peel_step",
                     help="0 = Ausgangsnetz. Jeder Schritt ist ein Durchlauf durch das Restnetz; entfernte Knoten sind grau und hohl.")
    play = st.button("▶ Schälen abspielen", key="play_peel", help="Spielt alle Durchläufe nacheinander ab.")
    holder = st.empty()
    if play:
        delay = min(0.5, 8.0 / max(1, len(log)))
        for s in range(len(log) + 1):
            with holder.container():
                st.plotly_chart(build_network(a.inst, a.core, A.removed_after(log, s)), width="stretch", key=f"net_play_{s}")
            time.sleep(delay)
    else:
        with holder.container():
            st.plotly_chart(build_network(a.inst, a.core, A.removed_after(log, step)), width="stretch", key=f"net_step_{step}")
    if step == 0:
        st.caption(f"Ausgangsnetz mit {a.inst.n} Knoten. Die Farbe zeigt die Kernzahl, die das Schälen am Ende vergibt.")
    else:
        ev = log[step - 1]
        left = a.inst.n - len(A.removed_after(log, step))
        if ev.entfernt:
            names = ", ".join(str(a.inst.labels[v]) if a.inst.labels else str(v) for v in ev.entfernt[:10]) + (" …" if len(ev.entfernt) > 10 else "")
            st.caption(f"Schwelle k = {ev.k}, Durchlauf {ev.durchlauf}: {len(ev.entfernt)} Knoten haben weniger als {ev.k} Nachbarn und fallen (Kernzahl {ev.k - 1}): {names}. Übrig: {left}.")
        else:
            st.caption(f"Schwelle k = {ev.k}, Durchlauf {ev.durchlauf}: nichts fällt mehr, der {ev.k}-Kern steht ({left} Knoten).")
with col_side:
    st.markdown("**Verbleibende Knoten über die Durchläufe**")
    st.plotly_chart(build_remaining(log, a.inst.n), width="stretch", key="remaining_chart")
    st.markdown("**Schalen**")
    st.dataframe([{"Kernzahl": k, "Knoten": cnt, "Anteil": f"{100 * cnt / a.inst.n:.0f} %"} for k, cnt in a.shells.items()], hide_index=True, width="stretch")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Trägt die Kernzahl hier Information, die der Grad nicht hat?")
kind, text = verdict_information(a)
getattr(st, kind)(text)
st.plotly_chart(build_core_vs_degree(A.degrees(a.inst.adj), list(a.core)), width="stretch", key="core_vs_degree")
st.caption("Jede Blase ist ein Paar (Grad, Kernzahl); die Größe zeigt, wie viele Knoten es sind. Auf der gestrichelten Diagonale ist die Kernzahl gleich dem Grad; darunter liegt, wer weniger Nachbarn im Kern hat, als er überhaupt hat.")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Wie viel spart der Bucket-Algorithmus?")
st.caption("Median über 5 feste Netze (SWEEP_SEEDS) für Zufall und skalenfrei; Gitter und Pfad sind deterministisch. Gezählt werden Elementarschritte, keine Laufzeit.")
rows = _steps()
st.plotly_chart(build_steps(rows), width="stretch", key="steps_chart")
kind, text = verdict_steps(rows)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 2: Auf welchen Netztypen trägt die Kernzahl Information?")
st.caption(f"Alle erzeugten Netztypen bei n = {settings.n}, c = {settings.c} und Seed {settings.seed} (die Einstellungen der Seitenleiste). Cliquenschranke: ω ≤ Degeneracy + 1, die Lücke ist die Differenz.")
trows = _types(settings)
st.dataframe(
    [{"Netztyp": r["netztyp"], "Knoten": r["n"], "Kanten": r["m"], "Schalen": r["schalen"], "höchster Kern": r["degeneracy"],
      "Knoten darin": r["im_hoechsten_kern"], "Rangkorrelation Grad–Kernzahl": "konstant" if r["rho"] is None else f"{r['rho']:.3f}",
      "Kernzahl = Grad": f"{100 * r['gleich']:.0f} %", "ω": "–" if r["omega"] is None else r["omega"], "Lücke d + 1 − ω": "–" if r["luecke"] is None else r["luecke"]}
     for r in trows],
    hide_index=True, width="stretch")
kind, text = verdict_types(trows)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Experiment 3: Was sagt die Ausbreitung wirklich voraus?")
st.markdown(
    "Jeder Knoten startet einmal als **Patient Null** eines SIR-Laufs (Regel wie in der [Demo zu Kaskaden und Ausbreitung](https://sebastianhanisch-kaskaden-demo.streamlit.app/): "
    f"Ansteckung mit Wahrscheinlichkeit β je Nachbar und Schritt, Genesung mit μ = {C.MU}). Seine **Ausbreitungskraft** ist die mittlere Endgröße über die Läufe. "
    "Verglichen werden fünf Maße: wie gut ordnet jedes die Knoten nach ihrer Ausbreitungskraft (Rangkorrelation), und wie gut sind die besten 5 % als Starter? "
    "Als Vergleich dient die Auswahl nach den Messläufen selbst: auf einer Hälfte der Läufe gewählt, auf der anderen bewertet. Sie ist verrauscht und kann von einem guten Maß übertroffen werden."
)
b1, b2 = st.columns(2)
beta_factor = b1.slider("β als Vielfaches der Mean-Field-Schwelle", C.BETA_FACTOR_MIN, C.BETA_FACTOR_MAX, C.DEFAULT_BETA_FACTOR, step=0.5, key="beta_factor",
                        help="Die Schwelle β_c = μ·⟨k⟩/⟨k²⟩ ist in endlichen Netzen zu niedrig; das 3-fache erzeugt meist spürbare Ausbrüche.")
runs = b2.slider("Läufe je Startknoten", C.RUNS_MIN, C.RUNS_MAX, C.DEFAULT_RUNS, step=2, key="runs",
                 help="Mehr Läufe machen die Rangfolge der Startknoten zuverlässiger, aber die Rechnung länger.")
spread_key = (settings, float(beta_factor), int(runs))
if st.button("Messung starten", key="spread_run", help="Rechnet jeden Knoten als Startknoten; bei großen Netzen und vielen Läufen kann das eine halbe Minute dauern."):
    with st.spinner("Rechne die Ausbreitung für jeden Startknoten …"):
        result = _spread(settings, float(beta_factor), int(runs))
    st.session_state["spread_state"] = (spread_key, result)
state = st.session_state.get("spread_state")
if state is None:
    st.caption("Noch keine Messung. Starten Sie sie mit dem Knopf oben (Ergebnisse bleiben nur für genau diese Einstellungen stehen).")
elif state[0] != spread_key:
    st.info("Die Einstellungen haben sich seit der letzten Messung geändert. Bitte die Messung neu starten.")
elif state[1] is None:
    st.warning("Dieses Netz hat keine Kanten: es gibt nichts auszubreiten.")
else:
    r = state[1]
    s1, s2 = st.columns(2)
    s1.metric("β (eingesetzt)", de(r.beta, 3), delta=f"Schwelle β_c = {de(r.beta_c, 3)}", delta_color="off")
    s2.metric("Läufe je Startknoten", r.runs)
    s3, s4 = st.columns(2)
    s3.metric("Zuverlässigkeit der Messung", "unbestimmt" if r.reliability is None else de(r.reliability, 2),
              delta="Rangkorrelation der beiden Hälften", delta_color="off")
    s4.metric("Mittlere Ausbreitungskraft", f"{de(r.mean_power)} Knoten")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Rangkorrelation mit der Ausbreitungskraft**")
        st.plotly_chart(build_spread_rho(r), width="stretch", key="spread_rho")
    with g2:
        st.markdown(f"**Die besten {r.k} Knoten ({100 * C.TOP_FRACTION:.0f} %) als Starter**")
        st.plotly_chart(build_spread_top(r), width="stretch", key="spread_top")
    kind, text = verdict_spread(r)
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Netz ist ungerichtet und ungewichtet** | Im Link-Netz wirkt jeder Link nur in eine Richtung; hier ist er in beide Richtungen zusammengefasst. Richtung und Stärke von Verbindungen gehen verloren, gerichtete Kerne gibt es hier nicht. | – (bewusst nicht umgesetzt) |
| **Ausbreitungskraft = erwartete Endgröße mit dem SIR-Modell** | Die Endgröße zählt kleine Ausbrüche mit; ein anderes Ziel (etwa die Wahrscheinlichkeit eines großen Ausbruchs) oder ein anderes Modell kann eine andere Rangfolge ergeben. β ist ein Vielfaches der Mean-Field-Schwelle, die in endlichen Netzen zu niedrig liegt. | Stück 6 (komplexe Ansteckung) |
| **Ein Starter** | Mehrere gleichzeitige Starter und ihr Abstand zueinander fehlen; für die Auswahl mehrerer Starter ist das der entscheidende Punkt. | Stück 5 (Einflussmaximierung) |
| **Synthetische Netze und ein selbst erzeugtes echtes Netz** | Das Ergebnis, dass die Kernzahl hier meist nicht besser vorhersagt als Grad oder Nähe, ist ein Befund für diese Modellnetze (Ausbreitung); am Link-Netz dieser Website ist nur Kernzahl gegen Grad gemessen. Er widerlegt keine Arbeit an großen echten Netzen. | – |
| **Elementarschritte statt Laufzeit** | Die Schrittzahlen vergleichen Verfahren, nicht Rechner; ein Faktor in Schritten ist kein Faktor in Sekunden. | – |
| **Die Auswahl nach den Messläufen ist eine Schätzung** | Sie wählt auf einer Hälfte der Läufe und wird auf der anderen bewertet; bei niedriger Zuverlässigkeit streut auch sie, und ein Maß kann sie übertreffen. Die Zuverlässigkeit steht neben jeder Messung. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein einfacher ungerichteter Graph $G = (V, E)$ mit $n$ Knoten und $m$ Kanten. Der **$k$-Kern** ist der größte Teilgraph, in dem jeder Knoten mindestens $k$ Nachbarn hat. Die **Kernzahl** von $v$ ist

$$\operatorname{core}(v) = \max \{\, k : v \in k\text{-Kern} \,\}$$

Die **Degeneracy** ist

$$d = \max_{v} \operatorname{core}(v)$$

**Cliquenschranke.** Eine Clique der Größe $s$ liegt im $(s-1)$-Kern, also gilt

$$\omega \le d + 1$$

**Schrittzahl des Bucket-Algorithmus.** Er legt $n$ Knoten in Fächer, ordnet $n$ Positionen und prüft jede Kante zweimal:

$$\text{Schritte} = n + n + 2m = 2n + 2m$$

**Naives Schälen.** Jeder Durchlauf prüft alle Restknoten; die Schrittzahl ist die Summe der Restknotenzahlen über alle Durchläufe plus $2m$ Gradabzüge. Im ungünstigen Pfad fällt je Durchlauf nur ein Paar von Enden, die Zahl der Durchläufe wächst mit $n/2$ und die Schrittzahl mit $n^2$.

**Ausbreitung.** Im diskreten SIR-Modell steckt jeder Infizierte jeden gesunden Nachbarn mit Wahrscheinlichkeit $\beta$ an und genest mit Wahrscheinlichkeit $\mu$. Die Mean-Field-Schwelle ist

$$\beta_c = \mu \, \frac{\langle k \rangle}{\langle k^2 \rangle}$$

**Rangkorrelation.** Mit mittleren Rängen $R(x_i)$ und $R(y_i)$ ist

$$\rho = \frac{\sum_i (R(x_i) - \bar R_x)(R(y_i) - \bar R_y)}{\sqrt{\sum_i (R(x_i) - \bar R_x)^2 \, \sum_i (R(y_i) - \bar R_y)^2}}$$

und nicht definiert, wenn eine Seite konstant ist.

**Literatur.**
- Batagelj, V., Zaveršnik, M. (2011): *An O(m) algorithm for cores decomposition of networks.* Advances in Data Analysis and Classification 5(2), 129–145.
- Malliaros, F. D., u. a. (2020): *The core decomposition of networks: theory, algorithms and applications.* The VLDB Journal 29(1), 61–92.
- Kitsak, M., u. a. (2010): *Identification of influential spreaders in complex networks.* Nature Physics 6, 888–893.
- Pastor-Satorras, R., Vespignani, A. (2001): *Epidemic spreading in scale-free networks.* Physical Review Letters 86(14), 3200–3203.

Der $k$-Kern wurde nach Batagelj und Zaveršnik 1983 von Seidman vorgeschlagen (Originalarbeit hier nicht geprüft).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
