// A parser for the small, fixed shape of YAML the person files use — and only
// that shape. Writing ~90 lines here keeps the project's "no dependencies" rule,
// which is what lets the whole thing run from a clone with nothing installed.
//
// What is supported, because it is all the records need:
//   key: scalar
//   key:              (nested map, one level)
//     sub: scalar
//   key:              (list of maps, one level)
//     - sub: scalar
//       sub2: scalar
//
// Anything else is a syntax error rather than a silent misread. A parser that
// guesses is worse than no parser: it would let a malformed record through and
// the mistake would surface as a missing person months later.

const unquote = raw => {
  const s = raw.trim();
  if (s === '') return '';
  if ((s.startsWith('"') && s.endsWith('"') && s.length > 1) || (s.startsWith("'") && s.endsWith("'") && s.length > 1)) {
    const body = s.slice(1, -1);
    return s[0] === '"' ? body.replace(/\\"/g, '"').replace(/\\\\/g, '\\') : body.replace(/''/g, "'");
  }
  return s;
};

export function parseFrontmatter(text, filename = '<string>') {
  if (!text.startsWith('---\n')) throw new Error(`${filename}: does not start with a --- frontmatter block`);
  const end = text.indexOf('\n---\n', 3);
  if (end === -1) throw new Error(`${filename}: frontmatter block is never closed with ---`);

  const head = text.slice(4, end + 1);
  const body = text.slice(end + 5).replace(/^\n+/, '').replace(/\s+$/, '');

  const data = {};
  let currentKey = null; // the key a nested block belongs to
  let currentItem = null; // the map currently being filled inside a list

  const lines = head.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim() || line.trim().startsWith('#')) continue;
    const indent = line.length - line.trimStart().length;
    const trimmed = line.trim();

    if (indent === 0) {
      const m = trimmed.match(/^([A-Za-z_][\w-]*):(.*)$/);
      if (!m) throw new Error(`${filename}: line ${i + 1} is not "key: value" — ${JSON.stringify(line)}`);
      const [, key, rest] = m;
      if (rest.trim() === '') {
        currentKey = key;
        currentItem = null;
        data[key] = undefined; // shape decided by the first child line
      } else {
        data[key] = unquote(rest);
        currentKey = null;
        currentItem = null;
      }
      continue;
    }

    if (!currentKey) throw new Error(`${filename}: line ${i + 1} is indented but belongs to nothing`);

    if (trimmed.startsWith('- ')) {
      if (data[currentKey] === undefined) data[currentKey] = [];
      if (!Array.isArray(data[currentKey])) throw new Error(`${filename}: line ${i + 1} mixes a list into the map "${currentKey}"`);
      const item = trimmed.slice(2);
      const m = item.match(/^([A-Za-z_][\w-]*):(.*)$/);
      if (m) {
        // A list of maps, like spouses.
        currentItem = {};
        data[currentKey].push(currentItem);
        currentItem[m[1]] = unquote(m[2]);
      } else {
        // A list of plain values, like source ids.
        currentItem = null;
        data[currentKey].push(unquote(item));
      }
      continue;
    }

    const m = trimmed.match(/^([A-Za-z_][\w-]*):(.*)$/);
    if (!m) throw new Error(`${filename}: line ${i + 1} is not "key: value" — ${JSON.stringify(line)}`);
    if (Array.isArray(data[currentKey])) {
      if (!currentItem) throw new Error(`${filename}: line ${i + 1} has no list item to belong to`);
      currentItem[m[1]] = unquote(m[2]);
    } else {
      if (data[currentKey] === undefined) data[currentKey] = {};
      data[currentKey][m[1]] = unquote(m[2]);
    }
  }

  for (const [k, v] of Object.entries(data)) {
    if (v === undefined) throw new Error(`${filename}: "${k}" has no value and no indented block`);
  }
  return { data, body };
}

// Quote only when the value would otherwise be misread. Leaving ordinary prose
// unquoted is what makes these files readable, which is the point of the format.
const needsQuoting = s =>
  s === '' ||
  /^[\s>|&*!%@`{}[\]#]/.test(s) ||
  /: /.test(s) ||
  /\s$/.test(s) ||
  /^(true|false|null|yes|no|on|off|~)$/i.test(s) ||
  /^-?\d+(\.\d+)?$/.test(s);

const scalar = v => {
  const s = String(v);
  return needsQuoting(s) ? `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"` : s;
};

export function stringifyFrontmatter(data, body, keyOrder = []) {
  const keys = [...keyOrder.filter(k => k in data), ...Object.keys(data).filter(k => !keyOrder.includes(k))];
  const out = ['---'];
  for (const key of keys) {
    const value = data[key];
    if (value == null || value === '') continue;
    if (Array.isArray(value)) {
      if (!value.length) continue;
      out.push(`${key}:`);
      for (const item of value) {
        if (item !== null && typeof item === 'object') {
          const entries = Object.entries(item).filter(([, v]) => v != null && v !== '');
          entries.forEach(([k, v], i) => out.push(`  ${i === 0 ? '- ' : '  '}${k}: ${scalar(v)}`));
        } else {
          out.push(`  - ${scalar(item)}`);
        }
      }
    } else if (typeof value === 'object') {
      const entries = Object.entries(value).filter(([, v]) => v != null && v !== '');
      if (!entries.length) continue;
      out.push(`${key}:`);
      for (const [k, v] of entries) out.push(`  ${k}: ${scalar(v)}`);
    } else {
      out.push(`${key}: ${scalar(value)}`);
    }
  }
  out.push('---', '');
  if (body && body.trim()) out.push(body.trim(), '');
  return out.join('\n');
}
