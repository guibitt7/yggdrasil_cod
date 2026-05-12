📁 docker-compose.yml
yaml
Copy
services:
  loki:
    image: grafana/loki:2.9.8
    container_name: loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/loki-config.yml
    volumes:
      - ./loki/loki-config.yml:/etc/loki/loki-config.yml:ro
      - loki_data:/loki
    networks:
      - ygg-net

  prometheus:
    image: prom/prometheus:v2.53.0
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --web.enable-lifecycle
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - ygg-net

  alertmanager:
    image: prom/alertmanager:v0.27.0
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - --config.file=/etc/alertmanager/alertmanager.yml
      - --storage.path=/alertmanager
    networks:
      - ygg-net

  grafana:
    image: grafana/grafana:11.1.0
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin123
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_FEATURE_TOGGLES_ENABLE: "lokiLive"
      GF_SMTP_ENABLED: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - loki
      - prometheus
    networks:
      - ygg-net

  node-exporter:
    image: prom/node-exporter:v1.8.1
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - --path.procfs=/host/proc
      - --path.sysfs=/host/sys
      - --path.rootfs=/rootfs
      - --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)
    networks:
      - ygg-net

networks:
  ygg-net:
    driver: bridge

volumes:
  loki_data:
  prometheus_data:
  grafana_data:
  alertmanager_data:
📁 loki/loki-config.yml
yaml
Copy
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: warn

common:
  path_prefix: /loki
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 744h          # 31 dias
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  max_query_series: 5000
  max_entries_limit_per_query: 50000
  allow_structured_metadata: true

compactor:
  working_directory: /loki/compactor
  retention_enabled: true
  delete_request_store: filesystem

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 150

querier:
  max_concurrent: 4

frontend:
  max_outstanding_per_tenant: 2048

analytics:
  reporting_enabled: false
📁 prometheus/prometheus.yml
yaml
Copy
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: yggdrasil
    env: production

rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:

  - job_name: prometheus
    static_configs:
      - targets:
          - localhost:9090

  - job_name: node-exporter-linux
    static_configs:
      - targets:
          - node-exporter:9100
        labels:
          machine: linux-server
          env: production

  # Adicione aqui os node-exporters das máquinas Windows
  # - job_name: node-exporter-windows
  #   static_configs:
  #     - targets:
  #         - 10.0.0.101:9182
  #         - 10.0.0.102:9182
  #       labels:
  #         env: production
  #         os: windows

  # Adicione aqui as APIs Python quando estiverem no k3s
  # - job_name: apis-python
  #   kubernetes_sd_configs:
  #     - role: pod
  #   relabel_configs:
  #     - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  #       action: keep
  #       regex: "true"
📁 alertmanager/alertmanager.yml
yaml
Copy
global:
  resolve_timeout: 5m

route:
  group_by:
    - alertname
    - automacao
    - machine_ip
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: default

  routes:
    - match:
        severity: critical
      receiver: critical-alerts
      repeat_interval: 1h

    - match:
        severity: warning
      receiver: default
      repeat_interval: 4h

receivers:
  - name: default
    # Email — descomente e configure quando quiser
    # email_configs:
    #   - to: time@empresa.com.br
    #     from: alertas@empresa.com.br
    #     smarthost: smtp.empresa.com.br:587
    #     auth_username: alertas@empresa.com.br
    #     auth_password: senha
    #     send_resolved: true

    # Teams — descomente e configure quando quiser
    # webhook_configs:
    #   - url: https://empresa.webhook.office.com/webhookb2/SEU_WEBHOOK
    #     send_resolved: true

  - name: critical-alerts
    # webhook_configs:
    #   - url: https://empresa.webhook.office.com/webhookb2/SEU_WEBHOOK_CRITICO
    #     send_resolved: true

inhibit_rules:
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal:
      - alertname
      - automacao
📁 grafana/provisioning/datasources/datasources.yml
yaml
Copy
apiVersion: 1

datasources:
  - name: Loki
    uid: loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: true
    editable: true
    jsonData:
      maxLines: 5000
      timeout: 60

  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    editable: true
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
      httpMethod: POST
📁 grafana/provisioning/dashboards/dashboards.yml
yaml
Copy
apiVersion: 1

providers:
  - name: Yggdrasil
    orgId: 1
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
📁 Estrutura final de pastas
text
Copy
~/ygg-observability/
├── docker-compose.yml
├── loki/
│   └── loki-config.yml
├── prometheus/
│   └── prometheus.yml
├── alertmanager/
│   └── alertmanager.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasources.yml
        └── dashboards/
            └── dashboards.yml
▶️ Criar pastas e subir tudo
bash
Copy
mkdir -p ~/ygg-observability/{loki,prometheus,alertmanager,grafana/provisioning/{datasources,dashboards}}
cd ~/ygg-observability

# Cole cada arquivo no caminho correto, depois:
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
✅ Testar se está tudo no ar
bash
Copy
curl http://localhost:3100/ready      # Loki → "ready"
curl http://localhost:9090/-/ready    # Prometheus → "Prometheus is Ready"
curl http://localhost:9093/-/ready    # Alertmanager → "OK"
curl http://localhost:3000/api/health # Grafana → {"database":"ok"}
🔗 Endpoint para o Alloy nas máquinas Windows
hcl
Copy
loki.write "yggdrasil" {
  endpoint {
    url = "http://IP_DA_VM:3100/loki/api/v1/push"
  }
}

{
  "dashboard": {
    "title": "Yggdrasil — Observabilidade de Automações",
    "uid": "yggdrasil-rpa-v1",
    "tags": [
      "yggdrasil",
      "rpa",
      "automacoes"
    ],
    "timezone": "browser",
    "schemaVersion": 38,
    "version": 1,
    "refresh": "30s",
    "time": {
      "from": "now-24h",
      "to": "now"
    },
    "templating": {
      "list": [
        {
          "name": "machine",
          "label": "Máquina",
          "type": "query",
          "datasource": {
            "type": "loki",
            "uid": "loki"
          },
          "query": "label_values(machine_ip)",
          "multi": true,
          "includeAll": true,
          "current": {
            "text": "All",
            "value": "$__all"
          }
        },
        {
          "name": "automacao",
          "label": "Automação",
          "type": "query",
          "datasource": {
            "type": "loki",
            "uid": "loki"
          },
          "query": "label_values(automacao)",
          "multi": true,
          "includeAll": true,
          "current": {
            "text": "All",
            "value": "$__all"
          }
        },
        {
          "name": "robot",
          "label": "Robô",
          "type": "query",
          "datasource": {
            "type": "loki",
            "uid": "loki"
          },
          "query": "label_values(robot)",
          "multi": true,
          "includeAll": true,
          "current": {
            "text": "All",
            "value": "$__all"
          }
        },
        {
          "name": "level",
          "label": "Level",
          "type": "custom",
          "options": [
            {
              "text": "All",
              "value": "$__all"
            },
            {
              "text": "DEBUG",
              "value": "DEBUG"
            },
            {
              "text": "INFO",
              "value": "INFO"
            },
            {
              "text": "WARNING",
              "value": "WARNING"
            },
            {
              "text": "ERROR",
              "value": "ERROR"
            },
            {
              "text": "CRITICAL",
              "value": "CRITICAL"
            }
          ],
          "multi": true,
          "includeAll": true,
          "current": {
            "text": "All",
            "value": "$__all"
          }
        },
        {
          "name": "status",
          "label": "Status",
          "type": "custom",
          "options": [
            {
              "text": "All",
              "value": "$__all"
            },
            {
              "text": "STARTED",
              "value": "STARTED"
            },
            {
              "text": "RUNNING",
              "value": "RUNNING"
            },
            {
              "text": "SUCCESS",
              "value": "SUCCESS"
            },
            {
              "text": "FAILED",
              "value": "FAILED"
            }
          ],
          "multi": true,
          "includeAll": true,
          "current": {
            "text": "All",
            "value": "$__all"
          }
        }
      ]
    },
    "panels": [
      {
        "type": "row",
        "title": "📊 Visão Geral",
        "gridPos": {
          "x": 0,
          "y": 0,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 1
      },
      {
        "id": 2,
        "title": "Total de Execuções",
        "type": "stat",
        "gridPos": {
          "x": 0,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "count_over_time({machine_ip=~\"$machine\", automacao=~\"$automacao\"} |= \"STARTED\" [$__range])",
            "legendFormat": "Execuções"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "sum"
            ]
          },
          "colorMode": "background"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "blue"
            }
          }
        }
      },
      {
        "id": 3,
        "title": "✅ Sucesso",
        "type": "stat",
        "gridPos": {
          "x": 4,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "count_over_time({machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | status=\"SUCCESS\" [$__range])",
            "legendFormat": "Sucesso"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "sum"
            ]
          },
          "colorMode": "background"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "green"
            }
          }
        }
      },
      {
        "id": 4,
        "title": "❌ Falhas",
        "type": "stat",
        "gridPos": {
          "x": 8,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "count_over_time({machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | status=\"FAILED\" [$__range])",
            "legendFormat": "Falhas"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "sum"
            ]
          },
          "colorMode": "background"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "red"
            }
          }
        }
      },
      {
        "id": 5,
        "title": "🔴 Erros Críticos",
        "type": "stat",
        "gridPos": {
          "x": 12,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "count_over_time({machine_ip=~\"$machine\"} | json | level=~\"ERROR|CRITICAL\" [$__range])",
            "legendFormat": "Erros"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "sum"
            ]
          },
          "colorMode": "background"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "green",
                  "value": 0
                },
                {
                  "color": "yellow",
                  "value": 1
                },
                {
                  "color": "red",
                  "value": 5
                }
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "⚙️ Em Execução Agora",
        "type": "stat",
        "gridPos": {
          "x": 16,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "count_over_time({machine_ip=~\"$machine\"} | json | status=\"RUNNING\" [5m])",
            "legendFormat": "Running"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "sum"
            ]
          },
          "colorMode": "background"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "orange"
            }
          }
        }
      },
      {
        "id": 7,
        "title": "🎯 Taxa de Sucesso",
        "type": "stat",
        "gridPos": {
          "x": 20,
          "y": 1,
          "w": 4,
          "h": 4
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum(count_over_time({machine_ip=~\"$machine\"} | json | status=\"SUCCESS\" [$__range])) / sum(count_over_time({machine_ip=~\"$machine\"} | json | status=~\"SUCCESS|FAILED\" [$__range])) * 100",
            "legendFormat": "Taxa %"
          }
        ],
        "options": {
          "reduceOptions": {
            "calcs": [
              "lastNotNull"
            ]
          },
          "colorMode": "background",
          "unit": "percent"
        },
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": 0
                },
                {
                  "color": "yellow",
                  "value": 80
                },
                {
                  "color": "green",
                  "value": 95
                }
              ]
            }
          }
        }
      },
      {
        "type": "row",
        "title": "📈 Timeline e Distribuição",
        "gridPos": {
          "x": 0,
          "y": 5,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 10
      },
      {
        "id": 11,
        "title": "Execuções por Status ao Longo do Tempo",
        "type": "timeseries",
        "gridPos": {
          "x": 0,
          "y": 6,
          "w": 16,
          "h": 8
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum by (status) (count_over_time({machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | status=~\"$status\" [$__interval]))",
            "legendFormat": "{{status}}"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "SUCCESS"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "green",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "FAILED"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "red",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "RUNNING"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "orange",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "STARTED"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "blue",
                    "mode": "fixed"
                  }
                }
              ]
            }
          ]
        }
      },
      {
        "id": 12,
        "title": "Distribuição por Level",
        "type": "piechart",
        "gridPos": {
          "x": 16,
          "y": 6,
          "w": 8,
          "h": 8
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum by (level) (count_over_time({machine_ip=~\"$machine\"} | json | level=~\"$level\" [$__range]))",
            "legendFormat": "{{level}}"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "DEBUG"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "gray",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "INFO"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "blue",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "WARNING"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "yellow",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "ERROR"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "orange",
                    "mode": "fixed"
                  }
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "CRITICAL"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "fixedColor": "red",
                    "mode": "fixed"
                  }
                }
              ]
            }
          ]
        }
      },
      {
        "type": "row",
        "title": "🤖 Por Automação e Máquina",
        "gridPos": {
          "x": 0,
          "y": 14,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 20
      },
      {
        "id": 21,
        "title": "Falhas por Automação",
        "type": "barchart",
        "gridPos": {
          "x": 0,
          "y": 15,
          "w": 12,
          "h": 8
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum by (automacao) (count_over_time({machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | status=\"FAILED\" [$__range]))",
            "legendFormat": "{{automacao}}"
          }
        ],
        "options": {
          "orientation": "horizontal"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "red"
            }
          }
        }
      },
      {
        "id": 22,
        "title": "Execuções por Máquina",
        "type": "barchart",
        "gridPos": {
          "x": 12,
          "y": 15,
          "w": 12,
          "h": 8
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum by (machine_ip) (count_over_time({machine_ip=~\"$machine\"} | json | status=~\"SUCCESS|FAILED\" [$__range]))",
            "legendFormat": "{{machine_ip}}"
          }
        ],
        "options": {
          "orientation": "horizontal"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            }
          }
        }
      },
      {
        "type": "row",
        "title": "⏱️ SLA e Duração",
        "gridPos": {
          "x": 0,
          "y": 23,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 30
      },
      {
        "id": 31,
        "title": "Duração das Execuções por Automação (últimas 24h)",
        "type": "timeseries",
        "gridPos": {
          "x": 0,
          "y": 24,
          "w": 24,
          "h": 8
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "{machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | status=~\"SUCCESS|FAILED\" | line_format \"{{.automacao}} | {{.exec_id}} | {{.status}} | {{.start_time}}\"",
            "legendFormat": "{{automacao}}"
          }
        ],
        "description": "Filtre por exec_id para ver a duração de uma execução específica"
      },
      {
        "type": "row",
        "title": "📋 Logs em Tempo Real",
        "gridPos": {
          "x": 0,
          "y": 32,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 40
      },
      {
        "id": 41,
        "title": "🔴 Logs de Erro e Crítico",
        "type": "logs",
        "gridPos": {
          "x": 0,
          "y": 33,
          "w": 24,
          "h": 10
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "{machine_ip=~\"$machine\", automacao=~\"$automacao\", robot=~\"$robot\"} | json | level=~\"ERROR|CRITICAL\"",
            "legendFormat": ""
          }
        ],
        "options": {
          "showTime": true,
          "showLabels": true,
          "showCommonLabels": false,
          "wrapLogMessage": true,
          "sortOrder": "Descending",
          "dedupStrategy": "none"
        }
      },
      {
        "id": 42,
        "title": "📜 Todos os Logs (com filtros)",
        "type": "logs",
        "gridPos": {
          "x": 0,
          "y": 43,
          "w": 24,
          "h": 12
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "{machine_ip=~\"$machine\", automacao=~\"$automacao\", robot=~\"$robot\"} | json | level=~\"$level\" | status=~\"$status\"",
            "legendFormat": ""
          }
        ],
        "options": {
          "showTime": true,
          "showLabels": true,
          "showCommonLabels": false,
          "wrapLogMessage": true,
          "sortOrder": "Descending",
          "dedupStrategy": "none"
        }
      },
      {
        "type": "row",
        "title": "🔍 Rastreabilidade (exec_id / trace_id / fluid_id)",
        "gridPos": {
          "x": 0,
          "y": 55,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 50
      },
      {
        "id": 51,
        "title": "Jornada Completa por exec_id",
        "type": "table",
        "gridPos": {
          "x": 0,
          "y": 56,
          "w": 24,
          "h": 10
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "{machine_ip=~\"$machine\", automacao=~\"$automacao\"} | json | line_format \"{{.timestamp}} | {{.level}} | {{.automacao}} | {{.robot}} | {{.machine_ip}} | {{.exec_id}} | {{.trace_id}} | {{.fluid_id}} | {{.status}} | {{.step}} | {{.message}} | {{.origin}}\"",
            "legendFormat": ""
          }
        ],
        "transformations": [
          {
            "id": "extractFields",
            "options": {
              "source": "labels"
            }
          },
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "timestamp": "Timestamp",
                "level": "Level",
                "automacao": "Automação",
                "robot": "Robô",
                "machine_ip": "Máquina",
                "exec_id": "Exec ID",
                "trace_id": "Trace ID",
                "fluid_id": "Fluid ID",
                "status": "Status",
                "step": "Step",
                "message": "Mensagem",
                "origin": "Origem"
              }
            }
          }
        ],
        "options": {
          "sortBy": [
            {
              "displayName": "Timestamp",
              "desc": true
            }
          ]
        },
        "fieldConfig": {
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "Level"
              },
              "properties": [
                {
                  "id": "custom.displayMode",
                  "value": "color-background"
                },
                {
                  "id": "mappings",
                  "value": [
                    {
                      "type": "value",
                      "options": {
                        "DEBUG": {
                          "color": "gray",
                          "text": "DEBUG"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "INFO": {
                          "color": "blue",
                          "text": "INFO"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "WARNING": {
                          "color": "yellow",
                          "text": "WARNING"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "ERROR": {
                          "color": "orange",
                          "text": "ERROR"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "CRITICAL": {
                          "color": "red",
                          "text": "CRITICAL"
                        }
                      }
                    }
                  ]
                }
              ]
            },
            {
              "matcher": {
                "id": "byName",
                "options": "Status"
              },
              "properties": [
                {
                  "id": "custom.displayMode",
                  "value": "color-background"
                },
                {
                  "id": "mappings",
                  "value": [
                    {
                      "type": "value",
                      "options": {
                        "STARTED": {
                          "color": "blue",
                          "text": "STARTED"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "RUNNING": {
                          "color": "orange",
                          "text": "RUNNING"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "SUCCESS": {
                          "color": "green",
                          "text": "SUCCESS"
                        }
                      }
                    },
                    {
                      "type": "value",
                      "options": {
                        "FAILED": {
                          "color": "red",
                          "text": "FAILED"
                        }
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      },
      {
        "type": "row",
        "title": "🚨 Alertas e Anomalias",
        "gridPos": {
          "x": 0,
          "y": 66,
          "w": 24,
          "h": 1
        },
        "collapsed": false,
        "id": 60
      },
      {
        "id": 61,
        "title": "Erros Críticos ao Longo do Tempo",
        "type": "timeseries",
        "gridPos": {
          "x": 0,
          "y": 67,
          "w": 12,
          "h": 7
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "sum by (automacao) (count_over_time({machine_ip=~\"$machine\"} | json | level=\"CRITICAL\" [$__interval]))",
            "legendFormat": "CRITICAL — {{automacao}}"
          },
          {
            "expr": "sum by (automacao) (count_over_time({machine_ip=~\"$machine\"} | json | level=\"ERROR\" [$__interval]))",
            "legendFormat": "ERROR — {{automacao}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            }
          }
        }
      },
      {
        "id": 62,
        "title": "Top Automações com Falha",
        "type": "barchart",
        "gridPos": {
          "x": 12,
          "y": 67,
          "w": 12,
          "h": 7
        },
        "datasource": {
          "type": "loki",
          "uid": "loki"
        },
        "targets": [
          {
            "expr": "topk(5, sum by (automacao) (count_over_time({machine_ip=~\"$machine\"} | json | status=\"FAILED\" [$__range])))",
            "legendFormat": "{{automacao}}"
          }
        ],
        "options": {
          "orientation": "horizontal"
        },
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "fixed",
              "fixedColor": "red"
            }
          }
        }
      }
    ]
  },
  "overwrite": true,
  "folderId": 0
}
