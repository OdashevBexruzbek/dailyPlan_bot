# Keep alive for 24/7 hosting (Replit, Glitch, etc.)
try:
    from keep_alive import keep_alive
    USE_KEEP_ALIVE = True
except ImportError:
    USE_KEEP_ALIVE = False

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Bot tokenini environment variable dan olish (server uchun xavfsiz)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8114466152:AAFlw1NuzjpV3r4NE35QYFUhj1xx9Om2xiY')

# ADMIN TELEGRAM ID - O'Z ID INGIZNI KIRITING!
# ID ni olish uchun botga /myid yuboring
ADMIN_ID = int(os.getenv('ADMIN_ID', '123456789'))  # BU YERGA O'Z ID INGIZNI YOZING!

# Ma'lumotlar fayllari
DATA_FILE = "schedules.json"
STATS_FILE = "statistics.json"

# Vaqt zonasi
TIMEZONE = pytz.timezone('Asia/Tashkent')

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

# Hafta kunlari
WEEKDAYS = {
    'dushanba': 0,
    'seshanba': 1,
    'chorshanba': 2,
    'payshanba': 3,
    'juma': 4,
    'shanba': 5,
    'yakshanba': 6
}

WEEKDAYS_UZ = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']


# States
class ScheduleStates(StatesGroup):
    waiting_for_schedule = State()
    waiting_for_daily_schedule = State()
    waiting_for_weekly_schedule = State()
    waiting_for_admin_message = State()


# Ma'lumotlar bazasi funksiyalari
def load_schedules() -> Dict:
    """JSON fayldan rejalarni yuklash"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_schedules(schedules: Dict):
    """Rejalarni JSON faylga saqlash"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)


def load_statistics() -> Dict:
    """Statistikani yuklash"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_statistics(stats: Dict):
    """Statistikani saqlash"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def parse_schedule(text: str, is_weekly: bool = False) -> List[Dict]:
    """
    Matnni tahlil qilib, rejalar ro'yxatini qaytarish
    """
    schedules = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.lower().split()
        weekday = None
        hour = None
        minute = 0
        description = line
        
        # Haftalik reja uchun hafta kunini topish
        if is_weekly:
            for i, part in enumerate(parts):
                if part in WEEKDAYS:
                    weekday = WEEKDAYS[part]
                    parts = parts[i+1:]
                    break
        
        # Vaqtni topish
        for i, part in enumerate(parts):
            if ':' in part:
                try:
                    time_parts = part.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    description = ' '.join(parts[i+1:])
                    break
                except:
                    continue
            elif part == 'soat' and i+1 < len(parts):
                try:
                    next_part = parts[i+1].replace('da', '').replace('de', '')
                    hour = int(next_part)
                    description = ' '.join(parts[i+2:])
                    break
                except:
                    continue
            elif part.isdigit() and i == 0:
                try:
                    hour = int(part)
                    description = ' '.join(parts[i+1:])
                    break
                except:
                    continue
        
        if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
            schedules.append({
                'weekday': weekday,
                'hour': hour,
                'minute': minute,
                'description': description.strip()
            })
    
    return schedules


def get_schedule_id(schedule: Dict) -> str:
    """Reja uchun unique ID yaratish"""
    wd = schedule.get('weekday', 'daily')
    return f"{wd}_{schedule['hour']:02d}_{schedule['minute']:02d}_{schedule['description'][:20]}"


def should_send_pre_reminder(user_id: int, schedule: Dict) -> bool:
    """10 daqiqa oldin eslatma yuborish kerakmi?"""
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    current_time = schedule['hour'] * 60 + schedule['minute']
    current_weekday = schedule.get('weekday')
    
    # Oldingi rejani topish
    for sch in user_schedules:
        if sch == schedule:
            continue
            
        sch_time = sch['hour'] * 60 + sch['minute']
        sch_weekday = sch.get('weekday')
        
        # Bir xil kunda yoki kunlik rejalar
        if (sch_weekday == current_weekday) or (sch_weekday is None and current_weekday is None):
            time_diff = current_time - sch_time
            # Agar 10 daqiqadan kam bo'lsa, pre-reminder yubormaymiz
            if 0 < time_diff <= 10:
                return False
    
    return True


async def send_pre_reminder(user_id: int, schedule: Dict):
    """10 daqiqa oldin eslatma yuborish (agar kerak bo'lsa)"""
    if not should_send_pre_reminder(user_id, schedule):
        return
    
    try:
        weekday_text = ""
        if schedule.get('weekday') is not None:
            weekday_text = f"{WEEKDAYS_UZ[schedule['weekday']]} "
        
        message_text = (
            f"⏰ <b>10 daqiqadan keyin:</b>\n\n"
            f"📅 {weekday_text}{schedule['hour']:02d}:{schedule['minute']:02d}\n"
            f"📝 {schedule['description']}"
        )
        
        await bot.send_message(
            user_id,
            message_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xatolik {user_id} ga pre-reminder yuborishda: {e}")


def get_previous_schedule(user_id: int, current_schedule: Dict) -> Dict:
    """Oldingi rejani topish"""
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    now = datetime.now(TIMEZONE)
    current_weekday = current_schedule.get('weekday')
    if current_weekday is None:
        current_weekday = now.weekday()
    
    current_time = current_schedule['hour'] * 60 + current_schedule['minute']
    
    # Eng yaqin oldingi rejani topish
    previous = None
    min_diff = float('inf')
    
    for sch in user_schedules:
        if sch == schedule:
            continue
        
        sch_weekday = sch.get('weekday')
        if sch_weekday is None:
            sch_weekday = now.weekday()
        
        # Faqat bir xil kunda
        if sch_weekday != current_weekday:
            continue
        
        sch_time = sch['hour'] * 60 + sch['minute']
        time_diff = current_time - sch_time
        
        # Faqat oldingi rejalar
        if time_diff > 0 and time_diff < min_diff:
            min_diff = time_diff
            previous = sch
    
    return previous


async def send_reminder(user_id: int, schedule: Dict):
    """Asosiy eslatma va oldingi reja haqida savol"""
    try:
        # Oldingi rejani topish
        previous_schedule = get_previous_schedule(user_id, schedule)
        
        # Agar oldingi reja bo'lsa, uning bajarilganligi haqida so'rash
        if previous_schedule:
            schedule_id = get_schedule_id(previous_schedule)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Bajardim", callback_data=f"done_{schedule_id}"),
                    InlineKeyboardButton(text="❌ Bajarmadim", callback_data=f"notdone_{schedule_id}")
                ]
            ])
            
            prev_text = (
                f"❓ <b>Oldingi reja bajarildimi?</b>\n\n"
                f"📝 {previous_schedule['description']}\n"
                f"🕐 {previous_schedule['hour']:02d}:{previous_schedule['minute']:02d}"
            )
            
            await bot.send_message(
                user_id,
                prev_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            await asyncio.sleep(1)
        
        # Joriy reja haqida eslatma
        weekday_text = ""
        if schedule.get('weekday') is not None:
            weekday_text = f"{WEEKDAYS_UZ[schedule['weekday']]} "
        
        message_text = (
            f"🔔 <b>Hozir vaqti:</b>\n\n"
            f"📅 {weekday_text}{schedule['hour']:02d}:{schedule['minute']:02d}\n"
            f"📝 {schedule['description']}"
        )
        
        await bot.send_message(
            user_id,
            message_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xatolik {user_id} ga reminder yuborishda: {e}")


async def send_weekly_stats(user_id: int):
    """Haftalik statistika yuborish"""
    try:
        stats = load_statistics()
        user_stats = stats.get(str(user_id), {})
        
        now = datetime.now(TIMEZONE)
        week_start = now - timedelta(days=now.weekday())
        week_start_str = week_start.strftime('%Y-%m-%d')
        
        total_done = 0
        total_not_done = 0
        
        for date, day_stats in user_stats.items():
            if date >= week_start_str:
                total_done += day_stats.get('done', 0)
                total_not_done += day_stats.get('not_done', 0)
        
        total = total_done + total_not_done
        percentage = (total_done / total * 100) if total > 0 else 0
        
        filled = int(percentage / 10)
        progress_bar = "🟩" * filled + "⬜" * (10 - filled)
        
        stats_text = (
            f"📊 <b>HAFTALIK STATISTIKA</b>\n"
            f"📅 {week_start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')}\n\n"
            f"✅ Bajarilgan: {total_done}\n"
            f"❌ Bajarilmagan: {total_not_done}\n"
            f"📈 Jami: {total}\n\n"
            f"{progress_bar}\n"
            f"💯 Foiz: {percentage:.1f}%\n\n"
        )
        
        if percentage >= 80:
            stats_text += "🏆 Ajoyib natija! Davom eting!"
        elif percentage >= 60:
            stats_text += "👍 Yaxshi ish! Yanada yaxshilashingiz mumkin!"
        elif percentage >= 40:
            stats_text += "💪 Yomon emas, lekin ko'proq harakat qiling!"
        else:
            stats_text += "⚠️ Rejalaringizga ko'proq e'tibor bering!"
        
        await bot.send_message(
            user_id,
            stats_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Xatolik {user_id} ga statistika yuborishda: {e}")


def update_statistics(user_id: int, schedule_id: str, is_done: bool):
    """Statistikani yangilash"""
    stats = load_statistics()
    user_id_str = str(user_id)
    
    if user_id_str not in stats:
        stats[user_id_str] = {}
    
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    
    if today not in stats[user_id_str]:
        stats[user_id_str][today] = {'done': 0, 'not_done': 0}
    
    if is_done:
        stats[user_id_str][today]['done'] += 1
    else:
        stats[user_id_str][today]['not_done'] += 1
    
    save_statistics(stats)


def get_user_statistics_text(user_id: int) -> str:
    """Foydalanuvchi statistikasini olish"""
    stats = load_statistics()
    user_stats = stats.get(str(user_id), {})
    
    if not user_stats:
        return "Statistika mavjud emas"
    
    total_done = sum(day.get('done', 0) for day in user_stats.values())
    total_not_done = sum(day.get('not_done', 0) for day in user_stats.values())
    total = total_done + total_not_done
    percentage = (total_done / total * 100) if total > 0 else 0
    
    return f"""
📊 Umumiy statistika:
✅ Bajarilgan: {total_done}
❌ Bajarilmagan: {total_not_done}
📈 Jami: {total}
💯 Foiz: {percentage:.1f}%
📅 Kunlar soni: {len(user_stats)}
"""


def setup_user_schedules(user_id: int):
    """Foydalanuvchi rejalarini scheduler ga qo'shish"""
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    # Eski rejalarni o'chirish
    for job in scheduler.get_jobs():
        if job.id.startswith(f"user_{user_id}_"):
            job.remove()
    
    # Yangi rejalarni qo'shish
    for idx, schedule in enumerate(user_schedules):
        weekday = schedule.get('weekday')
        hour = schedule['hour']
        minute = schedule['minute']
        
        # Asosiy eslatma
        main_job_id = f"user_{user_id}_main_{idx}"
        
        if weekday is not None:
            scheduler.add_job(
                send_reminder,
                CronTrigger(
                    day_of_week=weekday,
                    hour=hour,
                    minute=minute,
                    timezone=TIMEZONE
                ),
                args=[user_id, schedule],
                id=main_job_id,
                replace_existing=True
            )
            
            # 10 daqiqa oldin eslatma (agar kerak bo'lsa)
            if should_send_pre_reminder(user_id, schedule):
                pre_hour = hour
                pre_minute = minute - 10
                if pre_minute < 0:
                    pre_minute += 60
                    pre_hour -= 1
                    if pre_hour < 0:
                        pre_hour = 23
                
                pre_job_id = f"user_{user_id}_pre_{idx}"
                scheduler.add_job(
                    send_pre_reminder,
                    CronTrigger(
                        day_of_week=weekday,
                        hour=pre_hour,
                        minute=pre_minute,
                        timezone=TIMEZONE
                    ),
                    args=[user_id, schedule],
                    id=pre_job_id,
                    replace_existing=True
                )
        else:
            # Kunlik reja
            scheduler.add_job(
                send_reminder,
                CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=TIMEZONE
                ),
                args=[user_id, schedule],
                id=main_job_id,
                replace_existing=True
            )
            
            # 10 daqiqa oldin eslatma (agar kerak bo'lsa)
            if should_send_pre_reminder(user_id, schedule):
                pre_hour = hour
                pre_minute = minute - 10
                if pre_minute < 0:
                    pre_minute += 60
                    pre_hour -= 1
                    if pre_hour < 0:
                        pre_hour = 23
                
                pre_job_id = f"user_{user_id}_pre_{idx}"
                scheduler.add_job(
                    send_pre_reminder,
                    CronTrigger(
                        hour=pre_hour,
                        minute=pre_minute,
                        timezone=TIMEZONE
                    ),
                    args=[user_id, schedule],
                    id=pre_job_id,
                    replace_existing=True
                )


def setup_weekly_stats():
    """Barcha foydalanuvchilar uchun haftalik statistikani sozlash"""
    schedules = load_schedules()
    
    for user_id in schedules.keys():
        job_id = f"weekly_stats_{user_id}"
        
        scheduler.add_job(
            send_weekly_stats,
            CronTrigger(
                day_of_week=6,
                hour=20,
                minute=0,
                timezone=TIMEZONE
            ),
            args=[int(user_id)],
            id=job_id,
            replace_existing=True
        )


# Klaviatura
def get_main_keyboard():
    """Asosiy klaviatura"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Reja qo'shish")],
            [KeyboardButton(text="📋 Mening rejalarim"), KeyboardButton(text="✏️ Tahrirlash")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🗑 Rejani o'chirish")],
            [KeyboardButton(text="ℹ️ Yordam"), KeyboardButton(text="👤 Adminga murojaat")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Callback handlerlar
@router.callback_query(F.data.startswith("done_") | F.data.startswith("notdone_"))
async def process_task_status(callback: CallbackQuery):
    """Vazifa bajarilganligini qayd qilish"""
    is_done = callback.data.startswith("done_")
    schedule_id = callback.data.split("_", 1)[1]
    user_id = callback.from_user.id
    
    update_statistics(user_id, schedule_id, is_done)
    
    if is_done:
        await callback.answer("✅ Bajarildi deb belgilandi!", show_alert=True)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ <b>Bajarildi!</b>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Bajarilmadi deb belgilandi", show_alert=True)
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>Bajarilmadi</b>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("delete_"))
async def process_delete_schedule(callback: CallbackQuery):
    """Rejani o'chirish"""
    user_id = callback.from_user.id
    schedule_idx = int(callback.data.split("_")[1])
    
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    if 0 <= schedule_idx < len(user_schedules):
        deleted = user_schedules.pop(schedule_idx)
        schedules[str(user_id)] = user_schedules
        save_schedules(schedules)
        
        setup_user_schedules(user_id)
        
        await callback.answer("🗑 Reja o'chirildi!", show_alert=True)
        await callback.message.edit_text(
            f"🗑 <b>O'chirilgan reja:</b>\n\n"
            f"📝 {deleted['description']}\n"
            f"🕐 {deleted['hour']:02d}:{deleted['minute']:02d}",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Reja topilmadi", show_alert=True)


@router.callback_query(F.data == "daily_schedule")
async def process_daily_schedule(callback: CallbackQuery, state: FSMContext):
    """Kunlik reja qo'shish"""
    await callback.message.edit_text(
        "📅 <b>Kunlik rejalaringizni kiriting:</b>\n\n"
        "<i>Misol:</i>\n"
        "9:00 ingliz tili\n"
        "12:00 tushlik\n"
        "14:30 sport\n\n"
        "Har bir rejani yangi qatordan kiriting.",
        parse_mode="HTML"
    )
    await state.set_state(ScheduleStates.waiting_for_daily_schedule)
    await callback.answer()


@router.callback_query(F.data == "weekly_schedule")
async def process_weekly_schedule(callback: CallbackQuery, state: FSMContext):
    """Haftalik reja qo'shish"""
    await callback.message.edit_text(
        "📆 <b>Haftalik rejalaringizni kiriting:</b>\n\n"
        "<i>Misol:</i>\n"
        "dushanba 9:00 ingliz tili\n"
        "seshanba 14:00 matematika\n"
        "juma 18:00 sport\n\n"
        "Har bir rejani yangi qatordan kiriting.",
        parse_mode="HTML"
    )
    await state.set_state(ScheduleStates.waiting_for_weekly_schedule)
    await callback.answer()


# Handlerlar
@router.message(Command("start"))
async def cmd_start(message: Message):
    """Start buyrug'i"""
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Men kunlik va haftalik rejalaringizni eslatib turuvchi botman.\n\n"
        "🔔 10 daqiqa oldin eslataman\n"
        "📊 Haftalik statistika beraman\n"
        "✅ Bajarilgan vazifalarni kuzataman\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_keyboard()
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Telegram ID ni ko'rsatish"""
    await message.answer(
        f"🆔 Sizning Telegram ID: <code>{message.from_user.id}</code>\n\n"
        "Bu ID ni admin ID sifatida ishlatishingiz mumkin.",
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: Message):
    """Yordam"""
    help_text = """
📖 <b>Bot qanday ishlatiladi:</b>

1️⃣ <b>Kunlik rejalar:</b>
<i>9:00 ingliz tili</i>
<i>soat 14da sport</i>

2️⃣ <b>Haftalik rejalar:</b>
<i>dushanba 9:00 ingliz tili</i>
<i>seshanba soat 14da matematika</i>
<i>juma 18:00 sport</i>

<b>Imkoniyatlar:</b>
✏️ Rejalarni tahrirlash
🗑 Rejalarni o'chirish
📊 Haftalik statistika
⏰ 10 daqiqa oldin eslatma
✅ Bajarilganlik holati
👤 Adminga murojaat

<b>Statistika:</b>
Har yakshanba 20:00 da haftalik hisobot olasiz!
"""
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "➕ Reja qo'shish")
async def add_schedule_start(message: Message):
    """Rejalar qo'shishni boshlash"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Kunlik reja", callback_data="daily_schedule")],
        [InlineKeyboardButton(text="📆 Haftalik reja", callback_data="weekly_schedule")]
    ])
    
    await message.answer(
        "📝 <b>Qaysi turdagi reja qo'shmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(ScheduleStates.waiting_for_daily_schedule)
async def add_daily_schedule_process(message: Message, state: FSMContext):
    """Kunlik rejalarni qabul qilish"""
    user_id = message.from_user.id
    
    new_schedules = parse_schedule(message.text, is_weekly=False)
    
    if not new_schedules:
        await message.answer(
            "❌ Rejalar topilmadi. Iltimos, to'g'ri formatda kiriting:\n\n"
            "<i>9:00 ingliz tili\n"
            "12:00 tushlik</i>",
            parse_mode="HTML"
        )
        return
    
    schedules = load_schedules()
    if str(user_id) not in schedules:
        schedules[str(user_id)] = []
    
    schedules[str(user_id)].extend(new_schedules)
    save_schedules(schedules)
    
    setup_user_schedules(user_id)
    setup_weekly_stats()
    
    result_text = "✅ Kunlik rejalar muvaffaqiyatli qo'shildi:\n\n"
    for schedule in new_schedules:
        result_text += f"🕐 {schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['description']}\n"
    
    await message.answer(result_text, reply_markup=get_main_keyboard())
    await state.clear()


@router.message(ScheduleStates.waiting_for_weekly_schedule)
async def add_weekly_schedule_process(message: Message, state: FSMContext):
    """Haftalik rejalarni qabul qilish"""
    user_id = message.from_user.id
    
    new_schedules = parse_schedule(message.text, is_weekly=True)
    
    if not new_schedules:
        await message.answer(
            "❌ Rejalar topilmadi. Iltimos, to'g'ri formatda kiriting:\n\n"
            "<i>dushanba 9:00 ingliz tili\n"
            "seshanba 14:00 matematika</i>",
            parse_mode="HTML"
        )
        return
    
    schedules = load_schedules()
    if str(user_id) not in schedules:
        schedules[str(user_id)] = []
    
    schedules[str(user_id)].extend(new_schedules)
    save_schedules(schedules)
    
    setup_user_schedules(user_id)
    setup_weekly_stats()
    
    result_text = "✅ Haftalik rejalar muvaffaqiyatli qo'shildi:\n\n"
    for schedule in new_schedules:
        weekday_text = WEEKDAYS_UZ[schedule['weekday']] if schedule.get('weekday') is not None else ""
        result_text += f"🕐 {weekday_text} {schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['description']}\n"
    
    await message.answer(result_text, reply_markup=get_main_keyboard())
    await state.clear()


@router.message(F.text == "📋 Mening rejalarim")
async def show_schedules(message: Message):
    """Rejalarni ko'rsatish"""
    user_id = message.from_user.id
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    if not user_schedules:
        await message.answer(
            "🔭 Sizda hali rejalar yo'q.\n\n"
            '"➕ Reja qo\'shish" tugmasini bosing.',
            reply_markup=get_main_keyboard()
        )
        return
    
    daily_schedules = [s for s in user_schedules if s.get('weekday') is None]
    weekly_schedules = [s for s in user_schedules if s.get('weekday') is not None]
    
    result_text = "📋 <b>Sizning rejalaringiz:</b>\n\n"
    
    if daily_schedules:
        result_text += "📅 <b>Kunlik rejalar:</b>\n"
        sorted_daily = sorted(daily_schedules, key=lambda x: (x['hour'], x['minute']))
        for schedule in sorted_daily:
            result_text += f"🕐 {schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['description']}\n"
        result_text += "\n"
    
    if weekly_schedules:
        result_text += "📆 <b>Haftalik rejalar:</b>\n"
        sorted_weekly = sorted(weekly_schedules, key=lambda x: (x['weekday'], x['hour'], x['minute']))
        for schedule in sorted_weekly:
            weekday_text = WEEKDAYS_UZ[schedule['weekday']]
            result_text += f"🕐 {weekday_text} {schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['description']}\n"
    
    await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_keyboard())


@router.message(F.text == "🗑 Rejani o'chirish")
async def delete_schedule_start(message: Message):
    """Rejani o'chirish"""
    user_id = message.from_user.id
    schedules = load_schedules()
    user_schedules = schedules.get(str(user_id), [])
    
    if not user_schedules:
        await message.answer(
            "🔭 Sizda rejalar yo'q.",
            reply_markup=get_main_keyboard()
        )
        return
    
    keyboard_buttons = []
    for idx, schedule in enumerate(user_schedules):
        weekday_text = ""
        if schedule.get('weekday') is not None:
            weekday_text = f"{WEEKDAYS_UZ[schedule['weekday']]} "
        
        button_text = f"{weekday_text}{schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['description'][:25]}"
        keyboard_buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=f"delete_{idx}")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        "🗑 <b>O'chirish uchun rejani tanlang:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    """Statistikani ko'rsatish"""
    user_id = message.from_user.id
    stats = load_statistics()
    user_stats = stats.get(str(user_id), {})
    
    if not user_stats:
        await message.answer(
            "📊 Hali statistika yo'q.\n\n"
            "Rejalarni bajaring, statistika to'planadi!",
            reply_markup=get_main_keyboard()
        )
        return
    
    today = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    today_stats = user_stats.get(today, {'done': 0, 'not_done': 0})
    
    now = datetime.now(TIMEZONE)
    week_start = now - timedelta(days=now.weekday())
    week_start_str = week_start.strftime('%Y-%m-%d')
    
    week_done = 0
    week_not_done = 0
    
    for date, day_stats in user_stats.items():
        if date >= week_start_str:
            week_done += day_stats.get('done', 0)
            week_not_done += day_stats.get('not_done', 0)
    
    week_total = week_done + week_not_done
    week_percentage = (week_done / week_total * 100) if week_total > 0 else 0
    
    filled = int(week_percentage / 10)
    progress_bar = "🟩" * filled + "⬜" * (10 - filled)
    
    stats_text = (
        f"📊 <b>STATISTIKA</b>\n\n"
        f"📅 <b>Bugun:</b>\n"
        f"✅ Bajarilgan: {today_stats['done']}\n"
        f"❌ Bajarilmagan: {today_stats['not_done']}\n\n"
        f"📆 <b>Shu hafta:</b>\n"
        f"✅ Bajarilgan: {week_done}\n"
        f"❌ Bajarilmagan: {week_not_done}\n"
        f"📈 Jami: {week_total}\n\n"
        f"{progress_bar}\n"
        f"💯 Foiz: {week_percentage:.1f}%"
    )
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=get_main_keyboard())


@router.message(F.text == "✏️ Tahrirlash")
async def edit_schedule_info(message: Message):
    """Tahrirlash yo'riqnomasi"""
    await message.answer(
        "✏️ <b>Rejani tahrirlash:</b>\n\n"
        "1. Avval rejani o'chiring: 🗑 Rejani o'chirish\n"
        "2. Keyin yangi reja qo'shing: ➕ Reja qo'shish\n\n"
        "Tez orada to'g'ridan-to'g'ri tahrirlash funksiyasi qo'shiladi!",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "👤 Adminga murojaat")
async def contact_admin(message: Message, state: FSMContext):
    """Adminga murojaat"""
    await message.answer(
        "📝 <b>Bot haqida fikr va mulohazalaringizni yozing:</b>\n\n"
        "Sizning xabaringiz to'g'ridan-to'g'ri admin ga yuboriladi.",
        parse_mode="HTML"
    )
    await state.set_state(ScheduleStates.waiting_for_admin_message)


@router.message(ScheduleStates.waiting_for_admin_message)
async def process_admin_message(message: Message, state: FSMContext):
    """Admin uchun xabarni qayta ishlash"""
    user_id = message.from_user.id
    username = message.from_user.username or "username yo'q"
    full_name = message.from_user.full_name
    
    # Foydalanuvchi statistikasi
    user_stats_text = get_user_statistics_text(user_id)
    
    # Admin ga xabar yuborish
    admin_message = f"""
📨 <b>YANGI XABAR</b>

👤 <b>Foydalanuvchi:</b>
- ID: <code>{user_id}</code>
- Ism: {full_name}
- Username: @{username}

💬 <b>Xabar:</b>
{message.text}

{user_stats_text}
"""
    
    try:
        await bot.send_message(
            ADMIN_ID,
            admin_message,
            parse_mode="HTML"
        )
        
        await message.answer(
            "✅ Xabaringiz adminga yuborildi!\n\n"
            "Tez orada javob olasiz.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        await message.answer(
            "❌ Xabar yuborishda xatolik yuz berdi.\n\n"
            "Keyinroq qayta urinib ko'ring.",
            reply_markup=get_main_keyboard()
        )
        print(f"Admin ga xabar yuborishda xatolik: {e}")
    
    await state.clear()


@router.message()
async def unknown_message(message: Message):
    """Noma'lum xabarlar"""
    await message.answer(
        "❓ Tushunmadim. Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_keyboard()
    )


async def main():
    """Asosiy funksiya"""
    schedules = load_schedules()
    for user_id in schedules.keys():
        setup_user_schedules(int(user_id))
    
    setup_weekly_stats()
    scheduler.start()
    
    print("✅ Bot ishga tushdi!")
    print(f"📝 Admin ID: {ADMIN_ID}")
    print("\nFunksiyalar:")
    print("✅ Haftalik va kunlik rejalar")
    print("✅ 10 daqiqa oldin eslatma (agar rejar orasida 10+ daqiqa bo'lsa)")
    print("✅ Inline tugmalar (Bajardim/Bajarmadim)")
    print("✅ Haftalik statistika (Yakshanba 20:00)")
    print("✅ Rejani o'chirish")
    print("✅ Adminga murojaat")
    print("\n🌐 Server uchun tayyor!")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    # 24/7 hosting uchun keep_alive ishga tushirish
    if USE_KEEP_ALIVE:
        keep_alive()
        print("🌐 Keep-alive server ishga tushdi (24/7 hosting)")
    
    asyncio.run(main())