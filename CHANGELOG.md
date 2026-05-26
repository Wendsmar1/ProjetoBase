# Changelog

## v0.4.1 - 2026-05-25

### Improved
- Dashboard HTML com redesign visual (cores, gradiente, cards e tabela refinada).
- Badges coloridas para status na tabela de execucoes.
- Bloco de alertas com destaque visual.

## v0.4.0 - 2026-05-25

### Added
- Comando `dashboard` para gerar painel HTML local a partir dos JSONs em `F:/DevHub/05_Logs`.
- Script de automacao `C:/DevHub/04_Scripts/run_projetobase_dashboard.ps1`.
- Tarefa agendada `DevHub Dashboard Refresh` (sexta 09:05).

### Improved
- README atualizado com fluxo completo incluindo dashboard.
- Testes ampliados para cobrir geracao do dashboard.

## v0.3.0 - 2026-05-25

### Added
- Saida `.json` para `scan`, `check-paths` e `weekly-report`.
- Comando `cleanup-plan` com classificacao de risco e plano sem remocao.
- Comando `apply-cleanup` com `dry-run` por padrao, filtro por risco e `--apply` para execucao real.

### Improved
- README atualizado com fluxo operacional completo.
- Cobertura de testes ampliada para todos os comandos principais e artefatos JSON.

## v0.2.0 - 2026-05-25

### Added
- CLI `scan` para varredura de `C:/DevHub` e `F:/DevHub`.
- CLI `check-paths` para detectar paths legados em `compose/.env`.
- CLI `weekly-report` para consolidar manutencao semanal.
- Saida dupla de relatorios: `.md` (humano) e `.json` (automacao).
- Suite de testes cobrindo comandos e geracao de relatorios.

### Operational
- Agendamento semanal no Windows Task Scheduler para gerar `weekly-report`.

### Notes
- Estrutura do projeto pronta para evolucao incremental com CI e versionamento.
