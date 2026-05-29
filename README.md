# Assistente MVP

Painel web leve para **tarefas**, **lembretes com som** e **informações climáticas**, desenvolvido para rodar em um **HomeLab de baixo consumo de recursos**.

## Tecnologias

### Backend

* Python
* FastAPI
* SQLite

### Frontend

* HTML
* CSS
* JavaScript (Vanilla JS)

### Infraestrutura

* Uvicorn
* systemd
* Tailscale + MagicDNS (acesso remoto recomendado)

## Funcionalidades

* ✅ Consulta de clima em Londrina-PR via Open-Meteo
* ✅ Gerenciamento de tarefas por prioridade

  * Alta
  * Média
  * Baixa
* ✅ Marcação de tarefas como concluídas
* ✅ Limpeza automática de tarefas concluídas após 3 dias
* ✅ Criação de lembretes com data e hora
* ✅ Reprodução de alertas sonoros (beep/chime) no servidor
* ✅ Botão para copiar texto e abrir o ChatGPT

## Objetivo do Projeto

Este projeto surgiu como um MVP (Minimum Viable Product) para meu HomeLab pessoal.

Os principais objetivos foram:

* Aprender conceitos de desenvolvimento web;
* Explorar APIs externas;
* Trabalhar com banco de dados SQLite;
* Entender a estrutura básica de uma aplicação FastAPI;
* Criar uma solução simples e leve para organização pessoal;
* Experimentar implantação em ambiente Linux.

## Características

* Interface simples e leve
* Baixo consumo de recursos
* Sem frameworks pesados no frontend
* Fácil implantação em servidores domésticos
* Estrutura adequada para futuras expansões

## Como executar

```bash
cd /opt/assist

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app:app --host 0.0.0.0 --port 8000
```

## Próximos Passos

* [ ] Sistema de autenticação
* [ ] Configurações por usuário
* [ ] Histórico de lembretes
* [ ] Integração com calendário
* [ ] Melhorias visuais na interface
* [ ] Notificações remotas

## Sobre o Desenvolvimento

Este projeto foi desenvolvido com forte auxílio de ferramentas de IA durante meu processo de aprendizado.

O objetivo principal não foi criar um produto final ou um sistema para produção, mas explorar conceitos relacionados a:

- Python
- APIs
- FastAPI
- SQLite
- Linux
- Automação
- Desenvolvimento web

Durante o desenvolvimento, pude ter contato com configuração de ambiente Linux, gerenciamento de dependências, integração com APIs, estruturação de aplicações web e uso de Git/GitHub.

O projeto permanece disponível como registro do meu aprendizado e da minha evolução técnica.
