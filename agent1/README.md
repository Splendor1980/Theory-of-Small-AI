# Agent 1 - Game Code Generator (Godot) с символьной памятью

Цель: из простой идеи на естественном языке получить рабочий
GDScript-скелет игры для Godot 4.x.

Фокус проекта: **офлайн, слабое железо, без тяжёлых LLM**.
Вместо того чтобы держать все знания в весах большой модели, Agent 1
держит знания в **символьной памяти** (граф + гипервекторы) и лишь
небольшой/правильный слой превращает запрос в код.

## Нейро-символический конвейер

```
question (RU/EN)
   |
   v
Memory.query()  --- 3 слоя:
   |   1. KnowledgeGraph (SQLite SPO-триплы)   -- точные факты
   |   2. Hypervector VSA/HDC (Barrier)        -- семантическая близость
   |   3. Hebbian (ассоциативные связи)        -- запоминание диалогов
   v
rule backend / tiny LLM ---- превращает вопрос + факты памяти ---> JSON-enums
   |
   v
GameIntent (protected vocabulary / enums)   -- валидация
   |
   v
render_skeleton  --  game.gd (шаблон с местами <HAND>)
```

Ключевая идея: **память правит генерацией**. Если в графе есть факт
`color_scheme is neon`, а пользователь пишет "игра с неоном" - память
переопределяет дефолтный `retro` на `neon`, и код генерируется под него.
LLM/правила не обязаны "знать" всё - они лишь считывают решения из памяти.

## Установка / запуск

Fallback (правила, без зависимостей) с памятью:

```powershell
# из корня вместе с папкой agent1
python -m agent1.agent_loop "neon platformer with chasing enemies" --seed agent1\seed_gdd.json
python -m agent1.agent_loop "puzzle with a timer" --out build
```

Память создаётся в `_data/` (SQLite knowledge.db + hebbian.db) автоматически.
`--seed` загружает стартовые факты `[subj, pred, obj]` из JSON.

С большой моделью через llama.cpp (если поставишь GGUF):

```powershell
pip install llama-cpp-python
python -m agent1.main "twin stick shooter" --backend llama_cpp --model path\to\model.gguf
```

## Структура

```
agent1/
  main.py                 CLI (старый, без памяти)
  agent_loop.py           CLI с памятью: MemoryAwareAgent
  memory/
    knowledge_graph.py    SQLite SPO-триплы (факты)
    hypervector.py        Векторно-символическая память (VSA/HDC, Kanerva-style)
    hebbian.py            Hebbian-ассоциации (совместная активация -> связи)
    orchestrator.py       Memory: 3 слоя + HDC-ворота + фиксация ходов
  tools/
    web_knowledge.py      Подтягивание знаний из интернета (stdlib-only)
    web_search.py         Поиск DuckDuckGo без API-ключей (stdlib-only)
    error_explainer.py    Переводчичек логов Godot -> человеческая инструкция
  gd_validator.py         Мини-валидатор GDScript (stdlib fallback без Godot)
  build_loop.py           Замкнутая петля генерация->проверка->память->починка
  agent_server.py         OpenAI-совместимый сервер (модель в opencode)
  core/
    schema.py             protected vocabulary + GameIntent (JSON-enums)
    prompter.py           строитель промпта + extract_json
    generator.py          render_skeleton -> game.gd
    template_library.py   роутер идей -> играбельные шаблоны (stdlib)
    theme_library.py      «логика + тема»: пресеты + подстановка {{THEME_*}}
  backends/
    base.py               абстракция LLM-бэкенда
    rule_backend.py       правило-fallback (без зависимостей)
    llama_cpp_backend.py  GGUF via llama-cpp-python
  templates/
    game_skeleton.gd      Godot-шаблон (с местами <HAND>)
    tic_tac_toe.gd        ПОЛНЫЙ играбельный MVP (крестики-нолики) + блок THEME
    pong.gd               играбельный MVP пинг-понг + блок THEME
    snake.gd              играбельный MVP змейка + блок THEME
  project/                каркас Godot-проекта под CI (project.godot, main, export_presets)
  ci/build-apk.yml        GitHub Actions: облачная сборка APK (см. ниже)
  tools/make_project.py   мост «идея -> Godot-проект» -> CI собирает APK
```

## Замкнутая петля «генерация -> проверка -> память -> починка»

Главный механизм (согласован с тезисами в `../ПЛАНОВЫЕ-ИДЕИ.md`):
Agent 1 не просто генерит — он **проверяет и чинит** свой код, а каждая
ошибка оседает в графе как `(<фича> fails_with <суть>)`.

```
idea -> skeleton (рельсы шаблона)
   |
   v
gd_validator.validate_script()  -- stdlib, работает без Godot
   |            (или godot --headless, если установлен)
   v
ошибка? -> error_explainer.explain()  -- переводит лог в человеческую инструкцию
   |            (детектор зацикливания: та же ошибка N раз -> стоп)
   v
auto_fix()  -- чинит по категориям (undeclared var, скобки, ...)
   |
   v
_ensure_memory_triples()  -- <фича> fails_with <суть> -> SQLite
   |
   v--- повтор до N итераций (лоботомия: каждый чистый запрос) ---
чистый .gd
```

Лоботомия контекста: каждая итерация - чистый запрос, не тянем старый
неудачный код. Памятные уроки остаются в графе и долгосрочно правят генерацию.

```powershell
python -m agent1.build_loop "neon platformer with enemies" --out build --seed agent1\seed_gdd.json
```

## Запуск как модель в opencode

Сервер (OpenAI-совместимый, stdlib-only):

```powershell
python agent1\agent_server.py --port 8971 --data agent1\_data --seed agent1\seed_gdd.json
```

Конфиг уже прописан: провайдер `agent1`, модель `agent1/agent1` =
«Agent 1 (offline symbolic)». Память правит ответами: «neon runner» -> runner/neon.

## «Логика + тема» и облачная сборка APK

Шаблоны разделены на «движок/логику» и «тему»: визуал/текст вынесены в блок
`## THEME_START..THEME_END` с плейсхолдерами `{{THEME_*}}`. `theme_library.py`
выбирает пресет (classic/neon/candy/cats_dogs/ocean) по ключевым словам идеи и
подставляет их. Меняется внешний вид и текст, механики не трогаются.

```powershell
python -m agent1.tools.make_project "змейка на конфетах" --out build\project
```

Собирает Godot-проект: копирует каркас `project/`, кладёт выбранную игру в
`games/`, применяет тему, выставляет `GAME_NAME` в `main.gd`. Затем облачный CI:

```text
make_project -> JDK17 + Android SDK -> debug.keystore(keytool) -> Godot headless
+ export templates 4.2.2.stable -> --check-only -> --export-debug "Android" -> APK
```

Чтобы включить: скопировать `agent1/ci/build-apk.yml` в корень GitHub-репо в
`.github/workflows/build-apk.yml`. Экспортные шаблоны обязательны (без них
`--export-debug` падает). keystore подаётся env-переменными
`ANDROID_KEYSTORE_DEBUG_*` и подставляется Godot'ом из `export_presets.cfg`.

## Что уже работает (проверено)

- 3-слойная память: точный факт, fuzzy LIKE, Hebbian-ассоциация. ?
- HDC-ворота: `gate_score()` предсказывает, насколько вопрос близок к
  доступным фактам (0..1). ?
- Память переопределяет дефолты rule-бэкенда (neon/runner sequencing). ?
- Валидный `.gd` в UTF-8, рендер по шаблону. ?
- Мини-валидатор GDScript: чистый скелет -> 0 ошибок; ловит незакрытые
  скобки и необъявленные переменные. ?
- Error Explainer: лог -> понятная инструкция + детектор зацикливания. ?
- Feedback-loop: скелет правится авто (undeclared var -> вставка `var`), 
  ошибки оседают как `fails_with`-триплы в граф. ?
- OpenAI-совместимый сервер: `/v1/models` + chat (SSE-стрим) рабоч. ?
- **Решающий эксперимент (вариант А, облегчённый):** идея «сделай крестики-нолики»
  -> ПОЛНЫЙ играбельный MVP (145 строк, доска/ходы/ИИ/победа), на чистом stdlib
  без LLM и pip. Роутер идей -> библиотека шаблонов. ?
- «Логика+тема»: pong/snake добавлены по образцу tico; темы (neon/candy/cats_dogs/ocean)
  применимы ко всем трём играм через универсальный парсер {{THEME_*}}. ?
- `make_project.py`: идея -> Godot-проект (тема применена, GAME_NAME выставлен). ?
- `project/` + `ci/build-apk.yml`: облачная APK-сборка по рецепту гугла (готово к включению). ?
- Весь прототип - **только stdlib Python** (sqlite3, urllib, json, http.server),
  без pip-зависимостей. ?

## Планы

1. Подключить настоящий Godot headless (`--check-only`) для полной проверки
   синтаксиса (сейчас fallback-валидатор).
2. llama_cpp backend для нечёткой генерации там, где правила не справляются.
3. Связка Agent 2 (assets) / Agent 3 (build) - конвейер из нескольких агентов
   на общей памяти.
4. Сжатие гипервектора в бит-паки для ещё более слабых машин (Android).
5. Расширение библиотеки скелетов (передвижение, стрельба, патруль).