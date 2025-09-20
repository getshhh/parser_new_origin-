from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    # Generic
    setting_keywords = State()
    setting_minus_keywords = State()
    editing_keywords = State()
    editing_minus_keywords = State()

    # Kwork
    setting_price_min = State()
    setting_price_max = State()
    setting_kwork_interval = State()

    # Habr
    setting_habr_salary_min = State()
    setting_habr_salary_max = State()
    setting_habr_cities = State()
    setting_habr_interval = State()

    # FL
    setting_fl_price_min = State()
    setting_fl_price_max = State()
    setting_fl_interval = State()

    # Guru
    setting_guru_price_min = State()
    setting_guru_price_max = State()
    setting_guru_interval = State()

    # YouDo
    setting_youdo_price_min = State()
    setting_youdo_price_max = State()
    setting_youdo_interval = State()

    # VK
    vk_price_min = State()
    vk_price_max = State()
    vk_groups = State()
    vk_interval = State()
    
    # Weblancer
    weblancer_price_min = State()
    weblancer_price_max = State()
    weblancer_interval = State()
    
    # Workzilla
    workzilla_price_min = State()
    workzilla_price_max = State()
    workzilla_interval = State()
