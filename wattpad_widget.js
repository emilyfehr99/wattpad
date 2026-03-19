// Wattpad Stats Widget for Scriptable
// Created for wlwsports (Emily Fehr)
// Instructions: Copy this code, open Scriptable on iPhone, create a new script named "Wattpad", and paste.

const DATA_URL = "https://raw.githubusercontent.com/emilyfehr99/wattpad/main/wattpad_stats.json";

async function createWidget() {
  let data;
  try {
    let req = new Request(DATA_URL);
    data = await req.loadJSON();
  } catch (e) {
    return createErrorWidget("Failed to load data");
  }

  const widget = new ListWidget();
  widget.backgroundColor = new Color("#FF8B10"); // Wattpad Orange

  // Title Row
  let titleRow = widget.addStack();
  let title = titleRow.addText("WATTPAD STATS");
  title.font = Font.boldSystemFont(14);
  title.textColor = Color.white();
  titleRow.addSpacer();
  
  // Date/Time
  let dateText = titleRow.addText(new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  dateText.font = Font.systemFont(10);
  dateText.textColor = new Color("#ffffff", 0.7);
  
  widget.addSpacer(8);

  // Main Stats Stack
  let statsStack = widget.addStack();
  statsStack.layoutHorizontally();
  
  // Reads Block
  let readsStack = statsStack.addStack();
  readsStack.layoutVertically();
  let readsVal = readsStack.addText(formatNumber(data.reads));
  readsVal.font = Font.boldSystemFont(20);
  readsVal.textColor = Color.white();
  let readsLabel = readsStack.addText("READS");
  readsLabel.font = Font.systemFont(10);
  readsLabel.textColor = Color.white();
  
  statsStack.addSpacer(20);
  
  // Followers Block
  let folsStack = statsStack.addStack();
  folsStack.layoutVertically();
  let folsVal = folsStack.addText(formatNumber(data.followers));
  folsVal.font = Font.boldSystemFont(20);
  folsVal.textColor = Color.white();
  let folsLabel = folsStack.addText("FOLLOWERS");
  folsLabel.font = Font.systemFont(10);
  folsLabel.textColor = Color.white();

  statsStack.addSpacer(20);

  // Engaged Readers Block
  let engStack = statsStack.addStack();
  engStack.layoutVertically();
  let engVal = engStack.addText(formatNumber(data.engaged_readers || 0));
  engVal.font = Font.boldSystemFont(20);
  engVal.textColor = Color.white();
  let engLabel = engStack.addText("ENGAGED");
  engLabel.font = Font.systemFont(10);
  engLabel.textColor = Color.white();

  widget.addSpacer(12);

  // Rankings Header
  let rankHeader = widget.addText("TOP RANKINGS");
  rankHeader.font = Font.boldSystemFont(11);
  rankHeader.textColor = new Color("#ffffff", 0.9);
  
  widget.addSpacer(4);

  // Story Rankings (Blue Lines, Red Flags)
  const rankings = data.rankings["Blue Lines, Red Flags"] || {};
  const showRanks = Object.entries(rankings).slice(0, 3);
  
  for (const [cat, rank] of showRanks) {
    let rPair = widget.addStack();
    let cText = rPair.addText(cat);
    cText.font = Font.systemFont(11);
    cText.textColor = Color.white();
    rPair.addSpacer();
    let vText = rPair.addText(rank);
    vText.font = Font.boldSystemFont(11);
    vText.textColor = Color.white();
    widget.addSpacer(2);
  }

  widget.addSpacer(6);
  
  // Engagement
  const eng = data.engagement["Blue Lines, Red Flags"] || {};
  let engLine = widget.addText(`Daily: ${eng.readers_today || 0} | Completion: ${eng.retention ? eng.retention[0] : 'N/A'}`);
  engLine.font = Font.italicSystemFont(10);
  engLine.textColor = Color.white();

  return widget;
}

function formatNumber(num) {
  if (num >= 1000) return (num / 1000).toFixed(1) + "k";
  return num.toString();
}

function createErrorWidget(msg) {
  let widget = new ListWidget();
  widget.addText(msg);
  return widget;
}

if (config.runsInWidget) {
  let widget = await createWidget();
  Script.setWidget(widget);
} else {
  let widget = await createWidget();
  await widget.presentMedium();
}

Script.complete();
