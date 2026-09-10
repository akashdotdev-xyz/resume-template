#!/usr/bin/env python3
"""
Resume Builder
==============
Edit `data.json` with your content, then run:

    python3 builder.py                  # generates output/resume.tex and output/resume.pdf
    python3 builder.py --no-pdf         # generates only the .tex file, skips PDF compilation
    python3 builder.py -i my_data.json  # use a custom JSON file

PDF compilation uses Tectonic (https://tectonic-typesetting.github.io/),
a self-contained LaTeX engine. Install it with: brew install tectonic
"""

import json
import argparse
import subprocess
import shutil
import sys
from pathlib import Path


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text.
    Skips text that already contains LaTeX commands (backslashes)."""
    if "\\" in text or "{" in text:
        return text  # already contains LaTeX markup, don't escape
    replacements = [
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def render_header(data: dict, colors: dict) -> str:
    """Render the header section with name and contact links."""
    header = data["header"]
    contact_parts = []
    for c in header["contacts"]:
        icon = f"\\{c['icon']}"
        part = (
            f'\\textcolor[HTML]{{{colors["accent"]}}}'
            f'{{\\href{{{c["url"]}}}'
            f'{{\\raisebox{{-0.05\\height}}{{{icon}}} {c["text"]}}}}}'
        )
        contact_parts.append(part)

    contacts_line = " $|$\n".join(contact_parts)

    return f"""% -------------------------------------
% HEADER
% -------------------------------------
\\begin{{tabularx}}{{\\linewidth}}{{@{{}} C @{{}}}}
\\textcolor[HTML]{{{colors["name"]}}}{{\\Huge {header["name"]}}} \\\\[6pt]
\\\\
{contacts_line}
\\end{{tabularx}}"""


def render_experience(data: dict, colors: dict) -> str:
    """Render the experience section."""
    lines = [
        "% -------------------------------------",
        "% EXPERIENCE SECTION",
        "% -------------------------------------",
        "\\section{Experience}",
    ]

    for exp in data["experience"]:
        lines.append(f"\\begin{{tabularx}}{{\\linewidth}}{{@{{}} l >{{\\raggedleft\\arraybackslash}}X @{{}}}}")
        lines.append(
            f'\\textbf{{\\href{{{exp["url"]}}}{{{exp["company"]}}}}} & '
            f'\\textcolor[HTML]{{{colors["accent"]}}}{{{exp["date"]}}}'
        )
        lines.append("\\end{tabularx}")
        lines.append(f'\\noindent\\textbf{{\\textit{{{exp["title"]}}}}}')
        lines.append("\\begin{itemize}[nosep, leftmargin=2em, itemsep=1pt]")
        for bullet in exp["bullets"]:
            lines.append(f"    \\item {bullet}")
        lines.append("\\end{itemize}")
        lines.append("")  # blank line between entries

    return "\n".join(lines)


def render_education(data: dict, colors: dict) -> str:
    """Render the education section."""
    lines = [
        "% -------------------------------------",
        "% EDUCATION SECTION",
        "% -------------------------------------",
        "\\section{Education}",
    ]

    for edu in data["education"]:
        grade_part = ""
        if edu.get("grade"):
            grade_part = (
                f' & \\textcolor[HTML]{{{colors["highlight"]}}}'
                f'{{\\textbf{{\\textit{{{edu["grade"]}}}}}}}'
            )

        lines.append(f"\\begin{{tabularx}}{{\\linewidth}}{{@{{}} l >{{\\raggedleft\\arraybackslash}}X @{{}}}}")
        lines.append(
            f'\\textcolor[HTML]{{{colors["name"]}}}{{\\textbf{{{edu["institution"]}}}}} & '
            f'\\textcolor[HTML]{{{colors["accent"]}}}{{{edu["date"]}}} \\\\'
        )
        lines.append(
            f'\\textcolor[HTML]{{{colors["accent"]}}}{{{edu["degree"]}}}{grade_part} \\\\'
        )
        lines.append("\\end{tabularx}")
        lines.append("")

    return "\n".join(lines)


def render_skills(data: dict) -> str:
    """Render the skills section."""
    lines = [
        "% -------------------------------------",
        "% SKILLS SECTION",
        "% -------------------------------------",
        "\\section{Skills}",
    ]

    for skill in data["skills"]:
        lines.append(f'\\noindent\\textbf{{{skill["category"]}:}} {skill["items"]}')
        lines.append("")

    return "\n".join(lines)


def render_achievements(data: dict, colors: dict) -> str:
    """Render the leadership & achievements section."""
    ach = data["achievements"]
    lines = [
        "% -------------------------------------",
        "% LEADERSHIP & ACHIEVEMENTS SECTION",
        "% -------------------------------------",
        f'\\section{{{ach["section_title"]}}}',
    ]

    for group in ach["groups"]:
        lines.append(
            f'\\noindent\\textcolor[HTML]{{{colors["name"]}}}'
            f'{{\\textbf{{{group["group_title"]}}}}}'
        )
        lines.append("")
        lines.append("\\begin{itemize}[nosep, leftmargin=2em, itemsep=2pt, topsep=0pt]")
        for bullet in group["bullets"]:
            lines.append(f"    \\item {bullet}")
        lines.append("\\end{itemize}")
        lines.append("")

    return "\n".join(lines)


def render_preamble(settings: dict) -> str:
    """Render the LaTeX preamble with packages and settings."""
    return f"""\\documentclass[{settings["paper"]},{settings["font_size"]}]{{article}}

% -------------------------------------
% PACKAGES
% -------------------------------------
\\usepackage{{parskip}}
\\usepackage{{fontspec}}
\\usepackage{{graphicx}}
\\usepackage[usenames,dvipsnames]{{xcolor}}
\\usepackage[scale={settings["scale"]}, top={settings["top_margin"]}, bottom={settings["bottom_margin"]}]{{geometry}}
\\usepackage{{tabularx}}
\\usepackage{{enumitem}}
\\usepackage{{titlesec}}
\\usepackage[unicode, draft=false]{{hyperref}}
\\usepackage{{fontawesome5}}
\\usepackage[normalem]{{ulem}}

% -------------------------------------
% CUSTOM SETTINGS
% -------------------------------------
\\newcolumntype{{C}}{{>{{\\centering\\arraybackslash}}X}}
\\titleformat{{\\section}}{{\\Large\\scshape\\raggedright}}{{}}{{0em}}{{}}[\\titlerule]
\\titlespacing{{\\section}}{{1pt}}{{2pt}}{{2pt}}
\\setmainfont{{{settings["font"]}}}"""


def build_resume(data: dict) -> str:
    """Assemble the complete LaTeX document from JSON data."""
    settings = data["settings"]
    colors = {
        "name": settings["name_color"],
        "accent": settings["accent_color"],
        "highlight": settings["highlight_color"],
    }

    sections = [
        render_preamble(settings),
        "",
        "% -------------------------------------",
        "% DOCUMENT START",
        "% -------------------------------------",
        "\\begin{document}",
        "\\pagestyle{empty}",
        "",
        render_header(data, colors),
        "",
        render_experience(data, colors),
        render_education(data, colors),
        render_skills(data),
        render_achievements(data, colors),
        "\\end{document}",
    ]

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Build resume from JSON data.")
    parser.add_argument(
        "-i", "--input",
        default="data.json",
        help="Path to JSON data file (default: data.json)",
    )
    parser.add_argument(
        "-o", "--output",
        default="output/akash_kumar.tex",
        help="Output .tex file path (default: output/akash_kumar.tex)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF compilation; only generate the .tex file",
    )
    args = parser.parse_args()

    # Load JSON
    json_path = Path(args.input)
    if not json_path.exists():
        print(f"Error: '{json_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build and write .tex
    tex_content = build_resume(data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tex_content, encoding="utf-8")
    print(f"Generated: {output_path}")

    # Compile to PDF by default
    if not args.no_pdf:
        if shutil.which("tectonic") is None:
            print(
                "Error: 'tectonic' not found on PATH. Install it with: brew install tectonic\n"
                "(or re-run with --no-pdf to only generate the .tex file)",
                file=sys.stderr,
            )
            sys.exit(1)

        print("Compiling with tectonic...")
        result = subprocess.run(
            ["tectonic", str(output_path.name)],
            cwd=output_path.parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            pdf_name = output_path.with_suffix(".pdf")
            print(f"PDF generated: {pdf_name}")
        else:
            print("Compilation failed. tectonic output:", file=sys.stderr)
            print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()