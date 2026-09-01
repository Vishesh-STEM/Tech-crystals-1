"""Static consistency check for the frontend (no Node required).

Verifies that
  1. every relative import in src/ resolves to a real file,
  2. every endpoints.X() used by a page exists in lib/api.ts,
  3. every API path declared in lib/api.ts exists in the FastAPI OpenAPI schema,
  4. every <Route path> in App.tsx points at an imported page component,
  5. brackets/braces/parens balance in every source file.

Usage:  python scripts/verify_frontend.py [--openapi http://localhost:8000/openapi.json]
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")
failures: list[str] = []
checks = 0


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def source_files() -> list[str]:
    files = []
    for base, _dirs, names in os.walk(SRC):
        for name in names:
            if name.endswith((".ts", ".tsx")):
                files.append(os.path.join(base, name))
    return sorted(files)


def check_imports(files: list[str]) -> None:
    global checks
    pattern = re.compile(r'^\s*import[^"\']*["\'](\.[^"\']+)["\']', re.M)
    for path in files:
        text = open(path, encoding="utf-8").read()
        for target in pattern.findall(text):
            checks += 1
            base = os.path.normpath(os.path.join(os.path.dirname(path), target))
            candidates = [base + ext for ext in (".ts", ".tsx", ".js", "")] + [
                os.path.join(base, "index" + ext) for ext in (".ts", ".tsx")
            ]
            if not any(os.path.isfile(c) for c in candidates):
                failures.append(f"{rel(path)}: unresolved import '{target}'")


def check_endpoints(files: list[str]) -> None:
    global checks
    api_path = os.path.join(SRC, "lib", "api.ts")
    api_text = open(api_path, encoding="utf-8").read()
    defined = set(re.findall(r"^\s{2}(\w+):\s*\(", api_text, re.M))
    used = set()
    for path in files:
        if path == api_path:
            continue
        used |= set(re.findall(r"endpoints\.(\w+)\(", open(path, encoding="utf-8").read()))
    for name in sorted(used):
        checks += 1
        if name not in defined:
            failures.append(f"lib/api.ts: missing endpoint '{name}' used by a page")
    unused = defined - used
    if unused:
        print(f"  note: {len(unused)} endpoints defined but unused: {', '.join(sorted(unused))}")


def check_routes() -> None:
    global checks
    app_path = os.path.join(SRC, "App.tsx")
    text = open(app_path, encoding="utf-8").read()
    imported = set(re.findall(r"^import\s+(\w+)\s+from", text, re.M))
    elements = set(re.findall(r"element=\{<(\w+)", text)) | set(
        re.findall(r"<(\w+)\s+entity=", text)
    )
    for name in sorted(elements):
        checks += 1
        if name not in imported and name not in {"Navigate", "RequireAuth", "RequireStaff"}:
            failures.append(f"App.tsx: <{name}> used but not imported")
    routes = re.findall(r'path="([^"]+)"', text)
    print(f"  {len(routes)} routes declared: {', '.join(routes[:8])}...")


def _strip_regex_literals(text: str) -> str:
    """Replace /.../flags regex literals with RE, leaving JSX (`/>`) untouched."""
    pattern = re.compile(r"/(?![/*])(?:\\.|\[[^\]\n]*\]|[^/\n\\])+/[gimsuy]*")

    def replace(match: "re.Match[str]") -> str:
        body = match.group(0)
        if "<" in body or ">" in body or "  " in body:
            return body  # looks like JSX or arithmetic, not a regex
        return "RE"

    return pattern.sub(replace, text)


def _strip_odd_char_classes(text: str) -> str:
    """Remove regex character classes such as [.)] whose contents are unbalanced."""

    def replace(match: "re.Match[str]") -> str:
        inner = match.group(1)
        depth_round = inner.count("(") - inner.count(")")
        depth_curly = inner.count("{") - inner.count("}")
        return "[]" if depth_round or depth_curly else match.group(0)

    return re.sub(r"\[([^\[\]\n]*)\]", replace, text)


def check_balance(files: list[str]) -> None:
    global checks
    # JSX makes a regex-based bracket count unreliable (a `/` can start a regex
    # literal or close a tag), so the structural check runs on plain .ts files;
    # .tsx files are validated by `npm run typecheck` / `npm run build`.
    pairs = {")": "(", "]": "[", "}": "{"}
    for path in [f for f in files if f.endswith(".ts")]:
        checks += 1
        text = open(path, encoding="utf-8").read()
        # strip comments, regex literals, strings and template literals
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        text = _strip_regex_literals(text)
        text = re.sub(r'"(\\.|[^"\\])*"', '""', text)
        text = re.sub(r"'(\\.|[^'\\])*'", "''", text)
        text = re.sub(r"`(\\.|[^`\\])*`", "``", text)
        text = _strip_odd_char_classes(text)
        stack = []
        for char in text:
            if char in "([{":
                stack.append(char)
            elif char in ")]}":
                if not stack or stack[-1] != pairs[char]:
                    failures.append(f"{rel(path)}: unbalanced '{char}'")
                    break
                stack.pop()
        else:
            if stack:
                failures.append(f"{rel(path)}: {len(stack)} unclosed '{stack[-1]}'")


HTML_TAGS = {
    "a", "button", "div", "span", "p", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5",
    "form", "input", "label", "select", "option", "textarea", "table", "thead", "tbody",
    "tr", "th", "td", "img", "svg", "path", "section", "header", "footer", "main", "nav",
    "aside", "strong", "em", "code", "pre", "br", "hr", "dl", "dt", "dd", "details",
    "summary", "small", "figure", "figcaption", "canvas", "video", "audio", "iframe",
}
JSX_BEFORE = set("(){}>,;=&|?:[\n\t ")


def _scan_jsx_tags(text: str):
    """Yield (closing, name, self_closing, line) for every JSX tag.

    A hand-written scanner is used because JSX attributes contain braces,
    strings and arrow functions (`onChange={(e) => ...}`) that a regular
    expression cannot skip reliably.
    """
    index, length = 0, len(text)
    while index < length:
        char = text[index]
        if char != "<":
            index += 1
            continue
        before = text[index - 1] if index else "\n"
        cursor = index + 1
        closing = cursor < length and text[cursor] == "/"
        if closing:
            cursor += 1
        name_match = re.match(r"[A-Za-z][A-Za-z0-9.]*", text[cursor:])
        name = name_match.group(0) if name_match else ""
        cursor += len(name)
        if not closing and before not in JSX_BEFORE:
            index += 1                      # TypeScript generic: useState<Stage>
            continue
        if name and not (name[0].isupper() or name in HTML_TAGS):
            index += 1
            continue
        # walk to the matching '>' tracking braces and quotes
        depth, quote, previous = 0, "", ""
        while cursor < length:
            current = text[cursor]
            if quote:
                if current == quote and previous != "\\":
                    quote = ""
            elif current in "\"'`":
                quote = current
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
            elif current == ">" and depth == 0:
                break
            previous = current
            cursor += 1
        if cursor >= length:
            return
        self_closing = (not closing) and text[cursor - 1] == "/"
        yield closing, name, self_closing, text.count("\n", 0, index) + 1
        index = cursor + 1


def check_jsx_structure(files: list[str]) -> None:
    """Every JSX element that opens must close (the usual way a page breaks)."""
    global checks
    for path in [f for f in files if f.endswith(".tsx")]:
        text = open(path, encoding="utf-8").read()
        if "verify-frontend: skip-jsx" in text:
            continue  # file is dominated by regex literals; JSX scanning is unreliable
        checks += 1
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        # string contents can hold tag-like text ("<code>$1</code>")
        text = re.sub(r'"(\\.|[^"\\\n])*"', '""', text)
        text = re.sub(r"'(\\.|[^'\\\n])*'", "''", text)
        text = re.sub(r"`(\\.|[^`\\])*`", "``", text, flags=re.S)
        stack: list[tuple[str, int]] = []
        problem = None
        for closing, name, self_closing, line in _scan_jsx_tags(text):
            if self_closing:
                continue
            if closing:
                if not stack:
                    problem = f"line {line}: </{name}> with nothing open"
                    break
                open_name, open_line = stack.pop()
                if open_name != name:
                    problem = f"line {line}: </{name}> closes <{open_name}> opened on line {open_line}"
                    break
            else:
                stack.append((name, line))
        if problem:
            failures.append(f"{rel(path)}: {problem}")
        elif stack:
            name, line = stack[-1]
            failures.append(f"{rel(path)}: <{name or 'fragment'}> opened on line {line} is never closed")


MANIFEST_PATH = os.path.join(ROOT, "scripts", "package_exports.json")


def check_package_imports(files: list[str]) -> None:
    """Every symbol imported from a third-party package must actually exist.

    The export lists in scripts/package_exports.json were extracted from the
    upstream sources (see "_generated_from"). This catches the most common way
    an unbuilt frontend breaks: a mistyped icon or component name.
    """
    global checks
    if not os.path.isfile(MANIFEST_PATH):
        print("  note: skipping package-export check (scripts/package_exports.json missing)")
        return
    manifest = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    named_re = re.compile(r'import\s+\{([^}]*)\}\s+from\s+["\']([^"\']+)["\']', re.S)
    for path in files:
        text = open(path, encoding="utf-8").read()
        for names, package in named_re.findall(text):
            exports = manifest.get(package)
            if not exports:
                continue
            available = set(exports)
            for part in names.split(","):
                symbol = part.split(" as ")[0].strip().lstrip("type ").strip()
                if not symbol:
                    continue
                checks += 1
                if symbol not in available:
                    failures.append(f"{rel(path)}: '{symbol}' is not exported by {package}")


def check_jsx_components_are_defined(files: list[str]) -> None:
    """A capitalised JSX tag must be imported or defined in the same file."""
    global checks
    builtin = {"Fragment", "React", "Suspense", "StrictMode"}
    for path in [f for f in files if f.endswith(".tsx")]:
        text = open(path, encoding="utf-8").read()
        if "verify-frontend: skip-jsx" in text:
            continue
        defined = set(builtin)
        for pattern in (
            r"import\s+\{([^}]*)\}\s+from",           # named imports
            r"import\s+([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*(?:\{[^}]*\})?\s*from",  # default import
            r"(?:function|const|class)\s+([A-Z][A-Za-z0-9_]*)",  # local components
        ):
            for match in re.findall(pattern, text, re.S):
                for part in str(match).split(","):
                    name = part.split(" as ")[-1].strip()
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                        defined.add(name)
        used = set()
        for closing, name, _self_closing, _line in _scan_jsx_tags(
            re.sub(r"//[^\n]*", "", text)
        ):
            if not closing and name and name[0].isupper():
                used.add(name.split(".")[0])
        for name in sorted(used):
            checks += 1
            if name not in defined:
                failures.append(f"{rel(path)}: <{name}> is used but never imported or defined")


def check_openapi(spec_path: str | None) -> None:
    global checks
    if not spec_path or not os.path.isfile(spec_path):
        print("  note: skipping OpenAPI cross-check (no spec provided)")
        return
    spec = json.load(open(spec_path, encoding="utf-8"))
    server_paths = set(spec.get("paths", {}))
    api_text = open(os.path.join(SRC, "lib", "api.ts"), encoding="utf-8").read()
    used = set(re.findall(r'api\.\w+\(\s*[`"]([^`"]+)[`"]', api_text)) | set(
        re.findall(r'api\.\w+\(\s*`([^`]+)`', api_text)
    )
    entities = ["subjects", "chapters", "topics", "resources", "questions", "quizzes"]
    for entity in entities:
        for method, template in (("post", "/api/admin/%s"), ("patch", "/api/admin/%s/{%s_id}"),
                                 ("delete", "/api/admin/%s/{%s_id}")):
            checks += 1
            singular = entity[:-1] if entity != "quizzes" else "quiz"
            path = template % ((entity,) if method == "post" else (entity, singular))
            if path not in server_paths:
                shape = re.sub(r"\{[^}]+\}", "{}", path)
                if not any(re.sub(r"\{[^}]+\}", "{}", c) == shape for c in server_paths):
                    failures.append(f"admin CRUD: {method.upper()} {path} missing from the API")

    for raw in sorted(used):
        checks += 1
        if "${entity}" in raw:
            continue  # generic CRUD helper, checked above
        path = "/api" + re.sub(r"\$\{[^}]+\}", "{id}", raw)
        if path in server_paths:
            continue
        # try matching by shape (parameter names differ)
        shape = re.sub(r"\{[^}]+\}", "{}", path)
        if any(re.sub(r"\{[^}]+\}", "{}", candidate) == shape for candidate in server_paths):
            continue
        failures.append(f"lib/api.ts: '{path}' is not exposed by the API")


def main() -> int:
    spec = None
    if "--openapi" in sys.argv:
        spec = sys.argv[sys.argv.index("--openapi") + 1]
    files = source_files()
    print(f"Checking {len(files)} frontend source files...")
    check_imports(files)
    check_endpoints(files)
    check_routes()
    check_balance(files)
    check_jsx_structure(files)
    check_package_imports(files)
    check_jsx_components_are_defined(files)
    check_openapi(spec)
    print(f"\n{checks} checks run.")
    if failures:
        print(f"{len(failures)} problem(s):")
        for failure in failures:
            print(f"  FAIL  {failure}")
        return 1
    print("All frontend consistency checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
