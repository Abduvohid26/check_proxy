from aiogram.filters import CommandStart, Command
from loader import dp, bot, db
from aiogram import types, F
import aiohttp
import re
from filters.my_filter import YouTubeLinkFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile
from aiogram.enums import ChatAction
import os

class ProxyAdd(StatesGroup):
    start = State()
    end = State()


@dp.callback_query(F.data == "proxies_data")
async def start_proxies(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    btn = InlineKeyboardBuilder()
    proxies_btn = InlineKeyboardBuilder()
    btn.button(text="Proxy Qo'shish", callback_data="proxy_add")
    proxies = db.select_all_proxies()
    if not proxies:
        await call.message.answer(text=f"Proxies Mavjud emas", reply_markup=btn.as_markup())
        await state.set_state(ProxyAdd.start)
        return
    for proxy in proxies:
        proxies_btn.button(text=f"ID: [ {proxy[0]} ] {proxy[1]}", callback_data=f"id_{proxy[0]}")
    proxies_btn.adjust(2)
    await call.message.answer(text=f"Proxies", reply_markup=proxies_btn.as_markup())


    
@dp.callback_query(F.data == "proxy_add", ProxyAdd.start)
async def add_proxy(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(text="Proxy ip ni kiriting:")
    await state.set_state(ProxyAdd.end)

@dp.message(ProxyAdd.end)
async def get_and_save_proxy(msg: types.Message, state: FSMContext):
    proxy = msg.text.strip()

    if not proxy:
        await msg.answer("⚠️ Iltimos, proxy IP-ni yuboring!")
        return

    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', proxy)
    if not match:
        await msg.answer("❌ Noto‘g‘ri format! Iltimos, faqat IP manzil yuboring.")
        return

    proxy_ip = match.group(1) 

    if db.select_proxy(proxy=proxy_ip):
        await msg.answer(f"❌ Bu proxy ({proxy_ip}) allaqachon bazada mavjud!")
        return

    db.add_proxy(proxy=proxy_ip)
    btn = InlineKeyboardBuilder()
    btn.button(text="Proxy Qo'shish", callback_data="proxy_add")
    await msg.answer(f"✅ Proxy qo'shildi: `{proxy_ip}`", parse_mode="Markdown", reply_markup=btn.as_markup())
    await state.clear()