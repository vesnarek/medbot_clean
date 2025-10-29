import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, PhotoSize,
    FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from aiogram.utils.markdown import hpre
from aiogram.utils.token import validate_token

from bot.fsm.states import SessionStates
from app.services.gpt import generate_gpt_response, generate_final_gpt_response
from app.db.database import init_db, save_session
from app.services.ocr import extract_text_from_photo
from app.services.pdf_generator import generate_session_pdf

import asyncio
import tempfile
from io import BytesIO


TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
assert TOKEN, "BOT_TOKEN не найден. Проверь .env"
validate_token(TOKEN)

ADMIN_IDS = [191586312]

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Стартовое меню
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Начать")],
        [KeyboardButton(text="ℹ️ Что это за бот?"), KeyboardButton(text="🔒 Конфиденциальность")]
    ],
    resize_keyboard=True
)

@dp.message(
    SessionStates.entering_symptoms,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.entering_onset,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.entering_context,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.entering_analyses,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.analysis_details,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.entering_psycho,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.entering_life_events,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.deep_question_1,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.deep_question_2,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.deep_question_3,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
@dp.message(
    SessionStates.deep_question_4,
    F.text.in_({"🚀 Начать", "ℹ️ Что это за бот?", "🔒 Конфиденциальность", "💾 Сохранить сессию", "🔄 Начать заново"})
)
async def handle_unexpected_button(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, сначала ответьте на текущий вопрос.")


@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.set_state(SessionStates.choosing_mode)
    await message.answer(
        "Здравствуйте. Я здесь, чтобы помочь вам глубже понять своё состояние — не только со стороны тела, "
        "но и с точки зрения эмоций, стресса и важных событий в жизни.\n\n"
        "Выберите, с чего начать 👇",
        reply_markup=start_keyboard
    )


@dp.message(F.text == "🚀 Начать")
async def begin_session(message: Message, state: FSMContext):
    await state.set_state(SessionStates.entering_diagnosis)
    await message.answer(
        "Есть ли у вас диагноз, который вы бы хотели обсудить?\n\n"
        "Если да, опишите его, или напишите «нет», если диагноза нет."
    )


@dp.message(SessionStates.entering_diagnosis)
async def handle_diagnosis(message: Message, state: FSMContext):
    diagnosis = message.text.strip().lower()
    await state.update_data(diagnosis=diagnosis)

    if diagnosis in ["нет", "no", "-", "—", "неа"]:
        await state.set_state(SessionStates.entering_analyses)
        await message.answer(
            "Хорошо, давайте перейдем к анализам.\n\n"
            "Есть ли у вас анализы? 📄\n"
            "— Вы можете прислать фото\n"
            "— Или ввести текстом (например: «Гемоглобин — 130, Сахар — 5.4»)\n\n"
            "Если у вас нет анализов, просто напишите «нет».\n\n"
            "Также, пожалуйста, укажите дату, когда были сданы анализы."
        )
    else:
        await state.set_state(SessionStates.entering_analyses)
        await message.answer(
            "Спасибо за информацию. Переходим к анализам.\n\n"
            "Есть ли у вас анализы? 📄\n"
            "— Вы можете прислать фото\n"
            "— Или ввести текстом (например: «Гемоглобин — 130, Сахар — 5.4»)\n\n"
            "Если у вас нет анализов, просто напишите «нет».\n\n"
            "Также, пожалуйста, укажите дату, когда были сданы анализы."
        )


@dp.message(SessionStates.entering_analyses, F.text)
async def handle_analysis_text(message: Message, state: FSMContext):
    text = message.text.strip().lower()

    if text in ["нет", "no", "-", "—", "неа"]:
        await state.update_data(analyses="нет")
        await state.set_state(SessionStates.entering_symptoms)
        await message.answer(
            "Теперь давайте поговорим о симптомах.\n\n"
            "Какие симптомы беспокоят вас в первую очередь?\n"
            "Примеры: головная боль, бессонница, тревожность, усталость, боль в животе и т.д.\n"
            "Напишите ваш симптом в свободной форме."
        )
    else:
        await state.update_data(analyses=message.text)
        await state.set_state(SessionStates.entering_symptoms)
        await message.answer(
            "Теперь давайте поговорим о симптомах.\n\n"
            "Какие симптомы беспокоят вас в первую очередь?\n"
            "Примеры: головная боль, бессонница, тревожность, усталость, боль в животе и т.д.\n"
            "Напишите ваш симптом в свободной форме."
        )


@dp.message(SessionStates.entering_analyses, F.photo)
async def handle_analysis_photo(message: Message, state: FSMContext):
    photo: PhotoSize = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(file.file_path)

    text = await extract_text_from_photo(photo_bytes.read())
    await state.update_data(analyses=text)

    await state.set_state(SessionStates.entering_symptoms)
    await message.answer(
        f"Распознанный текст:\n\n{hpre(text)}\n\n"
        "Теперь давайте поговорим о симптомах.\n\n"
        "Какие симптомы беспокоят вас в первую очередь?\n"
        "Примеры: головная боль, бессонница, тревожность, усталость, боль в животе и т.д.\n"
        "Напишите ваш симптом в свободной форме."
    )



@dp.message(SessionStates.entering_symptoms)
async def handle_custom_symptom(message: Message, state: FSMContext):
    await state.update_data(symptoms=message.text)
    await state.set_state(SessionStates.entering_onset)
    await message.answer("Когда это началось? Можете указать точную дату или примерно: «месяц назад», «неделю назад» и т.д.")


@dp.message(SessionStates.entering_onset)
async def handle_onset(message: Message, state: FSMContext):
    await state.update_data(onset=message.text)
    await state.set_state(SessionStates.entering_context)
    await message.answer("Что происходило в вашей жизни в тот момент?\n\n"
                         "Были ли стрессовые события, перемены, конфликты, потери?")


@dp.message(SessionStates.entering_context)
async def handle_context(message: Message, state: FSMContext):
    await state.update_data(context=message.text)
    await state.set_state(SessionStates.entering_psycho)
    await message.answer(
        "Теперь немного о вашем эмоциональном фоне.\n\n"
        "Вы бы назвали своё состояние скорее:\n"
        "— напряжённым\n"
        "— опустошённым\n"
        "— тревожным\n"
        "Или опишите своими словами."
    )


@dp.message(SessionStates.entering_psycho)
async def handle_psycho_state(message: Message, state: FSMContext):
    await state.update_data(psycho_state=message.text)
    await state.set_state(SessionStates.entering_life_events)
    await message.answer(
        "Были ли недавние перемены в вашей жизни?\n\n"
        "Переезд, развод, потеря близкого человека, увольнение, смена ролей?"
    )


@dp.message(SessionStates.entering_life_events)
async def handle_life_events(message: Message, state: FSMContext):
    await state.update_data(life_events=message.text)
    user_data = await state.get_data()

    await message.answer("🧠 Анализирую ваш запрос...")

    gpt_reply, follow_up = await generate_gpt_response(user_data)
    await state.update_data(gpt_reply=gpt_reply, follow_up=follow_up)

    await message.answer(gpt_reply)

    if follow_up:
        await message.answer(follow_up)

    await state.set_state(SessionStates.waiting_follow_up)


@dp.message(SessionStates.waiting_follow_up)
async def handle_follow_up_answer(message: Message, state: FSMContext):
    await state.update_data(follow_up_answer=message.text)
    await state.set_state(SessionStates.deep_question_1)
    await message.answer("Теперь немного глубже. Что изменилось в вашей жизни до появления симптома?")


@dp.message(SessionStates.deep_question_1)
async def handle_deep_q1(message: Message, state: FSMContext):
    await state.update_data(deep_q1=message.text)
    await state.set_state(SessionStates.deep_question_2)
    await message.answer("Есть ли ситуации, которые вызывают это же чувство — тревоги, обиды, стеснения?")

@dp.message(SessionStates.deep_question_2)
async def handle_deep_q2(message: Message, state: FSMContext):
    await state.update_data(deep_q2=message.text)
    await state.set_state(SessionStates.deep_question_3)
    await message.answer("Если бы ваш симптом был образом или эмоцией — что бы это было?")

@dp.message(SessionStates.deep_question_3)
async def handle_deep_q3(message: Message, state: FSMContext):
    await state.update_data(deep_q3=message.text)
    await state.set_state(SessionStates.deep_question_4)
    await message.answer("Когда вы в последний раз чувствовали, что не можете что-то «переварить», «удержать» или «выразить»?")

@dp.message(SessionStates.deep_question_4)
async def handle_deep_q4(message: Message, state: FSMContext):
    await state.update_data(deep_q4=message.text)
    user_data = await state.get_data()

    await message.answer("🧠 Обрабатываю ваши ответы...")
    gpt_reply = await generate_final_gpt_response(user_data)
    await message.answer(gpt_reply)

    consult_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧑‍⚕️ Перейти к консультации", url="http://tatishakirova.ru/")]
        ]
    )
    await message.answer("💬 Если хотите подробнее обсудить свои переживания, запишитесь на личную консультацию:", reply_markup=consult_markup)

    await state.set_state(SessionStates.post_recommendations)
    await message.answer(
        "Хотите сохранить свои ответы, чтобы вернуться к ним позже?\nИли попробовать поработать с другим симптомом?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💾 Сохранить сессию")],
                [KeyboardButton(text="🔄 Начать заново")]
            ],
            resize_keyboard=True
        )
    )



@dp.message(SessionStates.post_recommendations, F.text == "💾 Сохранить сессию")
async def save_user_session(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id
    gpt_reply = user_data.get("gpt_reply", "—")

    save_session(user_id, user_data, gpt_reply)

    await state.clear()
    await message.answer("✅ Сессия успешно сохранена. Вы всегда можете вернуться к ней позже.",
                         reply_markup=start_keyboard)  # ← вернули стартовое меню


@dp.message(F.text == "ℹ️ Что это за бот?")
async def about_bot(message: Message):
    await message.answer(
        "Этот бот помогает вам понять возможные психосоматические причины вашего самочувствия. "
        "Он не ставит диагнозов, но подсказывает, на что обратить внимание, основываясь на вашем физическом, эмоциональном и жизненном фоне."
    )

@dp.message(F.text == "🔒 Конфиденциальность")
async def privacy(message: Message):
    await message.answer(
        "Все введённые вами данные используются только для генерации ответа и не сохраняются без вашего согласия. "
        "Бот не заменяет врача. Вы всегда можете удалить свои данные."
    )

@dp.message(F.text == "/sessions")
async def show_sessions(message: Message):
    import sqlite3
    conn = sqlite3.connect("sessions.db")
    c = conn.cursor()
    c.execute("SELECT user_id, created_at, symptoms, psycho_state, gpt_reply FROM sessions ORDER BY created_at DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await message.answer("Пока нет сохранённых сессий.")
        return

    for row in rows:
        user_id, created_at, symptoms, psycho, gpt_reply = row


        try:
            user = await bot.get_chat(user_id)
            username = f"@{user.username}" if user.username else user.full_name
        except Exception:
            username = f"<code>{user_id}</code>"

        await message.answer(
            f"👤 Пользователь: {username}\n"
            f"🕒 Дата: {created_at}\n"
            f"📌 Симптомы: {symptoms or '-'}\n"
            f"🧠 Эмоц. фон: {psycho or '-'}\n\n"
            f"🧾 Ответ GPT:\n<blockquote>{gpt_reply or '-'}</blockquote>",
            parse_mode="HTML"
        )



@dp.message(F.text == "/вернуться")
async def restore_session(message: Message, state: FSMContext):
    user_id = message.from_user.id

    import sqlite3
    conn = sqlite3.connect("sessions.db")
    c = conn.cursor()
    c.execute("SELECT symptoms, onset, context, analyses, psycho_state, life_events, gpt_reply FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        await message.answer("❌ У вас пока нет сохранённых сессий.")
        return

    symptoms, onset, context, analyses, psycho_state, life_events, gpt_reply = row

    await message.answer("🔄 Вот ваша последняя сессия:")
    await message.answer(
        f"📌 Симптомы: {symptoms or '—'}\n"
        f"🕒 Когда началось: {onset or '—'}\n"
        f"⚙️ Контекст: {context or '—'}\n"
        f"📋 Анализы: {analyses or '—'}\n"
        f"🧠 Эмоц. фон: {psycho_state or '—'}\n"
        f"🌍 События: {life_events or '—'}\n\n"
        f"🧠 GPT-ответ:\n{gpt_reply or '—'}"
    )

    await message.answer(
        "🔁 Хотите продолжить с этой информацией или начать заново?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔄 Начать заново")],
            ],
            resize_keyboard=True
        )
    )

@dp.message(F.text == "🔄 Начать заново")
async def restart_session(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Начинаем заново.\n\n"
        "Какие симптомы беспокоят вас в первую очередь?\n"
        "Напишите ваш симптом в свободной форме.\n\n"
        "Примеры: головная боль, бессонница, тревожность, усталость и т.д.",
        reply_markup=start_keyboard
    )
    await state.set_state(SessionStates.entering_symptoms)




@dp.message(F.text == "/testpdf")
async def test_pdf(message: Message):
    from app.services.pdf_generator import generate_session_pdf
    from aiogram.types import FSInputFile
    import tempfile


    user_data = {
        "symptoms": "Головная боль",
        "onset": "2 недели назад",
        "context": "Смена работы, стресс",
        "analyses": "Анализ крови, МРТ",
        "analysis_details": "Гемоглобин в норме, МРТ чисто",
        "psycho_state": "Чувствую тревогу и упадок сил",
        "life_events": "Развод, переезд"
    }
    gpt_reply = "Похоже, ваше состояние связано со стрессом. Рекомендуется отдых, поддержка близких и консультация специалиста."


    pdf_bytes = generate_session_pdf(user_data, gpt_reply)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes.read())
        tmp_path = tmp_file.name

    await message.answer("📄 Вот тестовый PDF-отчёт:")
    await message.answer_document(FSInputFile(tmp_path, filename="test_session_report.pdf"))


@dp.message(SessionStates.entering_symptoms)
@dp.message(SessionStates.entering_onset)
@dp.message(SessionStates.entering_context)
@dp.message(SessionStates.entering_analyses)
@dp.message(SessionStates.analysis_details)
@dp.message(SessionStates.entering_psycho)
@dp.message(SessionStates.entering_life_events)
@dp.message(SessionStates.deep_question_1)
@dp.message(SessionStates.deep_question_2)
@dp.message(SessionStates.deep_question_3)
@dp.message(SessionStates.deep_question_4)
@dp.message(SessionStates.post_recommendations)
async def handle_unexpected_text(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, ответьте на вопрос, введя текст.")

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_db()
    asyncio.run(main())
