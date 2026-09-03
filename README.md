# Теория малого ИИ — Agent 1

Офлайн ИИ-ассистент для слабых устройств (Godot-игры), гибрид
«символьная память + маленькая LLM + интернет». Основа: stdlib Python, без pip.

Документация и описание рабочих механизмов — в `agent1/README.md`.
Тезисы, ход эксперимента и принятые решения — в `ПЛАНОВЫЕ-ИДЕИ.md`.

## CI: облачная сборка Android APK

Файл `.github/workflows/build-apk.yml` собирает APK на GitHub Actions
(бесплатно, не нагружая слабую машину).

Поток: `make_project.py` (Python stdlib) -> Godot-проект под игру ->
JDK17 + Android SDK -> keytool debug.keystore -> Godot headless +
export templates -> `--export-debug "Android"` -> APK artifact.

Запуск вручную: Actions -> **build-apk** -> *Run workflow* -> поле `idea`
(по умолчанию «змейка на конфетах»). Поле принимает идею игры, например
«neon пинг-понг», «крестики-нолики как кошки и собаки».

Примечание: экспортные Godot templates (4.2.2.stable) обязательны; их
скачивает сам воркфлоу. keystore подаётся env-переменными и генерируется
на лету в CI.
