# 🎓 MathMentor AI

> Gia sư toán AI cá nhân hóa cho học sinh THPT Việt Nam, xây dựng trên nền tảng RAG, bộ nhớ người học và chiến lược sư phạm thích ứng.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

## Giới thiệu

**MathMentor AI** không chỉ trả lời câu hỏi toán. Hệ thống theo dõi mức độ thành thạo của từng học sinh, phát hiện các hiểu sai thường gặp, rồi chọn cách giảng phù hợp (gợi mở, từng bước, ví dụ mẫu...) trước khi sinh câu trả lời bằng GPT-4o. Câu trả lời được bám vào kho kiến thức (wiki) toán học bằng tiếng Việt thông qua RAG, kèm nguồn tham chiếu.

### Tính năng chính

- **Hỏi đáp toán có nguồn trích dẫn:** truy xuất kiến thức từ wiki Markdown, hỗ trợ công thức LaTeX.
- **Hybrid retrieval:** kết hợp tìm kiếm ngữ nghĩa (pgvector) và từ khóa (PostgreSQL full-text), gộp bằng RRF, sau đó rerank bằng cross-encoder.
- **Chiến lược sư phạm thích ứng:** 6 chiến lược (Socratic, từng bước, giải thích trực tiếp, gợi ý trước, ví dụ mẫu, siêu nhận thức) và mục tiêu theo thang Bloom, chọn theo trạng thái người học.
- **Bộ nhớ người học:** cập nhật mức thành thạo theo EMA, phát hiện hiểu sai, ước lượng tải nhận thức và mức phụ thuộc vào gợi ý.
- **Streaming:** trả lời theo thời gian thực qua Server-Sent Events.
- **Xử lý nền:** cập nhật bộ nhớ, ingest wiki và đánh giá định kỳ chạy bằng Celery.
- **Quan sát hệ thống:** log có cấu trúc (structlog) và metrics Prometheus.

## Kiến trúc

```
Học sinh ──► FastAPI (JWT) ──► MathTutorOrchestrator
                                   │
        ┌──────────────────────────┼───────────────────────────┐
        ▼                          ▼                           ▼
 Intent Detector            Trạng thái người học         Query Rewriter
 (luật, dễ kiểm toán)       (User State Interpreter)           │
        │                          │                           ▼
        │                          ▼                  Hybrid Retriever
        │                 Pedagogy Selector            ├─ pgvector (bge-m3)
        │                 (chiến lược + Bloom)         └─ Full-text (ts_rank_cd)
        │                          │                           │ RRF
        │                          │                           ▼
        │                          │                  Cross-Encoder Reranker
        │                          │                           │
        │                          │                           ▼
        │                          │                  LaTeX-safe Compressor
        │                          ▼                           │
        └──────────────► Prompt Builder ◄──────────────────────┘
                                   │
                                   ▼
                       GPT-4o ──► Response Postprocessor
                                   │
                                   ▼
                  Trả lời + nguồn + gợi ý câu hỏi tiếp theo
                                   │
                                   ▼ (bất đồng bộ)
                     Celery: cập nhật EMA / bộ nhớ / log
```

## Công nghệ sử dụng

| Nhóm | Công nghệ |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| Cơ sở dữ liệu | PostgreSQL 16 + pgvector, SQLAlchemy 2.0 (async, `asyncpg`), Alembic |
| LLM | OpenAI GPT-4o (temperature 0.3) |
| Embedding | `BAAI/bge-m3` (1024 chiều) qua `sentence-transformers` |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Hàng đợi / cache | Celery 5, Redis 7 (broker, result backend, Celery Beat) |
| Bảo mật | JWT (`python-jose`), `bcrypt`, admin API key |
| Quan sát | structlog, prometheus-client |
| Chất lượng code | pytest, pytest-asyncio, ruff, black, pip-audit |
| Triển khai | Docker, Docker Compose |

Lý do cho từng lựa chọn kỹ thuật được ghi trong [`docs/adr/`](docs/adr/):

| ADR | Quyết định |
|---|---|
| [0001](docs/adr/0001-pgvector-over-dedicated-vector-db.md) | Dùng pgvector thay vì vector DB riêng |
| [0002](docs/adr/0002-cross-encoder-reranking.md) | Rerank bằng cross-encoder sau hybrid retrieval |
| [0003](docs/adr/0003-celery-for-memory-updates.md) | Dùng Celery thay vì `BackgroundTasks` cho cập nhật bộ nhớ |
| [0004](docs/adr/0004-gpt-4o-temperature-for-math.md) | GPT-4o với temperature 0.3 cho sinh lời giải toán |
| [0005](docs/adr/0005-bge-m3-embeddings.md) | Embedding tự host bằng bge-m3 |

## Cấu trúc thư mục

```
mathmentor-ai/
├── app/
│   ├── api/v1/          # Router, endpoint và schema (auth, chat, sessions, users, admin)
│   ├── core/            # Orchestrator, intent, query rewriter, pedagogy, prompt, postprocessor
│   ├── rag/             # Retriever, RRF, reranker, context compressor
│   ├── wiki/            # Validate schema, chunker, embedding, ingestion pipeline
│   ├── memory/          # EMA updater, phát hiện hiểu sai, diễn giải trạng thái người học
│   ├── llm/             # OpenAI client
│   ├── db/              # Models và session
│   ├── tasks/           # Celery app và các task nền
│   ├── utils/           # Logging, metrics, tiện ích LaTeX
│   ├── config.py        # Cấu hình từ biến môi trường
│   └── main.py          # App factory
├── alembic/             # Migration
├── docker/              # Dockerfile và docker-compose
├── docs/                # ADR và mô tả cấu trúc dự án
├── scripts/             # seed_wiki.py, create_indexes.sql
├── tests/               # unit và integration
└── wiki_content/        # Kho kiến thức toán (Markdown)
```

## Bắt đầu nhanh

### Yêu cầu

- Docker và Docker Compose, **hoặc** Python 3.12+, PostgreSQL 16 có pgvector và Redis 7
- OpenAI API key

### 1. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc `mathmentor-ai/`:

```env
DATABASE_URL=postgresql+asyncpg://mathmentor:mathmentor@localhost:5432/mathmentor
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

SECRET_KEY=doi-thanh-chuoi-bi-mat-dai-ngau-nhien
ADMIN_API_KEY=doi-thanh-admin-key-cua-ban
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

CORS_ALLOW_ORIGINS=http://localhost:3000
```

> ⚠️ **Không commit file `.env`** và không chia sẻ API key. Hãy đổi `SECRET_KEY` và `ADMIN_API_KEY` khỏi giá trị mặc định khi triển khai thật.

Các tham số khác (kích thước pool DB, `RAG_TOP_K_*`, `MAX_CONTEXT_TOKENS`, `EMA_ALPHA`, ...) có giá trị mặc định trong [`app/config.py`](app/config.py).

### 2. Chạy bằng Docker (khuyến nghị)

```bash
docker compose up --build
```

Lệnh này khởi động 5 service: `api` (cổng 8000, tự chạy `alembic upgrade head`), `worker`, `beat`, `db` (pgvector) và `redis`.

Nạp kiến thức mẫu vào hệ thống:

```bash
docker compose exec api python scripts/seed_wiki.py
```

> Lần đầu chạy, `sentence-transformers` sẽ tải model `BAAI/bge-m3`, nên mất một lúc và cần dung lượng ổ đĩa đáng kể.

### 3. Chạy cục bộ không dùng Docker

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

alembic upgrade head
python scripts/seed_wiki.py
uvicorn app.main:create_app --factory --reload
```

Chạy worker và scheduler ở các terminal khác:

```bash
celery -A app.tasks.celery_app worker -Q memory_updates,ingestion,evaluation,maintenance -c 2 --loglevel=INFO
celery -A app.tasks.celery_app beat --loglevel=INFO
```

### 4. Kiểm tra

- Swagger UI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- Metrics Prometheus: <http://localhost:8000/metrics>

## API

Tất cả endpoint nằm dưới tiền tố `/api/v1`. Các endpoint trừ đăng ký và đăng nhập đều cần header `Authorization: Bearer <token>`.

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/auth/register` | Đăng ký tài khoản |
| `POST` | `/auth/login` | Đăng nhập, nhận JWT |
| `GET` | `/users/{user_id}/profile` | Xem hồ sơ học tập |
| `PATCH` | `/users/{user_id}/profile` | Cập nhật hồ sơ |
| `POST` | `/chat` | Gửi câu hỏi, nhận câu trả lời đầy đủ |
| `GET` | `/chat/stream` | Nhận câu trả lời dạng stream (SSE) |
| `POST` | `/chat/feedback` | Gửi đánh giá cho một câu trả lời |
| `GET` | `/sessions` | Danh sách phiên chat |
| `GET` | `/sessions/{session_id}` | Chi tiết một phiên chat |
| `POST` | `/admin/wiki/ingest` | Ingest wiki (cần header `X-Admin-Api-Key`) |

Ví dụ gọi chat:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Giải phương trình 2x^2 - 5x + 3 = 0"}'
```

Phản hồi gồm `session_id`, `message_id`, `response`, `teaching_strategy_used`, `topics_covered`, `sources` (bài viết và mục được trích dẫn) và `follow_up_suggestions`.

## Thêm nội dung vào wiki

Kiến thức được viết bằng Markdown trong `wiki_content/`, có frontmatter mô tả metadata để hỗ trợ lọc khi truy xuất:

```markdown
---
title: "Phương Trình Bậc Hai"
subject: "Toán"
grade_range: [10, 12]
difficulty: 0.4
tags: ["phương trình", "đại số", "bậc hai"]
concepts: ["discriminant", "Vieta's formulas"]
skills: ["solve_quadratic"]
prerequisites: ["linear_equations"]
source_refs: ["SGK Toán 10 - Chương 3"]
last_updated: 2026-01-01
---
## Concept
...
## Formula
...
## Example
...
```

Sau khi thêm file, chạy lại `python scripts/seed_wiki.py` hoặc gọi `POST /api/v1/admin/wiki/ingest`. Hệ thống sẽ kiểm tra schema, cắt chunk mà không làm vỡ công thức LaTeX, rồi tạo embedding.

## Chiến lược sư phạm

`PedagogySelector` chọn chiến lược theo loại người học (`struggling` / `average` / `advanced`), loại câu hỏi và mức phụ thuộc vào gợi ý:

- Tải nhận thức cao (> 0.8) thì giải thích trực tiếp.
- Phát hiện hiểu sai thì hướng dẫn từng bước.
- Các trường hợp còn lại tra theo ma trận. Ví dụ học sinh trung bình gặp bài tập thì được đưa ví dụ mẫu, học sinh giỏi gặp bài tập thì được hỏi theo kiểu Socratic.

## Kiểm thử và chất lượng code

```bash
pytest                      # chạy toàn bộ test
ruff check .                # lint (có rule bảo mật)
black --check .             # kiểm tra định dạng
pip-audit                   # quét lỗ hổng dependency
```

## Tình trạng dự án

Dự án đang trong giai đoạn phát triển (v0.1.0). Chưa có frontend; backend cho phép CORS từ `http://localhost:3000` để sẵn sàng kết nối với một ứng dụng web về sau.

## Đóng góp

1. Fork repo và tạo nhánh mới: `git checkout -b feature/ten-tinh-nang`
2. Đảm bảo `ruff`, `black` và `pytest` đều qua
3. Mở Pull Request mô tả rõ thay đổi

## Giấy phép

Chưa chỉ định. Hãy thêm file `LICENSE` (ví dụ MIT) trước khi công khai.
