from __future__ import annotations

import argparse
import csv
import json
import shutil
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


def _collect_cleanup_candidates(c_root: Path, f_root: Path) -> list[dict[str, str | int]]:
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
                candidates.append({"path": str(p), "kind": "dir", "risk": risk, "reason": reason, "suggested_action": "review_then_remove"})
            elif p.is_file():
                if p.name.endswith("~"):
                    candidates.append({"path": str(p), "kind": "file", "risk": "baixo", "reason": "Arquivo temporario de editor", "suggested_action": "review_then_remove"})
                    continue
                for suf, (risk, reason) in file_suffix_rules.items():
                    if p.suffix.lower() == suf:
                        candidates.append({"path": str(p), "kind": "file", "risk": risk, "reason": reason, "suggested_action": "review_then_remove"})
                        break
    return candidates


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
    alerts: list[str] = []
    if not c_stats["exists"]:
        alerts.append("C:/DevHub nao encontrado")
    if not f_stats["exists"]:
        alerts.append("F:/DevHub nao encontrado")
    if not shared_names:
        alerts.append("Sem nomes de pastas duplicados nos primeiros niveis")
    else:
        alerts.append("Pastas com nomes repetidos entre C e F (ate nivel 2)")
    lines = [
        "# DevHub Scan Report", "", f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"- C root: {c_root}", f"- F root: {f_root}", "",
        "## Summary", f"- C exists: {c_stats['exists']}", f"- C dirs: {c_stats['dirs']}", f"- C files: {c_stats['files']}",
        f"- F exists: {f_stats['exists']}", f"- F dirs: {f_stats['dirs']}", f"- F files: {f_stats['files']}", "", "## Alerts",
    ]
    for a in alerts:
        lines.append(f"- {a}")
    for name in shared_names[:30]:
        lines.append(f"  - {name}")
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(report_json, {"type": "scan", "timestamp": ts, "c_root": str(c_root), "f_root": str(f_root), "c_stats": c_stats, "f_stats": f_stats, "shared_names": shared_names, "alerts": alerts, "report_md": str(report)})
    return report


def check_paths(root: Path = Path("F:/DevHub"), out_dir: Path | None = None, legacy_patterns: Iterable[str] | None = None) -> Path:
    if legacy_patterns is None:
        legacy_patterns = ("F:/03_Projetos", "F:\\03_Projetos", "C:/docker_pre_devhub", "C:\\docker_pre_devhub")
    include_names = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", ".env"}
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
    lines = ["# DevHub Legacy Paths Report", "", f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"- Root: {root}", f"- Hits: {len(hits)}", "", "## Findings"]
    if not hits:
        lines.append("- Nenhum path legado encontrado.")
    else:
        for file, line_no, line, suggestion in hits:
            lines.append(f"- {file}:{line_no}")
            lines.append(f"  - atual: {line}")
            lines.append(f"  - sugestao: {suggestion}")
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(report_json, {"type": "check-paths", "timestamp": ts, "root": str(root), "hits": [{"file": str(file), "line": line_no, "current": line, "suggestion": suggestion} for file, line_no, line, suggestion in hits], "hits_count": len(hits), "report_md": str(report)})
    return report


def cleanup_plan(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None) -> Path:
    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = _collect_cleanup_candidates(c_root, f_root)
    by_risk = {"baixo": 0, "medio": 0, "alto": 0}
    for c in candidates:
        by_risk[str(c["risk"])] += 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out_dir / f"devhub_cleanup_plan_{ts}.md"
    report_json = out_dir / f"devhub_cleanup_plan_{ts}.json"
    lines = ["# DevHub Cleanup Plan", "", "- Modo: analise apenas (nenhuma remocao executada)", f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"- C root: {c_root}", f"- F root: {f_root}", f"- Itens candidatos: {len(candidates)}", f"- Risco baixo: {by_risk['baixo']}", f"- Risco medio: {by_risk['medio']}", f"- Risco alto: {by_risk['alto']}", "", "## Candidatos (top 100)"]
    for item in candidates[:100]:
        lines.append(f"- [{item['risk']}] {item['path']} | {item['reason']}")
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(report_json, {"type": "cleanup-plan", "timestamp": ts, "mode": "analysis_only", "c_root": str(c_root), "f_root": str(f_root), "candidates_count": len(candidates), "risk_summary": by_risk, "candidates": candidates, "report_md": str(report)})
    return report


def apply_cleanup(c_root: Path = Path("C:/DevHub"), f_root: Path = Path("F:/DevHub"), out_dir: Path | None = None, risk: str = "baixo", apply: bool = False) -> Path:
    if out_dir is None:
        out_dir = f_root / "05_Logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = _collect_cleanup_candidates(c_root, f_root)
    allowed = [c for c in candidates if str(c["risk"]) == risk]
    removed: list[str] = []
    failed: list[dict[str, str]] = []
    for c in allowed:
        p = Path(str(c["path"]))
        if not p.exists():
            continue
        if not apply:
            removed.append(str(p))
            continue
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            removed.append(str(p))
        except OSError as exc:
            failed.append({"path": str(p), "error": str(exc)})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "apply" if apply else "dry-run"
    report = out_dir / f"devhub_apply_cleanup_{ts}.md"
    report_json = out_dir / f"devhub_apply_cleanup_{ts}.json"
    lines = [
        "# DevHub Apply Cleanup",
        "",
        f"- Mode: {mode}",
        f"- Risk filter: {risk}",
        f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Candidates in risk: {len(allowed)}",
        f"- {'Would remove' if not apply else 'Removed'}: {len(removed)}",
        f"- Failed: {len(failed)}",
        "",
        "## Items",
    ]
    for p in removed[:200]:
        lines.append(f"- {p}")
    if failed:
        lines.append("")
        lines.append("## Failures")
        for f in failed:
            lines.append(f"- {f['path']} | {f['error']}")
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(report_json, {
        "type": "apply-cleanup",
        "timestamp": ts,
        "mode": mode,
        "risk": risk,
        "apply": apply,
        "c_root": str(c_root),
        "f_root": str(f_root),
        "candidates_in_risk": len(allowed),
        "processed": removed,
        "failed": failed,
        "report_md": str(report),
    })
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
    lines = ["# DevHub Weekly Report", "", f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"- C root: {c_root}", f"- F root: {f_root}", "", "## Outputs", f"- Scan report: {scan_report}", f"- Paths report: {paths_report}", "", "## Status", "- Consolidado gerado com sucesso."]
    report.write_text("\n".join(lines), encoding="utf-8")
    _write_json(report_json, {"type": "weekly-report", "timestamp": ts, "c_root": str(c_root), "f_root": str(f_root), "scan_report_md": str(scan_report), "paths_report_md": str(paths_report), "weekly_report_md": str(report), "status": "ok"})
    return report


def build_dashboard(logs_dir: Path = Path("F:/DevHub/05_Logs"), out_html: Path | None = None) -> Path:
    if out_html is None:
        out_html = logs_dir / "dashboard_devhub.html"
    logs_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for p in sorted(logs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            records.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    by_type: Counter[str] = Counter(str(r.get("type", "unknown")) for r in records)
    latest = records[:20]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    alerts: list[str] = []
    latest_check = next((r for r in records if str(r.get("type")) == "check-paths"), None)
    if latest_check and int(latest_check.get("hits_count", 0)) > 0:
        alerts.append(f"Paths legados detectados: {latest_check.get('hits_count')}")

    latest_weekly = next((r for r in records if str(r.get("type")) == "weekly-report"), None)
    if latest_weekly and str(latest_weekly.get("status", "")).lower() != "ok":
        alerts.append("Weekly report com status diferente de ok.")

    cleanup_plans = [r for r in records if str(r.get("type")) == "cleanup-plan"][:2]
    if len(cleanup_plans) == 2:
        curr = int(cleanup_plans[0].get("candidates_count", 0))
        prev = int(cleanup_plans[1].get("candidates_count", 0))
        if prev > 0 and curr > int(prev * 1.2):
            alerts.append(f"Crescimento de candidatos de limpeza: {prev} -> {curr}")

    rows = []
    runs_rows: list[list[str]] = []
    for r in latest:
        typ = str(r.get("type", "unknown"))
        rts = str(r.get("timestamp", "-"))
        status = str(r.get("status", "-"))
        badge_class = "badge badge-ok" if status.lower() == "ok" else "badge badge-warn"
        rows.append(f"<tr><td>{typ}</td><td>{rts}</td><td><span class='{badge_class}'>{status}</span></td></tr>")
        runs_rows.append([typ, rts, status])

    cards = "".join(
        f"<div class='card'><h3>{k}</h3><p>{v}</p></div>"
        for k, v in sorted(by_type.items())
    ) or "<div class='card'><h3>Sem dados</h3><p>0</p></div>"

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DevHub Dashboard</title>
  <style>
    :root {{
      --bg: #f1f5f9;
      --surface: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #dbe7f3;
      --accent: #0ea5e9;
      --accent-soft: #e0f2fe;
      --ok: #16a34a;
      --warn: #ea580c;
      --shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
    }}
    body {{
      font-family: "Segoe UI", "Trebuchet MS", Arial, sans-serif;
      margin: 0;
      background: radial-gradient(circle at top right, #e0f2fe 0%, var(--bg) 45%);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1100px;
      margin: 24px auto;
      padding: 0 16px 24px;
    }}
    .hero {{
      background: linear-gradient(135deg, #0ea5e9, #0369a1);
      color: #fff;
      border-radius: 14px;
      padding: 18px 20px;
      box-shadow: var(--shadow);
      margin-bottom: 16px;
    }}
    .hero h1 {{ margin: 0 0 6px; font-size: 1.5rem; }}
    .muted {{ opacity: 0.92; font-size: 0.92rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      box-shadow: var(--shadow);
    }}
    .card h3 {{ margin: 0; font-size: 0.92rem; color: var(--muted); font-weight: 700; }}
    .card p {{ margin: 8px 0 0; font-size: 1.45rem; font-weight: 700; color: #0b3b5a; }}
    h2 {{ margin: 16px 0 10px; }}
    .alerts {{ background: #fff7ed; border-color: #fed7aa; }}
    .alert-item {{ margin: 0 0 6px; color: #9a3412; font-weight: 600; }}
    .ok {{ color: var(--ok); font-weight: 700; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }}
    th, td {{ padding: 10px; border-bottom: 1px solid #edf2f7; text-align: left; }}
    th {{ background: var(--accent-soft); color: #0c4a6e; }}
    tbody tr:hover {{ background: #f8fafc; }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      background: #e2e8f0;
      color: #334155;
    }}
    .badge-ok {{ background: #dcfce7; color: #166534; }}
    .badge-warn {{ background: #ffedd5; color: #9a3412; }}
  </style>
</head>
<body>
  <div class="wrap">
  <div class="hero">
    <h1>DevHub Dashboard</h1>
    <div class="muted">Gerado em: {ts} | Logs: {logs_dir}</div>
  </div>
  <div class="grid">
    <div class='card'><h3>Total JSON</h3><p>{len(records)}</p></div>
    {cards}
  </div>
  <h2>Alertas</h2>
  <div class="card alerts">
    {''.join(f"<p class='alert-item'>• {a}</p>" for a in alerts) if alerts else '<p class="ok">Sem alertas críticos.</p>'}
  </div>
  <br />
  <table>
    <thead><tr><th>Tipo</th><th>Timestamp</th><th>Status</th></tr></thead>
    <tbody>
      {''.join(rows) if rows else '<tr><td colspan="3">Sem registros</td></tr>'}
    </tbody>
  </table>
  </div>
</body>
</html>"""
    out_html.write_text(html, encoding="utf-8")

    summary_csv = logs_dir / "dashboard_devhub_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["total_json", len(records)])
        for k, v in sorted(by_type.items()):
            w.writerow([f"type_{k}", v])
        w.writerow(["alerts_count", len(alerts)])

    runs_csv = logs_dir / "dashboard_devhub_runs.csv"
    with runs_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "timestamp", "status"])
        w.writerows(runs_rows)

    return out_html


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

    p_apply = sub.add_parser("apply-cleanup", help="aplica limpeza por risco; dry-run por padrao")
    p_apply.add_argument("--c-root", default="C:/DevHub")
    p_apply.add_argument("--f-root", default="F:/DevHub")
    p_apply.add_argument("--out-dir", default=None)
    p_apply.add_argument("--risk", choices=["baixo", "medio", "alto"], default="baixo")
    p_apply.add_argument("--apply", action="store_true")

    p_weekly = sub.add_parser("weekly-report", help="gera relatorio semanal consolidado")
    p_weekly.add_argument("--c-root", default="C:/DevHub")
    p_weekly.add_argument("--f-root", default="F:/DevHub")
    p_weekly.add_argument("--out-dir", default=None)
    p_dash = sub.add_parser("dashboard", help="gera dashboard HTML a partir dos JSONs de logs")
    p_dash.add_argument("--logs-dir", default="F:/DevHub/05_Logs")
    p_dash.add_argument("--out-html", default=None)

    args = parser.parse_args(argv)
    if args.command == "scan":
        report = scan_devhub(Path(args.c_root), Path(args.f_root), Path(args.out_dir) if args.out_dir else None)
        print(f"Relatorio gerado: {report}")
        return 0
    if args.command == "check-paths":
        report = check_paths(Path(args.root), Path(args.out_dir) if args.out_dir else None)
        print(f"Relatorio gerado: {report}")
        return 0
    if args.command == "cleanup-plan":
        report = cleanup_plan(Path(args.c_root), Path(args.f_root), Path(args.out_dir) if args.out_dir else None)
        print(f"Relatorio gerado: {report}")
        return 0
    if args.command == "apply-cleanup":
        report = apply_cleanup(Path(args.c_root), Path(args.f_root), Path(args.out_dir) if args.out_dir else None, args.risk, args.apply)
        print(f"Relatorio gerado: {report}")
        return 0
    if args.command == "weekly-report":
        report = weekly_report(Path(args.c_root), Path(args.f_root), Path(args.out_dir) if args.out_dir else None)
        print(f"Relatorio gerado: {report}")
        return 0
    if args.command == "dashboard":
        out_html = Path(args.out_html) if args.out_html else None
        html = build_dashboard(Path(args.logs_dir), out_html)
        print(f"Dashboard gerado: {html}")
        return 0

    name = args.name if args.command == "run" else "mundo"
    print(run(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
