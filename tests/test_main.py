from pathlib import Path

from projetobase.main import check_paths, main, run, scan_devhub, weekly_report


def test_run_default():
    out = run()
    assert "Ola, mundo!" in out
    assert "ProjetoBase v0.1.0" in out


def test_run_custom_name():
    assert run("Wendsmar") == "Ola, Wendsmar! ProjetoBase v0.1.0"


def test_scan_generates_report(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    (c_root / "Apps").mkdir(parents=True)
    (f_root / "Apps").mkdir(parents=True)
    (f_root / "05_Logs").mkdir(parents=True)
    (c_root / "Apps" / "a.txt").write_text("ok", encoding="utf-8")

    report = scan_devhub(c_root, f_root)
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "DevHub Scan Report" in content
    assert "C exists: True" in content


def test_check_paths_finds_legacy(tmp_path: Path):
    root = tmp_path / "DevHub"
    stack = root / "02_Docker" / "Stacks" / "x"
    stack.mkdir(parents=True)
    (stack / ".env").write_text("PROJECTS_ROOT=F:/03_Projetos\n", encoding="utf-8")

    report = check_paths(root, out_dir=tmp_path)
    content = report.read_text(encoding="utf-8")
    assert "Hits: 1" in content
    assert "F:/DevHub/Projetos/Ativos/03_Projetos" in content


def test_weekly_report(tmp_path: Path):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    (c_root / "Apps").mkdir(parents=True)
    stack = f_root / "02_Docker" / "Stacks" / "x"
    stack.mkdir(parents=True)
    (stack / ".env").write_text("PROJECTS_ROOT=F:/03_Projetos\n", encoding="utf-8")

    report = weekly_report(c_root, f_root, tmp_path)
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "DevHub Weekly Report" in content
    assert "Scan report:" in content
    assert "Paths report:" in content


def test_main_scan_command(tmp_path: Path, capsys):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    c_root.mkdir()
    f_root.mkdir()

    rc = main(["scan", "--c-root", str(c_root), "--f-root", str(f_root), "--out-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Relatorio gerado:" in out


def test_main_check_paths_command(tmp_path: Path, capsys):
    root = tmp_path / "F_DevHub"
    root.mkdir()
    rc = main(["check-paths", "--root", str(root), "--out-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Relatorio gerado:" in out


def test_main_weekly_command(tmp_path: Path, capsys):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    c_root.mkdir()
    f_root.mkdir()
    rc = main(["weekly-report", "--c-root", str(c_root), "--f-root", str(f_root), "--out-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Relatorio gerado:" in out
