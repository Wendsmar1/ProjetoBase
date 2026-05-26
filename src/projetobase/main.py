from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

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
    return sorted(n for n in a if n in b)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def scan_devhub(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None) -> Path:
    c_stats = _scan_root(c_root)
    f_stats = _scan_root(f_root)
    shared_names = _find_duplicates(c_root, f_root)

    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_scan_{ts}.md"
    report_json = out_dir / f"devhub_scan_{ts}.json"

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

    alerts: list[str] = []
    if not c_stats["exists"]:
        alerts.append("C:/DevHub nao encontrado")
    if not f_stats["exists"]:
        alerts.append("F:/DevHub nao encontrado")
    if not shared_names:
        alerts.append("Sem nomes de pastas duplicados nos primeiros niveis")
    else:
        alerts.append("Pastas com nomes repetidos entre C e F (ate nivel 2)")

    for a in alerts:
        lines.append(f"- {a}")
    for name in shared_names[:30]:
        lines.append(f"  - {name}")

    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(
        report_json,
        {
            "type": "scan",
            "timestamp": ts,
            "c_root": str(c_root),
            "f_root": str(f_root),
            "c_stats": c_stats,
            "f_stats": f_stats,
            "shared_names": shared_names,
            "alerts": alerts,
            "report_md": str(report),
        },
    )
    return report


def check_paths(
    root: Path = Path("F:/DevHub"),
    out_dir: Path | None = None,
    legacy_patterns: Iterable[str] | None = None,
) -> Path:
    if legacy_patterns is None:
        legacy_patterns = (
            "F:/03_Projetos",
            "F:\\03_Projetos",
            "C:/docker_pre_devhub",
            "C:\\docker_pre_devhub",
        )

    include_names = {
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
        ".env",
    }

    hits: list[tuple[Path, int, str, str]] = []
    if root.exists():
        for file in root.rglob("*"):
            if not file.is_file() or file.name not in include_names:
                continue
            try:
                content = file.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for line_no, line in enumerate(content, start=1):
                for pattern in legacy_patterns:
                    if pattern in line:
                        suggestion = line.replace(pattern, "F:/DevHub/Projetos/Ativos/03_Projetos")
                        hits.append((file, line_no, line.strip(), suggestion.strip()))

    if out_dir is None:
        out_dir = root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_check_paths_{ts}.md"
    report_json = out_dir / f"devhub_check_paths_{ts}.json"

    lines = [
        "# DevHub Legacy Paths Report",
        "",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Root: {root}",
        f"- Hits: {len(hits)}",
        "",
        "## Findings",
    ]
    if not hits:
        lines.append("- Nenhum path legado encontrado.")
    else:
        for file, line_no, line, suggestion in hits:
            lines.append(f"- {file}:{line_no}")
            lines.append(f"  - atual: {line}")
            lines.append(f"  - sugestao: {suggestion}")

    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(
        report_json,
        {
            "type": "check-paths",
            "timestamp": ts,
            "root": str(root),
            "hits": [
                {
                    "file": str(file),
                    "line": line_no,
                    "current": line,
                    "suggestion": suggestion,
                }
                for file, line_no, line, suggestion in hits
            ],
            "hits_count": len(hits),
            "report_md": str(report),
        },
    )
    return report


def cleanup_plan(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None) -> Path:
    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    roots = [c_root, f_root]
    candidates: list[dict[str, str | int]] = []
    dir_rules = {
        "__pycache__": ("baixo", "Remover cache Python"),
        ".pytest_cache": ("baixo", "Remover cache de testes"),
        ".mypy_cache": ("baixo", "Remover cache de tipagem"),
        ".ruff_cache": ("baixo", "Remover cache de lint"),
    }
    file_suffix_rules = {
        ".tmp": ("baixo", "Arquivo temporario"),
        ".bak": ("medio", "Backup antigo; revisar antes"),
        ".old": ("medio", "Arquivo legado; revisar antes"),
        ".log": ("baixo", "Log pode ser arquivado/removido"),
    }

    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_dir() and p.name in dir_rules:
                risk, reason = dir_rules[p.name]
                candidates.append(
                    {
                        "path": str(p),
                        "kind": "dir",
                        "risk": risk,
                        "reason": reason,
                        "suggested_action": "review_then_remove",
                    }
                )
            elif p.is_file():
                if p.name.endswith("~"):
                    candidates.append(
                        {
                            "path": str(p),
                            "kind": "file",
                            "risk": "baixo",
                            "reason": "Arquivo temporario de editor",
                            "suggested_action": "review_then_remove",
                        }
                    )
                    continue
                for suf, (risk, reason) in file_suffix_rules.items():
                    if p.suffix.lower() == suf:
                        candidates.append(
                            {
                                "path": str(p),
                                "kind": "file",
                                "risk": risk,
                                "reason": reason,
                                "suggested_action": "review_then_remove",
                            }
                        )
                        break

    by_risk = {"baixo": 0, "medio": 0, "alto": 0}
    for c in candidates:
        by_risk[str(c["risk"])] += 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_cleanup_plan_{ts}.md"
    report_json = out_dir / f"devhub_cleanup_plan_{ts}.json"

    lines = [
        "# DevHub Cleanup Plan",
        "",
        "- Modo: analise apenas (nenhuma remocao executada)",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- C root: {c_root}",
        f"- F root: {f_root}",
        f"- Itens candidatos: {len(candidates)}",
        f"- Risco baixo: {by_risk['baixo']}",
        f"- Risco medio: {by_risk['medio']}",
        f"- Risco alto: {by_risk['alto']}",
        "",
        "## Candidatos (top 100)",
    ]
    for item in candidates[:100]:
        lines.append(f"- [{item['risk']}] {item['path']} | {item['reason']}")

    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(
        report_json,
        {
            "type": "cleanup-plan",
            "timestamp": ts,
            "mode": "analysis_only",
            "c_root": str(c_root),
            "f_root": str(f_root),
            "candidates_count": len(candidates),
            "risk_summary": by_risk,
            "candidates": candidates,
            "report_md": str(report),
        },
    )
    return report


def weekly_report(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None) -> Path:
    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    scan_report = scan_devhub(c_root, f_root, out_dir)
    paths_report = check_paths(f_root, out_dir)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_weekly_report_{ts}.md"
    report_json = out_dir / f"devhub_weekly_report_{ts}.json"
    lines = [
        "# DevHub Weekly Report",
        "",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- C root: {c_root}",
        f"- F root: {f_root}",
        "",
        "## Outputs",
        f"- Scan report: {scan_report}",
        f"- Paths report: {paths_report}",
        "",
        "## Status",
        "- Consolidado gerado com sucesso.",
    ]
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(
        report_json,
        {
            "type": "weekly-report",
            "timestamp": ts,
            "c_root": str(c_root),
            "f_root": str(f_root),
            "scan_report_md": str(scan_report),
            "paths_report_md": str(paths_report),
            "weekly_report_md": str(report),
            "status": "ok",
        },
    )
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

    p_check = sub.add_parser("check-paths", help="detecta paths legados em compose/.env")
    p_check.add_argument("--root", default="F:/DevHub")
    p_check.add_argument("--out-dir", default=None)

    p_cleanup = sub.add_parser("cleanup-plan", help="gera plano de limpeza seguro sem apagar nada")
    p_cleanup.add_argument("--c-root", default="C:/DevHub")
    p_cleanup.add_argument("--f-root", default="F:/DevHub")
    p_cleanup.add_argument("--out-dir", default=None)

    p_weekly = sub.add_parser("weekly-report", help="gera relatorio semanal consolidado")
    p_weekly.add_argument("--c-root", default="C:/DevHub")
    p_weekly.add_argument("--f-root", default="F:/DevHub")
    p_weekly.add_argument("--out-dir", default=None)

    args = parser.parse_args(argv)

    if args.command == "scan":
        out_dir = Path(args.out_dir) if args.out_dir else None
        report = scan_devhub(Path(args.c_root), Path(args.f_root), out_dir)
        print(f"Relatorio gerado: {report}")
        return 0

    if args.command == "check-paths":
        out_dir = Path(args.out_dir) if args.out_dir else None
        report = check_paths(Path(args.root), out_dir)
        print(f"Relatorio gerado: {report}")
        return 0

    if args.command == "cleanup-plan":
        out_dir = Path(args.out_dir) if args.out_dir else None
        report = cleanup_plan(Path(args.c_root), Path(args.f_root), out_dir)
        print(f"Relatorio gerado: {report}")
        return 0

    if args.command == "weekly-report":
        out_dir = Path(args.out_dir) if args.out_dir else None
        report = weekly_report(Path(args.c_root), Path(args.f_root), out_dir)
        print(f"Relatorio gerado: {report}")
        return 0

    name = args.name if args.command == "run" else "mundo"
    print(run(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
