import asyncio
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from zk_texts import ZK_TEXTS
from kch_texts import KCH_TEXTS
from arcane_types import get_arcane_type, get_adult_meaning


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

ADMIN_ID = 387254782

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_choice = {}
users = set()
calculations_count = 0


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


START_TEXT = """✨ Если бы ваша жизнь стала книгой, как бы назывались её главы? ✨

У каждого человека есть своя уникальная история: таланты, судьбоносные повороты, сильные стороны, скрытые возможности и жизненные уроки.

📖 На основе вашей даты рождения я создам для вас бесплатное нумерологическое предисловие к книге вашей жизни и покажу первые главы будущего оглавления.

Сейчас для вас доступны первые разделы:

✅ Зона комфорта для детей
Узнайте, в какой среде ребёнок чувствует себя счастливым, уверенным и раскрывает свои лучшие качества.

✅ Проблемы в партнёрстве
Помогает увидеть основные уроки и сложности, которые могут проявляться в отношениях.

✅ Аркан Судьбы или Аркан Воли
Показывает, какими энергиями вы живёте.

🎁 Следите за обновлениями! Каждую неделю Книга Жизни будет дополняться новыми разделами, позволяя глубже понять себя, свои таланты, задачи и возможности.

Выберите интересующий расчёт в меню ниже и начните своё путешествие по страницам собственной истории.

✨ Возможно, самая интересная книга, которую вы когда-либо читали, — это книга о вас самих.
"""


@dp.message(CommandStart())
async def start(message: Message):
    users.add(message.from_user.id)

    await message.answer(
        START_TEXT,
        reply_markup=main_menu()
    )


@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "📊 Админ-панель\n\n"
        f"👥 Пользователей за время работы: {len(users)}\n"
        f"🧮 Расчётов за время работы: {calculations_count}"
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
    if message.from_user.id in user_choice:
        await message.answer(
            "Вы уже выбрали расчёт.\n\n"
            "Введите дату рождения, чтобы продолжить:\n\n"
            "Можно так: 01.01.1989\n"
            "Или так: 01011989\n\n"
            "Или нажмите «Выбрать другой расчёт»."
        )
        return

    user_choice[message.from_user.id] = message.text

    await message.answer(
        "Введите дату рождения.\n\n"
        "Можно так: 01.01.1989\n"
        "Или так: 01011989"
    )


@dp.message(F.text)
async def handle_date(message: Message):
    global calculations_count

    users.add(message.from_user.id)
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
            "01.01.1970 или 01011970"
        )
        return

    if choice == "Зона комфорта для детей":
        result = calculate_comfort_zone(day, month, year)
        text = ZK_TEXTS.get(result, "Для этого аркана пока нет расшифровки.")

        await message.answer(
            f"Зона комфорта для детей = {result}\n\n"
            f"{text}"
        )

    elif choice == "Проблемы в партнерстве":
        result = calculate_partner_problem(day, month, year)
        text = KCH_TEXTS.get(result, "Для этого аркана пока нет расшифровки.")

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

    calculations_count += 1
    user_choice.pop(message.from_user.id, None)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
