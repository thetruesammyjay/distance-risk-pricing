import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { createCanvas } = require(process.env.CANVAS_MODULE ?? "@napi-rs/canvas");

const root = process.cwd();
const outputDir = path.join(root, "docs", "diagrams");
fs.mkdirSync(outputDir, { recursive: true });

const colors = {
  page: "#f8fafc",
  ink: "#172033",
  muted: "#526176",
  blue: "#dbeafe",
  blueStroke: "#2563eb",
  violet: "#ede9fe",
  violetStroke: "#7c3aed",
  green: "#dcfce7",
  greenStroke: "#15803d",
  amber: "#fef3c7",
  amberStroke: "#b45309",
  rose: "#ffe4e6",
  roseStroke: "#be123c",
  slate: "#e2e8f0",
  slateStroke: "#475569",
  white: "#ffffff",
};

const esc = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const htmlLabel = (value) => esc(value).replaceAll("\n", "<br>");
const drawioText = (value) => String(value).replaceAll("\n", "<br>");
const xmlAttr = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

function node(id, label, x, y, w, h, kind = "rect", style = {}) {
  return { id, label, x, y, w, h, kind, ...style };
}

function edge(source, target, points, label = "", style = {}) {
  return { source, target, points, label, ...style };
}

function center(n) {
  return { x: n.x + n.w / 2, y: n.y + n.h / 2 };
}

function drawText(ctx, text, x, y, maxWidth, options = {}) {
  const size = options.size ?? 16;
  const weight = options.weight ?? "400";
  const color = options.color ?? colors.ink;
  const lineHeight = options.lineHeight ?? Math.round(size * 1.3);
  ctx.font = `${weight} ${size}px Arial`;
  ctx.fillStyle = color;
  ctx.textAlign = options.align ?? "center";
  ctx.textBaseline = "middle";

  const lines = [];
  for (const paragraph of String(text).split("\n")) {
    const words = paragraph.split(/\s+/).filter(Boolean);
    if (!words.length) {
      lines.push("");
      continue;
    }
    let line = "";
    for (const word of words) {
      const candidate = line ? `${line} ${word}` : word;
      if (line && ctx.measureText(candidate).width > maxWidth) {
        lines.push(line);
        line = word;
      } else {
        line = candidate;
      }
    }
    lines.push(line);
  }

  const startY = y - ((lines.length - 1) * lineHeight) / 2;
  lines.forEach((line, index) => ctx.fillText(line, x, startY + index * lineHeight));
  return lines.length;
}

function roundedRect(ctx, x, y, w, h, radius, fill, stroke, dashed = false) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, radius);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2;
  ctx.setLineDash(dashed ? [8, 6] : []);
  ctx.stroke();
  ctx.setLineDash([]);
}

function drawNode(ctx, n) {
  const fill = n.fill ?? colors.white;
  const stroke = n.stroke ?? colors.slateStroke;
  if (n.kind === "actor") {
    const cx = n.x + n.w / 2;
    const headY = n.y + 22;
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, headY, 12, 0, Math.PI * 2);
    ctx.moveTo(cx, headY + 12);
    ctx.lineTo(cx, n.y + 58);
    ctx.moveTo(cx - 24, n.y + 32);
    ctx.lineTo(cx + 24, n.y + 32);
    ctx.moveTo(cx, n.y + 58);
    ctx.lineTo(cx - 19, n.y + 82);
    ctx.moveTo(cx, n.y + 58);
    ctx.lineTo(cx + 19, n.y + 82);
    ctx.stroke();
    drawText(ctx, n.label, cx, n.y + n.h - 14, n.w, { size: 14, weight: "600" });
    return;
  }
  if (n.kind === "diamond") {
    ctx.beginPath();
    ctx.moveTo(n.x + n.w / 2, n.y);
    ctx.lineTo(n.x + n.w, n.y + n.h / 2);
    ctx.lineTo(n.x + n.w / 2, n.y + n.h);
    ctx.lineTo(n.x, n.y + n.h / 2);
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.stroke();
    drawText(ctx, n.label, n.x + n.w / 2, n.y + n.h / 2, n.w * 0.65, { size: 14, weight: "600" });
    return;
  }
  if (n.kind === "ellipse") {
    ctx.beginPath();
    ctx.ellipse(n.x + n.w / 2, n.y + n.h / 2, n.w / 2, n.h / 2, 0, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.stroke();
    drawText(ctx, n.label, n.x + n.w / 2, n.y + n.h / 2, n.w * 0.72, { size: 14, weight: "600" });
    return;
  }
  if (n.kind === "database") {
    const ry = Math.min(18, n.h * 0.17);
    const cx = n.x + n.w / 2;
    const rx = n.w / 2;
    ctx.fillStyle = fill;
    ctx.fillRect(n.x, n.y + ry, n.w, n.h - 2 * ry);
    ctx.beginPath();
    ctx.ellipse(cx, n.y + n.h - ry, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx, n.y + ry, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = stroke;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(n.x, n.y + ry);
    ctx.lineTo(n.x, n.y + n.h - ry);
    ctx.moveTo(n.x + n.w, n.y + ry);
    ctx.lineTo(n.x + n.w, n.y + n.h - ry);
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(cx, n.y + ry, rx, ry, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(cx, n.y + n.h - ry, rx, ry, 0, 0, Math.PI * 2);
    ctx.stroke();
    drawText(ctx, n.label, cx, n.y + n.h / 2, n.w * 0.78, { size: 14, weight: "600" });
    return;
  }
  if (n.kind === "class") {
    roundedRect(ctx, n.x, n.y, n.w, n.h, 8, fill, stroke, n.dashed);
    const headerH = n.interface ? 52 : 34;
    ctx.fillStyle = stroke;
    ctx.beginPath();
    ctx.roundRect(n.x, n.y, n.w, headerH, 8);
    ctx.fill();
    ctx.fillRect(n.x, n.y + headerH - 10, n.w, 10);
    if (n.interface) {
      drawText(ctx, "<<interface>>", n.x + n.w / 2, n.y + 12, n.w - 20, { size: 10, weight: "400", color: colors.white });
      drawText(ctx, n.title, n.x + n.w / 2, n.y + 34, n.w - 20, { size: 14, weight: "700", color: colors.white });
    } else {
      drawText(ctx, n.title, n.x + n.w / 2, n.y + 17, n.w - 20, { size: 15, weight: "700", color: colors.white });
    }
    const members = n.members ?? [];
    members.forEach((member, index) => {
      drawText(ctx, member, n.x + 12, n.y + headerH + 14 + index * 22, n.w - 24, { size: 11, align: "left", color: colors.ink });
    });
    return;
  }
  if (n.kind === "entity") {
    roundedRect(ctx, n.x, n.y, n.w, n.h, 4, fill, stroke, n.dashed);
    const headerH = 42;
    ctx.fillStyle = stroke;
    ctx.fillRect(n.x, n.y, n.w, headerH);
    drawText(ctx, n.title, n.x + n.w / 2, n.y + headerH / 2, n.w - 20, { size: 17, weight: "700", color: colors.white });
    const rowH = (n.h - headerH) / n.fields.length;
    n.fields.forEach((field, index) => {
      const top = n.y + headerH + index * rowH;
      if (index % 2 === 0) {
        ctx.fillStyle = "#f1f5f9";
        ctx.fillRect(n.x + 1, top, n.w - 2, rowH);
      }
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(n.x, top);
      ctx.lineTo(n.x + n.w, top);
      ctx.stroke();
      const marker = field.key ? `${field.key} ` : "";
      drawText(ctx, `${marker}${field.name}`, n.x + 14, top + rowH / 2, n.w * 0.55, { size: 11, align: "left", weight: field.key ? "700" : "400" });
      drawText(ctx, field.type, n.x + n.w - 14, top + rowH / 2, n.w * 0.38, { size: 10, align: "right", color: colors.muted });
    });
    return;
  }
  if (n.kind === "note") {
    roundedRect(ctx, n.x, n.y, n.w, n.h, 6, colors.amber, colors.amberStroke, true);
    drawText(ctx, n.label, n.x + n.w / 2, n.y + n.h / 2, n.w - 20, { size: 13, color: colors.ink });
    return;
  }
  roundedRect(ctx, n.x, n.y, n.w, n.h, n.kind === "round" ? 24 : 8, fill, stroke, n.dashed);
  drawText(ctx, n.label, n.x + n.w / 2, n.y + n.h / 2, n.w - 24, { size: n.fontSize ?? 14, weight: "600" });
}

function arrowHead(ctx, from, to, color, open = false) {
  const angle = Math.atan2(to.y - from.y, to.x - from.x);
  const length = 10;
  const wing = Math.PI / 7;
  const a = { x: to.x - length * Math.cos(angle - wing), y: to.y - length * Math.sin(angle - wing) };
  const b = { x: to.x - length * Math.cos(angle + wing), y: to.y - length * Math.sin(angle + wing) };
  ctx.beginPath();
  ctx.moveTo(to.x, to.y);
  ctx.lineTo(a.x, a.y);
  ctx.lineTo(b.x, b.y);
  ctx.closePath();
  if (open) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  } else {
    ctx.fillStyle = color;
    ctx.fill();
  }
}

function pathMidpoint(points) {
  let total = 0;
  for (let index = 1; index < points.length; index += 1) {
    total += Math.hypot(points[index].x - points[index - 1].x, points[index].y - points[index - 1].y);
  }
  let remaining = total / 2;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const length = Math.hypot(current.x - previous.x, current.y - previous.y);
    if (remaining <= length) {
      const ratio = length === 0 ? 0 : remaining / length;
      return {
        point: { x: previous.x + (current.x - previous.x) * ratio, y: previous.y + (current.y - previous.y) * ratio },
        previous,
      };
    }
    remaining -= length;
  }
  return { point: points.at(-1), previous: points.at(-2) };
}

function drawEdge(ctx, e, nodes) {
  const source = nodes.get(e.source);
  const target = nodes.get(e.target);
  const points = e.points ?? [center(source), center(target)];
  ctx.strokeStyle = e.color ?? colors.slateStroke;
  ctx.lineWidth = e.width ?? 1.8;
  ctx.setLineDash(e.dashed ? [8, 6] : []);
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.stroke();
  ctx.setLineDash([]);
  if (e.arrow !== false) arrowHead(ctx, points.at(-2), points.at(-1), e.color ?? colors.slateStroke, e.openArrow);
  if (e.label) {
    const midpoint = pathMidpoint(points);
    const mid = midpoint.point;
    const previous = midpoint.previous;
    const dx = mid.x - previous.x;
    const dy = mid.y - previous.y;
    const horizontal = Math.abs(dx) >= Math.abs(dy);
    const labelX = mid.x + (horizontal ? 0 : (e.labelOffset ?? 22));
    const labelY = mid.y + (horizontal ? (e.labelOffset ?? -18) : 0);
    const labelWidth = e.labelWidth ?? 120;
    ctx.fillStyle = colors.page;
    ctx.fillRect(labelX - labelWidth / 2, labelY - 15, labelWidth, 30);
    drawText(ctx, e.label, labelX, labelY, labelWidth - 8, { size: e.fontSize ?? 12, weight: "600", color: e.color ?? colors.slateStroke });
  }
}

function classValue(n) {
  const interfaceLine = n.interface ? `&lt;&lt;interface&gt;&gt;<br>` : "";
  return `${interfaceLine}<b>${n.title}</b><hr>${n.members.join("<br>")}`;
}

function entityValue(n) {
  const rows = n.fields.map((field) => `<tr><td>${field.key ? `<b>${field.key}</b> ` : ""}${field.name}</td><td align="right">${field.type}</td></tr>`).join("");
  return `<table border="1" cellpadding="5" cellspacing="0" width="100%"><tr><th colspan="2">${n.title}</th></tr>${rows}</table>`;
}

function drawioStyle(n) {
  if (n.kind === "actor") return "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;fillColor=#dbeafe;strokeColor=#2563eb;";
  if (n.kind === "ellipse") return "ellipse;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#15803d;";
  if (n.kind === "diamond") return "rhombus;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#b45309;";
  if (n.kind === "database") return "shape=cylinder;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#7c3aed;";
  if (n.kind === "class") return `shape=umlClass;html=1;whiteSpace=wrap;fillColor=#${n.fill?.slice(1) ?? "ffffff"};strokeColor=#${n.stroke?.slice(1) ?? "475569"};${n.dashed ? "dashed=1;" : ""}`;
  if (n.kind === "entity") return "shape=table;html=1;whiteSpace=wrap;fillColor=#ffffff;strokeColor=#475569;";
  if (n.kind === "note") return "shape=note;whiteSpace=wrap;html=1;fillColor=#fef3c7;strokeColor=#b45309;dashed=1;";
  const fill = n.fill?.slice(1) ?? "ffffff";
  const stroke = n.stroke?.slice(1) ?? "475569";
  const rounded = n.kind === "round" ? "rounded=1;arcSize=24;" : "rounded=1;";
  return `${rounded}whiteSpace=wrap;html=1;fillColor=#${fill};strokeColor=#${stroke};${n.dashed ? "dashed=1;" : ""}`;
}

function drawioValue(n) {
  if (n.kind === "class") return classValue(n);
  if (n.kind === "entity") return entityValue(n);
  return drawioText(n.label);
}

function drawioXml(diagram) {
  const cells = ["<mxCell id=\"0\"/>", "<mxCell id=\"1\" parent=\"0\"/>"];
  for (const n of diagram.nodes) {
    const value = xmlAttr(drawioValue(n));
    cells.push(`<mxCell id=\"${n.id}\" value=\"${value}\" style=\"${drawioStyle(n)}\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"${n.x}\" y=\"${n.y}\" width=\"${n.w}\" height=\"${n.h}\" as=\"geometry\"/></mxCell>`);
  }
  for (const [index, e] of diagram.edges.entries()) {
    const points = e.points ?? [];
    const pointXml = points.length > 2 ? `<Array as=\"points\">${points.slice(1, -1).map((p) => `<mxPoint x=\"${p.x}\" y=\"${p.y}\"/>`).join("")}</Array>` : "";
    const style = `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=${e.arrow === false ? "none" : e.openArrow ? "open" : "block"};${e.dashed ? "dashed=1;" : ""}`;
    cells.push(`<mxCell id=\"edge-${index}\" value=\"${esc(e.label)}\" style=\"${style}\" edge=\"1\" parent=\"1\" source=\"${e.source}\" target=\"${e.target}\"><mxGeometry relative=\"1\" as=\"geometry\">${pointXml}</mxGeometry></mxCell>`);
  }
  return `<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" modified="2026-09-23T00:00:00.000Z" agent="Codex" version="24.7.17" type="device"><diagram id="${diagram.id}" name="${esc(diagram.name)}"><mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${diagram.width}" pageHeight="${diagram.height}" math="0" shadow="0"><root>${cells.join("")}</root></mxGraphModel></diagram></mxfile>`;
}

function render(diagram) {
  const canvas = createCanvas(diagram.width, diagram.height);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = colors.page;
  ctx.fillRect(0, 0, diagram.width, diagram.height);
  ctx.fillStyle = colors.ink;
  ctx.font = "700 22px Arial";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText(diagram.title, 28, 24);
  ctx.strokeStyle = "#cbd5e1";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(28, 58);
  ctx.lineTo(diagram.width - 28, 58);
  ctx.stroke();

  const nodes = new Map(diagram.nodes.map((n) => [n.id, n]));
  diagram.edges.forEach((e) => drawEdge(ctx, e, nodes));
  diagram.nodes.forEach((n) => drawNode(ctx, n));
  return canvas.toBuffer("image/png");
}

const architecture = {
  id: "architecture",
  name: "Architecture",
  title: "Figure 4.1 — Implemented distance-risk-aware pricing architecture",
  width: 1450,
  height: 900,
  nodes: [
    node("U", "Passenger or\nResearcher", 40, 390, 190, 70, "round", { fill: colors.blue, stroke: colors.blueStroke }),
    node("W", "Next.js Web\nApplication", 300, 150, 220, 70, "round", { fill: colors.blue, stroke: colors.blueStroke }),
    node("PX", "Next.js Server-side\nAPI Proxy", 300, 320, 250, 70, "round", { fill: colors.violet, stroke: colors.violetStroke }),
    node("API", "FastAPI API Gateway", 300, 490, 240, 70, "round", { fill: colors.violet, stroke: colors.violetStroke }),
    node("CAT", "FUTO CSV Location\nCatalog", 650, 90, 230, 70, "rect", { fill: colors.green, stroke: colors.greenStroke }),
    node("FES", "Fare Estimation\nService", 650, 490, 230, 70, "rect", { fill: colors.amber, stroke: colors.amberStroke }),
    node("REP", "Fare Quote\nRepository", 980, 90, 220, 70, "rect", { fill: colors.slate, stroke: colors.slateStroke }),
    node("DB", "PostgreSQL / Neon", 1230, 90, 180, 70, "database", { fill: colors.violet, stroke: colors.violetStroke }),
    node("RT", "Routing Service", 980, 350, 220, 70, "rect", { fill: colors.blue, stroke: colors.blueStroke }),
    node("OSRM", "OSRM Routing\nProvider", 1230, 350, 180, 70, "rect", { fill: colors.blue, stroke: colors.blueStroke }),
    node("RK", "Risk Service", 980, 500, 220, 70, "rect", { fill: colors.rose, stroke: colors.roseStroke }),
    node("RISK", "FUTO Survey /\nOptional Risk Provider", 1230, 500, 180, 70, "rect", { fill: colors.rose, stroke: colors.roseStroke }),
    node("DM", "Demand Service", 980, 650, 220, 70, "rect", { fill: colors.green, stroke: colors.greenStroke }),
    node("TOD", "Time-of-day\nDemand Provider", 1230, 650, 180, 70, "rect", { fill: colors.green, stroke: colors.greenStroke }),
    node("PE", "Pricing Engine", 650, 690, 230, 70, "rect", { fill: colors.amber, stroke: colors.amberStroke }),
  ],
  edges: [
    edge("U", "W", [{ x: 230, y: 425 }, { x: 265, y: 425 }, { x: 265, y: 185 }, { x: 300, y: 185 }]),
    edge("W", "PX", [{ x: 410, y: 220 }, { x: 410, y: 320 }]),
    edge("PX", "API", [{ x: 425, y: 390 }, { x: 425, y: 490 }]),
    edge("API", "CAT", [{ x: 540, y: 525 }, { x: 590, y: 525 }, { x: 590, y: 125 }, { x: 650, y: 125 }]),
    edge("API", "FES", [{ x: 540, y: 525 }, { x: 650, y: 525 }]),
    edge("FES", "REP", [{ x: 880, y: 525 }, { x: 930, y: 525 }, { x: 930, y: 125 }, { x: 980, y: 125 }]),
    edge("REP", "DB", [{ x: 1200, y: 125 }, { x: 1230, y: 125 }]),
    edge("FES", "RT", [{ x: 880, y: 525 }, { x: 930, y: 525 }, { x: 930, y: 385 }, { x: 980, y: 385 }]),
    edge("RT", "OSRM", [{ x: 1200, y: 385 }, { x: 1230, y: 385 }]),
    edge("FES", "RK", [{ x: 880, y: 525 }, { x: 980, y: 535 }]),
    edge("RK", "RISK", [{ x: 1200, y: 535 }, { x: 1230, y: 535 }]),
    edge("FES", "DM", [{ x: 880, y: 525 }, { x: 930, y: 525 }, { x: 930, y: 685 }, { x: 980, y: 685 }]),
    edge("DM", "TOD", [{ x: 1200, y: 685 }, { x: 1230, y: 685 }]),
    edge("FES", "PE", [{ x: 765, y: 560 }, { x: 765, y: 690 }]),
  ],
};

const useCase = {
  id: "use-case",
  name: "Use Case",
  title: "Figure 4.2 — Use case view of the implemented system",
  width: 1500,
  height: 900,
  nodes: [
    node("P", "Passenger /\nResearcher", 55, 280, 150, 110, "actor", { fill: colors.blue, stroke: colors.blueStroke }),
    node("D", "Developer /\nResearcher", 55, 650, 150, 110, "actor", { fill: colors.violet, stroke: colors.violetStroke }),
    node("R", "OSRM Routing\nProvider", 1270, 120, 160, 90, "actor", { fill: colors.blue, stroke: colors.blueStroke }),
    node("K", "Risk Data\nProvider", 1270, 310, 160, 90, "actor", { fill: colors.rose, stroke: colors.roseStroke }),
    node("B", "PostgreSQL\nDatabase", 1270, 550, 160, 90, "database", { fill: colors.violet, stroke: colors.violetStroke }),
    node("UC1", "View FUTO\nendpoints", 300, 100, 220, 72, "ellipse", { fill: colors.green, stroke: colors.greenStroke }),
    node("UC2", "Select origin and\ndestination", 300, 220, 220, 72, "ellipse", { fill: colors.green, stroke: colors.greenStroke }),
    node("UC3", "Enter requested\ntrip time", 300, 340, 220, 72, "ellipse", { fill: colors.green, stroke: colors.greenStroke }),
    node("UC4", "Request fare\nestimate", 300, 460, 220, 72, "ellipse", { fill: colors.amber, stroke: colors.amberStroke }),
    node("UC7", "Configure\nmodel", 300, 650, 220, 72, "ellipse", { fill: colors.violet, stroke: colors.violetStroke }),
    node("UC8", "Run automated\ntests", 300, 770, 220, 72, "ellipse", { fill: colors.violet, stroke: colors.violetStroke }),
    node("UC5", "View route and\nfare breakdown", 700, 220, 240, 72, "ellipse", { fill: colors.amber, stroke: colors.amberStroke }),
    node("UC6", "Inspect risk and\ndemand provenance", 700, 360, 240, 72, "ellipse", { fill: colors.amber, stroke: colors.amberStroke }),
    node("UC9", "Persist and\nretrieve quote", 700, 550, 240, 72, "ellipse", { fill: colors.slate, stroke: colors.slateStroke }),
  ],
  edges: [],
};

const useCaseNodes = new Map(useCase.nodes.map((n) => [n.id, n]));
useCase.edges = [
  ...[["P", "UC1"], ["P", "UC2"], ["P", "UC3"], ["P", "UC4"], ["P", "UC5"], ["P", "UC6"], ["D", "UC7"], ["D", "UC8"], ["D", "UC6"]].map(([a, b]) => edge(a, b, [center(useCaseNodes.get(a)), center(useCaseNodes.get(b))], "", { arrow: false, dashed: true })),
  edge("UC4", "R", [{ x: 520, y: 496 }, { x: 1100, y: 496 }, { x: 1100, y: 165 }, { x: 1270, y: 165 }]),
  edge("UC4", "K", [{ x: 520, y: 496 }, { x: 1120, y: 496 }, { x: 1120, y: 355 }, { x: 1270, y: 355 }]),
  edge("UC4", "UC9", [{ x: 520, y: 496 }, { x: 610, y: 496 }, { x: 610, y: 586 }, { x: 700, y: 586 }]),
  edge("UC9", "B", [{ x: 940, y: 586 }, { x: 1270, y: 595 }]),
];

const activity = {
  id: "activity",
  name: "Activity",
  title: "Figure 4.3 — Activity diagram for fare estimation",
  width: 1350,
  height: 1350,
  nodes: [
    node("S", "Start", 570, 80, 180, 55, "ellipse", { fill: colors.green, stroke: colors.greenStroke }),
    node("L", "Load FUTO endpoint\ncatalog", 510, 180, 300, 70, "rect", { fill: colors.blue, stroke: colors.blueStroke }),
    node("I", "User selects origin,\ndestination, and time", 510, 300, 300, 70, "rect", { fill: colors.blue, stroke: colors.blueStroke }),
    node("V", "Request\nvalid?", 560, 420, 200, 100, "diamond", { fill: colors.amber, stroke: colors.amberStroke }),
    node("E1", "Return validation\nerror", 110, 440, 260, 70, "rect", { fill: colors.rose, stroke: colors.roseStroke }),
    node("R", "Calculate route\nwith OSRM", 510, 590, 300, 70, "rect", { fill: colors.blue, stroke: colors.blueStroke }),
    node("RQ", "Route\navailable?", 560, 710, 200, 100, "diamond", { fill: colors.amber, stroke: colors.amberStroke }),
    node("E2", "Return routing\nerror", 1000, 730, 260, 70, "rect", { fill: colors.rose, stroke: colors.roseStroke }),
    node("K", "Assess route risk", 510, 870, 300, 70, "rect", { fill: colors.rose, stroke: colors.roseStroke }),
    node("D", "Generate time-of-day\ndemand scenario", 510, 970, 300, 70, "rect", { fill: colors.green, stroke: colors.greenStroke }),
    node("M", "Calculate demand\nmultiplier", 510, 1070, 300, 70, "rect", { fill: colors.green, stroke: colors.greenStroke }),
    node("F", "Calculate fare and\nbreakdown", 510, 1170, 300, 70, "rect", { fill: colors.amber, stroke: colors.amberStroke }),
    node("P", "Persist complete quote", 930, 1000, 260, 70, "rect", { fill: colors.slate, stroke: colors.slateStroke }),
    node("O", "Return quote, provenance,\nand timings", 930, 1120, 260, 70, "rect", { fill: colors.slate, stroke: colors.slateStroke }),
    node("X", "End", 570, 1270, 180, 45, "ellipse", { fill: colors.green, stroke: colors.greenStroke }),
  ],
  edges: [
    edge("S", "L", [{ x: 660, y: 135 }, { x: 660, y: 180 }]),
    edge("L", "I", [{ x: 660, y: 250 }, { x: 660, y: 300 }]),
    edge("I", "V", [{ x: 660, y: 370 }, { x: 660, y: 420 }]),
    edge("V", "E1", [{ x: 560, y: 470 }, { x: 370, y: 470 }], "No"),
    edge("E1", "X", [{ x: 240, y: 510 }, { x: 240, y: 1292 }, { x: 570, y: 1292 }]),
    edge("V", "R", [{ x: 660, y: 520 }, { x: 660, y: 590 }], "Yes"),
    edge("R", "RQ", [{ x: 660, y: 660 }, { x: 660, y: 710 }]),
    edge("RQ", "E2", [{ x: 760, y: 760 }, { x: 1000, y: 765 }], "No"),
    edge("E2", "X", [{ x: 1130, y: 800 }, { x: 1130, y: 1292 }, { x: 750, y: 1292 }]),
    edge("RQ", "K", [{ x: 660, y: 810 }, { x: 660, y: 870 }], "Yes"),
    edge("K", "D", [{ x: 660, y: 940 }, { x: 660, y: 970 }]),
    edge("D", "M", [{ x: 660, y: 1040 }, { x: 660, y: 1070 }]),
    edge("M", "F", [{ x: 660, y: 1140 }, { x: 660, y: 1170 }]),
    edge("F", "P", [{ x: 810, y: 1205 }, { x: 860, y: 1205 }, { x: 860, y: 1035 }, { x: 930, y: 1035 }]),
    edge("P", "O", [{ x: 1060, y: 1070 }, { x: 1060, y: 1120 }]),
    edge("O", "X", [{ x: 930, y: 1155 }, { x: 850, y: 1155 }, { x: 850, y: 1292 }, { x: 750, y: 1292 }]),
  ],
};

const sequenceParticipants = [
  ["User", "actor"], ["Web", "rect"], ["API", "rect"], ["FES", "rect"], ["Route", "rect"], ["OSRM", "rect"], ["Risk", "rect"], ["RiskProvider", "rect"], ["Demand", "rect"], ["Time", "rect"], ["Repo", "rect"], ["DB", "database"],
];
const sequence = {
  id: "sequence",
  name: "Sequence",
  title: "Figure 4.4 — Sequence diagram for a successful fare estimate",
  width: 2200,
  height: 1120,
  nodes: sequenceParticipants.map(([label, kind], index) => node(`s${index}`, label, 35 + index * 175, 90, 145, kind === "actor" ? 105 : 58, kind === "actor" ? "actor" : kind, { fill: index % 3 === 0 ? colors.blue : colors.slate, stroke: index % 3 === 0 ? colors.blueStroke : colors.slateStroke })),
  edges: [],
};
const seqX = Object.fromEntries(sequence.nodes.map((n) => [n.label, n.x + n.w / 2]));
const seqMessages = [
  ["User", "Web", "Select endpoints and requested time"],
  ["Web", "API", "POST /api/v1/fares/estimate"],
  ["API", "API", "Validate coordinates and timestamp"],
  ["API", "FES", "estimate(request)"],
  ["FES", "Route", "estimate(origin, destination)"],
  ["Route", "OSRM", "Request route"],
  ["OSRM", "Route", "Distance, duration, geometry"],
  ["Route", "FES", "RouteResult"],
  ["FES", "Risk", "assess(route, requested_at)"],
  ["Risk", "RiskProvider", "Get risk observation"],
  ["RiskProvider", "Risk", "Components and provenance"],
  ["Risk", "FES", "RiskEstimate"],
  ["FES", "Demand", "estimate(route, requested_at)"],
  ["Demand", "Time", "Get time-of-day snapshot"],
  ["Time", "Demand", "Synthetic requests and drivers"],
  ["Demand", "FES", "DemandEstimate and multiplier"],
  ["FES", "FES", "Calculate fare breakdown"],
  ["FES", "Repo", "Save complete quote"],
  ["Repo", "DB", "Insert fare_quotes record"],
  ["DB", "Repo", "Commit"],
  ["Repo", "FES", "Saved"],
  ["FES", "API", "FareEstimateResponse"],
  ["API", "Web", "JSON quote"],
  ["Web", "User", "Route, risk, demand, and fare"],
];
seqMessages.forEach(([from, to, label], index) => {
  const y = 210 + index * 34;
  const selfMessage = from === to;
  const points = selfMessage
    ? [{ x: seqX[from], y }, { x: seqX[from] + 62, y }, { x: seqX[from] + 62, y: y + 14 }, { x: seqX[from], y: y + 14 }]
    : [{ x: seqX[from], y }, { x: seqX[to], y }];
  sequence.edges.push(edge(`s${sequenceParticipants.findIndex(([name]) => name === from)}`, `s${sequenceParticipants.findIndex(([name]) => name === to)}`, points, label, { labelWidth: 150, fontSize: 12, openArrow: from === "OSRM" || from === "RiskProvider" || from === "Time" || from === "DB" || from === "Repo" || from === "FES" || from === "API" || from === "Web" && to === "User", dashed: from === "OSRM" || from === "RiskProvider" || from === "Time" || from === "DB" || from === "Repo" && to === "FES" }));
});
sequence.edges.push(...sequence.nodes.map((n) => edge(n.id, n.id, [{ x: n.x + n.w / 2, y: 150 }, { x: n.x + n.w / 2, y: 1080 }], "", { arrow: false, dashed: true, color: "#94a3b8", width: 1 })));

function classNode(id, title, x, y, w, members, style = {}) {
  const headerHeight = style.interface ? 52 : 34;
  return node(id, "", x, y, w, headerHeight + 14 + members.length * 22, "class", { title, members, ...style });
}

const classDiagram = {
  id: "class",
  name: "Class Diagram",
  title: "Figure 4.5 — Class diagram of the principal application services",
  width: 1550,
  height: 1240,
  nodes: [
    classNode("FES", "FareEstimationService", 35, 90, 350, ["+ estimate(request) FareEstimateResponse", "+ readiness() dict", "+ close() None"], { fill: colors.amber, stroke: colors.amberStroke }),
    classNode("Routing", "RoutingService", 470, 90, 300, ["+ estimate(origin, destination) RouteResult", "+ ready() bool"], { fill: colors.blue, stroke: colors.blueStroke }),
    classNode("OSRM", "OSRMAdapter", 1020, 90, 300, ["+ get_route(origin, destination) RouteResult", "+ health_check() bool"], { fill: colors.blue, stroke: colors.blueStroke }),
    classNode("Risk", "RiskService", 35, 370, 350, ["+ assess(origin, destination, requested_at) RiskEstimate", "+ ready() bool"], { fill: colors.rose, stroke: colors.roseStroke }),
    classNode("RiskProvider", "RiskProvider", 470, 340, 390, ["+ get_observation(origin, destination, requested_at) RiskObservation", "+ health_check() bool"], { fill: colors.rose, stroke: colors.roseStroke, interface: true, dashed: true }),
    classNode("Demand", "DemandService", 1020, 370, 300, ["+ estimate(origin, destination, requested_at) DemandEstimate", "+ ready() bool"], { fill: colors.green, stroke: colors.greenStroke }),
    classNode("Pricing", "PricingEngine", 35, 700, 300, ["+ calculate_fare(context, config) FareBreakdown"], { fill: colors.amber, stroke: colors.amberStroke }),
    classNode("DemandProvider", "DemandProvider", 470, 680, 390, ["+ get_snapshot(origin, destination, requested_at) DemandEstimate", "+ health_check() bool"], { fill: colors.green, stroke: colors.greenStroke, interface: true, dashed: true }),
    classNode("Time", "TimeOfDayDemandProvider", 1020, 680, 360, ["+ get_snapshot(origin, destination, requested_at) DemandEstimate", "+ health_check() bool"], { fill: colors.green, stroke: colors.greenStroke }),
    classNode("Repo", "FareQuoteRepository", 35, 1000, 350, ["+ save(quote) None", "+ get(quote_id) dict"], { fill: colors.slate, stroke: colors.slateStroke, interface: true, dashed: true }),
    classNode("MemoryRepo", "InMemoryFareQuoteRepository", 470, 1000, 360, [], { fill: colors.slate, stroke: colors.slateStroke }),
    classNode("SqlRepo", "SqlAlchemyFareQuoteRepository", 980, 1000, 400, [], { fill: colors.slate, stroke: colors.slateStroke }),
  ],
  edges: [
    edge("FES", "Routing", [{ x: 385, y: 135 }, { x: 470, y: 135 }]),
    edge("FES", "Risk", [{ x: 210, y: 204 }, { x: 210, y: 370 }]),
    edge("FES", "Demand", [{ x: 385, y: 180 }, { x: 900, y: 180 }, { x: 900, y: 415 }, { x: 1020, y: 415 }]),
    edge("FES", "Pricing", [{ x: 140, y: 204 }, { x: 140, y: 700 }]),
    edge("FES", "Repo", [{ x: 280, y: 204 }, { x: 280, y: 1000 }]),
    edge("Routing", "OSRM", [{ x: 770, y: 135 }, { x: 1020, y: 135 }]),
    edge("Risk", "RiskProvider", [{ x: 385, y: 416 }, { x: 470, y: 395 }]),
    edge("Demand", "DemandProvider", [{ x: 1020, y: 416 }, { x: 900, y: 416 }, { x: 900, y: 735 }, { x: 860, y: 735 }]),
    edge("Time", "DemandProvider", [{ x: 1020, y: 726 }, { x: 860, y: 726 }], "implements", { dashed: true, openArrow: true }),
    edge("MemoryRepo", "Repo", [{ x: 650, y: 1000 }, { x: 390, y: 1000 }], "implements", { dashed: true, openArrow: true }),
    edge("SqlRepo", "Repo", [{ x: 980, y: 1024 }, { x: 900, y: 1024 }, { x: 900, y: 1150 }, { x: 385, y: 1150 }, { x: 385, y: 1055 }], "implements", { dashed: true, openArrow: true }),
  ],
};

const erFields = [
  ["id", "VARCHAR(36)", "PK"], ["created_at", "TIMESTAMPTZ", ""], ["requested_at", "TIMESTAMPTZ", ""], ["origin_latitude", "NUMERIC(10,7)", ""], ["origin_longitude", "NUMERIC(10,7)", ""], ["destination_latitude", "NUMERIC(10,7)", ""], ["destination_longitude", "NUMERIC(10,7)", ""], ["distance_km", "NUMERIC(12,3)", ""], ["estimated_duration_minutes", "INTEGER", ""], ["risk_score", "NUMERIC(6,4)", ""], ["risk_classification", "VARCHAR(32)", ""], ["demand_multiplier", "NUMERIC(8,4)", ""], ["currency", "VARCHAR(3)", ""], ["base_fare", "NUMERIC(12,2)", ""], ["distance_component", "NUMERIC(12,2)", ""], ["risk_adjustment", "NUMERIC(12,2)", ""], ["demand_adjustment", "NUMERIC(12,2)", ""], ["total_fare", "NUMERIC(12,2)", ""], ["formula_mode", "VARCHAR(32)", ""], ["formula_version", "VARCHAR(32)", ""], ["pricing_coefficient_version", "VARCHAR(64)", ""], ["risk_source_summary", "TEXT", ""], ["demand_source_type", "VARCHAR(32)", ""], ["payload", "JSON", ""],
];
const er = {
  id: "er",
  name: "Entity Relationship Diagram",
  title: "Figure 4.6 — Physical entity relationship diagram",
  width: 1450,
  height: 1050,
  nodes: [node("FARE_QUOTES", "", 90, 90, 1270, 850, "entity", { title: "FARE_QUOTES", stroke: colors.slateStroke, fill: colors.white, fields: erFields.map(([name, type, key]) => ({ name, type, key })) })],
  edges: [],
};

const diagrams = [architecture, useCase, activity, sequence, classDiagram, er];
for (const diagram of diagrams) {
  const base = path.join(outputDir, `chapter-four-${diagram.id}`);
  fs.writeFileSync(`${base}.drawio`, drawioXml(diagram), "utf8");
  fs.writeFileSync(`${base}.png`, render(diagram));
}
console.log(`Generated ${diagrams.length} draw.io sources and PNG exports in ${path.relative(root, outputDir)}`);
