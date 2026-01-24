# Assistente (MVP)

MVP local com FastAPI + SQLite:
- Clima (Open-Meteo)
- Tarefas (prioridade alta/média/baixa + concluir)
- Lembretes (beep ao chegar o horário)
- Interface web simples (HTML puro)

## Rodar local
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
