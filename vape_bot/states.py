# states.py
from aiogram.fsm.state import State, StatesGroup

class LiquidStates(StatesGroup):
    """Состояния для добавления жидкости"""
    name = State()
    flavor = State()
    strength = State()
    volume = State()
    image = State()