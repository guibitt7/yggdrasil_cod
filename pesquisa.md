# 📋 Pesquisa de Padronização de Logs (Automação & API)

> Preencha este formulário após revisar os modelos de log apresentados (Automação e API).
> Sua opinião é essencial para garantir que o padrão funcione bem para toda a equipe.

---

## Seção 1: Clareza e Estrutura

**1.** Em uma escala de 1 a 5, quão fácil é entender o que aconteceu em uma execução apenas olhando para o JSON de exemplo?
- [ ] 1 — Muito confuso
- [ ] 2 — Confuso
- [ ] 3 — Neutro
- [ ] 4 — Claro
- [ ] 5 — Muito claro

---

**2.** Você sentiu falta de algum campo essencial para o seu dia a dia de troubleshooting?

> _Resposta:_ _______________________________________________

---

**3.** Os nomes dos campos (ex: `exec_id`, `trace_id`, `fluid_id`) estão intuitivos ou algum deles parece ambíguo?

> _Resposta:_ _______________________________________________

---

## Seção 2: Operação e Grafana (Loki)

**4.** Considerando que vamos criar Dashboards no Grafana, você prefere que o campo de mensagem principal se chame `msg` (curto) ou `message` (padrão de mercado)?
- [ ] `msg`
- [ ] `message`
- [ ] Indiferente

---

**5.** Para as APIs, os campos de banco de dados (`db_queries_count`, `db_failed_count`) são úteis para você ou poluem o log desnecessariamente?
- [ ] Útil — uso isso no dia a dia
- [ ] Neutro — não me atrapalha
- [ ] Desnecessário — prefiro remover

---

**6.** Você acredita que o campo `status` (SUCCESS/FAILED) é redundante em relação ao `level` (INFO/ERROR) ou ajuda na filtragem rápida?

> _Resposta:_ _______________________________________________

---

## Seção 3: Contexto de Negócio

**7.** Na automação, deveríamos incluir um campo fixo para o "ID de Negócio" (ex: CPF, Número do Pedido, NF) para facilitar a busca por chamados de clientes?
- [ ] Sim, sempre
- [ ] Não, é desnecessário
- [ ] Depende da automação

---

**8.** Existe algum dado sensível (LGPD) que você notou nos exemplos e que deveríamos mascarar antes de enviar para o Loki?

> _Resposta:_ _______________________________________________

---

## Seção 4: Sugestões Gerais

**9.** O que você removeria desses modelos para torná-los mais leves?

> _Resposta:_ _______________________________________________

---

**10.** O que você adicionaria que salvaria sua vida durante um plantão ou incidente crítico?

> _Resposta:_ _______________________________________________

---

## Seção 5: Perguntas Extras

**11.** O modelo de log da **Automação** e o da **API** estão suficientemente diferentes entre si para atender às necessidades específicas de cada contexto, ou você acha que deveriam ser ainda mais distintos?
- [ ] Estão bem diferenciados
- [ ] Poderiam ser mais distintos
- [ ] Deveriam ser idênticos para facilitar a padronização

---

**12.** O campo `stacktrace` no log de erro da API é útil para você como desenvolvedor/analista, ou preferiria que ele ficasse apenas em uma ferramenta separada (ex: Sentry, Datadog)?
- [ ] Prefiro ter no próprio log (Loki/Grafana)
- [ ] Prefiro em uma ferramenta separada
- [ ] Ambos, dependendo da gravidade

---

**13.** Em uma situação de incidente crítico em produção, qual seria o **primeiro campo** que você buscaria no Grafana para começar a investigação?
- [ ] `trace_id`
- [ ] `level` / `status`
- [ ] `exec_id` / `robot`
- [ ] `exception` / `stacktrace`
- [ ] Outro: _______________________________________________

---

**14.** Você conseguiria, sem ajuda, escrever uma query básica no Grafana (LogQL) usando esses campos para filtrar erros de uma automação específica? Isso indica se o padrão está claro o suficiente.
- [ ] Sim, com certeza
- [ ] Sim, mas precisaria de um exemplo inicial
- [ ] Não, precisaria de treinamento
- [ ] Nunca usei Grafana/Loki

---

**15.** De 0 a 10, qual a sua nota geral para os modelos de log apresentados? Considere clareza, completude e utilidade prática.

> _Nota (0–10):_ _______

> _Justificativa (opcional):_ _______________________________________________

---

*Obrigado pelo seu feedback! Suas respostas vão ajudar a construir um padrão de observabilidade sólido para toda a equipe.* 🚀
