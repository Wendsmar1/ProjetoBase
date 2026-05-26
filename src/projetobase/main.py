from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

from projetobase import __version__


def run(name: str = "mundo") -> str:
    return f"Ola, {name}! ProjetoBase v{__version__}"


def _scan_root(root: Path) -> dict[str, int | bool]:
    if not root.exists():
        return {"exists": False, "dirs": 0, "files": 0}

    dirs = 0
    files = 0
    for p in root.rglob("*"):
        if p.is_dir():
            dirs += 1
        elif p.is_file():
            files += 1

    return {"exists": True, "dirs": dirs, "files": files}


def _find_duplicates(root_a: Path, root_b: Path, depth: int = 2) -> list[str]:
    def collect_names(root: Path) -> Counter[str]:
        names: Counter[str] = Counter()
        if not root.exists():
            return names
        for p in root.rglob("*"):
            if p.is_dir() and len(p.relative_to(root).parts) <= depth:
                names[p.name.lower()] += 1
        return names

    a = collect_names(root_a)
    b = collect_names(root_b)
    shared = sorted(n for n in a if n in b)
    return shared


def scan_devhub(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None) -> Path:
    c_stats = _scan_root(c_root)
    f_stats = _scan_root(f_root)
    shared_names = _find_duplicates(c_root, f_root)

    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_scan_{ts}.md"

    lines = [
        "# DevHub Scan Report",
        "",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- C root: {c_root}",
        f"- F root: {f_root}",
        "",
        "## Summary",
        f"- C exists: {c_stats['exists']}",
        f"- C dirs: {c_stats['dirs']}",
        f"- C files: {c_stats['files']}",
        f"- F exists: {f_stats['exists']}",
        f"- F dirs: {f_stats['dirs']}",
        f"- F files: {f_stats['files']}",
        "",
        "## Alerts",
    ]

    if not c_stats["exists"]:
        lines.append("- C:/DevHub nao encontrado")
    if not f_stats["exists"]:
        lines.append("- F:/DevHub nao encontrado")
    if not shared_names:
        lines.append("- Sem nomes de pastas duplicados nos primeiros niveis")
    else:
        lines.append("- Pastas com nomes repetidos entre C e F (ate nivel 2):")
        for name in shared_names[:30]:
            lines.append(f"  - {name}")

    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="projetobase")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="mensagem de ola")
    p_run.add_argument("--name", default="mundo")

    p_scan = sub.add_parser("scan", help="escaneia C:/DevHub e F:/DevHub")
    p_scan.add_argument("--c-root", default="C:/DevHub")
    p_scan.add_argument("--f-root", default="F:/DevHub")
    p_scan.add_argument("--out-dir", default=None)

    args = parser.parse_args(argv)

    if args.command == "scan":
        out_dir = Path(args.out_dir) if args.out_dir else None
        report = scan_devhub(Path(args.c_root), Path(args.f_root), out_dir)
        print(f"Relatorio gerado: {report}")
        return 0

    name = args.name if args.command == "run" else "mundo"
    print(run(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
