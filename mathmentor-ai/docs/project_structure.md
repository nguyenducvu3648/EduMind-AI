# Mô tả cấu trúc thư mục dự án MathMentor AI

Tài liệu này giải thích vai trò của các thư mục và file chính trong dự án.

## Root của dự án

- `.env.example`
  - Mẫu biến môi trường để cấu hình ứng dụng khi chạy cục bộ hoặc trong Docker.
- `alembic.ini`
  - Cấu hình Alembic cho quản lý migration cơ sở dữ liệu.
- `docker-compose.yml`
  - Định nghĩa dịch vụ Docker cho môi trường phát triển / triển khai.
- `pyproject.toml`
  - Cấu hình dự án Python, dependencies, package metadata và script.
- `README.md`
  - Tài liệu giới thiệu dự án và hướng dẫn cài đặt cơ bản.
- `scripts/`
  - Chứa các script tiện ích, ví dụ `create_indexes.sql`, `seed_wiki.py`.
- `tests/`
  - Chứa các bài kiểm thử đơn vị và tích hợp.
- `wiki_content/`
  - Kho nội dung wiki toán học dưới dạng markdown, dùng để ingest vào hệ thống.

## `app/`

`app/` là nơi chứa toàn bộ ứng dụng FastAPI và logic nghiệp vụ chính.

### `app/main.py`
- Entrypoint khởi tạo FastAPI app.
- Thường dùng để chạy server `uvicorn`.

### `app/config.py`
- Cấu hình ứng dụng chung như kết nối DB, CORS, các biến môi trường.

### `app/dependencies.py`
- Định nghĩa dependency injection cho FastAPI, ví dụ session DB hoặc auth.

### `app/__init__.py`
- Khởi tạo package `app`.

## `app/api/`

Chứa định nghĩa API endpoint và schema dữ liệu.

### `app/api/v1/router.py`
- Tập hợp các route API của phiên bản 1.

### `app/api/v1/endpoints/`
- `auth.py` - endpoint đăng ký, đăng nhập, xác thực JWT.
- `chat.py` - endpoint chat/trao đổi với hệ thống.
- `sessions.py` - endpoint quản lý phiên trò chuyện.
- `users.py` - endpoint đọc/cập nhật thông tin người dùng.
- `admin/` - có thể chứa endpoint dành cho quản trị.

### `app/api/v1/schemas/`
- `chat.py`, `session.py`, `user.py`, `wiki.py`
- Định nghĩa các schema Pydantic cho request/response API.

## `app/core/`

Chứa logic chuyên môn, xử lý ngôn ngữ, bộ điều phối và bảo mật.

- `intent_detector.py` - phát hiện mục đích người dùng.
- `orchestrator.py` - điều phối luồng xử lý chính.
- `pedagogy_selector.py` - chọn chiến lược sư phạm phù hợp.
- `prompt_builder.py` - xây dựng prompt cho mô hình ngôn ngữ.
- `query_rewriter.py` - viết lại truy vấn người dùng nếu cần.
- `response_postprocessor.py` - xử lý, lọc, chỉnh sửa đầu ra trả về.
- `security.py` - các hàm liên quan đến bảo mật.

## `app/db/`

Chứa tầng truy cập dữ liệu và ORM.

- `base.py` - định nghĩa base class SQLAlchemy.
- `session.py` - cấu hình Session và engine database.
- `models/` - các model SQLAlchemy.

### `app/db/models/`
- `user.py` - model người dùng.
- `session.py` - model phiên trò chuyện.
- `interaction_log.py` - model log tương tác.
- `evaluation.py` - model đánh giá.
- `wiki_chunk.py` - model chunk nội dung wiki.

## `app/llm/`

Chứa client và logic tương tác với OpenAI hoặc LLM.

- `openai_client.py` - kết nối và gọi API OpenAI.

## `app/memory/`

Quản lý bộ nhớ người dùng và trạng thái học tập.

- `ema_updater.py` - cập nhật bảng EMA/nhớ lâu dài.
- `misconception_detector.py` - phát hiện sai sót, hiểu nhầm.
- `user_state_interpreter.py` - diễn giải trạng thái người dùng.

## `app/rag/`

Chứa thành phần RAG (retrieval-augmented generation) và tìm kiếm ngữ cảnh.

- `context_compressor.py` - nén ngữ cảnh truy vấn.
- `reranker.py` - xếp hạng lại kết quả truy vấn.
- `retriever.py` - tìm kiếm nội dung phù hợp từ wiki.
- `rrf.py` - thuật toán Reciprocal Rank Fusion.
- `types.py` - định nghĩa kiểu dữ liệu hỗ trợ RAG.

## `app/tasks/`

Chứa các tác vụ nền và Celery.

- `celery_app.py` - cấu hình ứng dụng Celery.
- `evaluation.py` - tác vụ đánh giá tự động.
- `memory_update.py` - cập nhật bộ nhớ người dùng nền.
- `wiki_ingestion.py` - tác vụ ingest nội dung wiki.

## `app/utils/`

Hàm tiện ích chung.

- `latex_utils.py` - xử lý LaTeX an toàn.
- `logging.py` - cấu hình logging.
- `metrics.py` - đo lường và định nghĩa metric.

## `app/wiki/`

Xử lý ingest và kiểm tra dữ liệu wiki.

- `chunker.py` - chia markdown wiki thành các chunk.
- `embedding_service.py` - tạo embedding nội dung.
- `ingestion_pipeline.py` - pipeline ingest wiki vào hệ thống.
- `schema_validator.py` - xác thực schema markdown wiki.

## `alembic/`

Chứa migration schema database.

- `env.py` - cấu hình môi trường Alembic.
- `versions/` - các file migration cụ thể.

## `docs/`

- `adr/` - Architecture Decision Records, lưu các quyết định kiến trúc.

## `tests/`

Chứa kiểm thử tự động.

- `unit/` - kiểm thử đơn vị.
- `integration/` - kiểm thử tích hợp.

## `wiki_content/`

Thư mục chứa nội dung bài học bằng markdown, ví dụ `grade_10/algebra/quadratic_equations.md`.

---

> Ghi chú: Đây là tài liệu tổng quan, giúp người mới hiểu nhanh từng thành phần chính của dự án.
