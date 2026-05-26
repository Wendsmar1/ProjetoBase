from pathlib import Path

from projetobase.main import main, run, scan_devhub


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


def test_main_scan_command(tmp_path: Path, capsys):
    c_root = tmp_path / "C_DevHub"
    f_root = tmp_path / "F_DevHub"
    c_root.mkdir()
    f_root.mkdir()

    rc = main(["scan", "--c-root", str(c_root), "--f-root", str(f_root), "--out-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Relatorio gerado:" in out
