from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    # Generic states
    setting_keywords = State()
    setting_minus_keywords = State()
    editing_keywords = State()
    editing_minus_keywords = State()
    setting_global_keywords = State()
    setting_price_min = State()
    setting_price_max = State()
    
    # Parser-specific states
    setting_vk_group_ids = State()
    setting_habr_cities = State()
