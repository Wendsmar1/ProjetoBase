# ProjetoBase

Projeto base em Python com estrutura pronta para evoluir e publicar no GitHub.

## Estrutura
- `src/projetobase/`: codigo da aplicacao
- `tests/`: testes automatizados
- `requirements.txt`: dependencias
- `pyproject.toml`: metadados e ferramentas

## Como usar
1. Criar ambiente virtual: `python -m venv .venv`
2. Ativar no PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Executar app: `$env:PYTHONPATH="src"; python -m projetobase.main run --name Wendsmar`
5. Rodar scan DevHub: `$env:PYTHONPATH="src"; python -m projetobase.main scan`
6. Checar paths legados: `$env:PYTHONPATH="src"; python -m projetobase.main check-paths --root F:/DevHub`
7. Gerar plano de limpeza (sem apagar): `$env:PYTHONPATH="src"; python -m projetobase.main cleanup-plan`
8. Relatorio semanal consolidado: `$env:PYTHONPATH="src"; python -m projetobase.main weekly-report`
9. Rodar testes: `pytest -q`

## Saidas
Cada comando de relatorio gera dois arquivos:
- `.md` para leitura humana
- `.json` para automacao
