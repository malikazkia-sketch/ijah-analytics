"""Evaluasi PoC (sama dengan Colab): Average Precision dan Precision@10 pada data sintetis."""
import numpy as np
from sklearn.metrics import average_precision_score
from prioritizer import reference_data, components, priority_score

df = reference_data()
comp = components(df)
score = priority_score(comp)
# ground truth sintetis, urutan random sama dengan Colab
latent = 0.5*comp["confidence"] + 0.3*comp["synergy"] + 0.2*comp["novelty"] + np.random.normal(0, 0.12, len(df))
y = (latent >= np.quantile(latent, 0.80)).astype(int)
ap = average_precision_score(y, score)
top10 = y[np.argsort(-score.values)[:10]].sum() / 10
print(f"Average Precision : {ap:.3f}")
print(f"Precision@10      : {top10:.2f}")
