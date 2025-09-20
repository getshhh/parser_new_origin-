from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    setting_keywords = State()
    setting_minus_words = State()
    setting_price_min = State()
    setting_price_max = State()

    # Kwork
    setting_kwork_interval = State()

    # Habr
    setting_habr_cities = State()
    setting_habr_interval = State()

    # FL
    setting_fl_interval = State()

    # Guru
    setting_guru_interval = State()

    # YouDo
    setting_youdo_interval = State()

    # VK
    vk_groups = State()
    vk_interval = State()
    
    # Weblancer
    weblancer_interval = State()
    
    # Workzilla
    workzilla_interval = State()
