# /opt/assist/app.py
from __future__ import annotations

import asyncio
import os
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "assist.db"

SOUNDS_DIR = BASE_DIR / "sounds"
BEEP_WAV = SOUNDS_DIR / "beep.wav"

TZ = ZoneInfo("America/Sao_Paulo")

# Londrina (aprox.)
LONDRINA_LAT = -23.310
LONDRINA_LON = -51.162

# Loop interval (segundos)
REMINDER_POLL_SECONDS = 2


# =========================
# DB
# =========================
def db_conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def now_dt() -> datetime:
    return datetime.now(TZ)


def now_iso() -> str:
    return now_dt().isoformat(timespec="seconds")


def db_init() -> None:
    with db_conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('high','med','low')),
                created_at TEXT NOT NULL,
                done_at TEXT
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                fired_at TEXT
            )
            """
        )
        con.commit()


# =========================
# Weather (Open-Meteo)
# =========================
def open_meteo_today() -> str:
    # daily: temp min/max, precipitation_probability_max, windspeed_10m_max
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LONDRINA_LAT,
        "longitude": LONDRINA_LON,
        "timezone": "America/Sao_Paulo",
        "daily": "temperature_2m_min,temperature_2m_max,precipitation_probability_max,windspeed_10m_max",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    d = data["daily"]
    tmin = d["temperature_2m_min"][0]
    tmax = d["temperature_2m_max"][0]
    pmax = d["precipitation_probability_max"][0]
    wmax = d["windspeed_10m_max"][0]

    # Open-Meteo não tem alertas nativos simples aqui; deixamos placeholder.
    alerta_txt = "⚠️ Alerta: (sem dados nesta API)"

    return (
        "📍 Londrina-PR\n"
        f"🌡️ Min {tmin}°C / Máx {tmax}°C\n"
        f"🌧️ Chance máx de chuva: {pmax}%\n"
        f"💨 Vento máx: {wmax} km/h\n"
        f"{alerta_txt}\n"
    )


# =========================
# Tasks
# =========================
def task_add(text: str, priority: str) -> None:
    with db_conn() as con:
        con.execute(
            "INSERT INTO tasks (text, priority, created_at, done_at) VALUES (?,?,?,NULL)",
            (text.strip(), priority, now_iso()),
        )
        con.commit()


def tasks_list(priority: str | None = None, include_done: bool = False):
    q = "SELECT id, text, priority, created_at, done_at FROM tasks"
    args = []
    where = []
    if priority:
        where.append("priority = ?")
        args.append(priority)
    if not include_done:
        where.append("done_at IS NULL")
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY id DESC"
    with db_conn() as con:
        return con.execute(q, args).fetchall()


def tasks_format(rows) -> str:
    if not rows:
        return "—"
    out = []
    map_pt = {"high": "ALTA", "med": "MÉDIA", "low": "BAIXA"}
    for r in rows:
        out.append(f"🧾 [{r['id']}] ({map_pt.get(r['priority'], r['priority'])}) {r['text']}")
    return "\n".join(out)


def task_done(task_id: int) -> bool:
    with db_conn() as con:
        cur = con.execute(
            "UPDATE tasks SET done_at = ? WHERE id = ? AND done_at IS NULL",
            (now_iso(), task_id),
        )
        con.commit()
        return cur.rowcount == 1


def tasks_cleanup_done_older_than(days: int = 3) -> int:
    cutoff = (now_dt() - timedelta(days=days)).isoformat(timespec="seconds")
    with db_conn() as con:
        cur = con.execute(
            "DELETE FROM tasks WHERE done_at IS NOT NULL AND done_at < ?",
            (cutoff,),
        )
        con.commit()
        return cur.rowcount


# =========================
# Reminders
# =========================
def parse_local_dt(date_s: str, time_s: str) -> datetime:
    # date: YYYY-MM-DD, time: HH:MM
    dt = datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=TZ)


def reminder_add(text: str, remind_at_iso: str) -> None:
    with db_conn() as con:
        con.execute(
            "INSERT INTO reminders (text, remind_at, created_at, fired_at) VALUES (?,?,?,NULL)",
            (text.strip(), remind_at_iso, now_iso()),
        )
        con.commit()


def reminders_list(include_fired: bool = False):
    q = "SELECT id, text, remind_at, created_at, fired_at FROM reminders"
    if not include_fired:
        q += " WHERE fired_at IS NULL"
    q += " ORDER BY remind_at ASC"
    with db_conn() as con:
        return con.execute(q).fetchall()


def reminders_format(rows) -> str:
    if not rows:
        return "—"
    out = []
    for r in rows:
        status = "⏰" if r["fired_at"] is None else "✅"
        out.append(f"{status} [{r['id']}] {r['remind_at']} — {r['text']}")
    return "\n".join(out)


def reminder_delete(rem_id: int) -> bool:
    with db_conn() as con:
        cur = con.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
        con.commit()
        return cur.rowcount == 1


def fetch_due_reminders():
    # fired_at NULL and remind_at <= now
    with db_conn() as con:
        return con.execute(
            """
            SELECT id, text, remind_at
            FROM reminders
            WHERE fired_at IS NULL AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (now_iso(),),
        ).fetchall()


def mark_fired(rem_id: int) -> None:
    with db_conn() as con:
        con.execute("UPDATE reminders SET fired_at = ? WHERE id = ?", (now_iso(), rem_id))
        con.commit()


def play_beep() -> None:
    # simples e confiável: aplay
    if not BEEP_WAV.exists():
        return
    try:
        subprocess.Popen(
            ["aplay", "-q", str(BEEP_WAV)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


async def reminder_loop(stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            # limpeza de tarefas concluídas antigas
            tasks_cleanup_done_older_than(3)

            due = fetch_due_reminders()
            if due:
                for r in due:
                    # marca antes de tocar (evita tocar várias vezes se travar)
                    mark_fired(int(r["id"]))
                    play_beep()
                    # log (aparece no console do uvicorn)
                    print(f"[REMINDER] {r['text']} ({r['remind_at']})", flush=True)

        except Exception as e:
            print("[REMINDER_LOOP_ERROR]", e, flush=True)

        await asyncio.sleep(REMINDER_POLL_SECONDS)


# =========================
# FastAPI
# =========================
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

_stop_event = asyncio.Event()
_bg_task: asyncio.Task | None = None


class TaskIn(BaseModel):
    text: str
    priority: str  # high|med|low


class DoneIn(BaseModel):
    id: int


class ReminderIn(BaseModel):
    text: str
    when_date: str  # YYYY-MM-DD
    when_time: str  # HH:MM


class ReminderDelIn(BaseModel):
    id: int


@app.on_event("startup")
async def _startup():
    global _bg_task
    db_init()
    _stop_event.clear()
    _bg_task = asyncio.create_task(reminder_loop(_stop_event))


@app.on_event("shutdown")
async def _shutdown():
    _stop_event.set()
    if _bg_task:
        try:
            await _bg_task
        except Exception:
            pass


@app.get("/", response_class=FileResponse)
def home():
    return FileResponse(str(BASE_DIR / "static" / "index.html"))


@app.get("/api/weather", response_class=PlainTextResponse)
def weather():
    try:
        return open_meteo_today()
    except Exception as e:
        return f"Erro ao buscar clima: {e}"


# ---- Tasks ----
@app.get("/api/tasks", response_class=PlainTextResponse)
def list_tasks(priority: str | None = None):
    if priority and priority not in ("high", "med", "low"):
        raise HTTPException(status_code=400, detail="priority inválida (use high|med|low)")
    rows = tasks_list(priority=priority, include_done=False)
    return tasks_format(rows)


@app.post("/api/tasks", response_class=PlainTextResponse)
def add_task(t: TaskIn):
    txt = (t.text or "").strip()
    if not txt:
        raise HTTPException(status_code=400, detail="texto vazio")
    if t.priority not in ("high", "med", "low"):
        raise HTTPException(status_code=400, detail="priority inválida (use high|med|low)")
    task_add(txt, t.priority)
    return "✅ Tarefa adicionada.\n\n" + tasks_format(tasks_list(include_done=False))


@app.post("/api/tasks/done", response_class=PlainTextResponse)
def done_task(d: DoneIn):
    ok = task_done(int(d.id))
    if not ok:
        return "Não encontrei essa tarefa (ou ela já estava concluída)."
    return "✅ Tarefa concluída. (Será apagada automaticamente em 3 dias)\n\n" + tasks_format(tasks_list(include_done=False))


# ---- Reminders ----
@app.get("/api/reminders", response_class=PlainTextResponse)
def list_reminders():
    return reminders_format(reminders_list(include_fired=False))


@app.post("/api/reminders", response_class=PlainTextResponse)
def add_reminder(r: ReminderIn):
    txt = (r.text or "").strip()
    if not txt:
        raise HTTPException(status_code=400, detail="texto vazio")
    try:
        dt = parse_local_dt(r.when_date, r.when_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato inválido. Use data (YYYY-MM-DD) e hora (HH:MM).")

    if dt < now_dt():
        raise HTTPException(status_code=400, detail="Horário já passou.")

    reminder_add(txt, dt.isoformat(timespec="seconds"))
    return "✅ Lembrete criado.\n\n" + reminders_format(reminders_list(include_fired=False))


@app.post("/api/reminders/delete", response_class=PlainTextResponse)
def del_reminder(d: ReminderDelIn):
    ok = reminder_delete(int(d.id))
    if not ok:
        return "Não encontrei esse lembrete."
    return "🗑️ Lembrete removido.\n\n" + reminders_format(reminders_list(include_fired=False))


@app.get("/api/beep", response_class=PlainTextResponse)
@app.post("/api/beep", response_class=PlainTextResponse)
def beep_test():
    play_beep()
    return "🔊 Beep acionado."
