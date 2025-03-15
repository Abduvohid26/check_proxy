from aiogram.filters import Command
from loader import dp, db
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
import asyncio
import aiohttp

PROXY_USER = "jkboomba"
PROXY_PASS = "ZVujI2aGhy"
PROXY_PORT = "50100"

class CheckLink(StatesGroup):
    start = State()

@dp.callback_query(F.data == "check_all")
async def check_proxies(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text="🔗 Youtube link yuboring:")
    await state.set_state(CheckLink.start)

@dp.message(CheckLink.start)
async def check_all_proxies(message: types.Message, state: FSMContext):
    if not message.text.startswith("http"):
        await message.answer("❌ Iltimos, to‘g‘ri link yuboring.")
        return

    url = message.text
    proxies = db.select_all_proxies()  # [(1, "179.60.183.97"), (2, "203.113.0.13"), ...]

    if not proxies:
        await message.answer("❌ Ma'lumotlar bazasida proxy serverlar topilmadi.")
        return

    await message.answer("🔍 Proxy serverlar tekshirilmoqda...")

    success_proxies = []
    failed_proxies = []

    async def check_proxy(proxy_id, proxy_ip):
        """Berilgan proxy orqali URL ni sinash"""
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy_ip}:{PROXY_PORT}"  # Proxy format
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=proxy_url, timeout=10) as response:
                    if response.status == 200:
                        return proxy_id, proxy_ip, True, None  # Muvaffaqiyatli
                    else:
                        return proxy_id, proxy_ip, False, f"Xatolik: {response.status}"
        except Exception as e:
            return proxy_id, proxy_ip, False, str(e)  # Xatolik

    tasks = [check_proxy(proxy[0], proxy[1]) for proxy in proxies]  # ID va IP-larni olamiz
    results = await asyncio.gather(*tasks)

    for proxy_id, proxy_ip, is_success, error in results:
        if is_success:
            success_proxies.append((proxy_id, proxy_ip))
        else:
            failed_proxies.append((proxy_id, proxy_ip, error))

    result_message = "✅ **Muvaffaqiyatli proxy serverlar:**\n"
    for proxy_id, proxy in success_proxies:
        result_message += f"- `{proxy_id}: {proxy}:{PROXY_PORT}`\n"

    result_message += "\n❌ **Ishlamagan proxy serverlar:**\n"
    for proxy_id, proxy, error in failed_proxies:
        result_message += f"- `{proxy_id}: {proxy}:{PROXY_PORT}`: {error}\n"

    await message.answer(result_message, parse_mode=ParseMode.MARKDOWN)
    await state.clear()



class DeleteProxy(StatesGroup):
    start = State()

@dp.callback_query(F.data == "delete_proxy")
async def delete_proxy_prompt(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🗑 Proxy ID ni kiriting:")
    await state.set_state(DeleteProxy.start)


@dp.message(DeleteProxy.start)
async def process_delete_proxy(message: types.Message, state: FSMContext):
    proxy_id = message.text.strip()

    if not proxy_id.isdigit():
        await message.answer("❌ Noto‘g‘ri format! Iltimos, faqat ID raqamini kiriting.")
        return

    proxy_id = int(proxy_id)

    if not db.select_proxy(id=proxy_id): 
        await message.answer(f"❌ ID {proxy_id} ga ega proxy topilmadi!")
        return

    try:
        db.delete_proxy(id=proxy_id)  
        await message.answer(f"✅ Proxy o‘chirildi: ID {proxy_id}")
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()  