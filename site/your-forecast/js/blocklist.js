// Display names refused at save (BACKEND.md §5: "checked against a short
// blocklist"). The name is printed on an image published from our domain.
//
// ⚠ OWNER'S LIST. This holds only names that would impersonate the site or the
// model, which is the harm specific to this service. Slurs and abuse are a
// content-policy decision for the owner; add patterns here, one per line, and
// the validator tests pick them up. Matching is on the NFKC-normalised name.
export const BLOCKED_NAME_PATTERNS = [
  /whysoserious/i,
  /\bthe model\b/i,
  /\bofficial\b/i,
  /\b(iec|electoral commission)\b/i,
];
