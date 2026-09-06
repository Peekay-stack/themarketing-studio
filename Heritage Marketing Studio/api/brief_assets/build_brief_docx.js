// Parameterised Word-document builder for the Comprehensive Brand Brief plugin.
// Usage: node build_brief_docx.js <brief.json> <output.docx>
//
// Reads a structured brief JSON (schema documented in references/docx-assembly.md),
// embeds the two PNG figures referenced inside it, and writes a paginated .docx.
//
// Assumes: docx >=8 is installed in the working directory (npm install docx).

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber,
} = require('docx');

const [,, briefJsonPath, outDocxPath] = process.argv;
if (!briefJsonPath || !outDocxPath) {
  console.error('Usage: node build_brief_docx.js <brief.json> <output.docx>');
  process.exit(1);
}

const brief = JSON.parse(fs.readFileSync(briefJsonPath, 'utf8'));
const briefDir = path.dirname(path.resolve(briefJsonPath));

const CONTENT_WIDTH = 10080;
const SOFT_BORDER = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
const SOFT_BORDERS = { top: SOFT_BORDER, bottom: SOFT_BORDER, left: SOFT_BORDER, right: SOFT_BORDER };
const CELL_MARGINS = { top: 80, bottom: 80, left: 120, right: 120 };
const GREEN = '3F814C';

function P(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 100, ...(opts.spacing || {}) },
    alignment: opts.alignment,
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italics, size: opts.size || 22, color: opts.color })],
  });
}

function PR(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: 100, ...(opts.spacing || {}) },
    alignment: opts.alignment,
    children: runs,
  });
}

function H1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28 })],
  });
}

function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, size: 24 })],
  });
}

function Bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 22 })],
  });
}

function Numbered(text) {
  return new Paragraph({
    numbering: { reference: 'numbers', level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 22 })],
  });
}

function cell(text, width, opts = {}) {
  const isHeader = opts.header === true;
  return new TableCell({
    borders: SOFT_BORDERS,
    width: { size: width, type: WidthType.DXA },
    margins: CELL_MARGINS,
    shading: isHeader ? { fill: 'F0F0F0', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.TOP,
    children: [new Paragraph({
      children: [new TextRun({
        text,
        bold: isHeader || opts.bold,
        italics: opts.italics,
        size: opts.size || 20,
      })],
    })],
  });
}

function imageFigure(figurePath, widthPx, heightPx, caption) {
  const abs = path.isAbsolute(figurePath) ? figurePath : path.join(briefDir, figurePath);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 80 },
      children: [new ImageRun({
        type: 'png',
        data: fs.readFileSync(abs),
        transformation: { width: widthPx, height: heightPx },
        altText: { title: caption, description: caption, name: path.basename(abs) },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: caption, italics: true, size: 18, color: '666666' })],
    }),
  ];
}

const titleBlock = [
  new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: `${brief.brand} — Brand Brief`, bold: true, size: 36 })],
  }),
  new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: `Prepared for: ${brief.prepared_for}   ·   Date: ${brief.date}`, size: 20, color: '666666' })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    children: [new TextRun({ text: `Sources: ${brief.sources_note}`, italics: true, size: 18, color: '666666' })],
  }),
];

const execSummary = [
  H1('1. Executive Summary'),
  ...brief.executive_summary.map((para) => P(para, { size: 22 })),
  PR([new TextRun({ text: brief.smp, bold: true, italics: true, size: 24 })], {
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 200 },
  }),
];

const competitorCols = [1600, 2200, 3100, 3180];
const competitorRows = [
  ['Competitor', 'Hero brands', 'Positioning in one line', 'Recent strategic moves'],
  ...brief.competitors.map((c) => [c.name, c.hero_brands, c.positioning, c.recent_moves]),
];
const competitorTable = new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: competitorCols,
  rows: competitorRows.map((row, ri) => new TableRow({
    children: row.map((text, ci) => cell(text, competitorCols[ci], { header: ri === 0 })),
  })),
});

const matrixBrands = brief.messaging_matrix.brands;
const matrixDims = brief.messaging_matrix.dimensions;
const matrixCells = brief.messaging_matrix.cells;
const matrixHeader = ['Dimension', ...matrixBrands];
const matrixDataRows = matrixDims.map((dim, di) => [dim, ...matrixCells[di]]);
const matrixColCount = matrixHeader.length;
const firstCol = 1400;
const otherCols = Math.floor((CONTENT_WIDTH - firstCol) / (matrixColCount - 1));
const matrixCols = [firstCol, ...Array(matrixColCount - 1).fill(otherCols)];
const matrixDelta = CONTENT_WIDTH - matrixCols.reduce((a, b) => a + b, 0);
matrixCols[matrixCols.length - 1] += matrixDelta;
const matrixTable = new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: matrixCols,
  rows: [matrixHeader, ...matrixDataRows].map((row, ri) => new TableRow({
    children: row.map((text, ci) => cell(text, matrixCols[ci], { header: ri === 0, size: 18 })),
  })),
});

const needscope = [
  H1('4. NeedScope Brand Positioning'),
  P('NeedScope (Kantar) maps brands across six colour-coded emotional territories arranged on a wheel: Power (Red) and Vitality (Yellow) are extroverted needs, Belonging (Green) and Security (Blue) are introverted needs, while Discernment (Purple) and Freedom (Orange) sit on the diagonals.', { size: 22 }),
  ...imageFigure(brief.needscope.figure_path, 540, 432, 'Figure 1. NeedScope wheel and strategic bridge for the brand and its competitive set.'),
  H2('Reading the wheel'),
  P(brief.needscope.reading, { size: 22 }),
  H2('Strategic implication'),
  P(brief.needscope.strategic_implication, { size: 22 }),
];

const cdSection = [
  H1('5. Messaging Strategy — Current → Desired'),
  P('The messaging job is most clearly framed as the shift the work has to deliver, not just what it has to say.', { size: 22 }),
  ...imageFigure(brief.cb_ca_db_da.figure_path, 600, 345, 'Figure 2. Current Behaviour & Attitude → Desired Behaviour & Attitude.'),
  PR([
    new TextRun({ text: 'The shift in one line: ', size: 22 }),
    new TextRun({ text: brief.cb_ca_db_da.shift_line, bold: true, size: 22 }),
    new TextRun({ text: ' ' + brief.cb_ca_db_da.caption, size: 22 }),
  ]),
];

const smpSection = [
  H1('6. Single Minded Proposition'),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 160 },
    border: {
      top: { style: BorderStyle.SINGLE, size: 6, color: GREEN, space: 6 },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: GREEN, space: 6 },
    },
    children: [new TextRun({ text: brief.smp, bold: true, italics: true, size: 32, color: GREEN })],
  }),
  H2(`Why only ${brief.brand} can say it`),
  ...brief.smp_defence.map((d) => Bullet(`${d.competitor}: ${d.why_collapses}`)),
  H2('What the SMP unlocks (illustrative — not final copy)'),
  Bullet(`Brand line: ${brief.smp_unlocks.brand_line}`),
  Bullet(`Mass line: ${brief.smp_unlocks.mass_line}`),
  Bullet(`Activation: ${brief.smp_unlocks.activation}`),
  Bullet(`Product: ${brief.smp_unlocks.product}`),
];

const pdcSection = [
  H1('7. Pricing, Distribution & Content Snapshot'),
  H2('Pricing'),
  P(brief.snapshots.pricing, { size: 22 }),
  H2('Distribution'),
  P(brief.snapshots.distribution, { size: 22 }),
  H2('Content & campaigns'),
  P(brief.snapshots.content_campaigns, { size: 22 }),
  H2('Content gaps to claim now'),
  P(brief.snapshots.content_gaps, { size: 22 }),
];

const otCols = [5040, 5040];
const otRows = [
  ['Opportunities', 'Threats'],
  ...brief.opportunities_threats.map((r) => [r.opportunity, r.threat]),
];
const otTable = new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: otCols,
  rows: otRows.map((row, ri) => new TableRow({
    children: row.map((text, ci) => cell(text, otCols[ci], { header: ri === 0, size: 20 })),
  })),
});

const recSection = [
  H1('9. Recommended Actions'),
  PR([new TextRun({ text: brief.recommendations.preface, italics: true, size: 22, color: '555555' })], { spacing: { after: 120 } }),
  H2('Quick wins (this quarter)'),
  ...brief.recommendations.quick_wins.map((s) => Bullet(s)),
  H2('Strategic moves (12–18 months)'),
  ...brief.recommendations.strategic_moves.map((s) => Numbered(s)),
];

const caveatsSection = [
  H1('10. Caveats'),
  P(brief.caveats, { size: 22 }),
  PR([new TextRun({ text: 'Prepared via the Comprehensive Brand Brief plugin.', italics: true, size: 18, color: '777777' })], { spacing: { before: 200, after: 80 } }),
];

const doc = new Document({
  creator: 'Comprehensive Brand Brief plugin',
  title: `${brief.brand} Brand Brief`,
  description: `Brand strategy brief for ${brief.brand} integrating NeedScope, CB/CA → DB/DA, and SMP.`,
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Arial', color: '2A2A2A' },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: 'Arial', color: GREEN },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bullets',
        levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: 'numbers',
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: `${brief.brand} Brand Brief  ·  `, size: 18, color: '888888' }),
            new TextRun({ children: ['Page ', PageNumber.CURRENT, ' of ', PageNumber.TOTAL_PAGES], size: 18, color: '888888' }),
          ],
        })],
      }),
    },
    children: [
      ...titleBlock,
      ...execSummary,
      H1('2. Competitor Snapshot'),
      competitorTable,
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun('')] }),
      H1('3. Messaging Comparison Matrix'),
      matrixTable,
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun('')] }),
      ...needscope,
      ...cdSection,
      ...smpSection,
      ...pdcSection,
      H1('8. Opportunities & Threats'),
      otTable,
      new Paragraph({ spacing: { after: 120 }, children: [new TextRun('')] }),
      ...recSection,
      ...caveatsSection,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outDocxPath, buf);
  console.log(`wrote ${outDocxPath} (${buf.length} bytes)`);
});
