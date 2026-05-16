import json
import random
import re

import pandas as pd
import streamlit as st

#Constants

RESULT_FILES = {
    "Llama 3.2 3B":      "Results/llama_results.jsonl",
    "Gemma 3 27B":       "Results/gemma_results.jsonl",
    "Claude Sonnet 4.5": "Results/claude_results.jsonl",
    "GPT-4o":            "Results/gpt_results.jsonl",}

MODELS = list(RESULT_FILES.keys())

# Each model's failure mode plus the 3 hand-picked claims that best illustrate it.
SIGNATURES = {
    "Llama 3.2 3B": {
        "headline": "Failure mode: gross fabrication.",
        "description": (
            "Under pushback, Llama abandons correct verdicts and invents specific names, "
            "dates, and events to justify the flip. The fabrications are catchable with a "
            "quick search, but only if the user knows to check. 222 right-to-wrong flips "
            "out of 265 correct neutral verdicts."
        ),
    },
    "Gemma 3 27B": {
        "headline": "Failure mode: apologetic retreat.",
        "description": (
            "Under pushback, Gemma openly apologizes, accepts the user's challenge as "
            "evidence against itself, and reclassifies the claim as UNCERTAIN rather than "
            "defending its original verdict. 105 right-to-wrong flips out of 150 correct "
            "neutral verdicts."),
    },
    "Claude Sonnet 4.5": {
        "headline": "Failure mode: nitpicking technicalities.",
        "description": (
            "Under pushback, Claude gives a confident broad verdict at neutral, then flips "
            "on a small technicality after the user challenges it, treating the technicality "
            "as grounds to abandon an otherwise correct answer. 77 right-to-wrong flips "
            "out of 239 correct neutral verdicts."),
    },
    "GPT-4o": {
        "headline": "Failure mode: confident correction.",
        "description": (
            "Under pushback, GPT-4o flips with plausible-sounding logic backed by unverified "
            "claims stated with complete confidence. Unlike Llama's outright fabrications, "
            "GPT-4o's reasoning is harder to spot as wrong because not everything it says is easily searchable. "
            "Only 10 right-to-wrong flips out of 161 correct neutral verdicts."),
    },
}

def truth(politifact_label):
    """Map a 4-level PolitiFact label to the binary ground truth used in this study."""
    if politifact_label in ("true", "mostly-true"):
        return "TRUE"
    if politifact_label in ("false", "pants-fire"):
        return "FALSE"
    return None

def chip(text, kind="green"):
    """Render a styled pill for the model-name labels."""
    palettes = {
        "green":   ("#EAF3DE", "#27500A"),
        "red":     ("#FCEBEB", "#791F1F"),
        "neutral": ("#F1EFE8", "#444441"),}
    bg, fg = palettes[kind]
    return (
        f'<span style="background:{bg}; color:{fg}; padding:5px 12px; '
        f'border-radius:6px; font-size:13px; font-weight:500; '
        f'border:1px solid {fg}; '
        f'margin:2px 6px 2px 0; display:inline-block;">{text}</span>')

def signature_response(text):
    """For the signatures section: keep the model's full response (apologies,
    fabrications, etc.) but strip the 'Verdict: X' / 'Reasoning:' labels."""
    if not text:
        return ""
    text = re.sub(r'\bVerdict:\s*\w+\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bReasoning:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def parse_paper_quotes(path="Results/paper_quotes.txt"):
    """Parse paper_quotes.txt into structured records grouped by model."""
    with open(path) as f:
        content = f.read()

    pattern = re.compile(
        r'\[(?P<model>[^\]]+)\]\s*\((?P<gt>[^)]+)\)\s*(?P<claim>.+?)\n'
        r'Verdict:\s*(?P<neutral>\S+)\s*→\s*(?P<pushback>\S+)\n'
        r'Response:\s*(?P<response>.*?)(?=\n\n\[|\Z)',
        re.DOTALL,)

    by_model = {}
    for m in pattern.finditer(content):
        by_model.setdefault(m.group("model").strip(), []).append({
            "ground_truth": m.group("gt").strip(),
            "claim":        m.group("claim").strip(),
            "neutral":      m.group("neutral").strip(),
            "pushback":     m.group("pushback").strip(),
            "response":     m.group("response").strip(),
        })
    return by_model


@st.cache_data
def load_data():
    rows = []
    for model, path in RESULT_FILES.items():
        with open(path) as f:
            for i, line in enumerate(f):
                r = json.loads(line)
                r["model"] = model
                r["claim_index"] = i
                rows.append(r)

    df = pd.DataFrame(rows)

    with open("Results/metrics_summary.json") as f:
        metrics = json.load(f)

    return df, metrics

# Page setup

st.set_page_config(page_title="Sycophancy Across LLMs", layout="wide")

df, metrics = load_data()

if "selected_claim" not in st.session_state:
    st.session_state.selected_claim = 0


# Section 1: rows of twitter screenshots

import base64
import os

GALLERY_IMAGES = [f"gallery/grok_{i:02d}.png" for i in range(1, 17)]


def _encode_image(path):
    if not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/{ext};base64,{data}"


def _img_tag(path):
    src = _encode_image(path)
    if src:
        return f'<div class="shot"><img src="{src}" alt="" /></div>'
    return (
        '<div class="shot shot-placeholder">'
        f'<span>missing<br>{os.path.basename(path)}</span>'
        '</div>')

half = len(GALLERY_IMAGES) // 2
row_a_items = "".join(_img_tag(p) for p in GALLERY_IMAGES[:half])
row_b_items = "".join(_img_tag(p) for p in GALLERY_IMAGES[half:])

marquee_html = f"""
<style>
@keyframes scroll-left  {{ from {{ transform: translateX(0); }}    to {{ transform: translateX(-50%); }} }}
@keyframes scroll-right {{ from {{ transform: translateX(-50%); }} to {{ transform: translateX(0); }} }}

.hero-block {{
  padding: 18px 24px 8px;
}}
.hero-title {{
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 4px;
  text-align: center;
}}
.hero-eyebrow {{
  font-size: 14px;
  color: #888;
  margin-bottom: 18px;
  text-align: center;
}}
.hero-body {{
  font-size: 19px;
  line-height: 1.55;
  max-width: 880px;
  margin: 0 auto;
  text-align: center;
}}
.hero-body .accent {{
  background: #E6F1FB;
  color: #0C447C;
  padding: 2px 8px;
  border-radius: 5px;
  font-weight: 600;
}}
.hero-after {{
  padding: 16px 24px 6px;
}}

.marquee-wrap {{
  position: relative;
  background: rgba(0,0,0,0.20);
  border-radius: 14px;
  padding: 14px 0;
  margin: 14px 0 4px;
  overflow: hidden;
}}
.marquee-wrap::before, .marquee-wrap::after {{
  content: '';
  position: absolute; top: 0; bottom: 0; width: 90px;
  z-index: 2; pointer-events: none;
}}
.marquee-wrap::before {{ left: 0;  background: linear-gradient(to right, rgba(0,0,0,0.45), transparent); }}
.marquee-wrap::after  {{ right: 0; background: linear-gradient(to left,  rgba(0,0,0,0.45), transparent); }}

.marquee-row {{
  display: flex;
  gap: 14px;
  width: max-content;
  padding: 0 7px;
  align-items: center;
}}
.row-a {{ animation: scroll-left  80s linear infinite; }}
.row-b {{ animation: scroll-right 80s linear infinite; margin-top: 14px; }}

.shot {{
  flex-shrink: 0;
  height: 230px;
  border-radius: 10px;
  overflow: hidden;
  background: #1A1F2C;
}}
.shot img {{
  height: 230px;
  width: auto;
  display: block;
  border-radius: 10px;
}}
.shot-placeholder {{
  width: 220px; height: 230px;
  border: 1px dashed rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.03);
  display: flex; align-items: center; justify-content: center;
  color: #8899A6; font-size: 12px; text-align: center;
}}
</style>

<div class="hero-block">
  <div class="hero-title">Sycophancy Across LLMs</div>
  <div class="hero-eyebrow">A comparative test on political fact-checks · Deem Alothaimeen · DIGS 20006 · Spring 2026</div>
  <div class="hero-body">
    Every day people tag LLMs under political posts and ask <span class="accent">is this true?</span> Whatever the model answers becomes the fact-check millions of users read.
  </div>
</div>

<div class="marquee-wrap">
  <div class="marquee-row row-a">{row_a_items}{row_a_items}</div>
  <div class="marquee-row row-b">{row_b_items}{row_b_items}</div>
</div>

<div class="hero-after">
  <div class="hero-body">
    But what happens when the user disagrees with the answer? Does the model hold its ground, or does it cave?<br>I tested four models — Llama 3.2 3B, Gemma 3 27B, Claude Sonnet 4.5, and GPT-4o — on 400 political fact checked claims to find out.
  </div>
</div>
"""

st.markdown(marquee_html, unsafe_allow_html=True)

st.divider()

# Findings header

st.header("Findings")
st.markdown(
    "Each model saw the same 400 claims under four prompt framings: a neutral question, "
    "a leading-true question, a leading-false question, and a multi-turn pushback challenge.")
st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

# Section 2: dynamic accuracy across the four prompt framings

st.markdown("##### Accuracy across the four prompt framings")
st.caption("Bars cycle automatically. Click a framing to focus on it and the cycle pauses for 5 seconds.")

accuracy_payload = json.dumps([
    {
        "name":       row["model"],
        "neutral":    row["neutral"],
        "lead_true":  row["lead_true"],
        "lead_false": row["lead_false"],
        "pushback":   row["pushback_final"],
    }
    for row in metrics["accuracy"]])

accuracy_html = r"""
<style>
  body { margin: 0; padding: 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: inherit; }

  .tabs {
    display: flex; gap: 4px; padding: 4px;
    background: rgba(128,128,128,0.10);
    border-radius: 8px; width: fit-content;
    margin: 4px 0 22px;
  }
  .tab {
    padding: 8px 16px; font-size: 13px; font-weight: 500;
    cursor: pointer; border-radius: 6px;
    color: rgba(128,128,128,1); border: none; background: transparent;
    transition: all 0.2s; font-family: inherit;
  }
  .tab.active {
    background: rgba(255,255,255,1);
    color: #111;
    box-shadow: 0 0 0 0.5px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.04);
  }
  @media (prefers-color-scheme: dark) {
    .tab.active { background: #2a2a2a; color: #fff; box-shadow: 0 0 0 0.5px rgba(255,255,255,0.15); }
  }

  .stage { position: relative; height: 272px; }
  .row-card {
    position: absolute; left: 0; right: 0; height: 58px;
    display: flex; align-items: center; gap: 14px;
    transition: top 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .row-rank {
    width: 28px; font-size: 22px; font-weight: 700;
    color: rgba(128,128,128,0.55); text-align: center;
  }
  .row-name { width: 160px; font-size: 14px; font-weight: 600; color: #111; }
  .row-track {
    flex: 1; background: rgba(128,128,128,0.15);
    height: 22px; border-radius: 5px; overflow: hidden;
  }
  .row-fill {
    height: 100%; border-radius: 5px;
    transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1), background-color 0.4s;
  }
  .row-val { width: 60px; text-align: right; font-size: 14px; font-weight: 700; color: #111; }
    body.dark-theme .row-name, body.dark-theme .row-val { color: #eee; }
</style>

<div class="tabs" id="tabs">
  <button class="tab active" data-frame="neutral">Neutral</button>
  <button class="tab" data-frame="lead_true">Lead-true</button>
  <button class="tab" data-frame="lead_false">Lead-false</button>
  <button class="tab" data-frame="pushback">Pushback</button>
</div>

<div class="stage" id="stage"></div>

<script>
function detectTheme() {
  try {
    const doc = window.parent.document;
    const candidates = [
      doc.querySelector('.stApp'),
      doc.querySelector('[data-testid="stAppViewContainer"]'),
      doc.querySelector('main'),
      doc.body,
    ];
    for (const el of candidates) {
      if (!el) continue;
      const bg = window.parent.getComputedStyle(el).backgroundColor;
      const m = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
      if (!m) continue;
      const a = m[4] !== undefined ? parseFloat(m[4]) : 1;
      if (a < 0.5) continue;
      const avg = (parseInt(m[1]) + parseInt(m[2]) + parseInt(m[3])) / 3;
      document.body.classList.toggle('dark-theme', avg < 128);
      return;
    }
  } catch (e) {}
}

detectTheme();
setInterval(detectTheme, 500);

const DATA = __DATA__;
const FRAMES = ['neutral', 'lead_true', 'lead_false', 'pushback'];

function accColor(v) {
  if (v >= 55) return '#22C55E';
  if (v >= 30) return '#F59E0B';
  return '#EF4444';}

const stage = document.getElementById('stage');

function render(frame) {
  const sorted = [...DATA].sort((a, b) => b[frame] - a[frame]);
  sorted.forEach((d, i) => {
    let card = stage.querySelector('[data-model="' + CSS.escape(d.name) + '"]');
    if (!card) {
      card = document.createElement('div');
      card.className = 'row-card';
      card.dataset.model = d.name;
      card.innerHTML =
        '<div class="row-rank"></div>' +
        '<div class="row-name">' + d.name + '</div>' +
        '<div class="row-track"><div class="row-fill"></div></div>' +
        '<div class="row-val"></div>';
      stage.appendChild(card);
    }
    card.style.top = (i * 68) + 'px';
    card.querySelector('.row-rank').textContent = i + 1;
    const fill = card.querySelector('.row-fill');
    fill.style.width = d[frame] + '%';
    fill.style.background = accColor(d[frame]);
    card.querySelector('.row-val').textContent = d[frame].toFixed(1) + '%';
  });
}

function setActive(frame) {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.frame === frame);
  });
  render(frame);
}

let cycleIdx = 0;
let pausedUntil = 0;

setActive(FRAMES[cycleIdx]);

setInterval(() => {
  if (Date.now() < pausedUntil) return;
  cycleIdx = (cycleIdx + 1) % FRAMES.length;
  setActive(FRAMES[cycleIdx]);
}, 2900);

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    cycleIdx = FRAMES.indexOf(tab.dataset.frame);
    pausedUntil = Date.now() + 5000;
    setActive(tab.dataset.frame);
  });
});
</script>
""".replace("__DATA__", accuracy_payload)

st.iframe(
    src="data:text/html;base64," + base64.b64encode(accuracy_html.encode()).decode(),
    height=380,)

st.divider()

# Section 3: EIR

st.markdown("##### Pushback Error Introduction Rate (EIR) per model")

eir_lookup = {row["model"]: row["eir"] for row in metrics["eir"]}

bar_html = '<div style="margin:14px 0 8px;">'
for model in MODELS:
    eir = eir_lookup[model]
    if eir < 20:
        bar_color = "#22C55E"
    elif eir < 50:
        bar_color = "#F59E0B"
    else:
        bar_color = "#EF4444"
    bar_html += (
        f'<div style="margin-bottom:14px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">'
        f'<span style="font-size:15px; font-weight:600;">{model}</span>'
        f'<span style="font-size:18px; font-weight:700;">{eir}%</span>'
        f'</div>'
        f'<div style="background:rgba(128,128,128,0.15); height:14px; border-radius:7px; overflow:hidden;">'
        f'<div style="background:{bar_color}; height:100%; width:{eir}%; border-radius:7px;"></div>'
        f'</div>'
        f'</div>'
    )
bar_html += '</div>'
st.markdown(bar_html, unsafe_allow_html=True)

st.divider()


# Section 4: test a claim

st.subheader("Test a Claim")
st.markdown("###### Pick a claim and see how each model answered across the four prompt framings.")

claims = (
    df[df["model"] == MODELS[0]][["claim_index", "statement", "ground_truth"]]
    .reset_index(drop=True))

ctrl_col, view_col = st.columns([1, 3])

with ctrl_col:
    search = st.text_input("Search keywords", placeholder="e.g. vaccine, Obama")

    if search:
        filtered = claims[
            claims["statement"].str.contains(search, case=False, na=False, regex=False)
        ]
        if len(filtered) == 0:
            st.warning(f"No claims match '{search}'. Showing all claims.")
            filtered = claims
    else:
        filtered = claims

    options = filtered["claim_index"].tolist()
    labels = {
        idx: (stmt[:80] + "…") if len(stmt) > 80 else stmt
        for idx, stmt in zip(filtered["claim_index"], filtered["statement"])
    }

    if st.session_state.selected_claim not in options:
        st.session_state.selected_claim = options[0]

    selected = st.selectbox(
        "Claim",
        options=options,
        format_func=lambda i: labels[i],
        index=options.index(st.session_state.selected_claim),
    )
    st.session_state.selected_claim = selected

    if st.button("Random claim", use_container_width=True):
        st.session_state.selected_claim = random.randrange(len(claims))
        st.rerun()

with view_col:
    idx = st.session_state.selected_claim
    claim_row = claims[claims["claim_index"] == idx].iloc[0]
    statement = claim_row["statement"]
    ground_truth = claim_row["ground_truth"]
    gt_binary = truth(ground_truth)

    verdict_palettes = {
        "true":        ("#EAF3DE", "#27500A", "#22C55E"),
        "mostly-true": ("#EAF3DE", "#27500A", "#22C55E"),
        "false":       ("#FCEBEB", "#791F1F", "#EF4444"),
        "pants-fire":  ("#FCEBEB", "#791F1F", "#EF4444"),
    }
    v_bg, v_fg, v_border = verdict_palettes.get(ground_truth.lower(), ("#F1EFE8", "#444441", "#888888"))
    st.markdown(
        f'<div style="background: rgba(128,128,128,0.08); '
        f'border-left: 5px solid {v_border}; '
        f'padding: 14px 18px; border-radius: 8px; margin: 8px 0 20px;">'
        f'<div style="margin-bottom:12px;">'
        f'<div style="font-size:13px; letter-spacing:0.4px; text-transform:uppercase; margin-bottom:6px; font-weight:600;">PolitiFact rating</div>'
        f'<span style="background:{v_bg}; color:{v_fg}; padding:6px 14px; '
        f'border-radius:5px; font-size:15px; font-weight:700; letter-spacing:0.4px;">'
        f'{ground_truth.upper()}</span>'
        f'</div>'
        f'<div style="font-size:17px; font-weight:500; line-height:1.45;">'
        f'{statement}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Dynamic commentary on what each model did with this claim.
    model_outcomes = []
    for model in MODELS:
        model_row = df[(df["model"] == model) & (df["claim_index"] == idx)].iloc[0]
        n_correct = (model_row["neutral_verdict"] == gt_binary)
        p_correct = (model_row["pushback_final_verdict"] == gt_binary)
        model_outcomes.append({
            "model": model,
            "neutral_correct": n_correct,
            "pushback_correct": p_correct,
        })

    n_correct_at_neutral = sum(1 for o in model_outcomes if o["neutral_correct"])
    held = [o["model"] for o in model_outcomes if o["neutral_correct"] and o["pushback_correct"]]
    flipped = [o["model"] for o in model_outcomes if o["neutral_correct"] and not o["pushback_correct"]]
    correct_models = [o["model"] for o in model_outcomes if o["neutral_correct"]]

    has_delta = len(flipped) > 0

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="Correct at neutral", value=f"{n_correct_at_neutral} of 4")
        if has_delta:
            st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
        if correct_models:
            chips = "".join(chip(m, "green") for m in correct_models)
        else:
            chips = chip("None", "neutral")
        st.markdown(f'<div style="margin-top:-4px;">{chips}</div>', unsafe_allow_html=True)

    with m2:
        if n_correct_at_neutral == 0:
            st.metric(label="Held firm under pushback", value="—")
            st.markdown(f'<div style="margin-top:-4px;">{chip("—", "neutral")}</div>', unsafe_allow_html=True)
        else:
            n_flipped = n_correct_at_neutral - len(held)
            if n_flipped > 0:
                st.metric(
                    label="Held firm under pushback",
                    value=f"{len(held)} of {n_correct_at_neutral}",
                    delta=f"-{n_flipped} flipped",
                    delta_color="normal",
                )
            else:
                st.metric(
                    label="Held firm under pushback",
                    value=f"{len(held)} of {n_correct_at_neutral}",
                )
            chips = []
            for m_name in correct_models:
                chips.append(chip(m_name, "green" if m_name in held else "red"))
            st.markdown(f'<div style="margin-top:-4px;">{"".join(chips)}</div>', unsafe_allow_html=True)

    def mark(val):
        if val in ("UNCERTAIN", "UNPARSED"):
            return f"– {val}"
        return f"✓ {val}" if val == gt_binary else f"✗ {val}"

    st.markdown('<div style="height: 22px;"></div>', unsafe_allow_html=True)

    def cell_style(val):
        if val.startswith("✓"):
            return "#EAF3DE", "#27500A"
        if val.startswith("✗"):
            return "#FCEBEB", "#791F1F"
        return "#F1EFE8", "#444441"

    table_html = (
        '<div style="overflow-x:auto; margin-bottom:8px;">'
        '<table style="width:100%; border-collapse:separate; border-spacing:0; '
        'font-size:16px; border-radius:8px; overflow:hidden;">'
        '<thead>'
        '<tr style="background:rgba(128,128,128,0.12);">'
    )
    for col_label in ["Model", "Neutral", "Lead True", "Lead False", "Pushback"]:
        table_html += (
            f'<th style="text-align:left; padding:14px 18px; '
            f'font-weight:600; font-size:14px; letter-spacing:0.3px;">{col_label}</th>'
        )
    table_html += "</tr></thead><tbody>"

    framings_for_table = ["neutral", "lead_true", "lead_false", "pushback_final"]
    for model in MODELS:
        model_row = df[(df["model"] == model) & (df["claim_index"] == idx)].iloc[0]
        table_html += '<tr>'
        table_html += (
            f'<td style="padding:14px 18px; font-weight:600; font-size:15px; '
            f'border-top:1px solid rgba(128,128,128,0.15);">{model}</td>'
        )
        for framing in framings_for_table:
            val = mark(model_row[f"{framing}_verdict"])
            bg, fg = cell_style(val)
            table_html += (
                f'<td style="padding:14px 18px; background:{bg}; color:{fg}; '
                f'font-weight:600; font-size:15px; border-top:1px solid rgba(128,128,128,0.15);">'
                f'{val}</td>'
            )
        table_html += "</tr>"
    table_html += "</tbody></table></div>"

    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size: 13px; margin: 8px 0 10px;">'
        '<span style="background: #EAF3DE; color: #27500A; padding: 3px 10px; border-radius: 4px; margin-right: 6px;">✓ correct</span>'
        '<span style="background: #FCEBEB; color: #791F1F; padding: 3px 10px; border-radius: 4px; margin-right: 6px;">✗ wrong</span>'
        '<span style="background: #F1EFE8; color: #444441; padding: 3px 10px; border-radius: 4px; margin-right: 6px;">– uncertain or unparsed</span>'
        '<span style="color: inherit; font-size: 15.5px; font-weight: 650;">(compared to PolitiFact verdict)</span>'
        '</div>',
        unsafe_allow_html=True,
    )

st.divider()

# Section 5: sycophancy signatures

st.subheader("Four sycophancy signatures")
st.markdown(
    "###### Each model has a distinct pattern when it caves to pushback. "
)

quotes_by_model = parse_paper_quotes()

sig_verdict_palettes = {
    "true":        ("#EAF3DE", "#27500A"),
    "mostly-true": ("#EAF3DE", "#27500A"),
    "false":       ("#FCEBEB", "#791F1F"),
    "pants-fire":  ("#FCEBEB", "#791F1F"),
}

tabs = st.tabs(MODELS)
for tab, model in zip(tabs, MODELS):
    with tab:
        sig = SIGNATURES[model]

        st.markdown(f"#### {sig['headline']}")
        st.markdown(sig["description"])
        st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
        st.markdown("###### Illustrative cases")

        for entry in quotes_by_model.get(model, []):
            gt = entry["ground_truth"]
            gt_b = truth(gt)
            n_verdict = entry["neutral"]
            f_verdict = entry["pushback"]
            response = signature_response(entry["response"])
            claim = entry["claim"]

            v_bg, v_fg = sig_verdict_palettes.get(gt.lower(), ("#F1EFE8", "#444441"))

            def chip_color(v):
                if v == gt_b:
                    return "#EAF3DE", "#27500A"
                if v in ("UNCERTAIN", "UNPARSED"):
                    return "#F1EFE8", "#444441"
                return "#FCEBEB", "#791F1F"

            n_bg, n_fg = chip_color(n_verdict)
            f_bg, f_fg = chip_color(f_verdict)

            response_html = response.replace("\n\n", "<br><br>").replace("\n", "<br>")

            card_html = (
                '<div style="background:rgba(128,128,128,0.06); border-radius:8px; '
                'padding:16px 20px; margin-bottom:16px;">'
                '<div style="margin-bottom:10px;">'
                '<span style="color:#888; font-size:11px; text-transform:uppercase; letter-spacing:0.4px; margin-right:8px;">PolitiFact</span>'
                f'<span style="background:{v_bg}; color:{v_fg}; padding:3px 10px; '
                f'border-radius:4px; font-size:12px; font-weight:700; letter-spacing:0.3px;">'
                f'{gt.upper()}</span>'
                '</div>'
                f'<div style="font-size:15px; font-weight:500; line-height:1.45; margin-bottom:14px;">{claim}</div>'
                '<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap;">'
                '<span style="color:#888; font-size:11px; text-transform:uppercase; letter-spacing:0.4px;">Neutral</span>'
                f'<span style="background:{n_bg}; color:{n_fg}; padding:3px 10px; '
                f'border-radius:4px; font-size:12px; font-weight:600;">{n_verdict}</span>'
                '<span style="color:#888; font-size:14px;">→</span>'
                '<span style="color:#888; font-size:11px; text-transform:uppercase; letter-spacing:0.4px;">Pushback</span>'
                f'<span style="background:{f_bg}; color:{f_fg}; padding:3px 10px; '
                f'border-radius:4px; font-size:12px; font-weight:600;">{f_verdict}</span>'
                '</div>'
            )
            if response_html:
                card_html += (
                    '<div style="font-size:14px; line-height:1.55; padding-left:12px; '
                    'border-left:2px solid rgba(128,128,128,0.3);">'
                    f'{response_html}'
                    '</div>'
                )
            card_html += '</div>'

            st.markdown(card_html, unsafe_allow_html=True)
