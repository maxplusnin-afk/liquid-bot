from aiogram.fsm.state import State, StatesGroup

class BrandStates(StatesGroup):
    name = State()
    photo = State()

class ProductStates(StatesGroup):
    brand_id = State()
    name = State()
    flavor = State()
    strength = State()
    price = State()
    edit_id = State()
    edit_field = State()
    edit_value = State()

class OrderStates(StatesGroup):
    username = State()