from aiogram.filters import CommandStart, Command
from loader import dp, bot
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
from .proxies import ProxyAdd

RAPID_API_KEY = "54e518fa11msha164dc2cecb21c8p18d479jsn65ee0a8c6b70"
RAPID_API_HOST = "youtube-media-downloader.p.rapidapi.com"

# Proxy ma'lumotlari
PROXY_USER = "jkboomba"  
PROXY_PASS = "ZVujI2aGhy"  
PROXY_IP = "64.113.1.138"  
PROXY_PORT = "50100"  
PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}"


@dp.message(CommandStart())
async def start_bot(message:types.Message, state: FSMContext):
    btn = InlineKeyboardBuilder()
    btn.button(text="Proxies", callback_data="proxies_data")
    btn.button(text="Proxy Qo'shish", callback_data="proxy_add")
    btn.button(text="O'chirish", callback_data="delete_proxy")
    btn.button(text="Tekshirish", callback_data="check_all")
    btn.adjust(2)
    await message.answer(f"Assalomu alaykum {message.from_user.full_name}!", reply_markup=btn.as_markup())
    await state.set_state(ProxyAdd.start)

class WSTATE(StatesGroup):
    start = State()
    end = State()

def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)    
    return match.group(1) if match else None

@dp.message(YouTubeLinkFilter())
async def get_video(message: types.Message, state: FSMContext):
    youtube_url = message.text.strip()
    video_id = extract_video_id(youtube_url)
    api_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_API_HOST
    }
    params = {"videoId": video_id}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            api_url, 
            headers=headers, 
            params=params,
            proxy=PROXY_URL
        ) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    btn = InlineKeyboardBuilder()
                    btn.button(text="Video", callback_data="video_download")  # Typo tuzatildi
                    btn.button(text="Audio", callback_data="audio_download")
                    btn.adjust(2)
                    await message.answer_photo(data["thumbnails"][-1]["url"], reply_markup=btn.as_markup())
                    await state.update_data({
                        "video_url": data["videos"]["items"][-1]["url"],
                        "audio_url": data["audios"]["items"][-1]["url"]
                    })
                    await state.set_state(WSTATE.start)
                except (KeyError, IndexError):
                    await message.answer("❌ Yuklab olish havolasi topilmadi.")
            else:
                await message.answer(f"❌ Xatolik yuz berdi: {response.status}")

@dp.callback_query(F.data == "audio_download", WSTATE.start)
async def get_audio(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    data = await state.get_data()
    audio_url = data.get("audio_url")
    
    if not audio_url:
        await call.message.answer("❌ Audio havolasi topilmadi.")
        return

    await bot.send_chat_action(chat_id=call.message.chat.id, action=ChatAction.UPLOAD_VOICE)
    await call.message.answer(text="Audio Yuklanmoqda kuting....")

    audio_path = f"audios_yt/{call.from_user.id}_audio.mp3"
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                audio_url,
                proxy=PROXY_URL  
            ) as response:
                print(response.status, response.text)
                if response.status == 200:
                    with open(audio_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(1024):
                            f.write(chunk)
                    
                    await call.message.answer_audio(audio=FSInputFile(audio_path))
                else:
                    await call.message.answer("❌ Audio yuklab olinmadi.")
    except aiohttp.ClientHttpProxyError:
        await call.message.answer("❌ Proxy serverga ulanib bo'lmadi. Iltimos, keyinroq urinib ko'ring.")
    except aiohttp.ClientConnectorError:
        await call.message.answer("❌ Proxy serverga ulanib bo'lmadi. Iltimos, keyinroq urinib ko'ring.")
    except TimeoutError:
        await call.message.answer("❌ Vaqt tugadi. Iltimos, keyinroq urinib ko'ring.")
    except Exception as e:
        await call.message.answer(f"❌ Kutilmagan xatolik: {e}")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    await state.clear()

@dp.callback_query(F.data == "video_download", WSTATE.start)
async def get_video(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=60)
    data = await state.get_data()
    video_url = data.get("video_url")
    
    if not video_url:
        await call.message.answer("❌ Video havolasi topilmadi.")
        return

    await bot.send_chat_action(chat_id=call.message.chat.id, action=ChatAction.UPLOAD_VIDEO)
    await call.message.answer(text="Video Yuklanmoqda kuting....")
    video_path = f"videos_yt/{call.from_user.id}_video.mp4"
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                video_url,
                proxy=PROXY_URL  
            ) as response:
                if response.status == 200:
                    with open(video_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(1024):
                            f.write(chunk)
                    
                    await call.message.answer_video(video=FSInputFile(video_path))
                else:
                    await call.message.answer("❌ Video yuklab olinmadi.")
    except aiohttp.ClientHttpProxyError:
        await call.message.answer("❌ Proxy serverga ulanib bo'lmadi. Iltimos, keyinroq urinib ko'ring.")
    except aiohttp.ClientConnectorError:
        await call.message.answer("❌ Proxy serverga ulanib bo'lmadi. Iltimos, keyinroq urinib ko'ring.")
    except TimeoutError:
        await call.message.answer("❌ Vaqt tugadi. Iltimos, keyinroq urinib ko'ring.")
    except Exception as e:
        await call.message.answer(f"❌ Kutilmagan xatolik: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
    
    await state.clear()