from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    waiting_text = State()
