# 💰 Smartspend AI

**Created by Suyash Verma**

A full-stack AI-powered Smartspend AI built with Flask + SQLite + Vanilla JS.

## Features

- ✅ Add / view / delete expenses with category, amount, date, note
- 📊 Monthly & category-wise charts
- 🤖 AI insights: top spend category, trend detection, personalised tips
- 🔎 Filter by month and category
- 📱 Responsive, dark-mode UI

---

## Project Structure

```
Smartspend AI /
├── app.py              # Flask backend (REST API + AI engine)
├── requirements.txt
├── Procfile            # For Render / Heroku
├── render.yaml         # Render deploy config
├── templates/
│   └── index.html      # Full frontend (HTML + CSS + JS)
└── expenses.db         # Auto-created SQLite database
```

---

## Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python app.py

# 3. Open browser
open http://localhost:5000
```

---

## REST API Reference

| Method | Route               | Description                                       |
| ------ | ------------------- | ------------------------------------------------- |
| GET    | `/api/expenses`     | List all (filter: `?month=YYYY-MM&category=Food`) |
| POST   | `/api/expenses`     | Add expense `{amount, category, date, note}`      |
| DELETE | `/api/expenses/:id` | Delete by ID                                      |
| GET    | `/api/summary`      | Total, this-month, count                          |
| GET    | `/api/insights`     | AI analysis, trends, suggestions                  |
| GET    | `/api/categories`   | Category list                                     |

---

## Deploy to Render (Free)

1. Push code to a GitHub repo
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. Click **Deploy** — your app is live 🎉

> **Note**: Render's free tier spins down after inactivity. For persistent SQLite, use a `/data` disk mount or swap to PostgreSQL for production.

---

## Tech Stack

| Layer    | Technology                                |
| -------- | ----------------------------------------- |
| Backend  | Python 3.11, Flask 3, Flask-CORS          |
| Database | SQLite (via Python stdlib)                |
| Frontend | HTML5, CSS3 (CSS Variables), Vanilla JS   |
| Charts   | Chart.js 4                                |
| Fonts    | DM Serif Display + DM Sans (Google Fonts) |
| Deploy   | Render (backend)                          |

---

## AI Insights Engine

Located in `app.py → generate_insights()`:

- **Category analysis** — sums spend per category, identifies top spender
- **Trend detection** — compares current vs previous month (% change)
- **Daily average** — rolling 30-day window
- **Personalised suggestions** — rule-based tips mapped to each category + spend level

---

## 👨‍💻 Author

**Suyash Verma**  
🔗 GitHub: https://github.com/suyashverma16  
🔗 LinkedIn: https://linkedin.com/in/suyashverma16
