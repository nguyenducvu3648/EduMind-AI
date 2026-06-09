import gradio as gr

def create_ui():

    custom_css = """
    .gradio-container {
        font-family: Arial;
        background-color: #ffffff;
        color: #000;
    }

    /* ===== SIDEBAR CHATGPT ===== */
    .sidebar {
        background: #f7f7f8;
        border-right: 1px solid #e5e5e5;
        min-height: 100vh;
        padding: 16px;
    }

    .profile-box {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 12px;
        background: white;
        border: 1px solid #e5e5e5;
        margin-bottom: 20px;
    }

    .avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: #10a37f;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 18px;
    }

    .session-item {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        background: white;
        border: 1px solid #ececec;
        cursor: pointer;
        transition: 0.2s;
    }

    .session-item:hover {
        background: #f0f7ff;
        border-color: #c9defc;
    }

    .new-chat-btn button {
        background: #10a37f !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
    }

    /* ===== MAIN ===== */

    .header {
        text-align: center;
        padding: 20px;
    }

    .box {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        background: #fafafa;
    }

    .scroll {
        max-height: 360px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 12px;
        border-radius: 8px;
        background: #fff;
    }

    summary {
        color: #1a73e8;
        font-weight: bold;
        cursor: pointer;
    }

    summary:hover {
        background-color: #eef5ff;
    }

    .login-box {
        border: 1px solid #e5e5e5;
        border-radius: 12px;
        padding: 20px;
        background: #fafafa;
        margin-bottom: 20px;
    }
    """

    with gr.Blocks(css=custom_css, title="AI Tutor Lớp 1–12") as app:

        with gr.Row():

            # ================= SIDEBAR =================
            with gr.Column(scale=1, elem_classes="sidebar"):

                gr.Markdown("## 🤖 AthenAI")

                with gr.Group(elem_classes="login-box"):

                    gr.Markdown("### 🔐 Login")

                    gr.Textbox(
                        label="Email",
                        placeholder="student@gmail.com"
                    )

                    gr.Textbox(
                        label="Password",
                        type="password",
                        placeholder="••••••••"
                    )

                    gr.Button(
                        "Đăng nhập",
                        variant="primary"
                    )

                # ===== PROFILE =====
                gr.Markdown("""
                <div class="profile-box">
                    <div class="avatar">A</div>
                    <div>
                        <b>Anh Nguyen</b><br>
                        <span style="color:gray;font-size:13px;">
                        Học sinh lớp 8
                        </span>
                    </div>
                </div>
                """)

                # ===== NEW CHAT =====
                with gr.Row(elem_classes="new-chat-btn"):
                    gr.Button("➕ Chat mới")

                gr.Markdown("### 💬 Lịch sử chat")

                gr.Markdown("""
                <div class="session-item">
                📘 Học lại phương trình lớp 8
                </div>

                <div class="session-item">
                🧮 Ôn tập phân số lớp 6
                </div>

                <div class="session-item">
                📗 Hình học tam giác cơ bản
                </div>

                <div class="session-item">
                📝 Luyện tập tiếng Anh lớp 7
                </div>
                """)

            # ================= MAIN CONTENT =================
            with gr.Column(scale=4):

                # ================= HEADER =================
                gr.Markdown("""
                <div class="header">
                    <h1>🎓 AI Tư Vấn Học Tập Cá Nhân Hóa </h1>
                    <p>Hệ thống học tập cá nhân hóa dựa trên LLM + Agentic RAG + User Memory</p>
                </div>
                """)

                # ================= INPUT =================
                with gr.Row():
                    with gr.Column(scale=2):

                        gr.Markdown("### 💬 Câu hỏi học sinh")

                        gr.Textbox(
                            value="Em yếu Toán lớp 8 phần phương trình, cần học lại từ đâu?",
                            label="Câu hỏi",
                            interactive=False
                        )

                        with gr.Row():
                            gr.Button("🚀 Gửi ", variant="primary")
                            gr.Button("🔄 Reset")

                gr.Markdown("---")

                # ================= ANSWER =================
                gr.Markdown("## ✅ Câu trả lời AI")

                gr.Markdown("""
                <div class="scroll">

                🎯 **Kế hoạch học lại Toán lớp 8 – Phương trình**

                ### 📌 Giai đoạn 1: Nền tảng SGK
                - Số học lớp 6–7: phân số, số nguyên  
                - Biểu thức đại số cơ bản  
                - Quy tắc chuyển vế  

                ### 📌 Giai đoạn 2: SGK lớp 8
                - Phương trình bậc nhất một ẩn  
                - Cách giải từng bước  
                - Kiểm tra nghiệm  

                ### 📌 Giai đoạn 3: Bài tập nâng cao
                - Bài toán thực tế SGK nâng cao  
                - Phương trình có tham số  
                - Tổng hợp kỹ năng  

                📌 **Cá nhân hóa (User Memory):**
                - Nếu học sinh yếu → quay lại lớp 6–7  
                - Nếu khá → tăng bài tập nâng cao  
                - Nếu nhanh → thêm bài nâng cao mở rộng  

                </div>
                """)

                gr.Markdown("---")

                # ================= RAW SGK DATA =================
                gr.Markdown("## 📘 DATA SGK ")

                gr.Markdown("""
                <div class="scroll">

                ### 📗 Toán lớp 8 — Phương trình bậc nhất một ẩn

                #### 📖 1. Khái niệm phương trình
                Phương trình là một đẳng thức có chứa ẩn.

                Ví dụ:
                - x + 2 = 5
                - 2x - 3 = 7

                Giá trị của ẩn làm cho hai vế bằng nhau gọi là nghiệm của phương trình.

                ---

                #### 📖 2. Phương trình bậc nhất một ẩn

                Dạng tổng quát:

                ax + b = 0

                Trong đó:
                - a ≠ 0
                - a, b là các số đã biết
                - x là ẩn

                Công thức nghiệm:

                x = -b / a

                </div>
                """)

                gr.Markdown("---")

                # ================= FOOTER =================
                gr.Markdown("""
                <div style="text-align:center; padding:20px; color:#666;">
                🎓 AI Tutor Demo | LLM + Agentic RAG + User Memory
                </div>
                """)

    return app


if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="127.0.0.1", server_port=7860)