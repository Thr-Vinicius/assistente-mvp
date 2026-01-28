# assistente-mvp

Painel web simples para **tarefas**, **lembretes com som (chime)** e **clima (Londrina-PR)**, feito para rodar em HomeLab com baixo consumo.

- Backend: FastAPI + SQLite
- Frontend: HTML/CSS/JS (sem framework)
- Acesso recomendado: Tailscale + MagicDNS
- Lembretes: disparam um som no **servidor**

## O que tem
- ✅ Clima do dia (Open-Meteo)
- ✅ Tarefas por prioridade (Alta / Média / Baixa)
- ✅ Concluir tarefas (auto-limpeza em 3 dias)
- ✅ Lembretes com data/hora + beep/chime no servidor
- ✅ Botão para copiar texto e abrir o ChatGPT (sem API no servidor)

## Como rodar (rápido)
```bash
cd /opt/assist
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
