# Changelog

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
