from aiogram.fsm.state import State, StatesGroup

class LiquidStates(StatesGroup):
    """Состояния для добавления жидкости"""
    name = State()
    flavor = State()
    strength = State()
    volume = State()
    price = State()  # Добавляем состояние для цены
    image = State()

class PurchaseStates(StatesGroup):
    """Состояния для покупки"""
    waiting_for_username = State()
    confirm_purchase = State()