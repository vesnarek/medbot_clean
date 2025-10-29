from aiogram.fsm.state import StatesGroup, State

class SessionStates(StatesGroup):
    choosing_mode = State()               # стартовое меню
    entering_diagnosis = State()          # выбор диагноза
    entering_symptoms = State()           # симптомы
    entering_timing = State()             # когда началось (ошибка была тут)
    entering_onset = State()              # альтернативное название — тоже "когда началось"
    entering_context = State()            # что происходило в жизни
    entering_analyses = State()           # анализы (фото или текст)
    analysis_details = State()            # доп. детали по анализу
    entering_psycho = State()             # психоэмоциональное состояние
    entering_life_events = State()        # жизненные перемены
    post_recommendations = State()        # Сохранить / начать заново
    deep_question_1 = State()             # что изменилось в жизни до симптома?
    deep_question_2 = State()             # ситуации, вызывающие это чувство
    deep_question_3 = State()             # симптом как образ/эмоция
    deep_question_4 = State()             # не смог переварить/удержать/выразить
    waiting_follow_up = State()           # ожидание ответа на уточняющий вопрос
    final_analysis = State()              # финальный анализ, перед выдачей рекомендаций
    session_completed = State()           # завершение сессии, переход к рекомендациям
    review_session = State()              # обзор сохраненных данных перед завершением
    consultation_follow_up = State()      # дополнительные вопросы по консультации



