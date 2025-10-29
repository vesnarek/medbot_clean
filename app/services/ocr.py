from PIL import Image
import pytesseract
import io

async def extract_text_from_photo(photo_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(photo_bytes))
        text = pytesseract.image_to_string(image, lang="rus+eng")
        return text.strip()
    except Exception as e:
        return f"❌ Не удалось распознать текст с фото. Ошибка: {e}"
