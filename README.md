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

## Инструкция для нового агента (continuation)

> Папка проекта: `D:\Проекты опен роутер\Теория малого ИИ\`
> Удалённый репозиторий: `https://github.com/Splendor1980/Theory-of-Small-AI` (ветка `main`)

### Цель
Довести облачную сборку Android APK через GitHub Actions (CI `build-apk`) до
зелёного статуса и получить готовый APK-артефакт для шаблонной игры
(«змейка на конфетах»). Инструменты и вики настроены; осталась только
отладка шага «Export APK».

### Состояние (на момент передачи)
- CI-workflow `.github/workflows/build-apk.yml` и шаблон `agent1/ci/build-apk.yml`
  **синхронизированы** (одинаковые содержимое).
- Доходит стабильно до шага `Export APK` и падает на нём;
  шаги `Prepare project` / `JDK17` / `Android SDK` / `keytool` /
  `Godot headless` / `templates` / `Configure editor settings` — проходят.
- export_templates `4.2.2.stable` распаковываются в CI; в пресете
  `use_gradle_build=true` (gradle-export).
- Keystore подаётся env-переменными и раскрывается в пресете sed'ом перед экспортом.

### Последнее точное по логу CI («Export APK»)
В предыдущем ране пресет ошибочно оказался `use_gradle_build=false` (classic),
и Godot выводил:
```
"Min SDK" can only be overridden when "Use Gradle Build" is enabled.
"Target SDK" can only be overridden when "Use Gradle Build" is enabled.
```
Сначала зафиксируй в репозитории presets-файл со значением `use_gradle_build=true`
(локально правка уже есть, но висит незакоммиченная — см. `git status`),
затем прогони CI и смотри свежий лог Export APK.

### Ранее исправленные корни
1. **Editor settings**: Godot 4.2 требует пути Android SDK/Java в
   `~/.config/godot/editor_settings-4.tres`; записывается через `printf`,
   а не heredoc (heredoc с YAML-отступами ломал `.tres`). Готово.
2. **Build template**: gradle-export требует распакованный
   `android_source.zip`; добавлен шаг распаковки в `res://android/build`
   проекта и в userdata `build_templates`. Готово, но ещё не верифицировано
   локально/в CI после возврата `use_gradle_build=true`.

### Что делать дальше
1. `git status` — закоммитьть `export_presets.cfg` (возврат `use_gradle_build=true`).
2. `gh workflow run build-apk -R Splendor1980/Theory-of-Small-AI -f idea="змейка на конфетах"`
   -> `gh run watch <id>` -> при красном `gh run view <id> --log-failed`.
3. Цель — зелёный Export APK и download артефакта `android-apk`.

### Полезное
- Локально godot-headless: `...\Temp\opencode\godot\Godot_v4.2.2-stable_win64.exe`
  (диагностика пути build template).
- `gh` авторизуется через env `GH_TOKEN` (fine-grained PAT), push — через
  remote URL с токеном. Не светить токены в коде.
- При длинных сессиях агент может деградировать (циклы) — начать новую сессию
  и дать ей эту инструкцию.
