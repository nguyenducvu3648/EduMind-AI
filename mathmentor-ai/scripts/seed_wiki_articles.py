"""Seed LLM-Wiki with curated articles for common math concepts."""

import asyncio

from app.db.session import AsyncSessionLocal
from app.db.models.wiki_article import WikiArticle
from sqlalchemy import select


ARTICLES = [
    {
        "slug": "phuong-trinh-bac-hai",
        "title": "Phương trình bậc hai một ẩn",
        "summary": "Định nghĩa, công thức nghiệm và cách giải phương trình bậc hai ax² + bx + c = 0",
        "content": """## Định nghĩa

Phương trình bậc hai một ẩn có dạng:

$$ax^2 + bx + c = 0 \\quad (a \\neq 0)$$

Trong đó:
- $a, b, c$ là các hệ số thực
- $x$ là ẩn số

## Công thức nghiệm

Tính biệt thức (delta):

$$\\Delta = b^2 - 4ac$$

- Nếu $\\Delta > 0$: phương trình có **2 nghiệm phân biệt**
  $$x_1 = \\frac{-b + \\sqrt{\\Delta}}{2a}, \\quad x_2 = \\frac{-b - \\sqrt{\\Delta}}{2a}$$

- Nếu $\\Delta = 0$: phương trình có **nghiệm kép**
  $$x = -\\frac{b}{2a}$$

- Nếu $\\Delta < 0$: phương trình **vô nghiệm** trên tập số thực

## Công thức nghiệm thu gọn

Khi $b = 2b'$, đặt $\\Delta' = b'^2 - ac$:

- $\\Delta' > 0$: $x_{1,2} = \\frac{-b' \\pm \\sqrt{\\Delta'}}{a}$
- $\\Delta' = 0$: $x = -\\frac{b'}{a}$
- $\\Delta' < 0$: vô nghiệm

## Định lý Viète

Nếu phương trình $ax^2 + bx + c = 0$ có hai nghiệm $x_1, x_2$ thì:

$$x_1 + x_2 = -\\frac{b}{a}, \\quad x_1 x_2 = \\frac{c}{a}$$

**Ứng dụng:** Nhẩm nghiệm, tìm hai số biết tổng và tích.

## Ví dụ

**Ví dụ 1:** Giải phương trình $x^2 - 5x + 6 = 0$

$$\\Delta = (-5)^2 - 4 \\cdot 1 \\cdot 6 = 25 - 24 = 1 > 0$$
$$x_1 = \\frac{5 + 1}{2} = 3, \\quad x_2 = \\frac{5 - 1}{2} = 2$$

## Lỗi thường gặp

1. **Quên điều kiện $a \\neq 0$**: Nếu $a = 0$, phương trình trở thành bậc nhất
2. **Tính sai $\\Delta$**: Đặc biệt khi $b$ âm, cần đặt trong ngoặc: $(-5)^2$
3. **Nhầm công thức Viète**: $x_1 + x_2 = -b/a$, không phải $b/a$
""",
        "subject": "toan",
        "grade": 10,
        "difficulty": 0.4,
        "tags": ["phuong_trinh", "bac_hai", "delta", "viete"],
        "concepts": ["phuong_trinh_bac_hai", "delta", "dinh_ly_viete"],
        "has_examples": True,
        "has_common_mistakes": True,
        "has_formula": True,
        "related_slugs": ["phuong-trinh-bac-nhat", "he-phuong-trinh"],
    },
    {
        "slug": "dao-ham",
        "title": "Đạo hàm",
        "summary": "Định nghĩa, quy tắc tính và bảng đạo hàm cơ bản",
        "content": """## Định nghĩa

Đạo hàm của hàm số $y = f(x)$ tại điểm $x_0$ ký hiệu là $f'(x_0)$:

$$f'(x_0) = \\lim_{\\Delta x \\to 0} \\frac{f(x_0 + \\Delta x) - f(x_0)}{\\Delta x} = \\lim_{x \\to x_0} \\frac{f(x) - f(x_0)}{x - x_0}$$

**Ý nghĩa hình học:** Đạo hàm $f'(x_0)$ là hệ số góc của tiếp tuyến với đồ thị hàm số tại điểm $M_0(x_0, f(x_0))$.

## Bảng đạo hàm cơ bản

| Hàm số | Đạo hàm |
|--------|---------|
| $c$ (hằng số) | $0$ |
| $x^n$ | $n x^{n-1}$ |
| $\\sqrt{x}$ | $\\frac{1}{2\\sqrt{x}}$ |
| $\\sin x$ | $\\cos x$ |
| $\\cos x$ | $-\\sin x$ |
| $\\tan x$ | $\\frac{1}{\\cos^2 x}$ |
| $e^x$ | $e^x$ |
| $\\ln x$ | $\\frac{1}{x}$ |

## Quy tắc tính

- $(u \\pm v)' = u' \\pm v'$
- $(u \\cdot v)' = u'v + uv'$
- $\\left(\\frac{u}{v}\\right)' = \\frac{u'v - uv'}{v^2}$
- Hàm hợp: $f(g(x))' = f'(g(x)) \\cdot g'(x)$

## Ví dụ

**Ví dụ 1:** Tính đạo hàm $y = x^3 + 2x^2 - 5x + 1$

$$y' = 3x^2 + 4x - 5$$

## Lỗi thường gặp

1. **Nhầm đạo hàm tích**: $(uv)' \\neq u'v'$
2. **Quên nhân thêm $u'$ khi tính đạo hàm hàm hợp**
3. **Đạo hàm $\\ln x$**: $\\frac{1}{x}$, không phải $\\frac{1}{|x|}$
""",
        "subject": "toan",
        "grade": 11,
        "difficulty": 0.5,
        "tags": ["dao_ham", "vi_phan", "tiep_tuyen"],
        "concepts": ["dao_ham", "quy_tac_tinh", "ham_hop"],
        "has_examples": True,
        "has_common_mistakes": True,
        "has_formula": True,
        "related_slugs": ["tich-phan", "ung-dung-dao-ham"],
    },
    {
        "slug": "tich-phan",
        "title": "Tích phân",
        "summary": "Định nghĩa, tính chất và phương pháp tính tích phân cơ bản",
        "content": """## Định nghĩa

Cho hàm số $f(x)$ liên tục trên đoạn $[a, b]$. Tích phân từ $a$ đến $b$ của $f(x)$:

$$\\int_{a}^{b} f(x) \\, dx = F(b) - F(a)$$

Trong đó $F(x)$ là một nguyên hàm của $f(x)$.

## Tính chất

- $\\int_{a}^{b} k \\cdot f(x) \\, dx = k \\int_{a}^{b} f(x) \\, dx$
- $\\int_{a}^{b} [f(x) \\pm g(x)] \\, dx = \\int_{a}^{b} f(x) \\, dx \\pm \\int_{a}^{b} g(x) \\, dx$
- $\\int_{a}^{b} f(x) \\, dx = \\int_{a}^{c} f(x) \\, dx + \\int_{c}^{b} f(x) \\, dx$
- $\\int_{a}^{b} f(x) \\, dx = -\\int_{b}^{a} f(x) \\, dx$

## Phương pháp tính

### Đổi biến số
$$\\int f(g(x)) \\cdot g'(x) \\, dx = \\int f(u) \\, du \\quad (u = g(x))$$

### Từng phần
$$\\int u \\, dv = uv - \\int v \\, du$$

## Ví dụ

**Ví dụ 1:** Tính $\\int_{0}^{1} x^2 \\, dx$

$$\\int_{0}^{1} x^2 \\, dx = \\left.\\frac{x^3}{3}\\right|_{0}^{1} = \\frac{1}{3} - 0 = \\frac{1}{3}$$

## Lỗi thường gặp

1. **Đặt sai $u, dv$ khi tính từng phần**: Ưu tiên $u$ là hàm logarit, đa thức
2. **Quên đổi cận khi đổi biến số**
3. **Tích phân hàm có trị tuyệt đối cần xét dấu**
""",
        "subject": "toan",
        "grade": 12,
        "difficulty": 0.6,
        "tags": ["tich_phan", "nguyen_ham", "dien_tich"],
        "concepts": ["tich_phan", "phuong_phap_tinh"],
        "has_examples": True,
        "has_common_mistakes": True,
        "has_formula": True,
        "related_slugs": ["dao-ham", "ung-dung-tich-phan"],
    },
    {
        "slug": "vector-trong-khong-gian",
        "title": "Vectơ trong không gian",
        "summary": "Các phép toán vectơ trong không gian và ứng dụng",
        "content": """## Định nghĩa

Vectơ trong không gian là một đoạn thẳng có hướng. Ký hiệu $\\overrightarrow{AB}$.

## Các phép toán

### Tổng hai vectơ

Quy tắc hình bình hành:
$$\\vec{a} + \\vec{b} = \\text{đường chéo của hình bình hành tạo bởi } \\vec{a}, \\vec{b}$$

### Hiệu hai vectơ
$$\\vec{a} - \\vec{b} = \\vec{a} + (-\\vec{b})$$

### Tích vectơ với một số
Với $k \\in \\mathbb{R}$:
- $|k\\vec{a}| = |k| \\cdot |\\vec{a}|$
- $k\\vec{a}$ cùng hướng với $\\vec{a}$ nếu $k > 0$, ngược hướng nếu $k < 0$

### Tích vô hướng
$$\\vec{a} \\cdot \\vec{b} = |\\vec{a}| \\cdot |\\vec{b}| \\cdot \\cos(\\vec{a}, \\vec{b})$$

### Tích có hướng
$$|\\vec{a} \\times \\vec{b}| = |\\vec{a}| \\cdot |\\vec{b}| \\cdot \\sin(\\vec{a}, \\vec{b})$$
Vectơ $\\vec{a} \\times \\vec{b}$ vuông góc với cả $\\vec{a}$ và $\\vec{b}$.

## Ứng dụng

- Tính góc giữa hai đường thẳng
- Tính khoảng cách từ điểm đến mặt phẳng
- Tính thể tích khối hộp: $V = |(\\vec{a} \\times \\vec{b}) \\cdot \\vec{c}|$

## Lỗi thường gặp

1. **Nhầm tích vô hướng với tích có hướng**: Kết quả là số vs vectơ
2. **Quên $\\cos$ trong tích vô hướng**: $\\vec{a} \\cdot \\vec{b} \\neq |\\vec{a}| \\cdot |\\vec{b}|$
""",
        "subject": "toan",
        "grade": 12,
        "difficulty": 0.5,
        "tags": ["vector", "khong_gian", "hinh_hoc"],
        "concepts": ["vector", "tich_vo_huong", "tich_co_huong"],
        "has_examples": False,
        "has_common_mistakes": True,
        "has_formula": True,
        "related_slugs": ["phuong-trinh-mat-phang"],
    },
]


async def main():
    async with AsyncSessionLocal() as session:
        count = 0
        for data in ARTICLES:
            existing = await session.execute(
                select(WikiArticle).where(WikiArticle.slug == data["slug"])
            )
            if not existing.scalar_one_or_none():
                article = WikiArticle(**data)
                session.add(article)
                count += 1
                print(f"  + {data['slug']}")
        await session.commit()
        print(f"\nSeeded {count} articles.")


if __name__ == "__main__":
    asyncio.run(main())
