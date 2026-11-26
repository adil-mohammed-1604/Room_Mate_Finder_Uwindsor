"""Builds the French translation files without needing GNU gettext (handy on Windows).

    pip install polib
    python locale/build_locale.py            # writes locale/fr/LC_MESSAGES/django.po and django.mo
    python locale/build_locale.py --list     # only prints every text that needs a translation

How it works
1. It scans the Python files and templates for translatable texts ({% trans %}, {% blocktrans %},
   _("..."), gettext(...), ngettext(...)).
2. It looks each text up in locale/fr_translations.py (the file you edit to change the French).
3. It writes django.po (readable) and django.mo (what Django actually loads).

To add a new text: wrap it in your code (see any template), run `--list` to see it, add its French
in fr_translations.py, then run the script again and restart the server.
"""
import ast
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", "venv", ".git", ".idea", "node_modules", "migrations", "locale", "__pycache__", "media",
             "private_media", "static", "staticfiles"}
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fr_translations import DYNAMIC, FR  # noqa: E402


def walk(suffixes):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(suffixes):
                yield Path(dirpath) / name


# ------------------------------------------------------------------ extraction

PY_FUNCS = {"_", "gettext", "gettext_lazy", "ugettext"}
PY_PLURAL = {"ngettext", "ngettext_lazy"}


def extract_python():
    found = {}
    for path in walk((".py",)):
        if path.name.startswith("test") or path.name == "tests.py" or path.name == "build_locale.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name in PY_FUNCS and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                found.setdefault(node.args[0].value, None)
            elif name in PY_PLURAL and len(node.args) >= 2 and all(
                    isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args[:2]):
                found[node.args[0].value] = node.args[1].value
    return found


TRANS_RE = re.compile(r"""\{%\s*(?:trans|translate)\s+(?P<q>["'])(?P<text>.*?)(?P=q)[^%]*?%\}""", re.S)
UNDERSCORE_RE = re.compile(r"""_\(\s*(?P<q>["'])(?P<text>.*?)(?P=q)\s*\)""", re.S)
BLOCK_RE = re.compile(r"\{%\s*blocktrans(?:late)?(?P<opts>[^%]*)%\}(?P<body>.*?)\{%\s*endblocktrans(?:late)?\s*%\}", re.S)
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def block_text(body, trimmed):
    if trimmed:
        body = re.sub(r"\s*\n\s*", " ", body.strip())
    out = VAR_RE.sub(lambda m: f"%({m.group(1)})s", body.replace("%", "%%"))
    # variables were turned into %(x)s after escaping, so restore the single % of the placeholders
    if "{{" in out or "{%" in out:
        raise SystemExit(f"blocktrans can only contain plain {{{{ variables }}}}: {body[:80]!r}")
    return out


def extract_templates():
    found = {}
    for path in walk((".html", ".txt")):
        text = path.read_text(encoding="utf-8")
        for m in TRANS_RE.finditer(text):
            found.setdefault(m.group("text"), None)
        # _("...") used inside {% ... %} and {{ ... }}
        for tag in re.finditer(r"\{[%{].*?[%}]\}", text, re.S):
            for m in UNDERSCORE_RE.finditer(tag.group(0)):
                found.setdefault(m.group("text"), None)
        for m in BLOCK_RE.finditer(text):
            trimmed = "trimmed" in m.group("opts")
            parts = re.split(r"\{%\s*plural\s*%\}", m.group("body"))
            singular = block_text(parts[0], trimmed)
            found[singular] = block_text(parts[1], trimmed) if len(parts) > 1 else found.get(singular)
    return found


# ------------------------------------------------------------------ build

def placeholders(text):
    return sorted(re.findall(r"%\(\w+\)[sd]", text))


def main():
    import polib

    list_only = "--list" in sys.argv
    found = {**extract_templates(), **{k: v for k, v in extract_python().items()}}
    missing = [m for m in sorted(found) if m not in FR]
    if list_only:
        print(f"{len(found)} texts found, {len(missing)} still without French:")
        for m in missing:
            print("  ", repr(m))
        return
    if missing:
        print(f"{len(missing)} texts have no French yet (add them to locale/fr_translations.py):")
        for m in missing:
            print("  ", repr(m))
        raise SystemExit(1)

    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "RoomMate Finder",
        "Language": "fr",
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "Plural-Forms": "nplurals=2; plural=(n > 1);",
    }
    problems = []
    for msgid in sorted(set(found) | set(DYNAMIC)):
        translation = FR[msgid]
        plural = found.get(msgid)
        if plural:
            singular_fr, plural_fr = translation
            if placeholders(msgid) != placeholders(singular_fr) or placeholders(plural) != placeholders(plural_fr):
                problems.append(msgid)
            entry = polib.POEntry(msgid=msgid, msgid_plural=plural,
                                  msgstr_plural={0: singular_fr, 1: plural_fr})
        else:
            if placeholders(msgid) != placeholders(translation):
                problems.append(msgid)
            entry = polib.POEntry(msgid=msgid, msgstr=translation)
        if "%(" in msgid:
            entry.flags.append("python-format")
        po.append(entry)
    if problems:
        print("These French texts have different %(placeholders)s than the English:")
        for p in problems:
            print("  ", repr(p))
        raise SystemExit(1)

    out = ROOT / "locale" / "fr" / "LC_MESSAGES"
    out.mkdir(parents=True, exist_ok=True)
    po.save(str(out / "django.po"))
    po.save_as_mofile(str(out / "django.mo"))
    unused = [k for k in FR if k not in found and k not in DYNAMIC]
    print(f"Wrote {len(po)} entries to {out}")
    if unused:
        print(f"Note: {len(unused)} texts in fr_translations.py are no longer used in the code.")


if __name__ == "__main__":
    main()
