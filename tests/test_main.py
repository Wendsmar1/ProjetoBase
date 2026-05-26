from projetobase.main import run


def test_run_default():
    out = run()
    assert "Ola, mundo!" in out
    assert "ProjetoBase v0.1.0" in out


def test_run_custom_name():
    assert run("Wendsmar") == "Ola, Wendsmar! ProjetoBase v0.1.0"
