from pathlib import Path
import zipfile, textwrap

root = Path("/mnt/data/chemroom_molar_mass")
(root / "python").mkdir(parents=True, exist_ok=True)
(root / "tools").mkdir(parents=True, exist_ok=True)

py = r'''"""
ChemRoom | Calculadora de masa molar
Elementos 1–103. Las masas se expresan con dos decimales (g/mol).
El parser acepta fórmulas convencionales, paréntesis y cantidades.
El orden de los elementos no afecta al resultado.
"""

ATOMIC_MASSES = {
    "H": 1.01, "He": 4.00,
    "Li": 6.94, "Be": 9.01, "B": 10.81, "C": 12.01, "N": 14.01, "O": 16.00, "F": 19.00, "Ne": 20.18,
    "Na": 22.99, "Mg": 24.31, "Al": 26.98, "Si": 28.09, "P": 30.97, "S": 32.06, "Cl": 35.45, "Ar": 39.95,
    "K": 39.10, "Ca": 40.08, "Sc": 44.96, "Ti": 47.87, "V": 50.94, "Cr": 52.00, "Mn": 54.94, "Fe": 55.85,
    "Co": 58.93, "Ni": 58.69, "Cu": 63.55, "Zn": 65.38, "Ga": 69.72, "Ge": 72.63, "As": 74.92, "Se": 78.97,
    "Br": 79.90, "Kr": 83.80, "Rb": 85.47, "Sr": 87.62, "Y": 88.91, "Zr": 91.22, "Nb": 92.91, "Mo": 95.95,
    "Tc": 98.00, "Ru": 101.07, "Rh": 102.91, "Pd": 106.42, "Ag": 107.87, "Cd": 112.41, "In": 114.82,
    "Sn": 118.71, "Sb": 121.76, "Te": 127.60, "I": 126.90, "Xe": 131.29, "Cs": 132.91, "Ba": 137.33,
    "La": 138.91, "Ce": 140.12, "Pr": 140.91, "Nd": 144.24, "Pm": 145.00, "Sm": 150.36, "Eu": 151.96,
    "Gd": 157.25, "Tb": 158.93, "Dy": 162.50, "Ho": 164.93, "Er": 167.26, "Tm": 168.93, "Yb": 173.05,
    "Lu": 174.97, "Hf": 178.49, "Ta": 180.95, "W": 183.84, "Re": 186.21, "Os": 190.23, "Ir": 192.22,
    "Pt": 195.08, "Au": 196.97, "Hg": 200.59, "Tl": 204.38, "Pb": 207.20, "Bi": 208.98, "Po": 209.00,
    "At": 210.00, "Rn": 222.00, "Fr": 223.00, "Ra": 226.00, "Ac": 227.00, "Th": 232.04, "Pa": 231.04,
    "U": 238.03, "Np": 237.00, "Pu": 244.00, "Am": 243.00, "Cm": 247.00, "Bk": 247.00, "Cf": 251.00,
    "Es": 252.00, "Fm": 257.00, "Md": 258.00, "No": 259.00, "Lr": 266.00
}

class FormulaError(ValueError):
    pass

def parse_formula(formula):
    """Return atom counts, accepting e.g. CHOOH, H2SO4, Ca(OH)2."""
    if not isinstance(formula, str) or not formula.strip():
        raise FormulaError("Escribe una fórmula química.")
    s = formula.strip().replace(" ", "")
    i = 0

    def parse_group(stop=None):
        nonlocal i
        counts = {}
        while i < len(s):
            ch = s[i]
            if ch == ")":
                if stop != ")":
                    raise FormulaError("Hay un paréntesis de cierre sin pareja.")
                i += 1
                return counts
            if ch == "(":
                i += 1
                inner = parse_group(")")
                if not inner:
                    raise FormulaError("Hay un grupo entre paréntesis vacío.")
                multiplier = read_number()
                for el, n in inner.items():
                    counts[el] = counts.get(el, 0) + n * multiplier
                continue
            if not ch.isupper():
                raise FormulaError(
                    f"Se esperaba el símbolo de un elemento en la posición {i+1}. "
                    "Usa mayúscula inicial y minúscula cuando corresponda (Na, Cl, Fe)."
                )
            symbol = ch
            i += 1
            if i < len(s) and s[i].islower():
                candidate = symbol + s[i]
                if candidate in ATOMIC_MASSES:
                    symbol = candidate
                    i += 1
            if symbol not in ATOMIC_MASSES:
                raise FormulaError(f"El símbolo «{symbol}» no está en los elementos 1–103.")
            amount = read_number()
            counts[symbol] = counts.get(symbol, 0) + amount
        if stop:
            raise FormulaError("Falta un paréntesis de cierre.")
        return counts

    def_unused = None
    def read_number():
        nonlocal i
        start = i
        while i < len(s) and s[i].isdigit():
            i += 1
        return int(s[start:i]) if i > start else 1

    result = parse_group()
    if i != len(s):
        raise FormulaError("No se pudo interpretar toda la fórmula.")
    return result

def calculate_molar_mass(formula):
    counts = parse_formula(formula)
    # Ordena por símbolo para que fórmulas con los mismos átomos den el mismo desglose.
    breakdown = []
    for element in sorted(counts):
        number = counts[element]
        atomic_mass = ATOMIC_MASSES[element]
        contribution = number * atomic_mass
        breakdown.append({
            "element": element,
            "count": number,
            "atomic_mass": atomic_mass,
            "contribution": contribution
        })
    total = sum(item["contribution"] for item in breakdown)
    return {"formula": formula, "counts": counts, "breakdown": breakdown, "total": total}

def calculate_json(formula):
    """JSON-friendly entry point used by the browser."""
    import json
    try:
        return json.dumps({"ok": True, **calculate_molar_mass(formula)}, ensure_ascii=False)
    except FormulaError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
'''
(root / "python" / "molar_mass.py").write_text(py, encoding="utf-8")

html = r'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Calculadora interactiva de masa molar de ChemRoom.">
  <title>Masa molar | ChemRoom</title>
  <style>
    :root {
      --bg: #0b1220; --panel: #121d2e; --panel2: #17263a;
      --text: #edf5fb; --muted: #9db0c3; --line: #26394f;
      --accent: #43d6c5; --accent2: #69b7ff; --danger: #ff8e8e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; padding: 36px 18px;
      background: radial-gradient(ellipse at 15% 0%, #163047 0, transparent 42%), var(--bg);
      color: var(--text); font: 16px/1.55 system-ui, -apple-system, Segoe UI, sans-serif;
    }
    .wrap { width: min(850px, 100%); margin: auto; }
    a { color: var(--accent); text-decoration: none; }
    .top { display:flex; justify-content:space-between; gap:16px; align-items:center; margin-bottom:30px; }
    .brand { font-weight:800; letter-spacing:.04em; font-size:1.05rem; }
    .eyebrow { color:var(--accent); text-transform:uppercase; letter-spacing:.14em; font-size:.76rem; font-weight:700; }
    h1 { font-size:clamp(2rem, 5vw, 3.2rem); line-height:1.08; margin:8px 0 12px; }
    .intro { color:var(--muted); max-width:650px; margin:0 0 26px; }
    .card { background:linear-gradient(145deg, rgba(23,38,58,.97), rgba(16,28,44,.97)); border:1px solid var(--line); border-radius:22px; padding:clamp(20px,4vw,32px); box-shadow:0 18px 55px #0003; }
    label { display:block; font-weight:650; margin-bottom:9px; }
    .entry { display:flex; gap:10px; }
    input {
      min-width:0; flex:1; border:1px solid #38516a; border-radius:12px;
      background:#0b1726; color:var(--text); padding:15px 16px; font:inherit;
      outline:none; transition:border .2s, box-shadow .2s;
    }
    input:focus { border-color:var(--accent); box-shadow:0 0 0 3px #43d6c522; }
    button { border:0; border-radius:12px; padding:0 22px; background:var(--accent); color:#06221f; font:700 1rem inherit; font-weight:750; cursor:pointer; }
    button:hover { filter:brightness(1.08); transform:translateY(-1px); }
    .hint { color:var(--muted); font-size:.88rem; margin:9px 0 0; }
    .examples { display:flex; flex-wrap:wrap; gap:8px; margin-top:15px; }
    .example { background:#20354a; border:1px solid #35516a; color:#d8e9f4; padding:6px 11px; border-radius:99px; cursor:pointer; font-size:.85rem; }
    .example:hover { border-color:var(--accent); }
    #status { min-height:24px; color:var(--danger); margin-top:12px; font-size:.92rem; }
    #result { display:none; margin-top:22px; }
    .result-head { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:end; gap:12px; padding-bottom:20px; border-bottom:1px solid var(--line); }
    .result-label { color:var(--muted); font-size:.9rem; }
    .mass { color:var(--accent); font-size:clamp(2rem,6vw,3rem); font-weight:800; letter-spacing:-.04em; }
    .formula { font-size:1.35rem; font-weight:700; }
    h2 { font-size:1.08rem; margin:22px 0 12px; }
    .equation { background:#0b1726; border:1px solid var(--line); border-radius:13px; padding:15px; overflow-wrap:anywhere; }
    .term { display:flex; justify-content:space-between; gap:16px; padding:11px 2px; border-bottom:1px solid #26394f99; }
    .term:last-child { border:0; }
    .term small { display:block; color:var(--muted); }
    .term strong { white-space:nowrap; font-variant-numeric:tabular-nums; }
    .total { display:flex; justify-content:space-between; padding-top:15px; margin-top:8px; font-weight:800; }
    .note { color:var(--muted); font-size:.86rem; margin-top:20px; }
    .loading { color:var(--accent2); }
    @media(max-width:560px) { .top { align-items:flex-start; } .entry { flex-direction:column; } button { padding:14px; } .term { align-items:flex-start; } }
  </style>
</head>
<body>
  <main class="wrap">
    <nav class="top"><a class="brand" href="../index.html">CHEMROOM</a><a href="../index.html">← Volver a herramientas</a></nav>
    <div class="eyebrow">Herramienta básica · 01</div>
    <h1>Calculadora de masa molar</h1>
    <p class="intro">Escribe una fórmula química y descubre su masa molar. ChemRoom identifica los elementos, cuenta cuántos átomos hay y muestra cómo se construye el resultado.</p>

    <section class="card" aria-label="Calculadora de masa molar">
      <label for="formula">Fórmula química</label>
      <div class="entry">
        <input id="formula" type="text" value="H2SO4" placeholder="Ej. H2SO4, Ca(OH)2, CHOOH" autocomplete="off" spellcheck="false">
        <button id="calculate" type="button">Calcular masa</button>
      </div>
      <p class="hint">No importa el orden de los elementos: CHOOH y CH₂O₂ representan la misma composición.</p>
      <div class="examples" aria-label="Ejemplos">
        <button class="example" data-formula="H2O" type="button">H₂O</button>
        <button class="example" data-formula="NaCl" type="button">NaCl</button>
        <button class="example" data-formula="H2SO4" type="button">H₂SO₄</button>
        <button class="example" data-formula="Ca(OH)2" type="button">Ca(OH)₂</button>
        <button class="example" data-formula="CHOOH" type="button">CHOOH</button>
        <button class="example" data-formula="C6H12O6" type="button">C₆H₁₂O₆</button>
      </div>
      <div id="status" role="status" aria-live="polite"></div>

      <section id="result" aria-live="polite">
        <div class="result-head">
          <div><div class="result-label">Fórmula interpretada</div><div id="normalized" class="formula"></div></div>
          <div><div class="result-label">Masa molar</div><div id="mass" class="mass"></div></div>
        </div>
        <h2>Desglose del cálculo</h2>
        <div id="breakdown"></div>
        <div class="equation" id="sum"></div>
        <p class="note">Las masas atómicas se muestran con dos decimales. El resultado se calcula con esos valores redondeados; los elementos 1–103 están incluidos.</p>
      </section>
    </section>
    <p class="note">ChemRoom · Química, cálculo y exploración.</p>
  </main>

  <script type="module">
    const input = document.querySelector("#formula");
    const button = document.querySelector("#calculate");
    const status = document.querySelector("#status");
    const result = document.querySelector("#result");
    const breakdown = document.querySelector("#breakdown");
    let pyodide;
    let calculator;

    async function loadPython() {
      if (calculator) return calculator;
      status.textContent = "Preparando el motor de cálculo…";
      status.className = "loading";
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js";
      document.head.appendChild(script);
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = () => reject(new Error("No se pudo cargar Pyodide. Revisa tu conexión a internet."));
      });
      pyodide = await loadPyodide();
      const response = await fetch("../python/molar_mass.py");
      if (!response.ok) throw new Error("No se pudo encontrar python/molar_mass.py.");
      const source = await response.text();
      pyodide.runPython(source);
      calculator = pyodide.globals.get("calculate_json");
      status.textContent = "";
      status.className = "";
      return calculator;
    }

    function prettyFormula(formula) {
      return formula.replace(/([A-Za-z)])(\d+)/g, "$1<sub>$2</sub>");
    }

    function showResult(data) {
      document.querySelector("#normalized").innerHTML = prettyFormula(data.formula);
      document.querySelector("#mass").textContent = `${data.total.toFixed(2)} g/mol`;
      breakdown.innerHTML = "";
      const terms = [];
      for (const item of data.breakdown) {
        const contribution = item.contribution;
        terms.push(`${item.count} × ${item.atomic_mass.toFixed(2)}`);
        const row = document.createElement("div");
        row.className = "term";
        const left = document.createElement("div");
        const symbol = document.createElement("strong");
        symbol.textContent = item.element;
        const detail = document.createElement("small");
        detail.textContent = `${item.count} átomo(s) × ${item.atomic_mass.toFixed(2)} g/mol`;
        left.append(symbol, detail);
        const right = document.createElement("strong");
        right.textContent = `${contribution.toFixed(2)} g/mol`;
        row.append(left, right);
        breakdown.append(row);
      }
      const total = document.createElement("div");
      total.className = "total";
      total.innerHTML = `<span>Suma total</span><span>${data.total.toFixed(2)} g/mol</span>`;
      breakdown.append(total);
      document.querySelector("#sum").textContent =
        terms.join(" + ") + ` = ${data.total.toFixed(2)} g/mol`;
      result.style.display = "block";
      status.textContent = "";
    }

    async function calculate() {
      const formula = input.value.trim();
      result.style.display = "none";
      status.className = "loading";
      try {
        const run = await loadPython();
        const raw = run(formula);
        const data = JSON.parse(raw);
        if (!data.ok) throw new Error(data.error);
        showResult(data);
      } catch (error) {
        status.className = "";
        status.textContent = error.message || "Ocurrió un error al calcular.";
      }
    }

    button.addEventListener("click", calculate);
    input.addEventListener("keydown", event => { if (event.key === "Enter") calculate(); });
    document.querySelectorAll(".example").forEach(chip => {
      chip.addEventListener("click", () => { input.value = chip.dataset.formula; calculate(); });
    });
    calculate();
  </script>
</body>
</html>
'''
(root / "tools" / "molar-mass.html").write_text(html, encoding="utf-8")

readme = """# ChemRoom — Molar Mass Calculator

## Archivos
- `tools/molar-mass.html`: interfaz web independiente y adaptable a móviles.
- `python/molar_mass.py`: tabla de masas atómicas (elementos 1–103), parser y cálculo.

## Integración
Copia las carpetas `tools/` y `python/` a la raíz del repositorio ChemRoom, conservando la estructura.

Añade un enlace desde tu `index.html` o desde la tarjeta de herramientas:
```html
<a href="tools/molar-mass.html">Abrir calculadora de masa molar</a>
```

La página carga Pyodide desde CDN y ejecuta el archivo Python en el navegador. No requiere servidor Python, pero sí conexión a internet para cargar Pyodide. Prueba el sitio publicado por GitHub Pages o mediante un servidor local; abrir el HTML directamente como `file://` puede bloquear `fetch()`.

## Comportamiento
- Reconoce elementos de los primeros 103 números atómicos.
- Acepta fórmulas como `H2SO4`, `Ca(OH)2`, `C6H12O6` y `CHOOH`.
- Agrupa elementos repetidos: `CHOOH` se interpreta como C1H2O2.
- Muestra contribución de cada elemento y suma final.
- Las masas atómicas se almacenan con dos decimales.

## Nota química
Para elementos sin peso atómico estándar, se utiliza un número de masa representativo convencional con dos decimales (por ejemplo, Tc = 98.00). Los valores son adecuados para una calculadora educativa; para trabajo metrológico o publicaciones, conviene documentar la fuente y el intervalo de pesos atómicos estándar.
"""
(root / "README.txt").write_text(readme, encoding="utf-8")

zip_path = Path("/mnt/data/chemroom_molar_mass_files.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob("*"):
        if p.is_file():
            z.write(p, p.relative_to(root.parent))

print(f"Created: {zip_path}")
print("Files:", [str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()])
