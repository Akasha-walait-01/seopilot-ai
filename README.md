# AI SEO Agent — Phase 1

## Setup

1. Create virtual environment:
   python -m venv venv
   venv\Scripts\activate   (Windows)

2. Install dependencies:
   pip install -r requirements.txt

3. Copy .env.example to .env and add your Gemini API key:
   copy .env.example .env

## Run

Terminal 1 (backend):
   uvicorn backend.main:app --reload

Terminal 2 (frontend):
   streamlit run frontend/app.py

## Test

- Open http://127.0.0.1:8000 in browser → should show {"status": "ok"}
- Open http://127.0.0.1:8000/docs → FastAPI swagger UI
- Open Streamlit URL shown in terminal (usually http://localhost:8501)
- Click "Test LLM Connection" button → should show a response from Gemini
- Fill the project form and click "Create Project" → should appear in the table below



📁 Project Setup
Field	Sample Input
Website URL	https://books.toscrape.com
Business Description	Online bookstore selling books across fiction, mystery, romance, and non-fiction genres
Target Country	Pakistan
Target Language	English
SEO Goal	Increase organic traffic and improve product page visibility for book categories
🔍 Technical SEO Audit
Field	Sample Input
Max pages to crawl	10
🔑 Keyword Research
Field	Sample Input
Seed Keyword	mystery books online
🏆 Competitors & Content Gaps
Field	Sample Input
Competitor Website URL	https://www.gutenberg.org (free ebooks — thematically related, bhi crawlable)
📝 Content Briefs & Optimizer

Tab 1 — Brief Generator:

Field	Sample Input
Topic	Best Mystery Books of All Time (ya "Use Content Gap" se select karo)

Tab 2 — Optimizer:

Field	Sample Input
Select Page	(dropdown se koi crawled book page)
Target keywords	mystery books, best fiction books online, buy books online
🧭 Orchestrator & Approval
Field	Sample Input
Goal	Analyze the bookstore website and create an SEO improvement strategy. Identify technical SEO issues, keyword opportunities, competitor insights against gutenberg.org, content gaps, and content optimization opportunities. Prioritize the most important actions and prepare them for human approval.
Max pages	10
🔗 Linking, Schema & AEO/GEO + ⚡ SEO Signals & Speed

Koi extra input nahi — bas dropdown se page select karo, "Generate"/"Check" click karo.

🔔 Monitoring & Refresh
Field	Sample Input
Max pages to crawl	10

WordPress Publishing ke liye ye site kaam nahi karegi (ye WordPress site nahi hai) — uske liye apni khud ki test WordPress site chahiye hogi jab bhi ready ho.

Note: books.toscrape.com pe robots meta / noindex tag nahi hai aur content bhara hua hai, isliye is baar wo empty_content_detected aur noindex_page wala confusion nahi aayega jo codicares.com pe aaya tha — is se tum clearly dekh paoge ke naya bug-fix sahi kaam kar raha hai.