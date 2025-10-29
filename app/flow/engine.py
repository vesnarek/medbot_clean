from typing import Dict, Tuple, Optional

S_ENTER_DIAGNOSIS      = "entering_diagnosis"
S_ENTER_ANALYSES       = "entering_analyses"
S_ENTER_SYMPTOMS       = "entering_symptoms"
S_ENTER_ONSET          = "entering_onset"
S_ENTER_CONTEXT        = "entering_context"
S_ENTER_PSYCHO         = "entering_psycho"
S_ENTER_LIFE_EVENTS    = "entering_life_events"
S_WAIT_FOLLOWUP        = "waiting_follow_up"
S_DEEP_Q1              = "deep_question_1"
S_DEEP_Q2              = "deep_question_2"
S_DEEP_Q3              = "deep_question_3"
S_DEEP_Q4              = "deep_question_4"
S_DONE                 = "done"

PROMPTS: Dict[str, str] = {
    S_ENTER_DIAGNOSIS: (
        "Есть ли у вас диагноз, который вы бы хотели обсудить?\n\n"
        "Если да, опишите его, или напишите «нет», если диагноза нет."
    ),
    S_ENTER_ANALYSES: (
        "Хорошо, давайте перейдем к анализам.\n\n"
        "Есть ли у вас анализы? 📄\n"
        "— Вы можете прислать фото\n"
        "— Или ввести текстом (например: «Гемоглобин — 130, Сахар — 5.4»)\n\n"
        "Если у вас нет анализов, просто напишите «нет».\n\n"
        "Также, пожалуйста, укажите дату, когда были сданы анализы."
    ),
    S_ENTER_SYMPTOMS: (
        "Теперь давайте поговорим о симптомах.\n\n"
        "Какие симптомы беспокоят вас в первую очередь?\n"
        "Примеры: головная боль, бессонница, тревожность, усталость, боль в животе и т.д.\n"
        "Напишите ваш симптом в свободной форме."
    ),
    S_ENTER_ONSET: "Когда это началось? Можете указать точную дату или примерно: «месяц назад», «неделю назад» и т.д.",
    S_ENTER_CONTEXT: (
        "Что происходило в вашей жизни в тот момент?\n\n"
        "Были ли стрессовые события, перемены, конфликты, потери?"
    ),
    S_ENTER_PSYCHO: (
        "Теперь немного о вашем эмоциональном фоне.\n\n"
        "Вы бы назвали своё состояние скорее:\n"
        "— напряжённым\n"
        "— опустошённым\n"
        "— тревожным\n"
        "Или опишите своими словами."
    ),
    S_ENTER_LIFE_EVENTS: (
        "Были ли недавние перемены в вашей жизни?\n\n"
        "Переезд, развод, потеря близкого человека, увольнение, смена ролей?"
    ),
    S_DEEP_Q1: "Теперь немного глубже. Что изменилось в вашей жизни до появления симптома?",
    S_DEEP_Q2: "Есть ли ситуации, которые вызывают это же чувство — тревоги, обиды, стеснения?",
    S_DEEP_Q3: "Если бы ваш симптом был образом или эмоцией — что бы это было?",
    S_DEEP_Q4: "Когда вы в последний раз чувствовали, что не можете что-то «переварить», «удержать» или «выразить»?",
}

def start_session() -> Tuple[str, str, Dict]:
    state = S_ENTER_DIAGNOSIS
    return state, PROMPTS[state], {}

def step(state: str, message: str, data: Dict) -> Tuple[str, str, Dict, Optional[str]]:
    msg = (message or "").strip()

    if state == S_ENTER_DIAGNOSIS:
        data["diagnosis"] = msg.lower()
        return S_ENTER_ANALYSES, PROMPTS[S_ENTER_ANALYSES], data, None

    if state == S_ENTER_ANALYSES:
        data["analyses"] = msg if msg else "нет"
        return S_ENTER_SYMPTOMS, PROMPTS[S_ENTER_SYMPTOMS], data, None

    if state == S_ENTER_SYMPTOMS:
        data["symptoms"] = msg
        return S_ENTER_ONSET, PROMPTS[S_ENTER_ONSET], data, None

    if state == S_ENTER_ONSET:
        data["onset"] = msg
        return S_ENTER_CONTEXT, PROMPTS[S_ENTER_CONTEXT], data, None

    if state == S_ENTER_CONTEXT:
        data["context"] = msg
        return S_ENTER_PSYCHO, PROMPTS[S_ENTER_PSYCHO], data, None

    if state == S_ENTER_PSYCHO:
        data["psycho_state"] = msg
        return S_ENTER_LIFE_EVENTS, PROMPTS[S_ENTER_LIFE_EVENTS], data, None

    if state == S_ENTER_LIFE_EVENTS:
        data["life_events"] = msg
        return S_WAIT_FOLLOWUP, "", data, "DO_GPT1"

    if state == S_WAIT_FOLLOWUP:
        data["follow_up_answer"] = msg
        return S_DEEP_Q1, PROMPTS[S_DEEP_Q1], data, None

    if state == S_DEEP_Q1:
        data["deep_q1"] = msg
        return S_DEEP_Q2, PROMPTS[S_DEEP_Q2], data, None

    if state == S_DEEP_Q2:
        data["deep_q2"] = msg
        return S_DEEP_Q3, PROMPTS[S_DEEP_Q3], data, None

    if state == S_DEEP_Q3:
        data["deep_q3"] = msg
        return S_DEEP_Q4, PROMPTS[S_DEEP_Q4], data, None

    if state == S_DEEP_Q4:
        data["deep_q4"] = msg
        return S_DONE, "", data, "DO_GPT_FINAL"

    return S_ENTER_DIAGNOSIS, PROMPTS[S_ENTER_DIAGNOSIS], data, None
