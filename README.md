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

### Итог: CI зелёный, APK собран (05.09.2026)
Шаг «Export APK» доведён до зелёного; `build_apk` → `success`, артефакт
`android-apk` (game.apk) выложен и скачан в `build/android/game.apk`.

Исправленные в этой сессии корни (по порядку срабатывания в CI):
1. **use_gradle_build=true** — возврат в `agent1/project/export_presets.cfg`.
2. **Путь распаковки шаблона** — `android_source.zip` содержит файлы
   (build.gradle, AndroidManifest.xml, src/...) на корне, поэтому распаковывается
   в `project_build/android/build/`, чтобы получился `res://android/build/build.gradle`
   (Godot 4.2 проверяет `DirAccess::exists("res://android/build")`).
3. **min_sdk 23→24** — mobile-рендерер требует SDK>=24.
4. **import_etc2_astc=true** — добавлено в `project.godot`. Без него export валится
   «Cannot export ... due to configuration errors» с ПУСТОЙ строкой (это единственный
   жёсткий чек без текста ошибки: `!should_import_etc2_astc()`); десктоп/headless
   хост даёт S3TC/BPTC, а Android нужен ETC2/ASTC.
5. **res://android/.build_version** = `4.2.2.stable` — gradle-export открывает этот
   файл и сверяет с версией (`VERSION_FULL_CONFIG`). Обычно создаёт «Install Android
   Build Template»; в CI пишем вручную. Иначе: «no version info for it exists».
6. **.gdignore в res://android/** — чтобы Godot НЕ импортировал ресурсы шаблона
   (splash.png и т.п.) и не создавал `*.png.import`; иначе gradle
   `:mergeDebugResources` падает «The file name must end with .xml or .png».
   FileAccess и gradle `.gdignore` не затрагивает.

Что дальше (опционально):
- Обновить шаблонную игру (поменять `idea` в workflow_dispatch) и пересобрать.
- Артефакт: Actions → run → `android-apk`, либо локально в `build/android/game.apk`.

### Полезное
- Локально godot-headless: `...\Temp\opencode\godot\Godot_v4.2.2-stable_win64.exe`
  (диагностика пути build template).
- `gh` авторизуется через env `GH_TOKEN` (fine-grained PAT), push — через
  remote URL с токеном. Не светить токены в коде.
- При длинных сессиях агент может деградировать (циклы) — начать новую сессию
  и дать ей эту инструкцию.
