# Experiment results (auto-generated)

- corpus: 2460 examples, train 1968, test 492
- template-holdout intent accuracy: **0.9980**

## Per-class precision / recall (holdout)

| intent | precision | recall | support |
|---|---|---|---|
| balance_query | 1.000 | 1.000 | 96 |
| bikri | 1.000 | 1.000 | 88 |
| hisaab | 0.857 | 1.000 | 6 |
| jama | 1.000 | 1.000 | 93 |
| kharcha | 1.000 | 1.000 | 99 |
| udhaar_diya | 1.000 | 1.000 | 103 |
| unknown | 1.000 | 0.857 | 7 |

## Confusion matrix (rows=true, cols=pred)

| true \ pred | balance_query | bikri | hisaab | jama | kharcha | udhaar_diya | unknown |
|---|---|---|---|---|---|---|---|
| balance_query | 96 | 0 | 0 | 0 | 0 | 0 | 0 |
| bikri | 0 | 88 | 0 | 0 | 0 | 0 | 0 |
| hisaab | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| jama | 0 | 0 | 0 | 93 | 0 | 0 | 0 |
| kharcha | 0 | 0 | 0 | 0 | 99 | 0 | 0 |
| udhaar_diya | 0 | 0 | 0 | 0 | 0 | 103 | 0 |
| unknown | 0 | 0 | 1 | 0 | 0 | 0 | 6 |

## Handwritten eval (30 sentences, written by hand, not generated)

- intent accuracy: **30/30 = 1.000**
- amount accuracy on handwritten items with amounts: **20/20 = 1.000**

## Train-size curve (holdout accuracy)

| train fraction | examples | accuracy |
|---|---|---|
| 0.10 | 196 | 0.9736 |
| 0.25 | 492 | 0.9878 |
| 0.50 | 984 | 0.9980 |
| 0.80 | 1574 | 0.9980 |
