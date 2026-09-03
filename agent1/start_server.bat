@echo off
REM Запуск offline OpenAI-совместимого сервера Agent 1 (без зависимостей)
cd /d "%~dp0"
python agent_server.py --port 8971 --data _data --seed seed_gdd.json
pause
