"""Generate the two analysis notebooks (01_eda, 02_results) from code, so they
are reproducible. After building, execute them with:

    jupyter nbconvert --to notebook --execute --inplace ml/notebooks/01_eda.ipynb
    jupyter nbconvert --to notebook --execute --inplace ml/notebooks/02_results.ipynb

Run:  python ml/notebooks/_build_notebooks.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent


def md(x):
    return nbf.v4.new_markdown_cell(x)


def code(x):
    return nbf.v4.new_code_cell(x)


# --------------------------------------------------------------------------- #
EDA = [
    md("# Gaia AI — Exploratory Data Analysis\n\n"
       "Synthetic dataset of persona-conditioned WhatsApp users (hidden style seeds). "
       "We inspect class balance across style axes, message/target lengths, and pairs per user."),
    code("import json, statistics as st\n"
         "from collections import Counter\n"
         "from pathlib import Path\n"
         "import matplotlib.pyplot as plt\n"
         "ROOT = Path.cwd()\n"
         "while not (ROOT/'ml'/'data'/'synthetic').exists() and ROOT != ROOT.parent:\n"
         "    ROOT = ROOT.parent\n"
         "SYN = ROOT/'ml'/'data'/'synthetic'\n"
         "def load(n):\n"
         "    p = SYN/n\n"
         "    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()] if p.exists() else []\n"
         "personas, histories, pairs = load('personas.jsonl'), load('histories.jsonl'), load('pairs.jsonl')\n"
         "len(personas), len(histories), len(pairs)"),
    md("## 1. Dataset size"),
    code("print(f'personas : {len(personas)}')\n"
         "print(f'histories: {len(histories)}')\n"
         "print(f'pairs    : {len(pairs)}')"),
    md("## 2. Style-axis distributions (the diversity matrix)"),
    code("axes = ['language','avg_length','emoji','slang','formality','rhythm']\n"
         "counts = {a: Counter() for a in axes}\n"
         "for p in personas:\n"
         "    hs = p.get('hidden_style', {})\n"
         "    for a in axes:\n"
         "        if hs.get(a) is not None: counts[a][hs[a]] += 1\n"
         "fig, axx = plt.subplots(2, 3, figsize=(14, 7))\n"
         "for ax, a in zip(axx.ravel(), axes):\n"
         "    c = counts[a]; ax.bar(range(len(c)), list(c.values()), color='#2b6cb0')\n"
         "    ax.set_xticks(range(len(c))); ax.set_xticklabels(list(c.keys()), rotation=30, ha='right', fontsize=8)\n"
         "    ax.set_title(a, fontweight='bold')\n"
         "plt.tight_layout(); plt.show()"),
    md("## 3. Message & target-reply length distributions"),
    code("hist_lens = [len(m) for h in histories for m in h.get('messages', [])]\n"
         "tgt_lens  = [len(p.get('target_response','')) for p in pairs]\n"
         "inc_lens  = [len(p.get('incoming_message','')) for p in pairs]\n"
         "fig, ax = plt.subplots(1, 3, figsize=(15, 4))\n"
         "ax[0].hist(hist_lens, bins=20, color='#2f855a', edgecolor='white'); ax[0].set_title('history msg length (chars)')\n"
         "ax[1].hist(tgt_lens, bins=20, color='#dd6b20', edgecolor='white'); ax[1].set_title('target reply length (chars)')\n"
         "ax[2].hist(inc_lens, bins=20, color='#2b6cb0', edgecolor='white'); ax[2].set_title('incoming msg length (chars)')\n"
         "plt.tight_layout(); plt.show()\n"
         "if tgt_lens: print('target len mean/median:', round(st.mean(tgt_lens),1), st.median(tgt_lens))"),
    md("## 4. Pairs per user"),
    code("per_user = Counter(p['user_id'] for p in pairs)\n"
         "if per_user:\n"
         "    plt.figure(figsize=(7,4)); plt.hist(list(per_user.values()), bins=10, color='#6b46c1', edgecolor='white')\n"
         "    plt.title('pairs per user'); plt.xlabel('pairs'); plt.ylabel('users'); plt.show()\n"
         "    print('users with pairs:', len(per_user), '| mean pairs/user:', round(st.mean(per_user.values()),1))"),
    md("## Takeaways\n"
       "- Style axes are spread across the diversity matrix (no single dominant class).\n"
       "- Message and reply lengths skew short, matching real WhatsApp behavior.\n"
       "- Static figures + a machine-readable `results/eda_stats.json` are produced by `ml/eda/run_eda.py`."),
]

RESULTS = [
    md("# Gaia AI — Evaluation Results\n\n"
       "Reads `ml/results/eval_report.json` and renders the comparison table and figures. "
       "Headline metric: **Style-Indistinguishability** (judge accuracy → 50% = indistinguishable)."),
    code("import json\n"
         "from pathlib import Path\n"
         "import matplotlib.pyplot as plt\n"
         "ROOT = Path.cwd()\n"
         "while not (ROOT/'ml'/'results').exists() and ROOT != ROOT.parent:\n"
         "    ROOT = ROOT.parent\n"
         "rep_path = ROOT/'ml'/'results'/'eval_report.json'\n"
         "rep = json.loads(rep_path.read_text(encoding='utf-8')) if rep_path.exists() else None\n"
         "print('loaded' if rep else 'run eval.run_all first'); rep and rep.get('test_size')"),
    md("## Results table"),
    code("import pandas as pd\n"
         "if rep:\n"
         "    rows = []\n"
         "    for m, r in rep['results'].items():\n"
         "        i, s, v = r['indistinguishability'], r['style_similarity'], r['relevance']\n"
         "        rows.append({'model': m, 'indist_acc': round(i['accuracy'],3),\n"
         "                     'ci95': f\"[{i['ci95_low']:.2f},{i['ci95_high']:.2f}]\",\n"
         "                     'style_sim': round(s['mean'],3), 'relevance': round(v['mean'],2)})\n"
         "    display(pd.DataFrame(rows))"),
    md("## Indistinguishability (50% = indistinguishable = success)"),
    code("if rep:\n"
         "    models = list(rep['results'])\n"
         "    acc = [rep['results'][m]['indistinguishability']['accuracy']*100 for m in models]\n"
         "    plt.figure(figsize=(7,4)); plt.bar(models, acc, color=['#dd6b20','#2b6cb0','#2f855a'][:len(models)])\n"
         "    plt.axhline(50, ls='--', color='crimson'); plt.ylim(0,100); plt.ylabel('judge accuracy %')\n"
         "    plt.title('Style Indistinguishability'); plt.show()"),
    md("> The fine_tuned arm is added after the QLoRA GPU run (see README). Static figures are in `visuals/results/`."),
]


def main():
    for name, cells in [("01_eda", EDA), ("02_results", RESULTS)]:
        nb = nbf.v4.new_notebook()
        nb.cells = cells
        nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3"},
                       "language_info": {"name": "python"}}
        (HERE / f"{name}.ipynb").write_text(nbf.writes(nb), encoding="utf-8")
        print(f"wrote {name}.ipynb ({len(cells)} cells)")


if __name__ == "__main__":
    main()
