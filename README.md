# assistente-mvp

Painel web leve para **tarefas**, **lembretes com som (chime/beep)** e **clima** (Londrina-PR), pensado para rodar em um **HomeLab de baixo consumo**.

- **Backend:** FastAPI + SQLite
- **Frontend:** HTML/CSS/JS (sem framework)
- **Acesso remoto recomendado:** Tailscale + MagicDNS
- **Lembretes:** disparam áudio no servidor (beep/chime)

## Funcionalidades

- ✅ Clima do dia (Open-Meteo)
- ✅ Tarefas por prioridade (Alta / Média / Baixa)
- ✅ Concluir tarefas (auto-limpeza em 3 dias)
- ✅ Lembretes com data/hora + beep/chime no servidor
- ✅ Botão para copiar texto e abrir o ChatGPT (sem API no servidor)

## Por que este projeto existe

Este projeto foi feito como um MVP para meu HomeLab, com foco em:
- simplicidade (sem dependências pesadas no frontend),
- baixo consumo,
- implantação prática (execução via Uvicorn / systemd),
- e boas práticas básicas (segredos fora do repositório, `.gitignore` bem definido).

## Como rodar (rápido)

```bash
cd /opt/assist
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000

