# Relatório de Avaliação — EQ02 (DSC)

| | |
|---|---|
| **Data** | 2026-06-25 |
| **Repositório** | https://github.com/des-sist-corp-ufpb/projeto-eq02 |
| **Aplicação** | https://eq02.dsc.rodrigor.com |
| **Período de atividade** | 2026-06-25 → 2026-06-25 |
| **Total de commits** (sem merges) | 3 |
| **Integrantes** | Lucas Henrique Da Silva Menezes (@DevLucasMenezes) |

---

## 1. Tecnologias

- Python
- FastAPI
- Uvicorn

---

## 2. Análise Funcional

### Endpoints REST (7 mapeados)

| Método | Path | Arquivo |
|--------|------|---------|
| `GET` | `/` | `api_server.py` |
| `GET` | `/api/dashboard_data` | `api_server.py` |
| `GET` | `/dashboard` | `api_server.py` |
| `GET` | `/hibrido` | `api_server.py` |
| `GET` | `/ping` | `api_server.py` |
| `POST` | `/login` | `api_server.py` |
| `POST` | `/register` | `api_server.py` |

### Entidades / Tabelas (4 encontradas)

- `clients (via 01_init_schema.sql)`
- `transactions (via 01_init_schema.sql)`
- `goals (via 01_init_schema.sql)`
- `user_memory (via 01_init_schema.sql)`

---

## 3. Análise Arquitetural

| Aspecto | Status | Observação |
|---------|--------|-----------|
| Arquitetura em camadas | ❌ | controller=✅  service=❌  repository=❌ |
| Testes automatizados | ❌ | 0 arquivo(s) de teste |
| Migrations versionadas | ❌ | não encontradas |
| Logging | ✅ | @Slf4j / LoggerFactory / logging.getLogger detectado |
| Autenticação / Segurança | ❌ | não detectado |
| DTOs / Separação de dados | ❌ | não detectado |
| Tratamento global de exceções | ❌ | não detectado |
| Documentação de API (OpenAPI) | ❌ | não detectado |
| Variáveis de ambiente | ✅ | .env / @Value / os.environ detectado |
| Dockerfile / docker-compose | ✅ | presente |

---

## 4. Contribuição por Usuário

### Resumo

| Usuário | Commits | % commits | Linhas adicionadas | Linhas no código atual | % código atual |
|---------|---------|-----------|-------------------|----------------------|----------------|
| Lucas Henrique Da Silva Menezes (@DevLucasMenezes) | 3 | 100% | 2.654 | 2.092 | 100% |

### Contribuição por Camada

| Camada | Total linhas | Lucas Henrique Da Silva Menezes (@DevLucasMenezes) |
|--------|-------------|---------|
| Frontend | 933 | 100% |

---

*Relatório gerado automaticamente em 2026-06-25.*
*Os dados de contribuição são baseados em `git log --numstat` (linhas adicionadas) e `git blame` (linhas no código atual), excluindo commits de merge.*