#!/usr/bin/env python3
"""Build the standalone editable LaTeX and PDF mathematics guide.

Requirements: Python >=3.10, Pandoc >=3, XeLaTeX, and the standard LaTeX
packages in TeX Live's latex-recommended/latex-extra collections. Fonts:
Latin Modern Roman, Sans, Mono, and Math. No Python packages are needed.

Usage: python scripts/build_guide.py

The final files are docs/mathematics.tex and docs/mathematics.pdf. Build
intermediates live in a temporary directory; no network access is used.
"""

from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def run(command, *, env=None, cwd=None):
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env, cwd=cwd)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, command))
                           + "\n" + result.stdout[-14000:])
    return result.stdout


def main():
    for tool in ("pandoc", "xelatex"):
        if shutil.which(tool) is None:
            raise SystemExit(f"Missing required program: {tool}")

    with tempfile.TemporaryDirectory(prefix="hassett-guide-") as temp:
        build = Path(temp)
        env = os.environ.copy()
        # Some minimal Debian containers have TeX files but no ls-R caches.
        # Fall back to direct filesystem discovery locally, without modifying
        # system configuration or relying on a network package installation.
        if shutil.which("kpsewhich"):
            found = subprocess.run(["kpsewhich", "article.cls"],
                                   capture_output=True, text=True, env=env)
            texdist = Path("/usr/share/texlive/texmf-dist")
            if not found.stdout.strip() and texdist.is_dir():
                env["TEXMFVAR"] = str(build / "texmf-var")
                env["TEXMFCONFIG"] = str(build / "texmf-config")
                env["TEXMF"] = "{" + ",".join([
                    env["TEXMFVAR"], env["TEXMFCONFIG"], "/etc/texmf",
                    "/usr/share/texmf", str(texdist)]) + "}"
            fmt = subprocess.run(["kpsewhich", "-format=fmt", "xelatex.fmt"],
                                 capture_output=True, text=True, env=env)
            if not fmt.stdout.strip():
                # A format is a generated cache, not an additional dependency.
                # Build it locally when the host TeX installation omits it.
                run(["xetex", "-ini", "-etex", "-jobname=xelatex",
                     "-progname=xelatex", "-interaction=nonstopmode",
                     "-halt-on-error", "-output-directory=" + str(build),
                     "xelatex.ini"], env=env, cwd=build)
                env["TEXFORMATS"] = str(build) + os.pathsep + env.get("TEXFORMATS", "")

        command = [
            "pandoc", str(DOCS / "mathematics.md"), "--standalone",
            "--from=markdown+tex_math_dollars", "--to=latex",
            "--number-sections", "--table-of-contents", "--toc-depth=2",
            "--include-in-header=" + str(DOCS / "guide_header.tex"),
            "--variable=documentclass:article", "--variable=fontsize:11pt",
            "--variable=papersize:a4", "--variable=geometry:margin=26mm",
            # TeX-distributed filenames work without registering fonts with
            # the host OS (notably older macOS/CoreText installations).
            "--variable=mainfont:lmroman10-regular.otf",
            "--variable=mainfontoptions:BoldFont=lmroman10-bold.otf,ItalicFont=lmroman10-italic.otf,BoldItalicFont=lmroman10-bolditalic.otf",
            "--variable=sansfont:lmsans10-regular.otf",
            "--variable=sansfontoptions:BoldFont=lmsans10-bold.otf,ItalicFont=lmsans10-oblique.otf,BoldItalicFont=lmsans10-boldoblique.otf",
            "--variable=monofont:lmmono10-regular.otf",
            "--variable=monofontoptions:ItalicFont=lmmono10-italic.otf",
            "--variable=mathfont:latinmodern-math.otf", "--variable=linestretch:1.04",
            "--output=" + str(DOCS / "mathematics.tex"),
        ]
        run(command, env=env, cwd=ROOT)
        tex_path = DOCS / "mathematics.tex"
        tex = tex_path.read_text()
        # Keep prose lead-ins in the same paragraph as their display. Pandoc's
        # default blank paragraph before \\[ permits orphaned "we obtain" lines.
        tex = tex.replace("\n\n\\[", "\n\\[")
        # Give the appendix table and bibliography clean page starts. These
        # layout changes leave every formula and validation value unchanged.
        tex = tex.replace(r"\section{Appendix:", "\\clearpage\n\\section{Appendix:")
        tex = tex.replace(r"\section{References}", "\\clearpage\n\\section{References}")
        # The only table has four columns; allocate room to the discriminant
        # lists instead of using Pandoc's four equal-width default columns.
        widths = iter(("0.18", "0.17", "0.43", "0.22"))
        tex = re.sub(r"\\real\{0\.2500\}",
                     lambda match: r"\real{" + next(widths) + "}", tex, count=4)
        tex_path.write_text(tex)
        command = ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                   "-file-line-error", "-output-directory=" + str(build),
                   str(DOCS / "mathematics.tex")]
        logs = []
        for _ in range(3):
            logs.append(run(command, env=env, cwd=DOCS))
        shutil.copy2(build / "mathematics.pdf", DOCS / "mathematics.pdf")
        final_log = (build / "mathematics.log").read_text(errors="replace")
        warnings = [line for line in final_log.splitlines()
                    if "Overfull" in line or "Missing character" in line]
        if warnings:
            raise RuntimeError("Review typesetting warnings:\n" + "\n".join(warnings))
        print("Built docs/mathematics.tex and docs/mathematics.pdf")
        if shutil.which("pdfinfo"):
            info = run(["pdfinfo", str(DOCS / "mathematics.pdf")])
            print("\n".join(line for line in info.splitlines()
                            if line.startswith(("Pages:", "Page size:", "File size:"))))


if __name__ == "__main__":
    main()
