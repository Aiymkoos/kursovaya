// JSON блоктарынан Word (.docx) құжатын жасайды. Қолданылуы: node tools/report_docx.js in.json out.docx
// Формат: A4, шет: сол 30, оң 15, жоғары/төмен 20 мм; Times New Roman 14, аралық 1,5.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, Footer, PageNumber, PageOrientation, LevelFormat,
  TabStopType, LeaderType, Tab,
  VerticalAlign, TableLayoutType,
} = require("docx");

const [, , inFile, outFile] = process.argv;
const data = JSON.parse(fs.readFileSync(inFile, "utf-8"));
const FONT = "Times New Roman";
const CONTENT = 9355;

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: 28, ...o });
const ph = (text, o = {}) => run(text, { shading: { type: ShadingType.CLEAR, fill: "FFFF00", color: "auto" }, ...o });    // толтырылатын орын (сары фон)
const body = (children, o = {}) => new Paragraph({
  children, alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 709 },
  spacing: { line: 360, before: 0, after: 0 }, ...o,
});
const center = (text, o = {}, ro = {}) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { line: 276, before: 0, after: 0, ...(o.spacing || {}) },
  children: [run(text, ro)],
});

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}

function imageParagraphs(b) {
  const { w, h, data } = pngSize(b.path);
  const pxW = Math.round(b.width_cm * 37.795);
  const pxH = Math.round(pxW * h / w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data, transformation: { width: pxW, height: pxH } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240, line: 276 },
      children: [run(b.caption)] }),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };

function tableBlock(b) {
  const size = b.size || 22;
  const cell = (text, width, header) => new TableCell({
    width: { size: width, type: WidthType.DXA }, borders, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    shading: header ? { fill: "E7E6E6", type: ShadingType.CLEAR, color: "auto" } : undefined,
    children: [new Paragraph({ spacing: { line: 240 }, alignment: AlignmentType.LEFT,
      children: [run(String(text), { size, bold: header })] })],
  });
  const rows = [new TableRow({ tableHeader: true, cantSplit: true,
    children: b.header.map((h, i) => cell(h, b.widths[i], true)) })];
  for (const r of b.rows) {
    rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, b.widths[i], false)) }));
  }
  const out = [];
  if (b.caption) {
    out.push(new Paragraph({ keepNext: true, spacing: { before: 120, after: 60, line: 276 },
      children: [run(b.caption)] }));
  }
  out.push(new Table({ width: { size: CONTENT, type: WidthType.DXA }, columnWidths: b.widths,
    layout: TableLayoutType.FIXED, rows }));
  out.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
  return out;
}

function codeBlock(b) {
  const out = [
    new Paragraph({ keepNext: true, spacing: { before: 240, after: 20, line: 276 },
      children: [run(b.title, { bold: true, size: 24 })] }),
  ];
  if (b.purpose) {
    out.push(new Paragraph({ keepNext: true, spacing: { after: 60, line: 276 },
      children: [run(b.purpose, { italics: true, size: 22 })] }));
  }
  for (const line of b.lines) {
    out.push(new Paragraph({ spacing: { line: 220, before: 0, after: 0 },
      children: [new TextRun({ text: line.length ? line : " ", font: "Courier New", size: 17 })] }));
  }
  return out;
}

// ---------- титул және тапсырма ----------
function titlePage() {
  const c = (t, before, ro = {}) => center(t, { spacing: { before } }, ro);
  const right = (parts, before = 160) => new Paragraph({ alignment: AlignmentType.LEFT,
    indent: { left: 4800 }, spacing: { before, line: 276 }, children: parts });
  return [
    c("Қарағанды жоғары политехникалық колледжі", 0, { bold: true }),
    c("«Ақпараттық жүйелер және дизайн» кафедрасы", 120),
    c("КУРСТЫҚ ЖОБА", 2600, { bold: true, size: 36 }),
    c("«Алгоритмдеу және бағдарламалау» пәні бойынша", 240),
    c("Тақырыбы:", 600, { bold: true }),
    c("«Көлеңке» — визуалды новелла, қозғалыс және жекпе-жек біріктірілген 2D ойыны", 120, { bold: true }),
    c("Мамандығы: 06130100 — Бағдарламалық қамтамасыз ету (түрлері бойынша)", 600),
    right([run("Орындаған: "), ph("[аты-жөні]")], 1500),
    right([run("Топ: "), ph("[топ шифры]")]),
    right([run("Жетекші: "), ph("[аты-жөні]")]),
    right([run("Қорғауға жіберілді: "), ph("[күні]")]),
    right([run("Бағасы: "), ph("[__________]")]),
    c("Қарағанды, 2026", 1700),
  ];
}

function taskPage() {
  const t = (parts, o = {}) => new Paragraph({ spacing: { line: 276, before: 80, after: 0 },
    alignment: AlignmentType.JUSTIFIED, ...o, children: parts });
  const r = (s, o = {}) => run(s, { size: 24, ...o });
  const item = (s) => new Paragraph({ numbering: { reference: "dash", level: 0 },
    spacing: { line: 276, before: 20 }, alignment: AlignmentType.JUSTIFIED, children: [r(s)] });
  return [
    center("КУРСТЫҚ ЖОБАҒА ТАПСЫРМА", { spacing: { after: 160 } }, { bold: true }),
    t([r("Студент: "), ph("[аты-жөні]", { size: 24 }), r(",  топ: "), ph("[шифры]", { size: 24 })]),
    t([r("Жобаның тақырыбы: ", { bold: true }),
       r("«Көлеңке» — визуалды новелла, қозғалыс және жекпе-жек біріктірілген 2D ойыны.")]),
    t([r("Бастапқы деректер:", { bold: true })]),
    item("Ойын мақсаты — жатақханадағы төрт танысты көлеңкеден құтқару. Оқиға қыстағы үш түн ішінде өтеді; көлеңке адамды өлтірмейді, оның жадын жұтады: жадынан айырылған адам силуэтке айналып, өзінің күнделікті әдеттерімен соғады."),
    item("Әр түн үш фазадан тұрады: сөйлесу → айналу → жекпе-жек. 1-түн (Дархан) — оқыту; 2-түн (Жанель және Мадина) — біреуімен ғана толық сөйлесуге болады; 3-түн (Бекзат) — финал, басты кейіпкердің өзі айнала бастайды. Аяқталу құтқарылғандар санына байланысты (төрт финал)."),
    item("Басқару: A/D немесе ← → — қозғалыс, E — әрекеттесу, Space — келесі реплика, 1–4 — жауап таңдау, Tab — журнал; жекпе-жекте J — жеңіл, K — ауыр соққы, L — блок (дәл сәтте — парирлеу), 1–3 — естелік, ESC — мәзір."),
    item("Диалог жүйесі JSON файлдарынан жүктеледі (түйіндер мен таңдау бұтақтары); флагтар таңдауларды кейінгі сахналарға және жекпе-жек параметрлеріне байланыстырады."),
    item("Жекпе-жек: кадрлық ақырлы автомат (FSM), hitbox/hurtbox, кадр дәлдігіндегі парирлеу терезесі, енгізу буфері. Бейімделгіш қарсылас ойыншы әрекеттерін жиілік кестесіне жазып (Марков тізбегі), келесі әрекетті болжайды; болжау дәлдігі өлшенеді."),
    item("Графика мен дыбыс: силуэттік кадрлық анимация, бөлшектер жүйесі, парирлеудегі баяулау; буран, соққы, парирлеу және әр кейіпкердің мотиві (пышақ, барабан, тігін машинасы, метроном); 60 кадр/с."),
    item("Технологиялар: Python, PyGame; сақтау — JSON; Windows үшін PyInstaller арқылы .exe жинау."),
    t([r("Түсініктеме жазбаның мазмұны: ", { bold: true }),
       r("Кіріспе; 1 Зерттеу бөлімі (1.1 Пәндік аумақты сипаттау, 1.2 Бағдарламалау құралдарына шолу); 2 Технологиялық бөлім (2.1 Тапсырманың қойылымы, 2.2 Бағдарламалау тілін таңдау, 2.3 Құрылымдық және функционалдық сызба); 3 Арнайы бөлім (3.1 Модульдер мен функциялар, 3.2 Идентификаторлар кестесі, 3.3 Эксперименттік нәтижелер); Қорытынды; Қолданылған деректер тізімі; Қосымшалар (А — техникалық тапсырма, Ә — қолданушы басқаруы, Б — бағдарлама листингі, В — құрылымдық сызба, Г — функционалдық сызба).")]),
    t([r("Графикалық бөлім: ", { bold: true }), r("құрылымдық сызба, функционалдық сызба (А4).")]),
    t([r("Тапсырма берілген күн: "), ph("[күні]", { size: 24 }), r("        Орындау мерзімі: "), ph("[күні]", { size: 24 })], { spacing: { before: 200, line: 276 } }),
    t([r("Жетекші: "), ph("[аты-жөні, қолы]", { size: 24 }), r("        Студент: "), ph("[қолы]", { size: 24 })]),
  ];
}

// ---------- мазмұн ----------
function tocBlock(toc) {
  const out = [center("МАЗМҰНЫ", { spacing: { after: 240 } }, { bold: true })];
  for (const e of toc) {
    out.push(new Paragraph({
      spacing: { line: 276, before: 40, after: 0 }, indent: { left: e.level === 2 ? 400 : 0 },
      tabStops: [{ type: TabStopType.RIGHT, position: CONTENT, leader: LeaderType.DOT }],
      children: [
        run(e.text, { size: 26, bold: e.level === 1 }),
        new TextRun({ children: [new Tab(), String(e.page || "")], font: FONT, size: 26 }),
      ],
    }));
  }
  return out;
}

// ---------- негізгі блоктар ----------
function convert(b) {
  switch (b.t) {
    case "h1":
      return [new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.pagebreak && !b.landscape,
        children: [run(b.text, { bold: true })] })];
    case "h2":
      return [new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(b.text, { bold: true })] })];
    case "h3":
      return [new Paragraph({ keepNext: true, spacing: { before: 160, after: 60, line: 360 },
        children: [run(b.text, { bold: true })] })];
    case "p": {
      const kids = [];
      if (b.lead) kids.push(run(b.lead, { bold: true }));
      kids.push(run(b.text));
      return [body(kids)];
    }
    case "bullets":
      return b.items.map((it) => new Paragraph({ numbering: { reference: "dash", level: 0 },
        alignment: AlignmentType.JUSTIFIED, spacing: { line: 360 }, children: [run(it)] }));
    case "refs":
      return b.items.map((it) => new Paragraph({ alignment: AlignmentType.LEFT,
        indent: { left: 709, hanging: 709 }, spacing: { line: 360 }, children: [run(it)] }));
    case "table": return tableBlock(b);
    case "image": return imageParagraphs(b);
    case "code": return codeBlock(b);
    default: throw new Error("белгісіз блок: " + b.t);
  }
}

const margins = { top: 1134, bottom: 1134, left: 1701, right: 850 };
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 28 })] })] });

const main = tocBlock(data.toc);
let landscape = null;
for (const b of data.blocks) {
  if (b.landscape) { landscape = []; }
  (landscape || main).push(...convert(b));
}
// мазмұннан кейін негізгі мәтін жаңа бетте басталады
main.splice(data.toc.length + 1, 0, new Paragraph({ pageBreakBefore: true, children: [] }));

const sections = [
  { properties: { page: { size: { width: 11906, height: 16838 }, margin: margins } },
    children: [...titlePage(), new Paragraph({ pageBreakBefore: true, children: [] }), ...taskPage()] },
  { properties: { page: { size: { width: 11906, height: 16838 }, margin: margins, pageNumbers: { start: 3 } } },
    footers: { default: footer }, children: main },
];
if (landscape) {
  sections.push({ properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
      margin: { top: 850, bottom: 850, left: 850, right: 850 } } },
    footers: { default: footer }, children: landscape });
}

const doc = new Document({
  creator: "Курстық жоба", title: "Көлеңке — курстық жоба",
  styles: {
    default: { document: { run: { font: FONT, size: 28 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "000000" },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240, line: 360 },
          keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "000000" },
        paragraph: { alignment: AlignmentType.LEFT, spacing: { before: 240, after: 120, line: 360 },
          indent: { firstLine: 709 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "dash", levels: [{ level: 0, format: LevelFormat.BULLET, text: "–",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1069, hanging: 360 } } } }] }] },
  sections,
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outFile, buf); });
