"""Model AI Experiment Prioritization - IJAH Analytics (Kelompok 7).

Dipindahkan dari PoC Colab. Perbedaan dari Colab:
- source_count dinormalisasi dengan batas tetap 0-7 (bukan min-max dari data),
  supaya satu permintaan API dengan satu kandidat tidak error.
- Clustering K-means (K=4) dilatih sekali pada data referensi sintetis,
  lalu kandidat baru dimasukkan ke cluster terdekat.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

W = {"confidence": 0.4, "evidence": 0.2, "novelty": 0.2, "synergy": 0.2}
SOURCE_MAX = 7          # batas atas source_count pada data PoC (0-7)
THRESH_HIGH = 0.52      # ~20% teratas pada data PoC
THRESH_MID = 0.34
COMPONENTS = ["confidence", "evidence", "novelty", "synergy"]
MODEL_VERSION = "poc-0.2"
DISCLAIMER = "Hasil prioritisasi tidak menggantikan validasi laboratorium (BPOM)."


def reference_data(n=500, seed=42):
    """Data sintetis PoC (urutan pemanggilan random sama dengan Colab)."""
    np.random.seed(seed)
    confidence = np.random.beta(2, 2, n)
    source_count = np.random.poisson(1.5, n)
    interaction_count = np.random.exponential(3, n)
    np.random.beta(2, 3, n)   # com_similarity (tidak dipakai skor)
    np.random.beta(2, 3, n)   # pro_similarity (tidak dipakai skor)
    synergy = np.random.beta(2, 2, n)
    df = pd.DataFrame({
        "compound_id": [f"C{i:04d}" for i in range(n)],
        "protein_id": [f"P{i:04d}" for i in range(n)],
        "confidence_score": confidence,
        "source_count": source_count,
        "interaction_count": interaction_count,
        "nims_synergy_score": synergy,
    })
    return df


def components(df):
    out = pd.DataFrame(index=df.index)
    out["confidence"] = df["confidence_score"].clip(0, 1)
    out["evidence"] = (df["source_count"] / SOURCE_MAX).clip(0, 1)
    out["novelty"] = 1 / (1 + df["interaction_count"].clip(lower=0))
    out["synergy"] = df["nims_synergy_score"].clip(0, 1)
    return out


def priority_score(comp):
    return sum(W[c] * comp[c] for c in COMPONENTS)


def label(score):
    return "Tinggi" if score >= THRESH_HIGH else ("Sedang" if score >= THRESH_MID else "Rendah")


# ---------- clustering ----------
CLUSTER_ADVICE = {
    "Kandidat mapan": "Bukti dan confidence terbaik; uji lebih dulu, risiko rendah.",
    "Potensi kombinasi": "Sinergi tertinggi; cocok diuji sebagai kombinasi senyawa.",
    "Eksplorasi baru": "Novelty tinggi tetapi bukti masih tipis; uji sebagian kecil sebagai eksplorasi.",
    "Prioritas rendah": "Semua komponen lemah; tunda.",
}


def _name_clusters(centers_df):
    """Beri nama otomatis dari komponen yang paling menonjol antar-cluster."""
    names, free = {}, set(centers_df.index)
    for comp, name in [("evidence", "Kandidat mapan"), ("novelty", "Eksplorasi baru"),
                       ("synergy", "Potensi kombinasi")]:
        # ranking relatif: z-score komponen di antara pusat cluster
        z = (centers_df[comp] - centers_df[comp].mean()) / (centers_df[comp].std() + 1e-9)
        pick = max(free, key=lambda i: z[i])
        names[pick] = name
        free.discard(pick)
    for i in free:
        names[i] = "Prioritas rendah"
    return names


class Prioritizer:
    def __init__(self, k=4, seed=42):
        ref = reference_data()
        comp = components(ref)
        self.scaler = StandardScaler().fit(comp[COMPONENTS])
        self.km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(
            self.scaler.transform(comp[COMPONENTS]))
        centers = pd.DataFrame(self.scaler.inverse_transform(self.km.cluster_centers_),
                               columns=COMPONENTS)
        self.names = _name_clusters(centers)
        self.ref = ref.assign(**comp, priority_score=priority_score(comp),
                              cluster_id=self.km.labels_)
        self.ref["cluster_label"] = self.ref["cluster_id"].map(self.names)

    def explain(self, row):
        parts = []
        if row["confidence"] >= 0.7: parts.append("confidence BLM-NII tinggi")
        elif row["confidence"] < 0.4: parts.append("confidence rendah")
        if row["synergy"] >= 0.7: parts.append("potensi sinergi tinggi")
        if row["evidence"] >= 0.4: parts.append(f"didukung {int(round(row['evidence']*SOURCE_MAX))} sumber data")
        elif row["evidence"] < 0.2: parts.append("bukti pendukung masih sedikit")
        if row["novelty"] >= 0.5: parts.append("novelty tinggi (belum banyak diteliti)")
        if not parts:
            return "Semua komponen berada pada tingkat sedang."
        text = ", ".join(parts)
        return text[0].upper() + text[1:] + "."

    def run(self, candidates: pd.DataFrame, top_k=None):
        comp = components(candidates)
        score = priority_score(comp)
        cid = self.km.predict(self.scaler.transform(comp[COMPONENTS]))
        res = candidates[["compound_id", "protein_id"]].copy()
        res["priority_score"] = score.round(4)
        res["priority_label"] = score.map(label)
        for c in COMPONENTS:
            res[c] = comp[c].round(4)
        res["cluster_id"] = cid
        res["cluster_label"] = res["cluster_id"].map(self.names)
        res["cluster_advice"] = res["cluster_label"].map(CLUSTER_ADVICE)
        res["explanation"] = [self.explain(r) for _, r in comp.iterrows()]
        res = res.sort_values("priority_score", ascending=False).reset_index(drop=True)
        res.insert(0, "rank", res.index + 1)
        return res.head(top_k) if top_k else res

    def cluster_summary(self):
        g = self.ref.groupby("cluster_label")[COMPONENTS + ["priority_score"]].mean().round(2)
        g["jumlah"] = self.ref.groupby("cluster_label").size()
        return g.sort_values("priority_score", ascending=False)


_model = None
def get_model():
    global _model
    if _model is None:
        _model = Prioritizer()
    return _model
