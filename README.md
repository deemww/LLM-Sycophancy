# Sycophancy Across LLMs
DIGS 20006 · Spring 2026 · Deem Alothaimeen

**Live site:** https://sycophancy-across-llms.streamlit.app/

> **Note:** Best viewed in light mode.

**Paper:** https://docs.google.com/document/d/10xe5A61gzaufyoVrCr6kvBQmpxXXEU7OZ73JJknNAy0/edit?usp=sharing

---

## Overview

This project tests whether large language models cave to user pushback when fact-checking political claims, and whether the severity of that sycophancy varies across model size and lab. Four LLMs (Llama 3.2 3B, Gemma 3 27B, Claude Sonnet 4.5, GPT-4o) were tested on 400 PolitiFact claims under four prompt framings.

## Repo structure

```
.
├── streamlit_app.py            # interactive demo site
├── final_analysis.ipynb        # generates metrics, charts, and quotes
├── requirements.txt
├── DIGS Project Final Paper.pdf
├── Data/
│   ├── politifact_factcheck_data.json   # source dataset
│   └── claims_sample.jsonl              # sampled 400 claims
├── Experiments/
│   ├── llama_experiment.ipynb
│   ├── gemma_experiment.ipynb
│   ├── claude_experiment.ipynb
│   └── gpt_experiment.ipynb
├── Results/
│   ├── llama_results.jsonl
│   ├── gemma_results.jsonl
│   ├── claude_results.jsonl
│   ├── gpt_results.jsonl
│   ├── metrics_summary.json
│   └── paper_quotes.txt
├── Figures/
│   ├── chart_eir.png
│   ├── chart_accuracy.png
│   └── chart_accuracy_by_direction.png
└── gallery/
    └── grok_01.png … grok_16.png       # screenshots used in the demo site
```

## Run locally

```bash
git clone https://github.com/deemww/LLM-Sycophancy.git
cd LLM-Sycophancy
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Re-running the analysis

Open `final_analysis.ipynb` in Jupyter and run all cells. It reads the four `Results/*_results.jsonl` files and regenerates `metrics_summary.json`, `paper_quotes.txt`, and the charts in `Figures/`.

## Re-running the experiments

The experiment notebooks in `Experiments/` require API keys for their respective providers. Set the appropriate environment variables (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`) before running, and have Ollama running locally for the Llama notebook.
