import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const data = JSON.parse(await fs.readFile("report_data.json", "utf8"));
const outputDir = "outputs/pr_report_improved";
const outputPath = `${outputDir}/AVALAB_Fastboard_Avalin_Itrielt_PR_Report_Improved.xlsx`;

const brands = data.summary.map((x) => x.brand);
const activeBrands = data.summary.filter((x) => x.messages > 0);
const totalUnique = Number(data.content["Всего сообщений"] || 0);
const totalMentions = data.summary.reduce((s, x) => s + Number(x.messages || 0), 0);
const totalIndex = data.summary.reduce((s, x) => s + Number(x.media_index || 0), 0);
const totalPositive = data.summary.reduce((s, x) => s + Number(x.positive || 0), 0);
const totalNegative = data.summary.reduce((s, x) => s + Number(x.negative || 0), 0);
const totalMainRole = data.summary.reduce((s, x) => s + Number(x.main_role || 0), 0);
const topByMessages = [...data.summary].sort((a, b) => b.messages - a.messages)[0];
const topByEfficiency = [...activeBrands].sort((a, b) => b.media_index_per_mention - a.media_index_per_mention)[0];

function colName(n) {
  let s = "";
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - m) / 26);
  }
  return s;
}

function ref(row, col, rows = 1, cols = 1) {
  const start = `${colName(col)}${row}`;
  const end = `${colName(col + cols - 1)}${row + rows - 1}`;
  return start === end ? start : `${start}:${end}`;
}

function put(sheet, row, col, values) {
  const matrix = Array.isArray(values[0]) ? values : [[values]];
  sheet.getRange(ref(row, col, matrix.length, matrix[0].length)).values = matrix;
  return sheet.getRange(ref(row, col, matrix.length, matrix[0].length));
}

function styleBlock(range, fill = "#FFFFFF") {
  range.format = {
    fill,
    font: { name: "Aptos", size: 10, color: "#172033" },
    borders: { preset: "outside", style: "thin", color: "#D9DEE7" },
    verticalAlignment: "center",
  };
}

function styleHeader(range) {
  range.format = {
    fill: "#1F4E5F",
    font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
    borders: { preset: "outside", style: "thin", color: "#1F4E5F" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
}

function styleTitle(sheet, title, subtitle) {
  sheet.getRange("B2:O3").merge();
  const titleRange = put(sheet, 2, 2, title);
  titleRange.format = {
    fill: "#173A47",
    font: { name: "Aptos Display", size: 22, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  sheet.getRange("B2:O3").format.borders = { preset: "outside", style: "thin", color: "#173A47" };
  sheet.getRange("B4:O4").merge();
  const sub = put(sheet, 4, 2, subtitle);
  sub.format = {
    fill: "#E9F1F4",
    font: { name: "Aptos", size: 10, color: "#37515C" },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
}

function setupColumns(sheet) {
  const widths = [24, 24, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 16, 18, 18];
  widths.forEach((w, i) => {
    sheet.getRange(`${colName(i + 1)}1:${colName(i + 1)}120`).format.columnWidthPx = w * 7;
  });
  sheet.getRange("1:120").format.font = { name: "Aptos", size: 10, color: "#172033" };
}

function dateLabel(iso) {
  const [, m, d] = String(iso).split("-");
  return `${d}.${m}`;
}

function topDailySpike() {
  const rows = data.daily_mentions.map((row) => ({
    date: row.date,
    value: brands.reduce((s, b) => s + Number(row[b] || 0), 0),
  }));
  return rows.sort((a, b) => b.value - a.value)[0] || { date: "", value: 0 };
}

const wb = Workbook.create();

try {
  wb.theme.colorScheme.set({
    name: "PR Analytics",
    themeColors: {
      accent1: "#1F4E5F",
      accent2: "#2FA7A0",
      accent3: "#F2B84B",
      accent4: "#D95D59",
      bg1: "#FFFFFF",
      tx1: "#172033",
    },
  });
} catch {}

const dashboard = wb.worksheets.add("Дашборд");
setupColumns(dashboard);
styleTitle(
  dashboard,
  "PR-отчет по упоминаниям в СМИ",
  `${data.content["Объекты"]}. Период: ${data.content["Временной период"]}. Подготовлено: ${data.content["Дата подготовки отчета"]}.`
);
dashboard.getRange("B2:O3").format.rowHeightPx = 42;
dashboard.getRange("B4:O4").format.rowHeightPx = 28;

const kpis = [
  ["Уникальных сообщений", totalUnique, "Всего материалов в отчете"],
  ["Объектных упоминаний", totalMentions, "Сумма упоминаний по объектам"],
  ["Суммарный МедиаИндекс", totalIndex.toFixed(1), "Сила присутствия в медиаполе"],
  ["Доля негатива", `${Math.round((totalNegative / Math.max(totalMentions, 1)) * 100)}%`, "Репутационный риск месяца"],
  ["Позитивная доля", `${Math.round((totalPositive / Math.max(totalMentions, 1)) * 100)}%`, "Позитив среди объектных упоминаний"],
  ["Главная роль", `${Math.round((totalMainRole / Math.max(totalMentions, 1)) * 100)}%`, "Объект не просто упомянут, а является фокусом материала"],
];

let card = 0;
for (const r of [6, 10]) {
  for (const c of [2, 7, 12]) {
    const [label, value, note] = kpis[card++];
    const block = dashboard.getRange(ref(r, c, 3, 4));
    styleBlock(block, card === 4 ? "#FFF4E1" : "#F6F9FB");
    dashboard.getRange(ref(r, c, 1, 4)).merge();
    dashboard.getRange(ref(r + 1, c, 1, 4)).merge();
    dashboard.getRange(ref(r + 2, c, 1, 4)).merge();
    put(dashboard, r, c, label).format.font = { name: "Aptos", size: 10, color: "#5A6B75", bold: true };
    put(dashboard, r + 1, c, String(value)).format.font = { name: "Aptos Display", size: 20, color: "#173A47", bold: true };
    put(dashboard, r + 2, c, note).format.font = { name: "Aptos", size: 9, color: "#6B7780" };
  }
}

const spike = topDailySpike();
const insights = [
  ["Что важно", "Вывод"],
  ["Лидер месяца", `${topByMessages.brand}: ${topByMessages.messages} объектных упоминаний и МедиаИндекс ${topByMessages.media_index}.`],
  ["Качество присутствия", `${topByEfficiency.brand}: максимальный МедиаИндекс на одно упоминание (${topByEfficiency.media_index_per_mention.toFixed(2)}).`],
  ["Репутационный фон", `Негативных упоминаний не зафиксировано. Позитивная доля по всем объектам: ${Math.round((totalPositive / Math.max(totalMentions, 1)) * 100)}%.`],
  ["Инфоповод", `${data.top_events[0]["Событие"]} - главный драйвер месяца по количеству сообщений и МедиаИндексу.`],
  ["Динамика", `Пик активности: ${dateLabel(spike.date)} - ${spike.value} объектных упоминаний.`],
  ["Белое пятно", "Win Solutions не получил заметного присутствия в СМИ за период."],
];
put(dashboard, 15, 2, insights);
styleHeader(dashboard.getRange("B15:C15"));
styleBlock(dashboard.getRange("B16:C21"), "#FFFFFF");
dashboard.getRange("B15:C21").format.wrapText = true;
dashboard.getRange("B16:B21").format.font = { bold: true, color: "#173A47" };
dashboard.getRange("C16:C21").format.columnWidthPx = 420;
dashboard.getRange("15:21").format.rowHeightPx = 46;

const brandChartData = [["Объект", "Упоминания", "МедиаИндекс"], ...data.summary.map((x) => [x.brand, x.messages, x.media_index])];
put(dashboard, 24, 2, brandChartData);
styleHeader(dashboard.getRange("B24:D24"));
styleBlock(dashboard.getRange(ref(25, 2, data.summary.length, 3)));
dashboard.getRange(`C25:D${24 + data.summary.length}`).format.numberFormat = "0.0";

const dailyTotal = [["Дата", "Все объекты"], ...data.daily_mentions.map((row) => [dateLabel(row.date), brands.reduce((s, b) => s + Number(row[b] || 0), 0)])];
put(dashboard, 24, 6, dailyTotal);
styleHeader(dashboard.getRange("F24:G24"));
styleBlock(dashboard.getRange(ref(25, 6, data.daily_mentions.length, 2)));

dashboard.charts.add("column", {
  title: "Сравнение объектов",
  categories: data.summary.map((x) => x.brand),
  series: [
    { name: "Упоминания", values: data.summary.map((x) => x.messages) },
    { name: "МедиаИндекс", values: data.summary.map((x) => x.media_index) },
  ],
  hasLegend: true,
  legend: { position: "bottom" },
  from: { row: 23, col: 8 },
  extent: { widthPx: 520, heightPx: 280 },
});

dashboard.charts.add("line", {
  title: "Динамика активности по дням",
  categories: dailyTotal.slice(1).map((x) => x[0]),
  series: [{ name: "Упоминания", values: dailyTotal.slice(1).map((x) => x[1]) }],
  hasLegend: false,
  from: { row: 35, col: 1 },
  extent: { widthPx: 700, heightPx: 280 },
});

const comparison = wb.worksheets.add("Сравнение объектов");
setupColumns(comparison);
styleTitle(comparison, "Сравнение объектов мониторинга", "Сводная таблица для оценки объема, качества и роли упоминаний.");

const compRows = [
  ["Объект", "Упоминания", "МедиаИндекс", "МИ / упоминание", "Позитив", "Нейтрально", "Негатив", "Главная роль", "Цитирование", "Комментарий"],
  ...data.summary.map((x) => [
    x.brand,
    x.messages,
    x.media_index,
    x.media_index_per_mention,
    x.positive_share,
    x.neutral_share,
    x.negative_share,
    x.main_role_share,
    x.citation_share,
    x.messages === 0
      ? "Нет присутствия за период"
      : x.negative > 0
        ? "Требуется разбор негатива"
        : x.positive_share >= 0.8
          ? "Сильный позитивный фон"
          : x.media_index_per_mention >= 2.5
            ? "Высокая сила контакта"
            : "Нужно усиливать заметность",
  ]),
];
put(comparison, 7, 2, compRows);
styleHeader(comparison.getRange("B7:K7"));
styleBlock(comparison.getRange(ref(8, 2, data.summary.length, 10)));
comparison.getRange(`F8:J${7 + data.summary.length}`).format.numberFormat = "0%";
comparison.getRange(`D8:E${7 + data.summary.length}`).format.numberFormat = "0.00";
comparison.getRange(`C8:C${7 + data.summary.length}`).format.numberFormat = "0.0";
comparison.getRange(`E8:E${7 + data.summary.length}`).conditionalFormats.add("dataBar", { color: "#2FA7A0", gradient: true });
comparison.getRange(`H8:H${7 + data.summary.length}`).conditionalFormats.add("colorScale", {
  criteria: [
    { type: "lowestValue", color: "#FFFFFF" },
    { type: "highestValue", color: "#D95D59" },
  ],
});

comparison.charts.add("bar", {
  title: "Структура тональности",
  categories: data.summary.map((x) => x.brand),
  series: [
    { name: "Позитив", values: data.summary.map((x) => x.positive) },
    { name: "Нейтрально", values: data.summary.map((x) => x.neutral) },
    { name: "Негатив", values: data.summary.map((x) => x.negative) },
  ],
  hasLegend: true,
  legend: { position: "bottom" },
  barOptions: { direction: "bar", grouping: "stacked" },
  from: { row: 14, col: 1 },
  extent: { widthPx: 620, heightPx: 280 },
});

const events = wb.worksheets.add("Инфоповоды");
setupColumns(events);
styleTitle(events, "Инфоповоды и рекомендации", "Не только факты, но и интерпретация: что двигало медиаполе и что делать дальше.");
const eventRows = [
  ["Инфоповод", "Сообщения", "Охват", "Заметность", "МедиаИндекс", "Практический вывод"],
  ...data.top_events.map((x, i) => [
    x["Событие"],
    x["Количество сообщений"],
    x["Охват (из открытых источников)"],
    x["Заметность события"],
    x["МедиаИндекс"],
    i === 0
      ? "Использовать как главный кейс месяца и вынести в PR-summary."
      : Number(x["МедиаИндекс"] || 0) >= 10
        ? "Поддержать повторной коммуникацией и ссылками на первоисточник."
        : "Оставить в мониторинге как нишевый инфоповод.",
  ]),
];
put(events, 7, 2, eventRows);
styleHeader(events.getRange("B7:G7"));
styleBlock(events.getRange(ref(8, 2, data.top_events.length, 6)));
events.getRange("B8:B30").format.columnWidthPx = 420;
events.getRange("G8:G30").format.columnWidthPx = 300;
events.getRange("B8:G30").format.wrapText = true;
events.getRange("8:30").format.rowHeightPx = 44;
events.getRange(`E8:F${7 + data.top_events.length}`).format.numberFormat = "0.00";
events.charts.add("column", {
  title: "МедиаИндекс по инфоповодам",
  categories: data.top_events.map((x, i) => `#${i + 1}`),
  series: [{ name: "МедиаИндекс", values: data.top_events.map((x) => Number(x["МедиаИндекс"] || 0)) }],
  hasLegend: false,
  from: { row: 20, col: 1 },
  extent: { widthPx: 620, heightPx: 260 },
});

const sources = wb.worksheets.add("Источники и география");
setupColumns(sources);
styleTitle(sources, "Источники, регионы, авторы", "Срезы для планирования медиапула и региональной PR-активности.");
const sourceRows = [
  ["СМИ", ...brands, "Всего"],
  ...data.top_sources_count.slice(0, 12).map((x) => {
    const vals = brands.map((b) => Number(x[b] || 0));
    return [x["Наименование СМИ"], ...vals, vals.reduce((s, v) => s + v, 0)];
  }),
];
put(sources, 7, 2, sourceRows);
styleHeader(sources.getRange(ref(7, 2, 1, sourceRows[0].length)));
styleBlock(sources.getRange(ref(8, 2, sourceRows.length - 1, sourceRows[0].length)));
sources.getRange("B8:B25").format.columnWidthPx = 300;
sources.getRange("B8:B25").format.wrapText = true;

const regionRows = [["Регион", "Упоминания", "МедиаИндекс"]];
for (const row of data.regions_raw.slice(2)) {
  const region = row[0];
  if (!region) continue;
  let mentions = 0;
  let index = 0;
  for (let i = 1; i < row.length; i += 2) {
    mentions += Number(row[i] || 0);
    index += Number(row[i + 1] || 0);
  }
  regionRows.push([region, mentions, index]);
}
put(sources, 7, 12, regionRows);
styleHeader(sources.getRange("L7:N7"));
styleBlock(sources.getRange(ref(8, 12, regionRows.length - 1, 3)));
sources.getRange(`N8:N${6 + regionRows.length}`).format.numberFormat = "0.0";
sources.charts.add("column", {
  title: "Регионы по упоминаниям",
  categories: regionRows.slice(1).map((x) => x[0]),
  series: [{ name: "Упоминания", values: regionRows.slice(1).map((x) => x[1]) }],
  hasLegend: false,
  from: { row: 20, col: 10 },
  extent: { widthPx: 520, heightPx: 260 },
});

const authorRows = [
  ["Автор", ...brands, "МедиаИндекс"],
  ...data.authors.slice(0, 10).map((x) => [x["Автор"], ...brands.map((b) => Number(x[b] || 0)), Number(x["МедиаИндекс"] || 0)]),
];
put(sources, 24, 2, authorRows);
styleHeader(sources.getRange(ref(24, 2, 1, authorRows[0].length)));
styleBlock(sources.getRange(ref(25, 2, authorRows.length - 1, authorRows[0].length)));

const words = wb.worksheets.add("Слова и темы");
setupColumns(words);
styleTitle(words, "Слова, рубрики и тематические кластеры", "Материал для настройки словарей, тегов и автокатегоризации в SaaS-платформе.");
const wordRows = [
  ["Слово", ...brands, "Всего"],
  ...data.words.map((x) => {
    const vals = brands.map((b) => Number(x[b] || 0));
    return [x["Слово"], ...vals, vals.reduce((s, v) => s + v, 0)];
  }),
];
put(words, 7, 2, wordRows);
styleHeader(words.getRange(ref(7, 2, 1, wordRows[0].length)));
styleBlock(words.getRange(ref(8, 2, wordRows.length - 1, wordRows[0].length)));
words.getRange(`H8:H${7 + data.words.length}`).conditionalFormats.add("dataBar", { color: "#F2B84B", gradient: true });

const raw = wb.worksheets.add("Данные");
setupColumns(raw);
styleTitle(raw, "Данные для импорта в продукт", "Чистые таблицы, из которых строятся дашборды и отчеты.");
put(raw, 7, 2, [["Объект", "Упоминания", "МедиаИндекс", "Негатив", "Нейтрально", "Позитив", "Главная роль", "Цитирование"], ...data.summary.map((x) => [x.brand, x.messages, x.media_index, x.negative, x.neutral, x.positive, x.main_role, x.citations])]);
styleHeader(raw.getRange("B7:I7"));
styleBlock(raw.getRange(ref(8, 2, data.summary.length, 8)));
put(raw, 16, 2, [["Дата", ...brands], ...data.daily_mentions.map((row) => [row.date, ...brands.map((b) => row[b] || 0)])]);
styleHeader(raw.getRange(ref(16, 2, 1, brands.length + 1)));
styleBlock(raw.getRange(ref(17, 2, data.daily_mentions.length, brands.length + 1)));
raw.freezePanes.freezeRows(16);

for (const sheet of [dashboard, comparison, events, sources, words, raw]) {
  try {
    sheet.getRange("A1:A120").format.columnWidthPx = 18;
  } catch {}
}

const errorScan = await wb.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
if (errorScan.ndjson && !errorScan.ndjson.includes("no matches")) {
  console.log(errorScan.ndjson);
}

await fs.mkdir(outputDir, { recursive: true });
for (const sheetName of ["Дашборд", "Сравнение объектов", "Инфоповоды", "Источники и география", "Слова и темы", "Данные"]) {
  const png = await wb.render({ sheetName, range: "A1:O45", format: "png", scale: 1 });
  await fs.writeFile(`${outputDir}/${sheetName}.png`, Buffer.from(await png.arrayBuffer()));
}
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(outputPath);
console.log(outputPath);
