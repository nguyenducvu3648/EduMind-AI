"""
LLM-Wiki Article Builder — dùng GPT-4o-mini để làm sạch và chuẩn hóa.

Đọc wiki_chunks → phân nhóm theo (grade, topic) →
gọi OpenAI để làm sạch + ghép nội dung → lưu vào wiki_articles.
"""

import asyncio
import json
import re
import sys
from collections import defaultdict

from openai import AsyncOpenAI
from sqlalchemy import text as sa_text

from app.config import Settings
from app.db.session import AsyncSessionLocal
from app.db.models.wiki_article import WikiArticle


CLEAN_PROMPT = """Bạn là một nhà toán học và chuyên gia biên soạn giáo khoa Toán THPT.
Tôi đưa cho bạn các đoạn trích (chunks) từ sách giáo khoa / tài liệu Toán Việt Nam.
Các đoạn này có thể bị lỗi: công thức dính chữ, mất LaTeX, mất xuống dòng, lặp nội dung.
Nhiệm vụ của bạn là viết LẠI thành một bài viết Markdown chuẩn chỉnh và hoàn chỉnh.

YÊU CẦU NGHIÊM NGẶT:
1. SỬA tất cả công thức về đúng LaTeX: $x^2 + 2x + 1 = 0$, $$\\int_a^b f(x) dx$$
2. PHỤC HỒI cấu trúc: xuống dòng, hệ phương trình, bảng biểu
3. LOẠI BỎ trùng lặp, nội dung thừa, số trang
4. CHUẨN HÓA ký hiệu: lim thành \\lim, sqrt thành \\sqrt, ∞ thành \\infty
5. TÁCH rõ các phần: Định nghĩa, Công thức, Ví dụ, Lưu ý
6. KHÔNG thêm nội dung không có trong đoạn gốc
7. Dùng $$...$$ cho công thức hiển thị, $...$ cho công thức inline
8. Giữ nguyên các ký hiệu Toán Việt Nam (tập xác định D = R\\{1}, ...)
9. ESCAPE đúng các ký tự đặc biệt trong JSON: \\n, \\t, \\", \\\\

Trả về JSON (KHÔNG markdown code block, CHỈ raw JSON):
{
  "title": "Tiêu đề bài viết",
  "summary": "Tóm tắt ngắn 1-2 câu",
  "content": "Nội dung Markdown đã làm sạch (escape \\n, \\\", \\\\)",
  "has_formula": true hoac false,
  "has_examples": true hoac false,
  "has_common_mistakes": true hoac false,
  "difficulty": 0.5
}"""


class WikiArticleBuilder:
    def __init__(self):
        settings = Settings()
        key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else ""
        self.client = AsyncOpenAI(api_key=key, base_url=settings.llm_base_url)
        self.model = settings.llm_model

    async def clean_with_llm(self, chunks: list, grade: int, topic: str) -> dict | None:
        """Gửi chunks đến LLM để làm sạch và chuẩn hóa."""
        # Gom chunks
        combined = []
        seen = set()
        for c in chunks:
            content = str(c.content or "").strip()
            if not content:
                continue
            # Loại bỏ trùng
            key = re.sub(r'\s+', ' ', content)[:80]
            if key in seen:
                continue
            seen.add(key)
            combined.append(content)

        if not combined:
            return None

        # Cắt gọn nếu quá dài
        full_text = "\n\n---\n\n".join(combined)
        if len(full_text) > 8000:
            full_text = full_text[:8000]

        prompt = f"""CHỦ ĐỀ: {topic}
LỚP: {grade}
MÔN: Toán

Dữ liệu thô (cần làm sạch):
{full_text}"""

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CLEAN_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
            )
            text = resp.choices[0].message.content or "{}"
            # Extract JSON object from text (in case model wraps in markdown)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group()
            try:
                data = json.loads(text)
                return data
            except json.JSONDecodeError:
                pass

            # Try harder: fix common JSON issues
            fixes = [
                (r'\\(?![\\/"bfnrtu])', r'\\\\'),  # Fix invalid escapes
                (r'\\n(?![:,\]\}])', r'\\n'),       # Preserve valid \n
                (r'\\t(?![:,\]\}])', r'\\t'),       # Preserve valid \t
            ]
            cleaned = text
            for pattern, replacement in fixes:
                cleaned = re.sub(pattern, replacement, cleaned)
            try:
                data = json.loads(cleaned)
                return data
            except json.JSONDecodeError as e2:
                # Last resort: extract content field manually
                content_match = re.search(r'"content"\s*:\s*"(.*)"\s*}', text, re.DOTALL)
                title_match = re.search(r'"title"\s*:\s*"([^"]+)"', text)
                if content_match and title_match:
                    # Fix content: unescape manually
                    raw_content = content_match.group(1)
                    raw_content = raw_content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                    raw_content = re.sub(r'\\(.)', r'\1', raw_content)
                    return {
                        "title": title_match.group(1),
                        "summary": "Tong hop tu lieu",
                        "content": raw_content,
                        "has_formula": True,
                        "has_examples": False,
                        "has_common_mistakes": False,
                        "difficulty": 0.5,
                    }
                print(f"    JSON parse failed: {e2}")
                print(f"    Raw: {text[:300]}...")
                return None
        except Exception as e:
            print(f"    LLM error: {e}")
            return None


async def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    builder = WikiArticleBuilder()
    log_file = open("build_wiki_articles.log", "w", encoding="utf-8")

    def log(msg: str):
        log_file.write(msg + "\n")
        log_file.flush()

    async with AsyncSessionLocal() as sess:
        r = await sess.execute(sa_text("""
            SELECT id, grade, COALESCE(topic, title) as raw_topic,
                   title, content, has_formula, chunk_type, chunk_index
            FROM wiki_chunks
            WHERE content IS NOT NULL AND content != ''
            ORDER BY grade, raw_topic, chunk_index
        """))
        rows = r.all()

    groups = defaultdict(list)
    for row in rows:
        t = str(row.raw_topic).strip()
        t = re.sub(r' \| SGK Toán.*$', '', t)
        t = re.sub(r' - loigiaihay.*$', '', t)
        t = re.sub(r' \(Lý thuyết.*$', '', t)
        t = re.sub(r' lớp \d+.*$', '', t)
        t = re.sub(r' \(hay,.*$', '', t)
        t = re.sub(r' hay, nhanh nhất$', '', t)
        t = re.sub(r' \(quan trọng\)$', '', t)
        t = re.sub(r' - Cách.*$', '', t)
        t = re.sub(r' lớp 12 \(.*$', '', t)
        t = t.strip()
        if not t:
            continue
        groups[(row.grade, t)].append(row)

    log(f"Found {len(groups)} topic groups")
    articles_created = 0
    articles_skipped = 0

    for (grade, topic), chunks in sorted(groups.items()):
        if len(chunks) < 2:
            articles_skipped += 1
            continue

        raw_slug = re.sub(r'[^a-zA-Z0-9]+', '-', topic.lower()).strip('-')
        raw_slug = re.sub(r'^-+|-+$', '', raw_slug)[:80]
        if not raw_slug:
            raw_slug = f"topic-{grade}"

        # Tạo slug duy nhất bằng cách thêm số thứ tự nếu trùng
        slug = raw_slug
        async with AsyncSessionLocal() as sess:
            for attempt in range(100):
                existing = await sess.execute(
                    sa_text(f"SELECT id FROM wiki_articles WHERE slug = '{slug}'")
                )
                if not existing.fetchone():
                    break
                slug = f"{raw_slug}-{attempt + 2}"
            else:
                articles_skipped += 1
                continue

        log(f"  [{grade}] {topic} ({len(chunks)} chunks) -> {slug}")

        async with AsyncSessionLocal() as sess:
            ids = [c.id for c in chunks]
            ids_str = ",".join(str(x) for x in ids)
            r2 = await sess.execute(
                sa_text(f"SELECT id, content, chunk_type, section, has_formula FROM wiki_chunks WHERE id IN ({ids_str}) ORDER BY chunk_index")
            )
            full_chunks = r2.all()

        result = await builder.clean_with_llm(full_chunks, grade, topic)

        if result is None or not result.get("content"):
            log("    SKIP (LLM fail)")
            articles_skipped += 1
            continue

        async with AsyncSessionLocal() as sess:
            article = WikiArticle(
                slug=slug,
                title=result.get("title", topic)[:500],
                summary=(result.get("summary") or "")[:1000],
                content=result["content"],
                subject="toan",
                grade=grade,
                difficulty=min(1.0, max(0.0, result.get("difficulty", 0.5))),
                tags=[slug.replace("-", "_")],
                concepts=[slug.replace("-", "_")],
                has_examples=result.get("has_examples", False),
                has_common_mistakes=result.get("has_common_mistakes", False),
                has_formula=result.get("has_formula", False),
                source="Tong hop tu nhieu nguon",
            )
            sess.add(article)
            await sess.commit()

        content_len = len(result.get("content", ""))
        log(f"    OK ({content_len} chars)")
        articles_created += 1

    log(f"\nDone! Created: {articles_created}, Skipped: {articles_skipped}")
    log_file.close()
    print(f"Done! Created: {articles_created}, Skipped: {articles_skipped}")


if __name__ == "__main__":
    asyncio.run(main())
