# File Renamer Bot (Rename + Metadata + Thumbnail + Stream Remove + Progress Bar)

## Features
- File anuppa new name kekkum, rename panni thirumba anuppum
- Custom thumbnail set panna mudiyum (`/set_thumb`)
- Custom caption template (`/set_caption`)
- Video oda audio/subtitle streams select panni **remove** panna mudiyum (ffmpeg `-map`)
- Download + Upload rendulukum live progress bar (%, speed, ETA)
- Railway la neraya deploy pannalam (Procfile + nixpacks.toml already irukku)

---

## 1. Telegram Credentials Vanguravadhu Epdi

1. **API_ID & API_HASH**: https://my.telegram.org ku poi login pannunga (unga phone number vachi) → "API Development Tools" → oru app create pannunga → `api_id` and `api_hash` kidaikum.
2. **BOT_TOKEN**: Telegram la `@BotFather` ku poi `/newbot` anuppunga → bot peru kudunga → token kidaikum.

## 2. Local la Test Pannuradhu (Optional)

```bash
git clone <your-repo-url>
cd filerenamebot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
