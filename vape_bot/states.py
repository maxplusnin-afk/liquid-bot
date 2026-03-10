from aiogram.fsm.state import State, StatesGroup

class BrandStates(StatesGroup):
    """Состояния для добавления бренда"""
    name = State()
    image = State()

class LiquidStates(StatesGroup):
    """Состояния для добавления жидкости"""
    brand_id = State()
    name = State()
    flavor = State()
    strength = State()
    price = State()

class PurchaseStates(StatesGroup):
    """Состояния для покупки"""
    waiting_for_username = State()
    confirm_purchase = State()