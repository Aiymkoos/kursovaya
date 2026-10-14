# Готовые запросы для картинок «Көлеңке»

Сайты (бесплатно): Bing Image Creator (bing.com/images/create), Leonardo.ai (phoenix, 150 токенов в день),
Ideogram.ai, Microsoft Designer. Для удаления фона у портретов: remove.bg или rembg.

Стиль (добавлять в каждый запрос): `STYLE = anime-inspired visual novel illustration, soft painterly shading, dark navy and violet palette with warm golden lamp light, cinematic lighting, snowstorm night outside, highly detailed, no text, no watermark`

Фоны: 16:9, класть в `assets/bg/`. Портреты: вертикально, по пояс, прозрачный фон (PNG), класть в `assets/portraits/`.
Игра сама подхватит файлы с точными именами, код менять не нужно.

## Фоны
- `corridor.png` — long dormitory corridor at night, one flickering lamp, snowstorm in the window, wooden doors, STYLE
- `room_darkhan.png` — cramped student room, bed, desk with a candle, bookshelf, window with blizzard, STYLE
- `room_girls.png` — room of two girls, sewing machine on a table, a drum in the corner, fabrics on the wall, dim lamp, STYLE
- `room_bekzat.png` — room with a metronome on the desk, sheet music and papers, window with blizzard, STYLE
- `hall_entrance.png` — dormitory entrance, door buried in snow, emergency lamp, blizzard outside, STYLE
- `menu_art.png` — wide shot of a snowbound dormitory at night, one lit window, giant faint shadow figure in the storm, STYLE
- `ending_1.png` … `ending_4.png` — dormitory window: 1 endless night; 2 gray half-dawn; 3 bitter pale dawn; 4 warm golden sunrise over snow, STYLE

## Портреты (одно и то же описание, меняется только состояние)
Шаблон: `half-body character portrait, [HERO], three-quarter view, [ACCENT] as the only color accent, [STATE], plain white background, visual novel sprite, STYLE`

STATE:
- human: clearly visible face, expressive eyes, detailed clothes
- fading: same pose, details dissolving into dark smoke, face erased, edges disintegrating, accent color dimming
- shadow: pure black silhouette of the same pose, no face, only a faint glowing accent color outline

HERO / ACCENT (файлы `<имя>_human.png`, `_fading.png`, `_shadow.png`):
- `darkhan` — young man, white baker's hat, flour-dusted apron, kind tired eyes / orange
- `zhanel` — young woman, long black hair, headphones around neck, teal hoodie / teal
- `madina` — young woman, hair in a bun, plum cardigan, measuring tape around neck / magenta
- `bekzat` — young man, round glasses, messy black hair, vest with tie, metronome pin / pale yellow
- `me` — protagonist, young person, dark brown hair, blue jacket, long scarf / light blue

## Спрайты для сцены ходьбы (`assets/sprites/<имя>.png`)
Полный рост, вид сбоку (лицом вправо), белый фон, потом вырезать фон (rembg / remove.bg). Формат вертикальный 2:3. Файл подхватывается автоматически;
без него в коридоре рисуется силуэт кодом. Готовы: `me.png`, `darkhan.png`. Нужны: `zhanel.png`, `madina.png`, `bekzat.png`.

Шаблон: `full-body character sprite, [HERO], standing, side view facing right, [ACCENT] as the only color accent, plain white background, visual novel game sprite, whole body from head to feet, anime-inspired illustration, soft painterly shading, dark navy and violet palette, highly detailed, no text, no watermark`

- `zhanel` — young woman, long black hair, headphones around neck, teal hoodie / teal
- `madina` — young woman, hair in a bun, plum cardigan, measuring tape around neck / magenta
- `bekzat` — young man, round glasses, messy black hair, vest with tie, metronome pin / pale yellow
