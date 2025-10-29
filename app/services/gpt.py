import os
import asyncio
from typing import Optional, Tuple, List, Dict
from openai import OpenAI

import httpx, certifi

def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) else default

def _make_client() -> OpenAI:
    key = _env("OPENAI_API_KEY") or ""
    base_url = _env("OPENAI_BASE") or _env("OPENAI_API_BASE")
    org = _env("OPENAI_ORG") or _env("OPENAI_ORGANIZATION")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required")

    http = httpx.Client(
        verify=certifi.where(),
        timeout=httpx.Timeout(30.0, connect=10.0, read=30.0),
    )
    return OpenAI(api_key=key, base_url=base_url, organization=org, http_client=http)

def _current_chat_model() -> str:
    return (
        _env("OPENAI_MODEL")
        or _env("OPENAI_CHAT_MODEL")
        or "gpt-4o"
    )

def _sdk_chat_sync(messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> Dict:
    req_model = model or _current_chat_model()
    temperature = float(kwargs.get("temperature", _env("OPENAI_TEMPERATURE", "0.7")))
    max_tokens = kwargs.get("max_tokens")

    last_err = None
    for _ in range(3):
        try:
            with _make_client() as client:
                resp = client.chat.completions.create(
                    model=req_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            return {
                "choices": [{
                    "message": {
                        "content": resp.choices[0].message.content,
                        "role": resp.choices[0].message.role or "assistant",
                    }
                }]
            }
        except Exception as e:
            last_err = e
    raise last_err



SYSTEM_PROMPT = """
Ты — внимательный и чуткий помощник по здоровью и самоощущению. Твоя задача — помогать человеку понять его состояние
с двух сторон: медицинской (куда обратиться, что проверить, какие вопросы задать врачу) и психоэмоциональной
(как стресс, переживания и внутренние конфликты могут отражаться в теле).

Тон: тёплый, поддерживающий, без категоричных утверждений и постановки диагнозов. Пиши чистым текстом, без звёздочек,
без жирного/курсива и без markdown. Будь конкретным и практичным.

Структура ответа (сохраняй заголовки и порядок):
1) Карта возможных причин
   Кратко и по делу: какие медицинские и какие психоэмоциональные механизмы могут объяснять описанные проявления.
   Дай несколько вариантов, если данных мало.

2) Что у вас совпадает
   Сделай связку с рассказом пользователя: укажи, какие детали его истории поддерживают те или иные объяснения.

3) Куда обратиться
   Подскажи, к каким специалистам имеет смысл пойти сначала и почему. Приведи пример базовых обследований/анализов,
   которые обычно помогают прояснить картину. Если есть понятный первичный маршрут — укажи его.

4) Красные флаги — срочно к врачу
   Перечисли симптомы и ситуации, при которых важно немедленно обратиться за медицинской помощью.
   Не запугивай, просто поясни, почему это важно.

5) Шаги самопомощи
   Дай простые действия на ближайшие 1–2 недели: краткая дыхательная практика (как делать и сколько минут),
   мягкая телесная поддержка/режим, идеи для дневника/рефлексии (3 вопроса), короткая привычка для стабилизации.

6) Метафоры и образы симптома
   Дай 2–3 образа, которые помогают почувствовать смысл телесной реакции и найти свой язык для разговора с собой.

7) Для разговора с врачом
   Сформулируй 3–5 корректных вопросов/наблюдений, которые помогут на приёме, без постановки диагноза.

8) Итог и следующий шаг
   Одним абзацем: что главное вынести сейчас и какой первый шаг сделать.

В конце добавь строку:
❗ Это не медицинская консультация. При ухудшении состояния обратитесь к врачу.
""".strip()




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
В каждом разделе будь конкретным и практичным. В разделе «Куда обратиться» предложи первичный маршрут и базовые обследования.
В разделе «Красные флаги» укажи ситуации, когда нужна срочная помощь. В конце добавь обязательную финальную строку-предупреждение.
Заверши одним коротким уточняющим вопросом на отдельной строке после разделителя \n---\n.
""".strip()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = await asyncio.to_thread(_sdk_chat_sync, messages, None)
    content = result["choices"][0]["message"]["content"].strip()
    return _split_answer_and_followup(content)


async def generate_final_gpt_response(user_data: dict) -> str:
    prompt = f"""
Дополнительные ответы пользователя.
Ответ на уточняющий вопрос: {user_data.get('follow_up_answer', '—')}
Что изменилось до симптома: {user_data.get('deep_q1')}
Ситуации, где чувство сильнее: {user_data.get('deep_q2')}
Образ/метафора симптома: {user_data.get('deep_q3')}
Опыт «не смог(ла) переварить/удержать/выразить»: {user_data.get('deep_q4')}

Сформируй итоговый ответ строго в той же структуре (8 разделов), без markdown и без звёздочек.
Усиль практичность:
- в «Куда обратиться» уточни маршрут (к кому сперва, что уточнить) и базовые обследования по симптомам;
- в «Красные флаги» перечисли ситуации для срочной помощи;
- в «Шаги самопомощи» добавь две дыхательные практики с длительностью, одну мягкую телесную практику на 5–7 минут и 3 вопроса для дневника;
- в «Для разговора с врачом» сформулируй 3–5 конкретных вопросов.
Закончить обязательной строкой-предупреждением.
""".strip()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = await asyncio.to_thread(_sdk_chat_sync, messages, None)
    return result["choices"][0]["message"]["content"].strip()
