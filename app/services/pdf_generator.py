from fpdf import FPDF
from pathlib import Path
from io import BytesIO

FONT_PATH = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"

def generate_session_pdf(user_data: dict, gpt_reply: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_font("DejaVu", "", str(FONT_PATH), uni=True)
    pdf.set_font("DejaVu", "", 16)

    pdf.cell(0, 10, "Отчёт по сессии", ln=True, align="C")
    pdf.ln(10)

    def add_field(title, value):
        pdf.set_font("DejaVu", "", 12)
        pdf.cell(0, 8, f"{title}:", ln=True)
        pdf.multi_cell(0, 8, value or "—")
        pdf.ln(2)

    add_field("Симптомы", user_data.get("symptoms"))
    add_field("Когда началось", user_data.get("onset"))
    add_field("Контекст", user_data.get("context"))
    add_field("Анализы", user_data.get("analyses"))
    add_field("Детали анализов", user_data.get("analysis_details"))
    add_field("Эмоциональное состояние", user_data.get("psycho_state"))
    add_field("Важные события", user_data.get("life_events"))

    pdf.ln(5)
    pdf.set_font("DejaVu", "", 14)
    pdf.cell(0, 10, "GPT-анализ", ln=True)
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 8, gpt_reply or "—")

    # 💾 Сохраняем PDF в BytesIO через строку
    pdf_bytes = BytesIO()
    pdf_content = pdf.output(dest="S").encode("latin1")
    pdf_bytes.write(pdf_content)
    pdf_bytes.seek(0)
    return pdf_bytes
