# UI Implementation Plan — MathMentor AI

## Công nghệ: Gradio (Python thuần)

**Lý do chọn Gradio:**
- Backend đã là Python FastAPI — Gradio chạy cùng ecosystem
- Không cần build tool, không cần npm, không cần CORS config phức tạp
- UI.py đã có base Gradio sẵn → giữ được tinh thần
- Gradio Blocks có thể làm multi-page SPA-like
- Có thể styled CSS custom hoàn toàn

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  Gradio App                       │
│  (mathmentor-ui\app.py)                          │
│                                                    │
│  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Sidebar     │  │       Main Content        │  │
│  │  ───────────  │  │  ──────────────────────   │  │
│  │  Login/Signup │  │  Page: Chat              │  │
│  │  Profile      │  │  Page: Wiki Viewer       │  │
│  │  Chat History │  │  Page: Profile Settings   │  │
│  │  New Chat     │  │                          │  │
│  │  Wiki View    │  │                          │  │
│  └──────────────┘  └──────────────────────────┘  │
│                                                    │
│  ┌──────────────── API Layer ───────────────────┐ │
│  │  httpx.AsyncClient → localhost:8000/api/v1/  │ │
│  └─────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## Pages / Tính năng

### 1. Login / Register Page
- Form login (email + password) → gọi `POST /auth/login`
- Form register (email + password + grade) → gọi `POST /auth/register`
- Lưu JWT token vào biến state (session)
- Tự động redirect vào Chat page sau login

### 2. Chat Page (trang chính)
- **Sidebar trái:**
  - Avatar + tên user + grade
  - Nút "Chat mới" (tạo session mới)
  - Danh sách session: mỗi item hiển thị `last_message` preview + thời gian
  - Click vào session → load messages
  - Nút "Tài liệu" → chuyển sang Wiki Viewer
- **Main:**
  - Header hiển thị "MathMentor AI" + chiến lược giảng dạy hiện tại
  - Chat box cuộn được: hiển thị user query + AI response (hỗ trợ LaTeX)
  - Input text box + nút Gửi (Enter gửi)
  - Hiển thị sources (wiki chunks tham khảo) dạng collapsible
  - Hiển thị teaching strategy + bloom level sau mỗi response

### 3. Wiki Viewer
- Danh sách các wiki chunk theo subject/grade
- Xem nội dung full của chunk
- Search trong wiki chunks

### 4. Profile Settings
- Xem profile: topic_mastery (dạng progress bars)
- weak_topics / strong_topics
- learning_speed, retention_strength...
- Update preferences: response_preference, hint_dependency_level, step_by_step_preference

## API Integration

| UI Action | API Call | Method |
|---|---|---|
| Login | `/auth/login` | POST |
| Register | `/auth/register` | POST |
| Get profile | `/users/{id}/profile` | GET |
| Update profile | `/users/{id}/profile` | PATCH |
| List sessions | `/sessions` | GET |
| Get messages | `/sessions/{id}/messages` | GET |
| Send chat | `/chat` (session_id + message) | POST |
| Stream chat | `/chat/stream?message=...&session_id=...` | GET |

## Màu sắc (Color Scheme)

Theme "Xanh dương - trắng" (khác ChatGPT xanh lá):

| Vai trò | Mã màu | Dùng cho |
|---|---|---|
| Primary | `#2563EB` (Blue 600) | Buttons, links, accent |
| Primary hover | `#1D4ED8` (Blue 700) | Hover states |
| Secondary | `#6366F1` (Indigo 500) | Badge, tag |
| Background | `#FFFFFF` | Main content |
| Sidebar | `#F8FAFC` (Slate 50) | Sidebar bg |
| Border | `#E2E8F0` (Slate 200) | Cards, dividers |
| Text primary | `#0F172A` (Slate 900) | Headings |
| Text secondary | `#64748B` (Slate 500) | Labels |
| Success | `#10B981` (Emerald) | Mastery bars |
| Warning | `#F59E0B` (Amber) | Weak topics |
| Error/Danger | `#EF4444` (Red) | Errors |

## File structure

```
mathmentor-ai/
├── mathmentor-ui/
│   ├── app.py            # Gradio app main entry
│   ├── api_client.py     # HTTP client wrapper (httpx)
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sidebar.py    # Sidebar component
│   │   ├── login.py      # Login/Register form
│   │   ├── chat.py       # Chat interface
│   │   ├── wiki.py       # Wiki viewer
│   │   └── profile.py    # Profile settings
│   ├── state.py           # Global app state (token, user, sessions...)
│   └── assets/
│       └── style.css      # Custom CSS
```

## Implementation Steps

1. Create `mathmentor-ui/` structure
2. `state.py` — global app state (token, current_user, sessions list)
3. `api_client.py` — httpx calls to FastAPI backend
4. `components/login.py` — login/register forms
5. `components/sidebar.py` — sidebar with profile + session list
6. `components/chat.py` — chat area with message history
7. `components/wiki.py` — wiki knowledge viewer
8. `components/profile.py` — user profile & settings
9. `app.py` — wire everything, routing between views

## Note

- Dùng `gr.State` để lưu JWT token và user info giữa các lần tương tác
- Mỗi page là 1 `gr.Column` hoặc `gr.Group`, show/hide bằng `visible`
- Không cần Gradio multi-page thật, dùng tab-like pattern
