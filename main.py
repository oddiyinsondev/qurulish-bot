from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import sqlite3
import logging
import openpyxl
import openpyxl
import os
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
import openpyxl
from config import BOT_TOKEN, admin, CHANNEL_ID, CHANNEL_URLS
from text import obuna, telefon_yuborish, goliblar

menyu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Mening hisobim 🗂")],
        [KeyboardButton(text="Maxsus linkim 🔗"), KeyboardButton(text="📊 Natijam (reyting)")],
    ],
    resize_keyboard=True
)






conn = sqlite3.connect("referral.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER,
    username TEXT,
    first_name TEXT,
    phone TEXT,
    is_subscribed INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

# === BOT SETUP ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# === STATES ===
class Register(StatesGroup):
    waiting_for_contact = State()

# === HANDLERS ===
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split(" ")
    referred_by = int(args[1]) if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id else None

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        username = message.from_user.username
        first_name = message.from_user.first_name
        cursor.execute("INSERT INTO users (user_id, referred_by, username, first_name) VALUES (?, ?, ?, ?)",
                       (user_id, referred_by, username, first_name))
        if referred_by:
            cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referred_by,))
        conn.commit()
    rasm = FSInputFile("image.png")
    member = await bot.get_chat_member(CHANNEL_ID, user_id)
    if member.status not in ["member", "creator", "administrator"]:
        markup = InlineKeyboardMarkup(inline_keyboard=[ 
            [InlineKeyboardButton(text="📢 Kanlaga qo'shilish", url=CHANNEL_URLS)],
            [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")]
        ])
        await message.answer_photo(photo=rasm, caption=obuna, reply_markup=markup)
        return

    contact_button = KeyboardButton(text="📱 Raqamni ulashish", request_contact=True)
    contact_markup = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True)
    await message.answer_photo(photo=rasm, caption=goliblar)
    await message.answer(text=telefon_yuborish, reply_markup=contact_markup)
    await state.set_state(Register.waiting_for_contact)





@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    rasm = FSInputFile("image.png")
    member = await bot.get_chat_member(CHANNEL_ID, user_id)
    if member.status not in ["member", "creator", "administrator"]:
        await callback.answer("Hali ham kanalga obuna bo'lmagansiz", show_alert=True)
    else:
        cursor.execute("UPDATE users SET is_subscribed = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        contact_button = KeyboardButton(text="📱 Raqamni ulashish", request_contact=True)
        contact_markup = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True)
        await callback.message.answer_photo(photo=rasm, caption=goliblar)
        await callback.message.answer(text=telefon_yuborish, reply_markup=contact_markup)
        await state.set_state(Register.waiting_for_contact)





@dp.message(Register.waiting_for_contact, F.contact)
async def save_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    conn.commit()

    referral_link = f"https://t.me/BuildAndWinBot?start={user_id}"
    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    ref_count = cursor.fetchone()[0]

    await message.answer(f"<b>✅ Rahmat! Sizning referal linkingiz:</b>\n{referral_link}\n\nTaklif qilgan do'stlaringiz soni: <b>{ref_count}</b>", reply_markup=menyu)



@dp.message(F.text == "Mening hisobim 🗂")
async def my_account(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    count = result[0] if result else 0
    await message.answer(f"Siz <b>{count}</b> ta tanishingizni taklif qilgansiz. Yana 10 ta do‘stingizni taklif qilib, 10 ta elektron pech o‘ynaladigan o‘yinga qo‘shiling!", reply_markup=menyu)


@dp.message(F.text == "Maxsus linkim 🔗")
async def MaxsuslinkimBot(message: Message):
    rasm = FSInputFile("Image5.jpg")
    user_id = message.from_user.id
    referral_link = f"https://t.me/BuildAndWinBot?start={user_id}"
    text = """Baxt Buildings qurilish kompaniyasining Namangan shaxrida qurilayotgan “BAXT CITY” loyihasi onlayn taqdimot kanalga qo’shiling va 10 ta Muzlatgich, 10 ta pilisos, 10 ta televizor, 10 ta to’k pech va eng asosiysi Baxt citydan 1 ta 2 xonali  xonadon shu sovg'alardan birini yutib oling 🎁
        
Konkursda qatnashish uchun quyidagi havola orqali o'ting 👇👇👇"""
    await message.answer_photo(photo="https://immo.uz/_ipx/f_webp/https://main.immo.uz/uploads/products/2238c23ba5c7e555c4f86b723d2aa393.jpg", caption=f"{text}\n\n\n{referral_link}")
    await message.answer(text="""👆👆👆 Bu postda sizning shaxsiy linkingiz joylashgan
        
    Yuqoridagi postni yaqinlaringizga tarqating, ular sizning linkingizni bosib botga start berishi va telegram kanalga obuna bo’lishi kerak.""", reply_markup=menyu)


@dp.message(F.text == "📊 Natijam (reyting)")
async def show_top_referrals(message: Message):
    user_id = message.from_user.id

    cursor.execute("""
        SELECT user_id, first_name, referrals
        FROM users
        WHERE referrals > 0
        ORDER BY referrals DESC
    """)
    users = cursor.fetchall()

    top_text = "<b>🏆 Referallar reytingi (TOP 25):</b>\n"
    for i, user in enumerate(users[:25], 1):
        top_text += f"{i}. {user[1]}  —  {user[2]} ta a'zo qo‘shgan\n"

    user_rank = next((i + 1 for i, u in enumerate(users) if u[0] == user_id), None)

    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    my_referrals = result[0] if result else 0

    if user_rank:
        top_text += f"\n📌 Sizning o‘rningiz: <b>{user_rank}</b> — {my_referrals} ta a'zo qo‘shgansiz"
    else:
        top_text += "\n❗️Siz hali hech kimni taklif qilmagansiz."

    await message.answer(top_text)





@dp.message(F.text == "/obunachilar", F.from_user.id.in_(admin))
async def show_stats(message: Message):
    if message.from_user.id not in admin:
        return await message.answer("Kechirasiz, bu buyruq faqat adminlar uchun.")

    # Statistika olish
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1")
    subscribed_users = cursor.fetchone()[0]

    cursor.execute("SELECT referred_by, COUNT(*) FROM users WHERE is_subscribed = 1 AND referred_by IS NOT NULL GROUP BY referred_by")
    ref_stats = cursor.fetchall()

    # Excel fayl yaratish
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"
    ws.append(["User ID", "Username", "First Name", "Phone", "Referrals", "Subscribed"])

    cursor.execute("SELECT user_id, username, first_name, phone, referrals, is_subscribed FROM users")
    for row in cursor.fetchall():
        ws.append(row)

    filename = "statistika.xlsx"
    wb.save(filename)
    document = FSInputFile(filename)

    # Statistika xabari
    text = (
        "<b>📊 Statistika</b>\n"
        f"👥 Botdan foydalanuvchilar: <b>{total_users}</b>\n"
        f"📢 Kanalga obuna bo‘lganlar: <b>{subscribed_users}</b>"
    )
    await message.answer(text)
    await message.answer_document(document=document, caption="📎 Excel fayl")

    os.remove(filename)

class ReklamaState(StatesGroup):
    waiting_for_post = State()

    
@dp.message(F.text == "/reklama", F.from_user.id.in_(admin))
async def start_reklama(message: Message, state: FSMContext):
    await message.answer("✉️ Iltimos, reklama postini yuboring.")
    await state.set_state(ReklamaState.waiting_for_post)

@dp.message(ReklamaState.waiting_for_post, F.from_user.id.in_(admin))
async def handle_full_post(message: Message, state: FSMContext):
    await state.clear()

    # Progressni ko‘rsatish
    progress_msg = await message.answer("🚀 Reklama yuborilmoqda, iltimos kuting...")

    # HAMMA foydalanuvchilar (obuna bo‘lmaganlar ham)
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]

    success = 0
    fail = 0

    for user_id in users:
        # Adminlarga yubormaymiz
        if user_id in admin or user_id == message.from_user.id:
            continue

        try:
            await bot.copy_message(chat_id=user_id,
                                   from_chat_id=message.chat.id,
                                   message_id=message.message_id)
            success += 1
        except Exception:
            fail += 1

    # Yuborilmoqda xabarini o‘chirish
    await bot.delete_message(chat_id=message.chat.id, message_id=progress_msg.message_id)

    # Natija
    await message.answer(
        f"✅ Sizning postingiz *barcha foydalanuvchilarga* tarqatildi!\n"
        f"Yuborildi: {success} ta\n"
        f"Yuborilmadi: {fail} ta",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    try:
        asyncio.run(dp.start_polling(bot))
    except:
        print("tugadi")