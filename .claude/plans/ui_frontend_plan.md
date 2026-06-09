# MathMentor AI — Frontend Plan (Next.js + Tailwind + Shadcn/ui)

## Tech Stack
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Shadcn/ui** + **Radix UI** (components)
- **Lucide React** (icons)
- Axios hoặc fetch API cho HTTP calls
- react-markdown + remark-math/rehype-katex cho hiển thị LaTeX

## Pages / Routes

| Route | Mô tả | Auth required |
|---|---|---|
| `/login` | Đăng nhập / Đăng ký | No |
| `/chat` | Chat chính (giống ChatGPT) | Yes |
| `/chat/[id]` | Chat với session cụ thể | Yes |
| `/wiki` | Knowledge base viewer | Yes |
| `/profile` | Profile + Learning Dashboard | Yes |

## Component Tree

```
RootLayout
├── (auth)
│   └── LoginPage (login + register tabs)
│
├── (dashboard)          ← layout.tsx có sidebar
│   ├── Sidebar
│   │   ├── UserInfo (avatar + name + grade)
│   │   ├── NewChatButton
│   │   ├── SessionList
│   │   │   └── SessionItem (preview message)
│   │   ├── NavLinks (Chat, Wiki, Profile)
│   │   └── LogoutButton
│   │
│   ├── ChatPage
│   │   ├── ChatHeader (title + strategy badge)
│   │   ├── MessageList
│   │   │   ├── UserMessage
│   │   │   ├── AIMessage (render LaTeX + sources)
│   │   │   └── SourcesDropdown
│   │   ├── ChatInput (textarea + send button)
│   │   └── EmptyState (khi chưa có session)
│   │
│   ├── WikiPage
│   │   ├── WikiSearch
│   │   ├── WikiFilter (by subject, grade)
│   │   └── WikiChunkCard
│   │
│   └── ProfilePage
│       ├── UserInfoCard
│       ├── TopicMasteryChart (progress bars)
│       ├── WeakTopicsSection
│       ├── LearningMetrics
│       └── PreferencesForm
```

## API Service Layer

```
/frontend/src/lib/
├── api.ts           — axios instance với interceptor (JWT)
├── auth.ts          — login, register, refresh
├── chat.ts          — sendMessage, streamChat, getMessages
├── sessions.ts      — listSessions, getSession
├── profile.ts       — getProfile, updateProfile
└── wiki.ts          — getWikiChunks, searchWiki
```

## Auth Flow

1. User login → nhận access_token + refresh_token
2. Lưu vào localStorage (hoặc httpOnly cookie qua Next.js API route)
3. Axios interceptor: tự động gắn Authorization header
4. Nếu 401 → redirect về /login

## Color Theme (Indigo/Blue - White)

Shadcn/ui base colors custom:
- **Primary:** Blue 600 (#2563EB)
- **Primary-foreground:** White
- **Sidebar bg:** Slate 50 (#F8FAFC)
- **Card bg:** White
- **Border:** Slate 200 (#E2E8F0)
- **Accent:** Indigo 500 (#6366F1)
- **Success:** Emerald 500 (#10B981)
- **Warning:** Amber 500 (#F59E0B)
- **Destructive:** Red 500 (#EF4444)

## Implementation Steps (thứ tự)

1. **Init:** `npx create-next-app@latest frontend` với TypeScript + Tailwind
2. **Setup Shadcn/ui:** `npx shadcn@latest init`
3. **Add components:** button, card, input, dialog, sidebar, avatar, badge, tabs, scroll-area, separator, sheet
4. **API layer:** axios instance + all api modules
5. **Auth pages:** login/register
6. **Layout:** dashboard layout with sidebar
7. **Chat page:** full chat interface
8. **Wiki page:** knowledge viewer
9. **Profile page:** dashboard + settings
