import os
import asyncio
from typing import Optional, Tuple, List, Dict
from gigachat import GigaChat




def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) else default


def _make_client() -> GigaChat:
    key = _env("GIGA_AUTH_KEY") or _env("GIGACHAT_AUTH_KEY") or ""
    scope = _env("GIGA_SCOPE", "GIGACHAT_API_PERS")
    ca_bundle = _env("SSL_CERT_FILE", "russian_trusted_root_ca_pem.crt")
    if not key:
        raise RuntimeError("GIGA_AUTH_KEY is required (Authorization key from Sber Studio)")
    return GigaChat(
        credentials=key,
        scope=scope,
        ca_bundle_file=ca_bundle,
        verify_ssl_certs=True
    )


def _current_chat_model() -> str:
    return (
        _env("GIGA_CHAT_MODEL")
        or _env("GIGA_MODEL")
        or _env("GIGACHAT_MODEL")
        or "GigaChat"
    )




SYSTEM_PROMPT = """
Ты — внимательный и чуткий помощник по здоровью и самоощущению. Твоя задача — помогать человеку понять его состояние
с двух сторон: медицинской (куда обратиться, что проверить, какие вопросы задать врачу) и психоэмоциональной
(как стресс, переживания и внутренние конфликты могут отражаться в теле).

Рабочая рамка: опирайся на PNEI (психо-нейро-эндокрино-иммунные связи). Объясняй, как стресс и регуляция через нервную систему,
гормональные оси (например, HPA) и иммунитет могут влиять на симптомы. Не ставь диагнозы.

Политика:
— Не используй «Германскую новую медицину (ГНМ)» как медицинскую модель и не давай по ней рекомендаций.
  Если пользователь её упоминает, нейтрально отметь, что ГНМ не имеет научной валидности и не применяется в доказательной медицине.
  ГНМ-термины допустимы только как метафоры переживаний (образ/смысл), но медицинские выводы — строго в рамках PNEI/доказательного подхода.
— Избегай категоричности. Пиши простым текстом, без звёздочек, без жирного/курсива и без markdown.

Структура ответа (сохраняй заголовки и порядок):
1) Карта возможных причин
   Кратко и по делу: какие медицинские и какие психоэмоциональные механизмы могут объяснять проявления.
   Обязательно свяжи с рамкой PNEI (нервная регуляция, стресс-гормоны/сон/ритмы/иммунные реакции).

2) Что у вас совпадает
   Связка с рассказом пользователя: 2–4 точных наблюдения, какие детали поддерживают эти объяснения.

3) Куда обратиться
   К каким специалистам пойти сначала и почему. Базовые обследования/анализы, которые проясняют картину.
   Если есть понятный первичный маршрут — укажи его.

4) Красные флаги — срочно к врачу
   Симптомы/ситуации, при которых нужна немедленная помощь, с кратким объяснением.

5) Шаги самопомощи
   Простые действия на 1–2 недели: дыхательная практика (как делать, сколько минут),
   мягкая телесная поддержка/режим, 3 вопроса для дневника, короткая стабилизирующая привычка.
   Отрази PNEI-логику (сон/ритмы, нагрузка, питание, стресс-менеджмент).

6) Метафоры и образы симптома
   2–3 образа, помогающих почувствовать смысл реакции и говорить с собой своим языком.

7) Для разговора с врачом
   3–5 корректных вопросов/наблюдений, которые помогут на приёме, без постановки диагноза.

8) Итог и следующий шаг
   Одним абзацем: что главное вынести сейчас и какой первый шаг сделать.

В конце добавь строку:
❗ Это не медицинская консультация. При ухудшении состояния обратитесь к врачу.
""".strip()




def _sdk_chat_sync(messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> Dict:
    req = {"messages": messages, "model": model or _current_chat_model()}
    req.update(kwargs)
    with _make_client() as gc:
        resp = gc.chat(req)
        return {
            "choices": [
                {
                    "message": {
                        "content": resp.choices[0].message.content,
                        "role": resp.choices[0].message.role or "assistant",
                    }
                }
            ]
        }




def _split_answer_and_followup(text: str) -> Tuple[str, Optional[str]]:
    if "\n---\n" in text:
        a, b = text.split("\n---\n", 1)
        return a.strip(), (b.strip() or None)
    lines = text.strip().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        low = lines[i].lower()
        if low.startswith("вопрос:") or low.startswith("уточняющий вопрос:"):
            main = "\n".join(lines[:i]).strip()
            q = lines[i].split(":", 1)[1].strip() if ":" in lines[i] else lines[i].strip()
            return main, (q or None)
    return text.strip(), None




async def generate_gpt_response(user_data: dict) -> Tuple[str, Optional[str]]:
    diagnosis = user_data.get("diagnosis", "не указан")

    prompt = f"""
Пользователь рассказал о своём состоянии.
Диагноз: {diagnosis}
Симптомы: {user_data.get('symptoms')}
Когда началось: {user_data.get('onset')}
Контекст: {user_data.get('context')}
Анализы: {user_data.get('analyses')}
Детали анализов: {user_data.get('analysis_details')}
Эмоциональный фон: {user_data.get('psycho_state')}
Важные события: {user_data.get('life_events')}

Сформируй ответ строго в заданной структуре (8 разделов), без markdown и без звёздочек.
Используй рамку PNEI (нервная регуляция, стресс-гормоны/HPA, иммунитет, сон/ритмы).
Не используй ГНМ как медицинскую модель; если пользователь её упомянет — кратко отметь недоказанность и при желании
оставь только как метафору (без медицинских выводов).

В «Куда обратиться» предложи первичный маршрут и базовые обследования.
В «Красные флаги» укажи ситуации для срочной помощи. В конце добавь финальную строку-предупреждение.

Заверши ОДНИМ очень коротким уточняющим вопросом (до 12 слов) — на отдельной строке после разделителя
---
пример: «Что усиливает это ощущение чаще всего?».
""".strip()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",  "content": prompt},
    ]
    result = await asyncio.to_thread(_sdk_chat_sync, messages, None, temperature=0.6)
    content = result["choices"][0]["message"]["content"].strip()
    return _split_answer_and_followup(content)


async def generate_final_gpt_response(user_data: dict) -> str:
    prev_reply = (user_data.get("gpt_reply") or "").strip()

    prompt = f"""
Это продолжение консультации. Ниже — первый ответ помощника (для контекста), а затем — новые ответы пользователя.
Первый ответ (НЕ повторяй его, используй только как базу):
<<<ПЕРВЫЙ_ОТВЕТ
{prev_reply or '—'}
ПЕРВЫЙ_ОТВЕТ>>>

Новые ответы пользователя:
— Ответ на уточняющий вопрос: {user_data.get('follow_up_answer','—')}
— Что изменилось до симптома: {user_data.get('deep_q1','—')}
— Ситуации, где чувство сильнее: {user_data.get('deep_q2','—')}
— Образ/метафора симптома: {user_data.get('deep_q3','—')}
— Опыт «не смог(ла) переварить/удержать/выразить»: {user_data.get('deep_q4','—')}

Сделай обновлённый разбор в той же структуре, добавив в начале раздел «0) Дополнения к разбору» (3–6 пунктов: что изменилось по сравнению с первым ответом).
Опирайся на рамку PNEI. Не используй ГНМ как медицинскую модель; если она упомянута — максимум как метафора с явным предупреждением о недоказанности.
В «Куда обратиться» — чёткий маршрут и приоритетные обследования (зачем именно). В «Шаги самопомощи» — 2 дыхательные практики с длительностью,
1 мягкая телесная практика на 5–7 минут, 3 персонализированных вопроса для дневника. Если новые данные мало меняют выводы — скажи это явно.

В конце добавь строку:
❗ Это не медицинская консультация. При ухудшении состояния обратитесь к врачу.
""".strip()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ]
    result = await asyncio.to_thread(_sdk_chat_sync, messages, None, temperature=0.8)
    return result["choices"][0]["message"]["content"].strip()
