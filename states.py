from aiogram.fsm.state import State, StatesGroup

class CategoryStates(StatesGroup):
    name = State()

class ProductStates(StatesGroup):
    category_id = State()
    name = State()
    flavor = State()
    strength = State()
    photo = State()
    edit_id = State()
    edit_field = State()
    edit_value = State()