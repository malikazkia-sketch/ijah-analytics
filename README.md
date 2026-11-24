# IJAH Analytics - AI Experiment Prioritization (Prototype, Kelompok 7)

Prototype memakai **data sintetis** (meniru struktur data IJAH). Data BLM-NII dan NIMS asli belum tersedia.

## Menjalankan
```
pip install -r requirements.txt
streamlit run app.py                 # UI (model dipanggil langsung)
uvicorn api:app --port 8000          # API terpisah (opsional)
IJAH_API_URL=http://localhost:8000 streamlit run app.py   # UI memakai API
python evaluate.py                   # Average Precision 0.608, Precision@10 0.80 (sama dengan Colab)
```

## File
- `prioritizer.py` model: 4 komponen, priority score, label, K-means (K=4), penjelasan
- `api.py` POST /api/v1/prioritize (kontrak LKP P6), GET /health
- `app.py` UI Streamlit: Pencarian, Analisis, Riwayat (SQLite), Bantuan

## Catatan
- Bobot (0.4/0.2/0.2/0.2) masih manual; rencana: dipelajari dari hasil uji lab.
- Metrik PoC dihitung dari label sintetis, jadi membuktikan alur berjalan, bukan akurasi sebenarnya.
- Hasil prioritisasi tidak menggantikan validasi laboratorium (BPOM).
