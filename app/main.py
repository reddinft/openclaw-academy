"""OpenClaw Academy — FastAPI application."""
import os
import time
import aiosqlite
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, mark_lesson_complete, mark_lesson_incomplete, get_progress, get_module_progress, save_quiz_attempt, get_quiz_best
from app.content import load_modules, load_module, load_lesson, load_quiz, get_all_progress_ids
from app.analytics import AnalyticsMiddleware

DB_PATH = os.environ.get("DB_PATH", "/data/progress.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="OpenClaw Academy", lifespan=lifespan)
app.add_middleware(AnalyticsMiddleware)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _enrich_modules(modules: list[dict], progress: dict) -> list[dict]:
    """Add progress counts to each module."""
    for m in modules:
        lessons = m.get("lessons", [])
        total = len(lessons)
        done = sum(
            1 for l in lessons
            if progress.get(f"{m['id']}::{l['slug']}", {}).get("completed", 0)
        )
        m["progress_done"] = done
        m["progress_total"] = total
        m["progress_pct"] = int((done / total * 100) if total else 0)
    return modules


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    modules = load_modules()
    progress = await get_progress()
    modules = _enrich_modules(modules, progress)

    total_lessons = sum(m["progress_total"] for m in modules)
    total_done = sum(m["progress_done"] for m in modules)
    overall_pct = int((total_done / total_lessons * 100) if total_lessons else 0)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "modules": modules,
        "total_lessons": total_lessons,
        "total_done": total_done,
        "overall_pct": overall_pct,
    })


@app.get("/module/{module_id}", response_class=HTMLResponse)
async def module_overview(request: Request, module_id: str):
    module = load_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    progress = await get_module_progress(module_id)
    lessons = module.get("lessons", [])
    for lesson in lessons:
        lid = f"{module_id}::{lesson['slug']}"
        lesson["completed"] = progress.get(lid, {}).get("completed", 0)
        lesson["completed_at"] = progress.get(lid, {}).get("completed_at")

    done = sum(1 for l in lessons if l["completed"])
    total = len(lessons)

    # Also load all modules for sidebar
    all_modules = load_modules()
    all_progress = await get_progress()
    all_modules = _enrich_modules(all_modules, all_progress)

    return templates.TemplateResponse("module.html", {
        "request": request,
        "module": module,
        "lessons": lessons,
        "done": done,
        "total": total,
        "pct": int((done / total * 100) if total else 0),
        "all_modules": all_modules,
    })


@app.get("/module/{module_id}/lesson/{lesson_slug}", response_class=HTMLResponse)
async def lesson_view(request: Request, module_id: str, lesson_slug: str):
    lesson_data = load_lesson(module_id, lesson_slug)
    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress = await get_progress()
    lesson_id = lesson_data["lesson_id"]
    is_completed = progress.get(lesson_id, {}).get("completed", 0)

    all_modules = load_modules()
    all_progress = await get_progress()
    all_modules = _enrich_modules(all_modules, all_progress)

    # Mark progress for lessons in sidebar
    for lesson in lesson_data["module"].get("lessons", []):
        lid = f"{module_id}::{lesson['slug']}"
        lesson["completed"] = all_progress.get(lid, {}).get("completed", 0)

    return templates.TemplateResponse("lesson.html", {
        "request": request,
        **lesson_data,
        "is_completed": is_completed,
        "all_modules": all_modules,
        "module_id": module_id,
    })


@app.post("/progress/toggle", response_class=HTMLResponse)
async def toggle_progress(
    request: Request,
    lesson_id: str = Form(...),
    module_id: str = Form(...),
    lesson_slug: str = Form(...),
    currently_completed: int = Form(0),
):
    """HTMX endpoint to toggle lesson completion."""
    if currently_completed:
        await mark_lesson_incomplete(lesson_id, module_id, lesson_slug)
        new_state = 0
    else:
        await mark_lesson_complete(lesson_id, module_id, lesson_slug)
        new_state = 1

    # Return the updated toggle button
    checked_class = "btn-success" if new_state else "btn-outline"
    label = "✅ Completed" if new_state else "Mark Complete"
    return HTMLResponse(f"""
        <form hx-post="/progress/toggle" hx-target="#progress-btn-wrap" hx-swap="outerHTML">
            <input type="hidden" name="lesson_id" value="{lesson_id}">
            <input type="hidden" name="module_id" value="{module_id}">
            <input type="hidden" name="lesson_slug" value="{lesson_slug}">
            <input type="hidden" name="currently_completed" value="{new_state}">
            <button type="submit" class="btn {checked_class}">{label}</button>
        </form>
    """)


@app.get("/module/{module_id}/quiz", response_class=HTMLResponse)
async def quiz_view(request: Request, module_id: str):
    module = load_module(module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    quiz = load_quiz(module_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")

    best = await get_quiz_best(quiz["id"])

    all_modules = load_modules()
    all_progress = await get_progress()
    all_modules = _enrich_modules(all_modules, all_progress)

    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "module": module,
        "quiz": quiz,
        "best": best,
        "all_modules": all_modules,
        "module_id": module_id,
        "submitted": False,
        "results": None,
    })


@app.post("/module/{module_id}/quiz", response_class=HTMLResponse)
async def quiz_submit(request: Request, module_id: str):
    module = load_module(module_id)
    quiz = load_quiz(module_id)
    if not module or not quiz:
        raise HTTPException(status_code=404)

    form = await request.form()
    questions = quiz.get("questions", [])

    correct = 0
    results = []
    answers = {}

    for q in questions:
        qid = q["id"]
        user_answer = form.get(qid, "")
        answers[qid] = user_answer
        is_correct = user_answer == q.get("correct")
        if is_correct:
            correct += 1
        results.append({
            "question": q,
            "user_answer": user_answer,
            "is_correct": is_correct,
        })

    total = len(questions)
    score_pct = int((correct / total * 100) if total else 0)

    await save_quiz_attempt(quiz["id"], correct, total, answers)
    best = await get_quiz_best(quiz["id"])

    all_modules = load_modules()
    all_progress = await get_progress()
    all_modules = _enrich_modules(all_modules, all_progress)

    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "module": module,
        "quiz": quiz,
        "best": best,
        "all_modules": all_modules,
        "module_id": module_id,
        "submitted": True,
        "results": results,
        "correct": correct,
        "total": total,
        "score_pct": score_pct,
        "passing": score_pct >= quiz.get("passing_score", 70),
    })


@app.get("/api/progress")
async def api_progress():
    progress = await get_progress()
    modules = load_modules()
    summary = []
    for m in modules:
        lessons = m.get("lessons", [])
        done = sum(1 for l in lessons if progress.get(f"{m['id']}::{l['slug']}", {}).get("completed", 0))
        summary.append({
            "module_id": m["id"],
            "title": m["title"],
            "done": done,
            "total": len(lessons),
            "pct": int((done / len(lessons) * 100) if lessons else 0),
        })
    return JSONResponse({"modules": summary, "raw": progress})


@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request):
    """Poor man's analytics dashboard — hit counts, geo, bot ratio."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Total hits last 30 days
            since = int(time.time()) - 86400 * 30
            async with db.execute("SELECT COUNT(*) as n FROM hits WHERE ts > ?", (since,)) as cur:
                total = (await cur.fetchone())["n"]
            async with db.execute("SELECT COUNT(*) as n FROM hits WHERE ts > ? AND is_bot=0", (since,)) as cur:
                humans = (await cur.fetchone())["n"]
            # Top countries
            async with db.execute(
                "SELECT country, COUNT(*) as n FROM hits WHERE ts > ? AND is_bot=0 GROUP BY country ORDER BY n DESC LIMIT 15",
                (since,)
            ) as cur:
                countries = await cur.fetchall()
            # Top pages
            async with db.execute(
                "SELECT path, COUNT(*) as n FROM hits WHERE ts > ? AND is_bot=0 GROUP BY path ORDER BY n DESC LIMIT 15",
                (since,)
            ) as cur:
                pages = await cur.fetchall()
            # Daily hits last 14 days
            async with db.execute(
                """SELECT date(ts, 'unixepoch') as day, COUNT(*) as n
                   FROM hits WHERE ts > ? AND is_bot=0
                   GROUP BY day ORDER BY day DESC LIMIT 14""",
                (int(time.time()) - 86400 * 14,)
            ) as cur:
                daily = await cur.fetchall()
    except Exception as e:
        return HTMLResponse(f"<pre>Stats unavailable: {e}</pre>")

    rows_countries = "".join(f"<tr><td>{r['country']}</td><td>{r['n']}</td></tr>" for r in countries)
    rows_pages = "".join(f"<tr><td>{r['path']}</td><td>{r['n']}</td></tr>" for r in pages)
    rows_daily = "".join(f"<tr><td>{r['day']}</td><td>{r['n']}</td></tr>" for r in daily)
    bots = total - humans

    html = f"""<!DOCTYPE html>
<html data-theme="dark"><head><meta charset="UTF-8">
<title>Academy Stats</title>
<style>
  body {{ font-family: monospace; background: #0f0a1e; color: #ccc; padding: 2rem; }}
  h1 {{ color: #a78bfa; }} h2 {{ color: #7c3aed; margin-top: 1.5rem; }}
  table {{ border-collapse: collapse; margin-top: .5rem; }}
  td, th {{ padding: .3rem 1rem; border: 1px solid #333; text-align: left; }}
  .big {{ font-size: 2rem; color: #a78bfa; }}
</style></head><body>
<h1>📊 OpenClaw Academy — Stats (last 30 days)</h1>
<p><span class="big">{humans}</span> human visits &nbsp;|&nbsp;
   <span class="big">{bots}</span> bots &nbsp;|&nbsp;
   <span class="big">{total}</span> total</p>
<h2>🌍 Top Countries (humans)</h2>
<table><tr><th>Country</th><th>Visits</th></tr>{rows_countries}</table>
<h2>📄 Top Pages (humans)</h2>
<table><tr><th>Path</th><th>Visits</th></tr>{rows_pages}</table>
<h2>📅 Daily (last 14 days, humans)</h2>
<table><tr><th>Day</th><th>Visits</th></tr>{rows_daily}</table>
<p style="margin-top:2rem;color:#666">
  Full analytics: <a href="https://openclaw-academy.goatcounter.com" style="color:#a78bfa">GoatCounter dashboard</a>
</p>
</body></html>"""
    return HTMLResponse(html)
