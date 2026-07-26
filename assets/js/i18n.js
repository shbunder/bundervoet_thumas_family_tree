// The words the page shows, in whichever language is chosen.
//
// Nothing here is written in this file. Every string comes from site/labels.json
// through the bundle, for the same reason no name or date is written into assets/:
// a label hard-coded in the code is a label that cannot be translated, and one that
// no longer has a single place it is edited. What lives here is only the machinery —
// which language is current, and how a stored string becomes a rendered one.

FamilyTree.createI18n = function (strings) {
  const STORE = 'familytree.lang';
  const langs = strings.languages;
  const codes = langs.map(l => l.code);
  const fallback = codes[0];

  // A browser that will not keep localStorage (private mode, file:// on some
  // browsers) is not a reason for the page to fail — it just forgets the choice.
  const remembered = (() => {
    try {
      return window.localStorage.getItem(STORE);
    } catch (e) {
      return null;
    }
  })();

  // Failing that, take the first of the reader's own languages this site speaks.
  // Most of the people in this tree spoke Dutch; most of the people reading it may
  // not. Neither is a reason to decide for them when the browser already has.
  const preferred = (navigator.languages || [navigator.language || ''])
    .map(l => String(l).slice(0, 2).toLowerCase())
    .find(l => codes.indexOf(l) >= 0);

  let lang = codes.indexOf(remembered) >= 0 ? remembered : preferred || fallback;
  const listeners = [];

  // ---- turning a stored value into a rendered one ----

  // Every translatable value is `{en: …, nl: …}`. A language with no entry falls
  // back rather than showing nothing, because a half-translated page is still
  // readable and a blank one is not.
  function pick(entry) {
    if (entry == null) return null;
    if (typeof entry === 'string') return entry;
    return entry[lang] != null ? entry[lang] : entry[fallback];
  }

  // "{n} person|{n} people". The plural sits in the string rather than in a rule
  // here, because the rule is not the same in every language — and the moment it is
  // a rule in the code, the third language has to come and edit the code.
  function plural(value, params) {
    if (value.indexOf('|') < 0 || !params || !('n' in params)) return value;
    const forms = value.split('|');
    return Number(params.n) === 1 ? forms[0] : forms[1];
  }

  // Substitution is raw: several of these strings carry markup of their own, so
  // whatever goes into them is escaped by the caller. Nothing here decides what is
  // safe, because nothing here knows.
  function fill(value, params) {
    if (!params) return value;
    return value.replace(/\{(\w+)\}/g, (m, key) => (key in params ? String(params[key]) : m));
  }

  // An unknown key renders as itself. A missing string that shows up as "lblMother"
  // gets fixed; one that renders as empty is invisible until someone notices a gap.
  function t(key, params) {
    const value = pick(strings.ui[key]);
    if (value == null) return key;
    return fill(plural(value, params), params);
  }

  // ---- the parts of the wording that are not plain strings ----

  const conf = code => pick(strings.confidenceLabels[code]) || code;
  // The legend reads these in the order site/labels.json lists them, so the order is
  // editable there rather than fixed in a second place.
  const confCodes = Object.keys(strings.confidenceLabels);
  const footer = () => pick(strings.footer) || '';
  const kin = () => strings.kinship[lang] || strings.kinship[fallback];

  // ---- switching ----

  function set(code) {
    if (codes.indexOf(code) < 0 || code === lang) return;
    lang = code;
    try {
      window.localStorage.setItem(STORE, code);
    } catch (e) {
      /* not remembering the choice is survivable; failing to make it is not */
    }
    document.documentElement.lang = code;
    listeners.forEach(fn => fn(code));
  }

  const next = () => codes[(codes.indexOf(lang) + 1) % codes.length];
  const info = code => langs.filter(l => l.code === (code || lang))[0];

  document.documentElement.lang = lang;

  return {
    get lang() {
      return lang;
    },
    languages: langs,
    codes,
    pick, t, conf, confCodes, footer, kin, set, next, info,
    onChange: fn => listeners.push(fn),
  };
};

// The page shell's own wording. `data-i18n` fills the text of an element;
// `data-i18n-attr` fills attributes, as `attr:key` pairs separated by `;` — that is
// how a placeholder and an aria-label get translated without either being written
// into the HTML, which would put a second copy of the English in a file nobody
// thinks of as wording.
FamilyTree.applyStatic = function (i18n, root) {
  const scope = root || document;
  scope.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = i18n.t(el.getAttribute('data-i18n'));
  });
  scope.querySelectorAll('[data-i18n-attr]').forEach(el => {
    el.getAttribute('data-i18n-attr')
      .split(';')
      .forEach(pair => {
        const at = pair.indexOf(':');
        if (at < 0) return;
        el.setAttribute(pair.slice(0, at).trim(), i18n.t(pair.slice(at + 1).trim()));
      });
  });
};
