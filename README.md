# ProjetoBase

Projeto base em Python com estrutura pronta para evoluir e publicar no GitHub.

## Como usar
1. Criar ambiente virtual: `python -m venv .venv`
2. Ativar no PowerShell: `.\.venv\Scripts\Activate.ps1`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Executar app: `$env:PYTHONPATH="src"; python -m projetobase.main run --name Wendsmar`
5. Rodar scan DevHub: `$env:PYTHONPATH="src"; python -m projetobase.main scan`
6. Checar paths legados: `$env:PYTHONPATH="src"; python -m projetobase.main check-paths --root F:/DevHub`
7. Gerar plano de limpeza (sem apagar): `$env:PYTHONPATH="src"; python -m projetobase.main cleanup-plan`
8. Simular limpeza risco baixo: `$env:PYTHONPATH="src"; python -m projetobase.main apply-cleanup --risk baixo`
9. Aplicar limpeza real risco baixo: `$env:PYTHONPATH="src"; python -m projetobase.main apply-cleanup --risk baixo --apply`
10. Relatorio semanal consolidado: `$env:PYTHONPATH="src"; python -m projetobase.main weekly-report`
11. Dashboard HTML local: `$env:PYTHONPATH="src"; python -m projetobase.main dashboard`\n12. Abrir dashboard automaticamente: `$env:PYTHONPATH="src"; python -m projetobase.main dashboard --open`
12. Rodar testes: `pytest -q`

## Saidas
Comandos de relatorio geram `.md` + `.json`.
O comando `dashboard` gera `dashboard_devhub.html`, `dashboard_devhub_summary.csv` e `dashboard_devhub_runs.csv`.


## Alertas no Dashboard
- Paths legados detectados em check-paths`n- Status anormal no weekly-report`n- Crescimento de candidatos no cleanup-plan`n


