import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder


from zk_texts import ZK_TEXTS

from kch_texts import KCH_TEXTS

from arcane_types import get_arcane_type, get_adult_meaning

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_choice = {}


def reduce_to_22(number):
    while number > 22:
        number -= 22
    return number


def calculate_year_arcane(year):
    result = sum(int(digit) for digit in str(year))
    return reduce_to_22(result)


def calculate_comfort_zone(day, month, year):
    dt = reduce_to_22(day)
    mt = month
    gt = calculate_year_arcane(year)

    result = dt + 2 * mt + gt
    return reduce_to_22(result)



def calculate_partner_problem(day, month, year):
    dt = reduce_to_22(day)
    gt = calculate_year_arcane(year)

    result = abs(dt - gt)

    if result == 0:
        result = 22

    return result



def parse_birth_date(text):
    text = text.strip()

    if text.isdigit() and len(text) == 8:
        text = text[:2] + "." + text[2:4] + "." + text[4:]

    birth_date = datetime.strptime(text, "%d.%m.%Y")
    return birth_date.day, birth_date.month, birth_date.year


def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Зона комфорта для детей")
    kb.button(text="Проблемы в партнерстве")
    kb.button(text="Аркан Судьбы или Воли")
    kb.button(text="Выбрать другой расчёт")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Выберите расчет:",
        reply_markup=main_menu()
    )


@dp.message(F.text == "Выбрать другой расчёт")
async def choose_another(message: Message):
    user_choice.pop(message.from_user.id, None)

    await message.answer(
        "Выберите расчет:",
        reply_markup=main_menu()
    )


@dp.message(F.text.in_([
    "Зона комфорта для детей",
    "Проблемы в партнерстве",
    "Аркан Судьбы или Воли"
]))
async def choose_calculation(message: Message):
    user_choice[message.from_user.id] = message.text

    await message.answer(
        "Введите дату рождения.\n\n"
        "Можно так: 01.01.1999\n"
        "Или так: 01011999"
    )


@dp.message(F.text)
async def handle_date(message: Message):
    choice = user_choice.get(message.from_user.id)

    if not choice:
        await message.answer(
            "Сначала выберите расчет:",
            reply_markup=main_menu()
        )
        return

    try:
        day, month, year = parse_birth_date(message.text)
    except ValueError:
        await message.answer(
            "Ошибка. Введите дату правильно:\n"
            "20.05.1981 или 20051981"
        )
        return

    if choice == "Зона комфорта для детей":
        result = calculate_comfort_zone(day, month, year)

        text = ZK_TEXTS.get(
            result,
            "Для этого аркана пока нет расшифровки."
        )

        await message.answer(
            f"Зона комфорта для детей = {result}\n\n"
            f"{text}"
        )

    elif choice == "Проблемы в партнерстве":
        result = calculate_partner_problem(day, month, year)

        text = KCH_TEXTS.get(
            result,
            "Для этого аркана пока нет расшифровки."
        )

        await message.answer(
            f"Проблемы в партнёрстве / КЧХ = {result}\n\n"
            f"{text}"
        )

    elif choice == "Аркан Судьбы или Воли":
        zk = calculate_comfort_zone(day, month, year)
        arcane_type = get_arcane_type(zk)
        meaning = get_adult_meaning(arcane_type)

        await message.answer(
            f"ЗК = {zk}\n"
            f"Тип: {arcane_type}\n\n"
            f"{meaning}"
        )

    else:
        await message.answer("Этот расчет добавим следующим шагом.")

    user_choice.pop(message.from_user.id, None)

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())