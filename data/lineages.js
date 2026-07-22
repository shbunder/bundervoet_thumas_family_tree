// Surname chains shown in the "Lineages" tab.
// Each chain is derived automatically by walking father-links up from `head`,
// so it always reflects the data — there is no hardcoded ancestor list to keep
// in sync. (An explicit `chain: [...]` is still honoured if ever needed.)
FamilyTree.lineages([
  {
    key: "Bundervoet",
    head: "kids",
    caption: "Father's line → Evergem farmers, then the Oostende docks. Documented to c.1560.",
  },
  {
    key: "De Keyser",
    head: "cosette",
    caption: "Cosette's father's line — Oostende (via Hamme); a wartime birth in London.",
  },
  {
    key: "Thumas",
    head: "dorien",
    caption: "Dorien's father's line — Grez-Doiceau (Walloon Brabant) → Kraainem, 1872. Documented to 1656 (recent link assumed).",
  },
  {
    key: "Janssens",
    head: "christiane",
    caption: "Dorien's mother's line — Brabant (Zaventem/Kraainem area). 20th-c. privacy wall.",
  }
]);
