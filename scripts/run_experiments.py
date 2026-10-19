"""Reproducible evaluation for the bolledger NLU. Prints a Markdown report.

    python3 scripts/run_experiments.py
"""
import json
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bolledger.corpus import build_corpus, train_test_split
from bolledger.nlu import INTENT_LABELS as INTENTS
from bolledger.nlu import HinglishNLU

def per_class(nlu, test):
    labels = sorted(set(INTENTS) | {"unknown"})
    conf = {a: {b: 0 for b in labels} for a in labels}
    for text, true in test:
        pred = nlu.parse(text)["intent"]
        conf[true][pred] += 1
    return labels, conf

def main():
    corpus = build_corpus()
    train, test = train_test_split(corpus)
    nlu = HinglishNLU(); nlu.train(train)

    acc = sum(1 for t, i in test if nlu.parse(t)["intent"] == i) / len(test)
    labels, conf = per_class(nlu, test)

    print("# Experiment results (auto-generated)\n")
    print(f"- corpus: {len(corpus)} examples, train {len(train)}, test {len(test)}")
    print(f"- template-holdout intent accuracy: **{acc:.4f}**\n")

    print("## Per-class precision / recall (holdout)\n")
    print("| intent | precision | recall | support |")
    print("|---|---|---|---|")
    for lab in labels:
        tp = conf[lab][lab]
        pred_total = sum(conf[t][lab] for t in labels)
        true_total = sum(conf[lab].values())
        if true_total == 0 and pred_total == 0:
            continue
        p = tp / pred_total if pred_total else 0.0
        r = tp / true_total if true_total else 0.0
        print(f"| {lab} | {p:.3f} | {r:.3f} | {true_total} |")

    print("\n## Confusion matrix (rows=true, cols=pred)\n")
    print("| true \\ pred | " + " | ".join(labels) + " |")
    print("|" + "---|" * (len(labels) + 1))
    for a in labels:
        row = conf[a]
        if sum(row.values()) == 0:
            continue
        print(f"| {a} | " + " | ".join(str(row[b]) for b in labels) + " |")

    hw = json.load(open("data/eval_handwritten.json"))
    ok = 0
    misses = []
    for e in hw:
        got = nlu.parse(e["text"])["intent"]
        if got == e["intent"]:
            ok += 1
        else:
            misses.append((e["text"], e["intent"], got))
    print(f"\n## Handwritten eval ({len(hw)} sentences, written by hand, not generated)\n")
    print(f"- intent accuracy: **{ok}/{len(hw)} = {ok/len(hw):.3f}**")
    for text, want, got in misses:
        print(f"  - MISS: {text!r} want {want}, got {got}")

    # amount extraction accuracy on eval items that carry amounts
    amt_ok = amt_total = 0
    for e in hw:
        if "amount" in e:
            amt_total += 1
            got = nlu.parse(e["text"])["amount"]
            if got is not None and abs(got - e["amount"]) < 1e-9:
                amt_ok += 1
    if amt_total:
        print(f"- amount accuracy on handwritten items with amounts: **{amt_ok}/{amt_total} = {amt_ok/amt_total:.3f}**")

    print("\n## Train-size curve (holdout accuracy)\n")
    print("| train fraction | examples | accuracy |")
    print("|---|---|---|")
    full = build_corpus()
    for frac in (0.1, 0.25, 0.5, 0.8):
        random.Random(7).shuffle(full)
        n = max(1, int(len(full) * frac * 0.8))
        m = HinglishNLU(); m.train(full[:n])
        a = sum(1 for t, i in test if m.parse(t)["intent"] == i) / len(test)
        print(f"| {frac:.2f} | {n} | {a:.4f} |")

if __name__ == "__main__":
    main()
