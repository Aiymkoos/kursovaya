# Көлеңке (Тень)

2D-игра: визуальная новелла + исследование + файтинг. Курсовая работа (Python + PyGame).
Жатақханадағы үш түн: буран, жарық пен байланыс жоқ, Көлеңке жолдастардың жадын жұтады.

## Запуск
```
pip install -r requirements.txt
python main.py            # полный экран (F11 — окно)
python main.py --windowed
python main.py --selftest # проверка без окна
python -m pytest -q       # тесты
```
Управление: A/D или ←→ — ходьба, E — действие, Space — следующая реплика, 1–4 — выбор ответа,
Tab — журнал воспоминаний, J/K — лёгкий/тяжёлый удар, L — блок (точно в момент удара — парирование),
1–3 — воспоминания в бою, M — звук, ESC — меню/назад.

## Сборка .exe (Windows)
`build_exe.bat` (PyInstaller, `kolenke.spec`) → `dist\Kolenke.exe`.

## Эксперимент с ИИ
`pip install -r requirements-dev.txt && python tools/experiment.py --fights 30 --enemy bekzat`
Результаты — `docs/experiment/`.

Планы и решения: `docs/PLAN.md`, список картинок (необязательно): `docs/ASSETS.md`.

## Отчёт курсовой (казахский)
`docs/report/Kolenke_kurstyk_zhoba.docx` (+ `.pdf`) — пояснительная записка по структуре методички (титул, задание, оглавление, введение, разделы 1–3, заключение, источники, приложения А, Ә, Б, В, Г).
Тексты — `docs/report/text/*.md`; таблицы функций и идентификаторов — `docs/report/*.csv` (проверяются тестами по реальному коду); числа эксперимента подставляются автоматически.
Пересборка:
```
python tools/screenshots.py        # скриншоты для приложения Ә
python tools/make_figures.py       # схемы (приложения В и Г)
python tools/build_report.py       # .docx + .pdf (нужны node, пакет docx, LibreOffice)
```
Жёлтым выделены поля, которые нужно заполнить: ФИО, группа, руководитель, даты.
