import json
from pathlib import Path

from projetobase.main import apply_cleanup, build_dashboard, check_paths, cleanup_plan, main, run, scan_devhub, weekly_report


def test_run_default():
    assert "Ola, mundo!" in run()


def test_scan_generates_report_and_json(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    (c_root / "Apps").mkdir(parents=True)
    (f_root / "Apps").mkdir(parents=True)
    report = scan_devhub(c_root, f_root, tmp_path)
    data = json.loads(Path(str(report).replace('.md', '.json')).read_text(encoding='utf-8'))
    assert data["type"] == "scan"


def test_check_paths_and_json(tmp_path: Path):
    root = tmp_path / "DevHub"
    stack = root / "02_Docker" / "Stacks" / "x"
    stack.mkdir(parents=True)
    (stack / ".env").write_text("PROJECTS_ROOT=F:/03_Projetos\n", encoding="utf-8")
    report = check_paths(root, out_dir=tmp_path)
    data = json.loads(Path(str(report).replace('.md', '.json')).read_text(encoding='utf-8'))
    assert data["hits_count"] == 1


def test_cleanup_plan_and_json(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    (c_root / "x" / "__pycache__").mkdir(parents=True)
    report = cleanup_plan(c_root, f_root, tmp_path)
    data = json.loads(Path(str(report).replace('.md', '.json')).read_text(encoding='utf-8'))
    assert data["type"] == "cleanup-plan"


def test_apply_cleanup_dry_run(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    target = c_root / "a" / "__pycache__"
    target.mkdir(parents=True)
    report = apply_cleanup(c_root, f_root, tmp_path, risk="baixo", apply=False)
    assert target.exists()
    data = json.loads(Path(str(report).replace('.md', '.json')).read_text(encoding='utf-8'))
    assert data["mode"] == "dry-run"


def test_weekly_report_and_json(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    c_root.mkdir()
    f_root.mkdir()
    report = weekly_report(c_root, f_root, tmp_path)
    data = json.loads(Path(str(report).replace('.md', '.json')).read_text(encoding='utf-8'))
    assert data["type"] == "weekly-report"


def test_build_dashboard(tmp_path: Path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "a.json").write_text('{"type":"weekly-report","timestamp":"x","status":"ok"}', encoding="utf-8")
    html = build_dashboard(logs)
    assert html.exists()
    content = html.read_text(encoding="utf-8")
    assert "DevHub Dashboard" in content
    assert (logs / "dashboard_devhub_summary.csv").exists()
    assert (logs / "dashboard_devhub_runs.csv").exists()


def test_build_dashboard_alerts(tmp_path: Path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "check.json").write_text('{"type":"check-paths","hits_count":2}', encoding="utf-8")
    html = build_dashboard(logs)
    content = html.read_text(encoding="utf-8")
    assert "Alertas" in content
    assert "Paths legados detectados" in content


def test_main_dashboard_command(tmp_path: Path, capsys):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "a.json").write_text('{"type":"scan","timestamp":"x"}', encoding="utf-8")
    rc = main(["dashboard", "--logs-dir", str(logs)])
    assert rc == 0
    assert "Dashboard gerado:" in capsys.readouterr().out
