"""UI Streamlit - IJAH Analytics: AI Experiment Prioritization (prototype)."""
import os, sqlite3, datetime
import pandas as pd
import altair as alt
import streamlit as st
from prioritizer import (get_model, reference_data, COMPONENTS, DISCLAIMER, CLUSTER_ADVICE,
                         THRESH_HIGH, THRESH_MID)

st.set_page_config(page_title="IJAH Analytics", page_icon="🌿", layout="wide")

# ---------- palet & teks ----------
LABEL_COLOR = {"Tinggi": "#2E7D32", "Sedang": "#F9A825", "Rendah": "#C62828"}
CLUSTER_COLOR = {"Kandidat mapan": "#2E7D32", "Eksplorasi baru": "#1976D2",
                 "Potensi kombinasi": "#7B1FA2", "Prioritas rendah": "#757575"}
CLUSTER_ICON = {"Kandidat mapan": "✅", "Eksplorasi baru": "🧭", "Potensi kombinasi": "🔗", "Prioritas rendah": "⏸️"}
COMP_COLOR = {"confidence": "#1976D2", "evidence": "#2E7D32", "novelty": "#F57C00", "synergy": "#7B1FA2"}
COMP_NAME = {"confidence": "Confidence", "evidence": "Evidence", "novelty": "Novelty", "synergy": "Synergy"}
COMP_DESC = {"confidence": "Seberapa yakin model bahwa senyawa ini berinteraksi dengan protein target",
             "evidence": "Berapa banyak sumber data yang mendukung hubungan ini",
             "novelty": "Seberapa baru atau belum banyak diteliti",
             "synergy": "Potensi bekerja baik jika dikombinasikan dengan senyawa lain"}
MENU_ICON = {"Pencarian": "🔍  Pencarian", "Analisis": "📊  Analisis",
             "Riwayat": "🕘  Riwayat", "Bantuan": "❓  Bantuan"}
MEDAL = ["🥇", "🥈", "🥉"]

# Nama familiar (DUMMY): dipetakan ke ID sintetis supaya bisa dicari pakai nama.
# Di versi asli, kolom ini diganti nama senyawa/protein dari database IJAH.
_CN = ["Kurkumin", "Xanthorrhizol", "Gingerol", "Shogaol", "Kuersetin", "Kaempferol", "Rutin", "Apigenin",
       "Luteolin", "Andrografolid", "Berberin", "Piperin", "Eugenol", "Katekin", "Epigalokatekin", "Asam klorogenat",
       "Resveratrol", "Naringenin", "Hesperidin", "Genistein", "Asam ursolat", "Asam oleanolat", "Mangiferin",
       "Sinensetin", "Eupatorin", "Demetoksikurkumin", "Bisdemetoksikurkumin", "Zingiberen", "Sineol", "Timol",
       "Karvakrol", "Linalool", "Limonen", "Asam galat", "Asam rosmarinat", "Silimarin", "Tanin", "Saponin", "Alisin", "Kapsaisin"]
_PN = ["TNF-alpha", "IL-6", "COX-2", "NF-kB", "EGFR", "VEGFA", "TP53", "AKT1", "MAPK1", "PTGS2", "INS", "PPARG",
       "ALB", "CASP3", "BCL2", "STAT3", "SRC", "HIF1A", "ESR1", "IL-1B", "MMP9", "JUN", "CCND1", "MTOR",
       "GSK3B", "PIK3CA", "HSP90AA1", "CDK2", "ACE", "NOS3", "SOD1", "CAT", "LDLR", "HMGCR", "DPP4", "PTPN1",
       "AR", "CYP3A4", "KIT", "FGF2"]
def _v(n): return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[n]
def cname(i):
    n = int(i[1:]); return f"{_CN[n % len(_CN)]}-{_v(n // len(_CN))}"
def pname(i):
    n = int(i[1:]); return f"{_PN[n % len(_PN)]}-{_v(n // len(_PN))}"
def cdisp(i): return f"{cname(i)} ({i})"
def pdisp(i): return f"{pname(i)} ({i})"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
h1,h2,h3,h4,p,li,label,.hero,.mcard,.pcard,.step,.tip,.brand,.brand-sub{font-family:'Poppins',sans-serif;}
.stApp{background:linear-gradient(180deg,#F4FAF3 0%,#FFFFFF 40%);}
[data-testid="stToolbar"],footer,#MainMenu{display:none !important;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1.5rem;max-width:1250px;}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"]{width:320px !important;min-width:320px !important;
  background:linear-gradient(180deg,#1B5E20 0%,#2E7D32 55%,#43A047 100%);}
section[data-testid="stSidebar"] *{color:#FFFFFF;}
section[data-testid="stSidebar"] .brand{font-size:2rem;font-weight:800;line-height:1.1;margin:8px 0 2px 0;}
section[data-testid="stSidebar"] .brand-sub{font-size:.95rem;opacity:.9;margin-bottom:22px;}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:10px;}
section[data-testid="stSidebar"] div[data-testid="stRadioGroup"], section[data-testid="stSidebar"] div[data-testid="stRadioGroup"] > div, section[data-testid="stSidebar"] div[data-testid="stRadio"]{width:100% !important;}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"],
section[data-testid="stSidebar"] div[role="radiogroup"] > label{
  padding:16px 20px;border-radius:12px;width:100%;box-sizing:border-box;display:flex;
  background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.30);transition:all .15s;cursor:pointer;}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover,
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{background:rgba(255,255,255,.25);transform:translateX(3px);}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child,
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child{display:none;}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] p,
section[data-testid="stSidebar"] div[role="radiogroup"] > label p{font-size:1.2rem !important;font-weight:700;margin:0;}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:has(input:checked),
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){
  background:#FFFFFF;border-color:#FFFFFF;box-shadow:0 3px 10px rgba(0,0,0,.30);}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:has(input:checked) p,
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p{color:#1B5E20 !important;}
.tip{background:rgba(255,255,255,.14);border:1px dashed rgba(255,255,255,.5);border-radius:12px;
  padding:12px 14px;font-size:.88rem;line-height:1.45;margin-top:10px;}

/* ===== Hero ===== */
.hero{position:relative;overflow:hidden;background:linear-gradient(120deg,#1B5E20 0%,#2E7D32 50%,#66BB6A 100%);
  color:#fff;border-radius:20px;padding:26px 32px;margin-bottom:16px;box-shadow:0 8px 22px rgba(27,94,32,.28);}
.hero:after{content:"🌿";position:absolute;right:26px;top:-6px;font-size:7rem;opacity:.18;}
.hero h1{margin:0;font-size:2rem;color:#fff;padding:0;font-weight:800;}
.hero p{margin:6px 0 10px 0;opacity:.95;font-size:1.05rem;max-width:760px;}
.badge{display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.45);
  border-radius:999px;padding:3px 12px;font-size:.8rem;margin-right:8px;}

/* ===== Stepper ===== */
.steps{display:flex;gap:10px;margin:6px 0 20px 0;flex-wrap:wrap;}
.step{flex:1;min-width:150px;background:#fff;border:2px solid #D7E6D7;border-radius:14px;padding:10px 14px;
  display:flex;align-items:center;gap:10px;font-weight:600;color:#6b7c6b;}
.step .n{background:#D7E6D7;color:#4b5d4b;width:28px;height:28px;border-radius:50%;display:flex;
  align-items:center;justify-content:center;font-weight:800;flex:none;}
.step.on{border-color:#2E7D32;color:#1B5E20;box-shadow:0 3px 10px rgba(46,125,50,.2);}
.step.on .n{background:#2E7D32;color:#fff;}
.step.done .n{background:#66BB6A;color:#fff;}

/* ===== Kartu metrik ===== */
.mcard{background:#fff;border:2px solid var(--c);border-left-width:8px;border-radius:14px;padding:14px 18px;
  box-shadow:0 3px 10px rgba(0,0,0,.06);}
.mcard .l{font-size:.88rem;color:#5b6b5b;font-weight:600;}
.mcard .v{font-size:2.1rem;font-weight:800;color:var(--c);line-height:1.2;}
.mcard .s{font-size:.8rem;color:#7a887a;}

/* ===== Kartu Top 3 ===== */
.pcard{background:#fff;border:2px solid #E3EDE3;border-top:8px solid var(--c);border-radius:16px;
  padding:16px 18px;box-shadow:0 4px 14px rgba(0,0,0,.07);height:100%;transition:all .15s;}
.pcard:hover{transform:translateY(-4px);box-shadow:0 10px 22px rgba(0,0,0,.12);}
.pcard .top{display:flex;justify-content:space-between;align-items:center;}
.pcard .medal{font-size:2rem;}
.pcard .ids{font-weight:800;font-size:1.15rem;color:#1F2D1F;margin:4px 0;}
.pcard .score{font-size:2.4rem;font-weight:800;color:var(--c);line-height:1;}
.pcard .score small{font-size:.8rem;color:#7a887a;font-weight:600;}
.pcard .why{font-size:.88rem;color:#4b5d4b;margin-top:10px;line-height:1.45;}

/* ===== Bar & pill ===== */
.bar-row{margin:12px 0 16px 0;}
.bar-head{display:flex;justify-content:space-between;font-weight:700;font-size:.98rem;}
.bar-desc{font-size:.8rem;color:#7a887a;margin-top:-1px;}
.bar-bg{background:#E3E8E3;border-radius:8px;height:14px;overflow:hidden;margin-top:5px;}
.bar-fg{height:100%;border-radius:8px;}
.pill{display:inline-block;color:#fff;padding:4px 14px;border-radius:999px;font-weight:700;font-size:.9rem;margin:2px 4px 2px 0;}
.advice{border-left:6px solid var(--c);background:#fff;border-radius:10px;padding:12px 16px;
  box-shadow:0 2px 8px rgba(0,0,0,.05);margin-top:8px;}

div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px;background:#fff;}
h2,h3{color:#1B5E20;font-weight:700;}
button[kind="primary"]{border-radius:12px;font-weight:700;padding:.6rem 1.4rem;}
button[kind="secondary"]{border-radius:12px;}
</style>
""", unsafe_allow_html=True)


# ---------- komponen tampilan ----------
def hero(title, sub):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{sub}</p>'
                f'<span class="badge">🧪 Data sintetis (prototype)</span>'
                f'<span class="badge">🔬 Bukan pengganti uji laboratorium</span></div>', unsafe_allow_html=True)


def stepper(active):
    names = ["Pilih kandidat", "Lihat ranking", "Pahami alasan", "Ambil keputusan"]
    html = '<div class="steps">'
    for i, n in enumerate(names, 1):
        cls = "on" if i == active else ("done" if i < active else "")
        html += f'<div class="step {cls}"><span class="n">{"✓" if i < active else i}</span>{n}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def mcard(label, value, color, sub=""):
    st.markdown(f'<div class="mcard" style="--c:{color}"><div class="l">{label}</div>'
                f'<div class="v">{value}</div><div class="s">{sub}</div></div>', unsafe_allow_html=True)


def bar(key, value):
    st.markdown(f'<div class="bar-row"><div class="bar-head"><span>{COMP_NAME[key]}</span><span>{value:.2f}</span></div>'
                f'<div class="bar-desc">{COMP_DESC[key]}</div>'
                f'<div class="bar-bg"><div class="bar-fg" style="width:{value*100:.0f}%;background:{COMP_COLOR[key]}"></div></div></div>',
                unsafe_allow_html=True)


def pill(text, color):
    return f'<span class="pill" style="background:{color}">{text}</span>'


def podium(r, i):
    c = LABEL_COLOR[r["priority_label"]]
    st.markdown(
        f'<div class="pcard" style="--c:{c}"><div class="top"><span class="medal">{MEDAL[i]}</span>'
        f'{pill(r["priority_label"], c)}</div>'
        f'<div class="ids">{cname(r["compound_id"])} ➜ {pname(r["protein_id"])}</div>'
        f'<div style="font-size:.78rem;color:#7a887a">{r["compound_id"]} ➜ {r["protein_id"]}</div>'
        f'<div class="score">{r["priority_score"]:.2f} <small>skor prioritas</small></div>'
        f'<div style="margin-top:8px">{CLUSTER_ICON[r["cluster_label"]]} {pill(r["cluster_label"], CLUSTER_COLOR[r["cluster_label"]])}</div>'
        f'<div class="why">{r["explanation"]}</div></div>', unsafe_allow_html=True)


def score_explainer():
    """Penjelasan rumus skor (dipakai di tab Detail dan menu Bantuan)."""
    st.markdown("**Rumus skor prioritas**")
    st.latex(r"\text{Skor}(i)=0{,}4\,C(i)+0{,}2\,E(i)+0{,}2\,N(i)+0{,}2\,S(i)")
    st.markdown(
        "- **C (Confidence)**: skor prediksi interaksi dari model BLM-NII, sudah berskala 0 sampai 1.\n"
        "- **E (Evidence)**: min(1, jumlah sumber ÷ 7). Makin banyak sumber, makin kuat buktinya.\n"
        "- **N (Novelty)**: 1 ÷ (1 + jumlah interaksi tercatat). Makin sedikit diteliti, makin tinggi.\n"
        "- **S (Synergy)**: skor potensi kombinasi multikomponen dari NIMS, berskala 0 sampai 1.\n\n"
        "Semua komponen berskala 0 sampai 1, lalu dijumlah dengan bobot di atas dan diurutkan dari skor tertinggi.")
    st.markdown("**Kenapa ada Novelty?**")
    st.write("Model prediksi cenderung yakin pada senyawa dan protein yang sudah banyak diteliti, karena datanya banyak. "
             "Tanpa novelty, ranking akan dipenuhi interaksi yang sudah diketahui sehingga eksperimen jarang menghasilkan temuan baru. "
             "Novelty menaikkan peringkat kandidat yang menjanjikan tetapi belum banyak disentuh. "
             "Bobotnya dibatasi 20% supaya kandidat dengan bukti minim tidak mendominasi, dan Confidence tetap yang terbesar (40%).")
    st.caption("Bobot dan batas label (Tinggi ≥ 0,52; Sedang 0,34 sampai 0,51; Rendah < 0,34) masih ditentukan manual di versi prototype.")


# ---------- penyimpanan riwayat (SQLite) ----------
DB = os.path.join(os.path.dirname(__file__), "history.db")
def db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS history(ts TEXT, keyword TEXT, n INTEGER, top_pair TEXT)")
    return con

@st.cache_resource
def model():
    return get_model()

@st.cache_data
def pool():
    d = reference_data()
    d["compound_name"] = d["compound_id"].map(cname)
    d["protein_name"] = d["protein_id"].map(pname)
    return d

def run_model(df, top_k):
    url = os.environ.get("IJAH_API_URL")           # opsional: pakai API FastAPI terpisah
    if url:
        import httpx
        body = {"top_k": top_k, "candidates": df[["compound_id", "protein_id", "confidence_score",
                "source_count", "interaction_count", "nims_synergy_score"]].to_dict(orient="records")}
        r = httpx.post(f"{url}/api/v1/prioritize", json=body, timeout=30).json()["results"]
        out = pd.DataFrame([{**{k: x[k] for k in ("rank", "compound_id", "protein_id", "priority_score",
              "priority_label", "cluster_label", "explanation")}, **x["components"]} for x in r])
        out["cluster_advice"] = out["cluster_label"].map(CLUSTER_ADVICE)
        return out
    return model().run(df, top_k=top_k)


# ---------- navigasi ----------
st.session_state.setdefault("menu", "Pencarian")
st.session_state.setdefault("kw", "")

def go(page, **state):
    st.session_state.update(state)
    st.session_state["menu"] = page

st.sidebar.markdown('<div class="brand">🌿 IJAH<br>Analytics</div>'
                    '<div class="brand-sub">AI Experiment Prioritization</div>', unsafe_allow_html=True)
menu = st.sidebar.radio("Menu", list(MENU_ICON), format_func=MENU_ICON.get, key="menu", label_visibility="collapsed")
st.sidebar.markdown('<div class="tip">💡 <b>Cara cepat:</b> buka <b>Pencarian</b>, tekan '
                    '<b>Mulai cepat</b>, lalu lihat hasilnya di <b>Analisis</b>.<br><br>'
                    '❓ Bingung istilahnya? Buka menu <b>Bantuan</b>.</div>', unsafe_allow_html=True)

# ================= PENCARIAN =================
if menu == "Pencarian":
    hero("Mau uji senyawa yang mana dulu?",
         "IJAH Analytics membantu peneliti jamu memilih pasangan senyawa-protein yang paling layak diuji lebih dulu di laboratorium.")
    stepper(1)

    with st.container(border=True):
        st.markdown("### 🚀 Mulai cepat")
        st.write("Belum punya kandidat tertentu? Langsung analisis **semua kandidat** tanpa perlu mengetik apa pun.")
        st.button("🚀 Analisis semua kandidat sekarang", type="primary", on_click=go,
                  args=("Analisis",), kwargs={"candidates": pool().copy(), "keyword": ""})

    st.write("")
    st.markdown("### 🔍 Atau cari kandidat tertentu")
    st.caption("Ketik nama senyawa atau protein yang kamu kenal (mis. kurkumin, COX-2). ID seperti C0083 juga bisa. Atau klik salah satu contoh.")
    kw = st.text_input("Nama senyawa atau protein", key="kw", placeholder="mis. kurkumin, gingerol, COX-2, TNF-alpha",
                       label_visibility="collapsed")
    ex = st.columns([1.3, 1.3, 1.3, 1.3, 2])
    for col, e in zip(ex, ["Kurkumin", "Gingerol", "COX-2", "TNF-alpha"]):
        col.button(f"Coba {e}", width="stretch", key=f"ex_{e}", on_click=lambda v=e: st.session_state.update(kw=v))

    df = pool()
    if kw.strip():
        k = kw.strip().lower()
        df = df[df["compound_id"].str.lower().str.contains(k) | df["protein_id"].str.lower().str.contains(k)
                | df["compound_name"].str.lower().str.contains(k, regex=False)
                | df["protein_name"].str.lower().str.contains(k, regex=False)]
    c1, c2, c3 = st.columns(3)
    with c1: mcard("Kandidat ditemukan", len(df), "#1976D2", "pasangan senyawa-protein")
    with c2: mcard("Rata-rata confidence", f"{df['confidence_score'].mean():.2f}" if len(df) else "-", "#2E7D32", "keyakinan model")
    with c3: mcard("Rata-rata sinergi", f"{df['nims_synergy_score'].mean():.2f}" if len(df) else "-", "#7B1FA2", "potensi kombinasi")
    st.write("")
    if df.empty:
        st.warning("😕 Tidak ada kandidat yang cocok. Coba ID lain atau hapus kata kunci.")
    else:
        with st.container(border=True):
            st.dataframe(df[["compound_name", "protein_name", "compound_id", "protein_id", "confidence_score", "source_count",
                             "interaction_count", "nims_synergy_score"]].round(3),
                         width='stretch', height=320, hide_index=True,
                         column_config={"compound_name": "Senyawa", "protein_name": "Protein", "compound_id": "ID senyawa", "protein_id": "ID protein",
                                        "confidence_score": "Confidence", "source_count": "Jumlah sumber",
                                        "interaction_count": "Interaksi tercatat", "nims_synergy_score": "Sinergi"})
    st.button("Lanjut ke Analisis ➜", type="primary", disabled=df.empty, key="go2", on_click=go,
              args=("Analisis",), kwargs={"candidates": df.copy(), "keyword": kw.strip()})

# ================= ANALISIS =================
elif menu == "Analisis":
    cand = st.session_state.get("candidates", pool())
    kw = st.session_state.get("keyword", "")
    hero("Hasil prioritas eksperimen",
         f"Menganalisis {len(cand)} kandidat" + (f" untuk pencarian “{kw}”" if kw else "") +
         ". Makin tinggi skornya, makin layak diuji lebih dulu.")
    stepper(3)

    top_k = st.slider("Berapa kandidat teratas yang ingin ditampilkan?", 5, 50, 10,
                      help="Geser untuk menambah atau mengurangi jumlah kandidat di daftar ranking.")
    full = run_model(cand, len(cand))
    full["compound_name"] = full["compound_id"].map(cname)
    full["protein_name"] = full["protein_id"].map(pname)
    res = full.head(top_k).reset_index(drop=True)

    if st.session_state.get("logged") != (kw, len(cand), top_k):      # catat riwayat sekali per kombinasi
        con = db()
        con.execute("INSERT INTO history VALUES (?,?,?,?)", (datetime.datetime.now().isoformat(timespec="seconds"),
                    kw or "(semua)", len(cand), f"{res.loc[0,'compound_id']}-{res.loc[0,'protein_id']}"))
        con.commit(); con.close()
        st.session_state["logged"] = (kw, len(cand), top_k)

    n_high = int((full["priority_label"] == "Tinggi").sum())
    n_map = int((full["cluster_label"] == "Kandidat mapan").sum())
    c1, c2, c3, c4 = st.columns(4)
    with c1: mcard("Kandidat dianalisis", len(full), "#1976D2", "pasangan senyawa-protein")
    with c2: mcard("Prioritas Tinggi", n_high, "#2E7D32", "layak diuji lebih dulu")
    with c3: mcard("Skor tertinggi", f"{full.loc[0,'priority_score']:.2f}", "#F57C00", "dari skala 0 sampai 1")
    with c4: mcard("Kandidat mapan", n_map, "#7B1FA2", "bukti dan confidence kuat")

    st.write("")
    st.markdown("### 🏆 Top 3 rekomendasi")
    cols = st.columns(3)
    for i in range(min(3, len(res))):
        with cols[i]:
            podium(res.iloc[i], i)

    st.write("")
    t1, t2, t3 = st.tabs(["📋  Daftar ranking", "🔬  Detail & alasan", "📈  Peta kandidat"])

    # ---- tab 1: ranking ----
    with t1:
        show = res[["rank", "compound_id", "protein_id", "priority_score", "priority_label", "cluster_label"]].copy()
        show.insert(1, "compound_name", show["compound_id"].map(cname))
        show.insert(2, "protein_name", show["protein_id"].map(pname))
        styled = (show.style
                  .map(lambda v: f"background-color:{LABEL_COLOR[v]};color:white;font-weight:700" if v in LABEL_COLOR else "",
                       subset=["priority_label"])
                  .map(lambda v: f"color:{CLUSTER_COLOR[v]};font-weight:700" if v in CLUSTER_COLOR else "",
                       subset=["cluster_label"]))
        st.dataframe(styled, width='stretch', hide_index=True, height=min(520, 40 + 35 * len(show)),
                     column_config={"rank": st.column_config.NumberColumn("Peringkat", width="small"),
                                    "compound_name": "Senyawa", "protein_name": "Protein",
                                    "compound_id": "ID senyawa", "protein_id": "ID protein",
                                    "priority_score": st.column_config.ProgressColumn(
                                        "Skor prioritas", min_value=0, max_value=1, format="%.2f"),
                                    "priority_label": "Prioritas", "cluster_label": "Tipe kandidat"})
        st.download_button("⬇️ Unduh hasil (CSV)", res.to_csv(index=False).encode(),
                           "hasil_prioritisasi.csv", "text/csv", type="primary")
        with st.expander("ℹ️ Cara membaca label prioritas"):
            st.markdown(f"- {pill('Tinggi', LABEL_COLOR['Tinggi'])} skor ≥ {THRESH_HIGH:.2f} → layak diuji lebih dulu\n"
                        f"- {pill('Sedang', LABEL_COLOR['Sedang'])} skor {THRESH_MID:.2f} sampai {THRESH_HIGH - 0.01:.2f} → pertimbangkan\n"
                        f"- {pill('Rendah', LABEL_COLOR['Rendah'])} skor < {THRESH_MID:.2f} → tunda", unsafe_allow_html=True)

    # ---- tab 2: detail ----
    with t2:
        pick = st.selectbox("Pilih kandidat yang ingin dilihat detailnya",
                            res.apply(lambda r: f"#{r['rank']}  {cname(r['compound_id'])} ➜ {pname(r['protein_id'])}", axis=1))
        r = res.iloc[int(pick.split()[0][1:]) - 1]
        lc, cc = LABEL_COLOR[r["priority_label"]], CLUSTER_COLOR[r["cluster_label"]]
        d1, d2 = st.columns([1, 2])
        with d1:
            with st.container(border=True):
                mcard("Skor prioritas", f"{r['priority_score']:.2f}", lc, f"{cdisp(r['compound_id'])} ➜ {pdisp(r['protein_id'])}")
                st.markdown(f"<br>Prioritas: {pill(r['priority_label'], lc)}<br>"
                            f"Tipe: {CLUSTER_ICON[r['cluster_label']]} {pill(r['cluster_label'], cc)}",
                            unsafe_allow_html=True)
        with d2:
            with st.container(border=True):
                st.markdown("**Dari mana skor ini berasal?**  \n"
                            "<span style='color:#6b7c6b;font-size:.85rem'>Bobot: Confidence 40% · Evidence 20% · Novelty 20% · Synergy 20%</span>",
                            unsafe_allow_html=True)
                for c in COMPONENTS:
                    bar(c, float(r[c]))
        st.markdown(f'<div class="advice" style="--c:{cc}"><b>💡 Saran:</b> {r["cluster_advice"]}</div>', unsafe_allow_html=True)
        st.info("🔎 **Alasan:** " + r["explanation"])
        with st.expander("🧮 Bagaimana skor ini dihitung?"):
            score_explainer()
        st.warning("⚠️ " + DISCLAIMER)

    # ---- tab 3: peta ----
    with t3:
        st.caption("Tiap titik adalah satu kandidat. Titik di pojok kanan atas = keyakinan tinggi dan masih baru diteliti. Titik besar = skor prioritas tinggi.")
        chart = (alt.Chart(full).mark_circle(opacity=.75, stroke="white", strokeWidth=1)
                 .encode(x=alt.X("novelty:Q", title="Novelty (makin kanan makin baru) →"),
                         y=alt.Y("confidence:Q", title="Confidence (makin atas makin yakin) →"),
                         color=alt.Color("cluster_label:N", title="Tipe kandidat",
                                         scale=alt.Scale(domain=list(CLUSTER_COLOR), range=list(CLUSTER_COLOR.values())),
                                         legend=alt.Legend(orient="bottom")),
                         size=alt.Size("priority_score:Q", legend=None, scale=alt.Scale(range=[30, 320])),
                         tooltip=[alt.Tooltip("compound_name:N", title="Senyawa"), alt.Tooltip("protein_name:N", title="Protein"),
                                  alt.Tooltip("priority_score:Q", title="Skor", format=".2f"),
                                  alt.Tooltip("cluster_label:N", title="Tipe")])
                 .properties(height=420).interactive())
        st.altair_chart(chart, width='stretch')
        st.markdown("#### Ringkasan tipe kandidat")
        cs = st.columns(4)
        for col, (name, cc) in zip(cs, CLUSTER_COLOR.items()):
            n = int((full["cluster_label"] == name).sum())
            with col:
                mcard(f"{CLUSTER_ICON[name]} {name}", n, cc, CLUSTER_ADVICE[name])

    # ---- langkah 4: ambil keputusan ----
    st.write("")
    st.markdown("### ✅ Ambil keputusan: kandidat mana yang diuji lebih dulu?")
    high = full[full["priority_label"] == "Tinggi"].reset_index(drop=True)
    if high.empty:
        st.info("Belum ada kandidat berprioritas Tinggi pada pencarian ini. Coba pakai kata kunci lain atau analisis semua kandidat.")
    else:
        with st.container(border=True):
            n_pick = st.slider("Berapa kandidat yang akan kamu uji di laboratorium?", 1, min(20, len(high)),
                               min(5, len(high)), key="n_pick",
                               help="Daftar uji diambil dari kandidat berprioritas Tinggi, urut dari skor tertinggi.")
            pick_df = high.head(n_pick).copy()
            k1, k2, k3 = st.columns(3)
            with k1: mcard("Kandidat dipilih", n_pick, "#2E7D32", f"dari {len(high)} berprioritas Tinggi")
            with k2: mcard("Rata-rata skor", f"{pick_df['priority_score'].mean():.2f}", "#F57C00", "skor prioritas daftar uji")
            with k3: mcard("Tipe terbanyak", pick_df["cluster_label"].mode()[0], "#7B1FA2", "di daftar uji")
            st.write("")
            out = pick_df[["rank", "compound_name", "protein_name", "compound_id", "protein_id",
                           "priority_score", "cluster_label", "cluster_advice"]]
            st.dataframe(out, width="stretch", hide_index=True,
                         height=min(420, 40 + 35 * len(out)),
                         column_config={"rank": st.column_config.NumberColumn("Peringkat", width="small"),
                                        "compound_name": "Senyawa", "protein_name": "Protein",
                                        "compound_id": "ID senyawa", "protein_id": "ID protein",
                                        "priority_score": st.column_config.ProgressColumn(
                                            "Skor prioritas", min_value=0, max_value=1, format="%.2f"),
                                        "cluster_label": "Tipe kandidat", "cluster_advice": "Saran"})
            st.download_button("⬇️ Unduh daftar uji untuk laboratorium (CSV)", out.to_csv(index=False).encode(),
                               "daftar_uji_laboratorium.csv", "text/csv", type="primary", key="dl_pick")
            st.caption("Daftar ini hanya usulan urutan uji. Keputusan akhir tetap pada peneliti, dan hasil perlu dikonfirmasi lewat uji laboratorium.")


# ================= RIWAYAT =================
elif menu == "Riwayat":
    hero("Riwayat pencarian", "Daftar analisis yang pernah kamu jalankan, supaya mudah diulang.")
    con = db()
    h = pd.read_sql("SELECT ts AS waktu, keyword AS kata_kunci, n AS jumlah_kandidat, top_pair AS kandidat_teratas "
                    "FROM history ORDER BY ts DESC LIMIT 50", con)
    con.close()
    if len(h):
        c1, c2 = st.columns(2)
        with c1: mcard("Total analisis", len(h), "#1976D2", "tercatat di riwayat")
        with c2: mcard("Terakhir", h.loc[0, "waktu"][11:16], "#2E7D32", h.loc[0, "waktu"][:10])
        st.write("")
        with st.container(border=True):
            st.dataframe(h, width='stretch', hide_index=True,
                         column_config={"waktu": "Waktu", "kata_kunci": "Kata kunci",
                                        "jumlah_kandidat": "Jumlah kandidat", "kandidat_teratas": "Kandidat teratas"})
    else:
        st.info("📭 Belum ada riwayat. Jalankan analisis pertamamu dari menu Pencarian.")
        st.button("🚀 Mulai analisis", type="primary", on_click=go, args=("Pencarian",))

# ================= BANTUAN =================
else:
    hero("Pusat bantuan", "Panduan singkat memakai IJAH Analytics dan arti istilah-istilahnya.")
    st.markdown("### 🧭 Cara memakai (3 langkah)")
    c1, c2, c3 = st.columns(3)
    with c1: mcard("1️⃣ Pilih kandidat", "Pencarian", "#1976D2", "Cari ID tertentu atau tekan Mulai cepat.")
    with c2: mcard("2️⃣ Lihat ranking", "Analisis", "#2E7D32", "Baca Top 3 dan daftar ranking lengkap.")
    with c3: mcard("3️⃣ Pahami & putuskan", "Detail", "#7B1FA2", "Cek alasan, saran, lalu unduh hasilnya.")
    st.write("")
    st.markdown("### 📖 Arti istilah")
    for c in COMPONENTS:
        st.markdown(f'<div class="advice" style="--c:{COMP_COLOR[c]}"><b>{COMP_NAME[c]}</b> — {COMP_DESC[c]}.</div>',
                    unsafe_allow_html=True)
    st.write("")
    st.markdown("### 🏷️ Arti tipe kandidat")
    for k, v in CLUSTER_ADVICE.items():
        st.markdown(f'<div class="advice" style="--c:{CLUSTER_COLOR[k]}">{CLUSTER_ICON[k]} {pill(k, CLUSTER_COLOR[k])} {v}</div>',
                    unsafe_allow_html=True)
    st.write("")
    st.markdown("### ❓ Pertanyaan umum")
    with st.expander("Apakah hasil ini pasti benar?"):
        st.write("Tidak. Ini perkiraan untuk membantu menentukan urutan uji. " + DISCLAIMER)
    with st.expander("Data apa yang dipakai?"):
        st.write("Prototype ini memakai data sintetis yang meniru struktur data IJAH. Nama senyawa dan protein (kurkumin, COX-2, dll.) "
                 "hanyalah label contoh yang dipasangkan ke ID sintetis, bukan data riwayat penelitian asli. "
                 "Data BLM-NII dan NIMS asli belum tersedia.")
    with st.expander("Bagaimana skor prioritas dihitung?", expanded=True):
        score_explainer()
