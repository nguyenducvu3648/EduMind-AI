# MathMentor AI — Gia sư Toán THPT Cá nhân hóa

---

## Slide 1 — Bối cảnh & Vấn đề

**Thực trạng:**
- Học sinh lớp 10–12 gặp khó khăn khi tự học Toán ở nhà
- Gia sư truyền thống có chi phí cao, không linh hoạt về thời gian
- Các công cụ AI hiện tại (ChatGPT, Gemini) trả lời chung chung, không bám sát chương trình THPT Việt Nam, không cá nhân hóa

**Cơ hội:**
- LLM (Large Language Models) đã đủ mạnh để làm gia sư AI
- RAG (Retrieval-Augmented Generation) giúp câu trả lời bám sát giáo trình
- Có thể xây dựng hệ thống "nhớ" từng học sinh — điểm mạnh, điểm yếu, sai lầm thường gặp

---

## Slide 2 — Giải pháp: MathMentor AI

**Một câu:** Hệ thống gia sư Toán AI cá nhân hóa, kết hợp **RAG + User Memory + Sư phạm thích ứng**.

**3 trụ cột:**

| Trụ cột | Vai trò |
|----------|---------|
| **RAG Engine** | Truy xuất kiến thức từ kho tài liệu Toán THPT |
| **User Memory** | Ghi nhớ trình độ, điểm yếu, sai lầm của từng học sinh |
| **Pedagogy Engine** | Chọn chiến lược giảng dạy phù hợp với từng học sinh |

**Công nghệ:**
- Backend: **FastAPI** (Python) + **PostgreSQL/pgvector**
- Frontend: **Next.js 15** (React, TypeScript)
- LLM: **DeepSeek Chat** (OpenAI-compatible)
- Embedding: **BGE** model cho vector search
- Reranker: **BAAI/bge-reranker-base**

---

## Slide 3 — Kiến trúc tổng thể (Layered Architecture)

```
┌─────────────────────────────────────────────────┐
│                 Frontend (Next.js)               │
│  Chat UI  │  Wiki Browser  │  Profile  │  Admin  │
└────────────────────┬────────────────────────────┘
                     │ REST API (JSON/SSE)
┌────────────────────▼────────────────────────────┐
│               API Layer (FastAPI)               │
│  Auth  │  Chat  │  Sessions  │  Users  │  Admin  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│          Orchestration Layer (Core)              │
│  Intent Detection → Query Rewriting             │
│  → Pedagogy Selection → Prompt Building         │
│  → Response Postprocessing                      │
│  ── gọi RAG, LLM, Memory ──                     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│             Data Layer (PostgreSQL)              │
│  users │ user_profiles │ sessions │ interaction  │
│  wiki_chunks (pgvector) │ wiki_articles          │
└─────────────────────────────────────────────────┘
```

---

## Slide 4 — Luồng xử lý Tutoring Pipeline (1)

**Khi học sinh gửi câu hỏi, pipeline chạy 7 bước:**

```
User: "Giải thích phương trình bậc hai"
         │
         ▼
┌─────────────────────┐
│  1. Intent Detection │  ← Xác định loại câu hỏi
│  (orchestrator.py)   │    (problem_solving / concept_explanation /
└─────────┬───────────┘     hint_request / review / clarification)
          │                 + trích xuất topic tags: ["quadratic_equations"]
          ▼
┌─────────────────────┐
│  2. Query Rewriting  │  ← Tạo biến thể truy vấn cho RAG
│  (query_rewriter.py) │    "quadratic equation discriminant delta
└─────────┬───────────┘     factoring roots" (mở rộng)
          │
          ▼
┌─────────────────────┐
│  3. RAG Retrieval    │  ← Chạy song song:
│  (retriever.py)      │    • Semantic search (pgvector + cosine)
└─────────┬───────────┘    • BM25 full-text search
          │                → RRF fusion → top-K chunks
          ▼
```

---

## Slide 5 — Luồng xử lý Tutoring Pipeline (2)

```
          │
          ▼
┌─────────────────────┐
│  4. User State       │  ← Đánh giá trạng thái học sinh
│  Interpretation      │    • Learner type: struggling/average/advanced
│  (user_state_int.)   │    • Cognitive load estimate
└─────────┬───────────┘    • Misconception detection
          │                • Weak topics liên quan đến câu hỏi
          ▼
┌─────────────────────┐
│  5. Pedagogy         │  ← Chọn chiến lược dạy:
│  Selection           │    Matrix dựa trên (learner_type, question_type)
│  (pedagogy_sel.)     │    struggling + problem_solving → HINT_FIRST
└─────────┬───────────┘    average + concept_explanation → SOCRATIC
          │                advanced + problem_solving → SOCRATIC
          ▼
┌─────────────────────┐
│  6. Prompt Building  │  ← Lắp ráp prompt từ:
│  (prompt_builder.py) │    • RAG context (đã compress)
│                      │    • History (6 messages gần nhất)
│                      │    • User state (learner type, cognitive load)
│                      │    • Chiến lược sư phạm
│                      │    • Bloom target level
│                      │    • Quy tắc LaTeX formatting
└─────────┬───────────┘
          ▼
```

---

## Slide 6 — Luồng xử lý Tutoring Pipeline (3)

```
          │
          ▼
┌─────────────────────┐
│  7. LLM Generation   │  → Gửi prompt đến DeepSeek Chat
│  (openai_client.py)  │  → Nhận response (streaming)
│                      │  → Trả về frontend qua SSE
│                      │
│  Sau khi trả response│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Memory Update       │  ← Cập nhật UserProfile:
│  (ema_updater.py)    │    • topic_mastery (EMA: alpha=0.35)
│                      │    • weak_topics (mastery < 0.4)
│                      │    • strong_topics (mastery > 0.75)
│                      │    • hint_dependency_level
│                      │    • error_recurrence_rate
│                      │    • misconception_patterns
└─────────────────────┘
```

---

## Slide 7 — RAG Engine: Hybrid Retrieval

**Vấn đề:** Search thuần vector hay thuần text đều có điểm yếu.

**Giải pháp:** Hybrid Search + Reciprocal Rank Fusion.

```
User Query: "giải phương trình bậc hai"
         │
    ┌────┴────┐
    ▼         ▼
Semantic     BM25
Search       Search
(pgvector)   (PostgreSQL FTS)
│            │
│ cosine     │ ts_rank_cd
│ distance   │
└────┬──────┘
     ▼
RRF Fusion  score = Σ 1/(k + rank_i)
     │
     ▼
Reranker (Cross-Encoder)
     │
     ▼
Context Compressor (LaTeX-safe)
     │
     ▼
Final Context → Prompt
```

- **Semantic search:** Nhúng query → tìm chunks gần nhất về ngữ nghĩa
- **BM25 search:** Tìm kiếm từ khoá trên PostgreSQL full-text index
- **RRF (k=60):** Gộp 2 danh sách xếp hạng
- **Reranker:** Cross-encoder đánh giá lại độ relevance
- **Compressor:** Giữ nguyên LaTeX, ưu tiên câu liên quan đến query

---

## Slide 8 — User Memory: EMA-based Mastery Tracking

**Cơ chế:** Exponential Moving Average (EMA) — cập nhật sau mỗi tương tác.

```
mastery_signal = correctness(0.35) + hint(0.20) + engagement(0.15)
               + repetition(0.15) + confusion(0.15)

new_mastery = α × signal + (1 - α) × old_mastery    (α = 0.35)
```

| Tín hiệu | Mô tả | Trọng số |
|----------|-------|---------|
| correctness | Feedback ≥ 4 → 1.0, < 4 → 0.5, null → 0.5 | 35% |
| hint | Không dùng hint → 1.0, có hint → 0.0 | 20% |
| engagement | Xem >30s → 1.0, <30s → 0.0 | 15% |
| repetition | Lặp lại ≥3 lần → 0.0, <3 lần → 1.0 | 15% |
| confusion | Clarification follow-up → 0.0, không → 1.0 | 15% |

**Kết quả:**
- `topic_mastery`: dict[topic → 0..1] cho mỗi chủ đề
- `weak_topics`: topic có mastery < 0.4
- `strong_topics`: topic có mastery > 0.75
- `misconception_patterns`: phát hiện lỗi tái diễn

---

## Slide 9 — Pedagogy: Tự động chọn cách dạy

### Dữ liệu từ đâu?

Hệ thống phân loại học sinh dựa trên **3 trường trong DB**:

```
UserProfile (bảng user_profiles)
├── topic_mastery: {"quadratic_equations": 0.7, "derivative": 0.3}
│   → Độ thành thạo từng chủ đề (0.0 - 1.0)
│   → Mastery < 0.4 → weak_topics
│   → Mastery > 0.75 → strong_topics
├── hint_dependency_level: 0.6
│   → Hay phải gợi ý không? (0.0 - 1.0)
├── error_recurrence_rate: 0.4
│   → Có tái phạm lỗi cũ không? (0.0 - 1.0)
└── misconception_patterns: [...]
    → Những sai lầm thường gặp
```

Ví dụ:
- `topic_mastery["quadratic_equations"] = 0.25` → Học sinh **yếu** → struggling
- `topic_mastery["quadratic_equations"] = 0.6` → Học sinh **trung bình** → average
- `topic_mastery["quadratic_equations"] = 0.85` → Học sinh **khá** → advanced

→ `learner_type` được xác định = trung bình cộng mastery của các chủ đề liên quan đến câu hỏi.

### Quy tắc chọn cách dạy

```
                      Loại câu hỏi
              Giải bài tập          Giải thích khái niệm
Yếu (mastery < 40%)   → Gợi ý / Từng bước   → Giảng thẳng
TB (40-70%)           → Làm mẫu              → Hỏi ngược
Khá ( > 70%)          → Hỏi ngược            → Tự nhận thức
```

**Ngoại lệ:** Quá tải → Giảng thẳng. Sai lầm tái diễn → Từng bước.

### 6 cách dạy

| Cách dạy | Làm gì? |
|----------|---------|
| **Giảng thẳng** | Giải thích luôn, rõ ràng |
| **Từng bước** | Chia nhỏ, làm từng bước |
| **Gợi ý trước** | Gợi ý rồi để học sinh tự làm |
| **Làm mẫu** | Cho bài mẫu hoàn chỉnh |
| **Hỏi ngược** | Đặt câu hỏi, học sinh tự nghĩ |
| **Tự nhận thức** | Hỏi "Em nghĩ thế nào?" |

---

## Slide 10 — Intent Detection & Query Rewriting

### Intent Detection (rule-based, không cần LLM)

```
Input: "Cho em hỏi về delta trong phương trình bậc hai"

Phân tích:
  - "hỏi" → không phải hint request
  - Không có "giải", "tìm", "=" → concept_explanation
  - Keyword "bậc hai", "delta" → topic: quadratic_equations
  - Có $$...$$? Không → math_entities: []

Kết quả:
  question_type: "concept_explanation"
  topic_tags: ["quadratic_equations"]
  difficulty: 0.45
```

### Query Rewriting — Tạo biến thể cho RAG

```
Original: "Giải thích phương trình bậc hai"
  → Variant 1: "Giải thích phương trình bậc hai" (giữ nguyên)
  → Variant 2: "Giải thích phương trình bậc hai
     Keywords: quadratic equation discriminant delta factoring roots"
  → Variant 3: "quadratic_equations"
```
Mỗi variant chạy semantic + BM25 riêng → RRF fusion.

---

## Slide 11 — Frontend: Tổng quan giao diện

**3 trang chính + Admin:**

### Chat (`/chat`)
- Streaming response qua SSE
- Hiển thị chiến lược sư phạm (badge) cho mỗi câu trả lời
- Hiển thị Bloom level
- Nguồn tham khảo (RAG sources) — collapsible
- Gợi ý follow-up
- Hỗ trợ LaTeX render (KaTeX)
- Sidebar: danh sách session (tự động poll 5s)

### Wiki (`/wiki`)
- Duyệt tài liệu Toán THPT
- Tìm kiếm full-text qua RAG
- Trang chi tiết bài học

### Profile (`/profile`)
- Mức độ thành thạo theo chủ đề (biểu đồ thanh)
- Chủ đề yếu / mạnh
- Thông số học tập (tốc độ học, ghi nhớ, tái phạm)
- Tuỳ chỉnh preferences

### Admin (`/admin`)
- Dashboard thống kê
- Quản lý người dùng
- Ingest tài liệu Wiki
- Evaluation

---

## Slide 12 — Chat UI: Trải nghiệm real-time

**Luồng streaming:**

```
Frontend gửi POST /api/v1/chat/ask
         │
         ▼
Backend xử lý pipeline (Intent → RAG → Pedagogy → Prompt → LLM)
         │
         ▼
SSE stream:
  event: token
  data: {"token": "Phương trình bậc hai có dạng "}

  event: token
  data: {"token": "$$ax^2 + bx + c = 0$$"}

  ...

  event: metadata
  data: {
    "session_id": "uuid",
    "message_id": "uuid",
    "teaching_strategy_used": "socratic",
    "bloom_level": "understand",
    "topics_covered": ["quadratic_equations"],
    "sources": [...],
    "follow_up_suggestions": [...]
  }
```

**Frontend render:**
- Token → ReactMarkdown + remark-math + rehype-katex
- Metadata → StrategyBadge, BloomBadge, SourceCards, FollowUp buttons

---

## Slide 13 — Database Schema

**6 bảng chính:**

```
users                    user_profiles                 sessions
├── id (UUID, PK)        ├── user_id (UUID, PK,FK)    ├── id (UUID, PK)
├── email (unique)       ├── topic_mastery (JSONB)    ├── user_id (FK)
├── hashed_password      ├── weak_topics (Text[])     ├── started_at
├── grade_level          ├── strong_topics (Text[])    ├── ended_at
├── role (student/admin) ├── misconception (JSONB[])  ├── message_count
├── created_at           ├── learning_speed (Float)   └── topics_covered (Text[])
└── updated_at           └── ... (8 metrics nữa)

interaction_logs          wiki_chunks                  wiki_articles
├── id (UUID, PK)        ├── id (INT, PK)             ├── id (UUID, PK)
├── session_id (FK)      ├── article_id               ├── slug (unique)
├── user_id (FK)         ├── content (Text)           ├── title
├── query                ├── embedding (VECTOR(1024)) ├── content (Text)
├── response             ├── tags (Text[])             ├── grade
├── topics_detected[]    ├── subject                  ├── is_published
├── teaching_strategy    ├── grade_min/max            └── updated_at
└── user_feedback        └── ... (metadata)
```

**Indexes đặc biệt:**
- `ix_wiki_chunks_embedding_ivfflat` — IVFFlat index cho vector search
- `ix_wiki_chunks_content_fts` — GIN index cho full-text search
- `ix_wiki_chunks_tags_gin`, `ix_wiki_chunks_concepts_gin` — GIN cho array

---

## Slide 14 — Admin Dashboard & Báo cáo

**4 tab chức năng:**

### 📊 Tiến độ
- Tổng quan: users, interactions, sessions, knowledge base
- Biểu đồ tương tác 7 ngày (zero-filled)
- Chiến lược giảng dạy (phân bố %)
- Top chủ đề được học nhiều nhất
- Top chủ đề yếu phổ biến

### 📥 Ingest Wiki
- Nhập đường dẫn server (file/folder .md)
- Upload file .md từ máy tính (drag & drop)
- Tự động chunking + embedding

### 👥 Người dùng
- Danh sách user + search email
- Xem profile học tập chi tiết
- Đổi role (student ↔ admin)
- Xoá user

### 🧪 Evaluation
- RAG Quality
- Response Quality
- Personalization

---

## Slide 15 — Wiki Ingestion Pipeline

**Tài liệu Toán THPT → Database:**

```
File .md (frontmatter + markdown)
  → MarkdownChunker.phân tích YAML frontmatter
  → Tách section (##, ###)
  → Tạo WikiChunkDraft cho mỗi section
  → EmbeddingService.embed_texts() (BGE model)
  → Upsert vào wiki_chunks table
  → commit
```

**File frontmatter example:**
```yaml
---
title: Phương trình bậc hai
subject: Toán
grade: 10
difficulty: 0.4
tags: ["quadratic_equations", "delta", "discriminant"]
concepts: ["quadratic formula", "discriminant"]
---
## 1. Định nghĩa
Phương trình bậc hai là phương trình có dạng...
```

**Chunking strategy:**
- Mỗi section → 1 chunk
- Giữ nguyên LaTeX
- Bảo toàn metadata (grade, tags, concepts)

---

## Slide 16 — Bảo mật & Authentication

### Student Auth
- Register với email + password
- JWT access token (60 phút) + refresh token (7 ngày)
- Lưu localStorage, gửi qua `Authorization: Bearer`
- Interceptor tự động redirect về /login nếu 401

### Admin Auth
- **2 phương thức:**
  1. API Key (`X-Admin-Api-Key` header) — cho script/automation
  2. JWT + role='admin' check — cho Admin UI
- Admin login: `POST /admin/auth/login` → kiểm tra email + password + role
- Admin layout riêng, **không có sidebar session**

### Rate Limiting
- 60 requests/phút/user
- 10 concurrent sessions/user

---

## Slide 17 — Admin layout & Phân quyền

```
frontend/src/app/
├── admin/                    ← Layout RIÊNG (no sidebar)
│   ├── layout.tsx            ← Header + logout + nút "Quay lại"
│   └── page.tsx              ← Admin dashboard
├── (dashboard)/              ← Layout user thường
│   ├── layout.tsx            ← Sidebar + session list
│   ├── chat/                 ← Chat UI
│   ├── wiki/                 ← Wiki browser
│   └── profile/              ← Student profile
└── login/                    ← Login/register
```

**Tại sao tách layout:**
- Admin cần toàn màn hình cho dashboard
- Admin không cần xem session chat của chính mình
- Không gây nhầm lẫn giữa vai trò

**Phân quyền backend:**
- Student endpoints: chỉ cần JWT hợp lệ
- Admin endpoints: JWT + role='admin' hoặc API Key
- User chỉ xem được profile của chính mình (`_assert_self`)

---

## Slide 18 — Metrics & Monitoring

**Prometheus metrics** (qua `app/utils/metrics.py`):

| Metric | Type | Labels | Mục đích |
|--------|------|--------|----------|
| `chat_latency` | Histogram | — | Thời gian xử lý mỗi request |
| `rag_retrieval_latency` | Histogram | stage (hybrid/semantic/bm25) | Hiệu năng RAG |
| `llm_token_usage` | Counter | model, type (prompt/completion) | Token consumption |
| `strategy_counter` | Counter | strategy, learner_type | Phân bố chiến lược |

**Logging structured** (qua `app/utils/logging.py`):
- Mỗi stage trong pipeline đều log: stage, status, duration
- Trace từ đầu đến cuối request

**Admin dashboard:**
- Tổng số users, sessions, interactions
- Biểu đồ daily interactions (7 ngày)
- Phân bố chiến lược giảng dạy
- Top weak topics

---

## Slide 19 — Công nghệ & Deployment

**Stack:**

| Layer | Công nghệ | Lý do chọn |
|-------|-----------|------------|
| **Backend** | FastAPI + Python 3.12 | Async, type-safe, OpenAPI tự động |
| **Frontend** | Next.js 15 + React + TypeScript | SSR/CSR linh hoạt, ecosystem mạnh |
| **Database** | PostgreSQL 16 + pgvector | Vector search + full-text + relational |
| **LLM** | DeepSeek Chat (OpenAI-compatible) | Chi phí thấp, quality tốt |
| **Embedding** | BAAI/bge (1024-d) | Open-source, quality cạnh tranh |
| **Reranker** | BAAI/bge-reranker-base | Cross-encoder, cải thiện RAG |
| **ORM** | SQLAlchemy 2.0 (async) | Mature, type-safe |
| **Migration** | Alembic | Version control DB schema |
| **Auth** | JWT + OAuth2 (FastAPI built-in) | Stateless, chuẩn web |
| **UI** | Tailwind CSS + shadcn/ui | Responsive, consistent |

**Deployment:**
- Docker container (backend + frontend)
- PostgreSQL riêng (cần pgvector extension)
- Biến môi trường qua `.env`

---

## Slide 20 — Demo: Luồng chi tiết

**Scenario:** Học sinh lớp 10 yếu phương trình bậc hai

```
1. Học sinh đăng ký → UserProfile tạo với mastery mặc định
2. Chat: "Phương trình bậc hai là gì?"
3. Intent Detection → concept_explanation + ["quadratic_equations"]
4. User State:
   - learner_type: struggling (mastery mới = 0.5, chưa có history)
   - weak_topics: [] (chưa có dữ liệu)
5. Pedagogy → DIRECT_EXPLANATION (struggling + concept_explanation)
6. RAG → chunks về phương trình bậc hai (lớp 10)
7. Prompt → system + context + user query → DeepSeek
8. Response streaming → frontend render LaTeX
9. Memory update:
   - topic_mastery[quadratic_equations] = EMA(0.5, signal)
   - Nếu signal thấp → weak_topics = ["quadratic_equations"]

Lần chat sau:
10. "Giải phương trình $x^2 - 5x + 6 = 0$"
11. User State thấy weak_topics → tăng scaffolding
12. Pedagogy → STEP_BY_STEP hoặc HINT_FIRST
13. Bloom target → REMEMBER
14. Prompt được điều chỉnh → phù hợp với học sinh yếu
```

---

## Slide 21 — Kết quả & Hướng phát triển

**Đã đạt được:**
- ✅ Pipeline tutoring hoàn chỉnh (Intent → RAG → Pedagogy → LLM → Memory)
- ✅ Retrieval hybrid (semantic + BM25 + RRF) bám sát giáo trình THPT
- ✅ Cá nhân hóa qua EMA memory với 5 tín hiệu
- ✅ 6 chiến lược sư phạm thích ứng theo learner type
- ✅ Streaming response real-time
- ✅ Hỗ trợ LaTeX đầy đủ
- ✅ Dashboard admin + quản lý user
- ✅ Ingest tài liệu markdown tự động
- ✅ Phân quyền admin (role-based + API key)

**Hướng phát triển:**
- 🔲 Multi-modal: hỗ trợ hình ảnh, đồ thị
- 🔲 Quiz & bài tập tự động chấm điểm
- 🔲 Recommendation engine: gợi ý bài học tiếp theo
- 🔲 Spaced repetition: lên lịch ôn tập dựa trên retention
- 🔲 Group learning: so sánh tiến độ theo lớp
- 🔲 Integration: Google Classroom, Moodle

---

## Slide 22 — Kiến trúc file (cho dev)

```
mathmentor-ai/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/         ← REST endpoints
│   │   │   ├── chat.py, auth.py, sessions.py, users.py
│   │   │   └── admin/         ← Admin endpoints
│   │   │       ├── auth.py, dashboard.py, users.py
│   │   │       ├── wiki.py, evaluation.py
│   │   ├── schemas/           ← Pydantic models
│   │   └── router.py          ← Route assembly
│   ├── core/                   ← Orchestration pipeline
│   │   ├── orchestrator.py     ← Pipeline chính
│   │   ├── intent_detector.py  ← Rule-based intent
│   │   ├── pedagogy_selector.py
│   │   ├── prompt_builder.py
│   │   ├── query_rewriter.py
│   │   └── response_postprocessor.py
│   ├── rag/                    ← RAG engine
│   │   ├── retriever.py        ← Hybrid retrieval
│   │   ├── reranker.py         ← Cross-encoder rerank
│   │   ├── context_compressor.py
│   │   ├── rrf.py              ← Reciprocal Rank Fusion
│   │   └── types.py
│   ├── memory/                 ← User memory
│   │   ├── ema_updater.py      ← EMA mastery update
│   │   ├── user_state_interpreter.py
│   │   └── misconception_detector.py
│   ├── wiki/                   ← Wiki ingestion
│   │   ├── ingestion_pipeline.py
│   │   ├── chunker.py
│   │   └── embedding_service.py
│   ├── llm/openai_client.py    ← LLM client
│   └── db/models/              ← SQLAlchemy models
├── frontend/src/
│   ├── app/(dashboard)/        ← Student UI
│   ├── app/admin/              ← Admin UI (layout riêng)
│   ├── components/admin/        ← Admin components
│   └── hooks/ lib/ types/      ← Shared
└── alembic/versions/           ← DB migrations
```

---

## Hết

**MathMentor AI** — Gia sư Toán cá nhân hóa cho học sinh THPT Việt Nam.
