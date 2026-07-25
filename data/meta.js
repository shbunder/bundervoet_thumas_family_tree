// Root of the tree, confidence labels, footer text.
FamilyTree.meta({
  root: "renee",
  roots: ["renee", "leon"],
  defaultSource: "Family knowledge (provided by the family)",
  confidenceLabels: {
    doc: "Documented record",
    fam: "Family knowledge",
    sup: "Strongly supported",
    unk: "Unknown — to research",
  },
  // Deliberately says nothing the tree itself records. A footer that lists
  // deepest roots and dates is a second copy of the data that quietly goes stale.
  footer: "A living draft. Documented lines rest on Belgian civil and parish records, reached through the state archives and the member trees credited in the sources list; the rest is family knowledge, marked as such. Living individuals were not researched beyond what the family volunteered."
});
