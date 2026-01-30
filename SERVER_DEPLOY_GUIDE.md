# 🚀 BOTNI BEPUL SERVERGA JOYLASHTIRISH

## 🎯 Eng Yaxshi Bepul Serverlar

### 1. **RENDER.COM** ⭐ (ENG YAXSHI)

**Afzalliklari:**
- ✅ 100% bepul
- ✅ 750 soat/oy (24/7 ishlaydi)
- ✅ Oson sozlash
- ✅ GitHub bilan integratsiya
- ✅ Avtomatik qayta ishga tushish

**Qanday joylashtirish:**

#### A. GitHub Repository yaratish

1. GitHub.com ga kiring
2. Yangi repository yarating: `telegram-todo-bot`
3. Repository ga quyidagi fayllarni yuklang:
   - `todo_final.py`
   - `requirements.txt`
   - `Procfile` (yangi fayl)
   - `runtime.txt` (yangi fayl)

#### B. Kerakli fayllar

**requirements.txt:**
```
aiogram==3.4.1
apscheduler==3.10.4
pytz==2024.1
```

**Procfile:**
```
worker: python todo_final.py
```

**runtime.txt:**
```
python-3.11.7
```

#### C. Render.com da deploy qilish

1. https://render.com ga kiring
2. "New +" → "Background Worker" ni tanlang
3. GitHub repository ni ulang
4. Sozlamalar:
   - **Name:** telegram-todo-bot
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python todo_final.py`
5. "Create Background Worker" ni bosing
6. Deploy bo'lishini kuting (3-5 daqiqa)

✅ **Bot 24/7 ishlaydi!**

---

### 2. **RAILWAY.APP** ⭐

**Afzalliklari:**
- ✅ Bepul $5 kredit/oy
- ✅ Juda oson deploy
- ✅ 500 soat/oy
- ✅ GitHub integratsiya

**Qanday joylashtirish:**

1. https://railway.app ga kiring
2. "New Project" → "Deploy from GitHub repo"
3. Repository ni tanlang
4. Avtomatik deploy qilinadi!

---

### 3. **PYTHONANYWHERE.COM**

**Afzalliklari:**
- ✅ 100% bepul
- ✅ Python uchun maxsus
- ✅ Oson sozlash

**Kamchiliklari:**
- ⚠️ Har 3 oyda bir marta qayta yoqish kerak

**Qanday joylashtirish:**

1. https://www.pythonanywhere.com ga ro'yxatdan o'ting
2. "Files" → fayllarni yuklang
3. "Consoles" → Bash console oching
4. Buyruqlar:
```bash
pip3 install --user -r requirements.txt
python3 todo_final.py
```

---

### 4. **HEROKU** (Yangi free tier yo'q, lekin GitHub Student Pack bilan bepul)

Agar talaba bo'lsangiz: https://education.github.com/pack

---

### 5. **FLY.IO**

**Afzalliklari:**
- ✅ Bepul tier mavjud
- ✅ 3 micro VM bepul

**Qanday joylashtirish:**

1. https://fly.io ga kiring
2. `flyctl` ni o'rnating
3. Repository papkasida:
```bash
fly launch
fly deploy
```

---

## 📝 MUHIM ESLATMALAR

### 1. Bot Tokenini Xavfsiz Saqlash

**Render.com da:**
- Dashboard → Environment → Add Environment Variable
- `BOT_TOKEN` = sizning tokeningiz

**Kodda:**
```python
import os
BOT_TOKEN = os.getenv('BOT_TOKEN', 'default_token')
ADMIN_ID = int(os.getenv('ADMIN_ID', '123456789'))
```

### 2. Ma'lumotlar Bazasi

Bepul serverlarda fayllar o'chib ketishi mumkin. Yaxshiroq variant:

**MongoDB Atlas (BEPUL):**
```python
# requirements.txt ga qo'shing:
pymongo

# Kodda:
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGODB_URI'))
db = client['todo_bot']
```

MongoDB Atlas: https://www.mongodb.com/cloud/atlas/register

---

## 🎯 TAVSIYA QILINADIGAN YO'L

### Render.com (Eng oson va ishonchli)

1. **GitHub ga yuklash:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/telegram-todo-bot.git
git push -u origin main
```

2. **Render.com ga deploy:**
- Render.com ga kiring
- GitHub ulang
- Background Worker yarating
- Deploy tugmasini bosing

3. **Environment Variables sozlash:**
```
BOT_TOKEN = sizning_bot_tokeningiz
ADMIN_ID = sizning_telegram_id
```

4. **Telegram ID ni olish:**
- @userinfobot ga `/start` yuboring
- ID ni ko'chirib oling

---

## ⚙️ TELEGRAM ID NI KODDA TOPISH

```python
@router.message(Command("myid"))
async def get_my_id(message: Message):
    await message.answer(f"Sizning Telegram ID: {message.from_user.id}")
```

Bot ishga tushgandan keyin `/myid` yuboring.

---

## 🔄 AVTOMATIK QAYTA ISHGA TUSHISH

**Render.com** da avtomatik qayta ishga tushadi.

**PythonAnywhere** da cron job sozlash:
```bash
# Har kuni soat 3:00 da qayta ishga tushirish
0 3 * * * /home/USERNAME/restart_bot.sh
```

---

## 📊 MONITORING

**UptimeRobot** (bepul):
- https://uptimerobot.com
- Botni har 5 daqiqada tekshiradi
- Ishlamasa email yuboradi

---

## 🆘 MUAMMOLAR VA YECHIMLAR

### Bot to'xtab qolsa:

1. **Loglarni tekshiring:**
   - Render: Dashboard → Logs
   - Railway: Deployment → Logs

2. **Qayta deploy qiling:**
   - GitHub ga yangi commit push qiling
   - Avtomatik deploy bo'ladi

3. **Environment variables tekshiring:**
   - BOT_TOKEN to'g'rimi?
   - ADMIN_ID to'g'rimi?

---

## 💡 QO'SHIMCHA MASLAHATLAR

1. **GitHub Actions** bilan avtomatik deploy
2. **Docker** ishlatish (ilg'or)
3. **Logging** qo'shish (muhim!)
4. **Error handling** yaxshilash

---

## 📞 YORDAM

Agar muammo bo'lsa:
1. Render.com documentation: https://render.com/docs
2. Railway documentation: https://docs.railway.app
3. Telegram Bot API: https://core.telegram.org/bots/api

---

## ✅ TEKSHIRISH RO'YXATI

- [ ] GitHub repository yaratildi
- [ ] requirements.txt yaratildi
- [ ] Procfile yaratildi
- [ ] runtime.txt yaratildi
- [ ] Render.com accounti yaratildi
- [ ] Repository ulandi
- [ ] Environment variables sozlandi
- [ ] Deploy qilindi
- [ ] Bot ishlayotganini tekshirdim

---

**Omad! Botingiz 24/7 ishlaydi! 🎉**
