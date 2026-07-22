import telebot, time, json, os, random, sqlite3
from datetime import datetime

TOKEN = '8885533139:AAHijpMZuDc2P4adNXHayboOGSjzFUcrNeI' # من @BotFather
ADMIN_ID = 7871770473 # من @userinfobot
bot = telebot.TeleBot(TOKEN)

# قاعدة بيانات
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, user TEXT, points INT, vip INT, ban INT, mute REAL, warns INT)')
c.execute('CREATE TABLE IF NOT EXISTS auto (key TEXT, value TEXT)')
conn.commit()

busy=False; maintenance=False; waiting={}

def kb(btns):
    m=telebot.types.InlineKeyboardMarkup(row_width=3)
    for row in btns: m.row(*[telebot.types.InlineKeyboardButton(t, callback_data=d) for t,d in row])
    return m

# القائمة الرئيسية
def main_menu():
    return kb([
        [("👤 المستخدمين","u"),("📨 الرسائل","m"),("🤖 الرد","a")],
        [("📊 احصائيات","s"),("🛡️ حماية","sec"),("🎁 ترفيه","f")],
        [("💎 VIP","vip"),("⚙️ اعدادات","set"),("📢 بث","b")]
    ])

@bot.message_handler(commands=['start'])
def start(m):
    if m.from_user.id==ADMIN_ID:
        bot.send_message(m.chat.id,"👑 لوحة تحكم 200 ميزة",reply_markup=main_menu())
    else:
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?,?,?)",(str(m.from_user.id),m.from_user.first_name,m.from_user.username,0,0,0,0,0))
        conn.commit()
        if maintenance: return bot.send_message(m.chat.id,"🛠️ البوت قيد الصيانة")
        bot.send_message(m.chat.id,"👋 هلا بيك\nدز رسالتك للادمن")

# رسائل المستخدمين
@bot.message_handler(func=lambda m: m.from_user.id!=ADMIN_ID)
def user_msg(m):
    uid=str(m.from_user.id)
    c.execute("SELECT ban,mute FROM users WHERE id=?",(uid,)); ban,mute=c.fetchone()
    if ban: return
    if mute>time.time(): return bot.send_message(m.chat.id,"🔇 انت مكتوم")

    c.execute("SELECT value FROM auto WHERE key=?",(m.text,)); r=c.fetchone()
    if r: return bot.send_message(m.chat.id,r[0])
    if busy: bot.send_message(m.chat.id,"⏰ المطور مشغول حالياً")

    text=f"📩 رسالة جديدة\nالاسم: {m.from_user.first_name}\nID:`{uid}`\n@{m.from_user.username}\n\n{m.text}"
    kb_user=kb([
        [("🚫حظر","ban_"+uid),("✅فك","unban_"+uid),("🔇كتم","mute_"+uid)],
        [("ℹ️معلومات","info_"+uid),("💬رد","reply_"+uid),("📝ملاحظة","note_"+uid)],
        [("🎁نقاط","points_"+uid),("👑VIP","vip_"+uid),("⚠️تحذير","warn_"+uid)]
    ])
    bot.send_message(ADMIN_ID,text,parse_mode="Markdown",reply_markup=kb_user)

# كل الازرار
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d=call.data

    if d=="u": bot.edit_message_text("👤 ادارة المستخدمين",call.message.chat.id,call.message.id,reply_markup=kb([ [("🚫حظر","ban_menu"),("✅فك","unban_menu"),("🔇كتم","mute_menu")], [("ℹ️معلومات","info_menu"),("📝ملاحظة","note_menu"),("🎁نقاط","points_menu")], [("👑VIP","vip_menu"),("🔍بحث","search_menu"),("🔙","back")] ]))
    if d=="m": bot.edit_message_text("📨 ادارة الرسائل",call.message.chat.id,call.message.id,reply_markup=kb([ [("💬رد","reply_menu"),("🗑️حذف","del_menu"),("📌تثبيت","pin_menu")], [("🏷️تصنيف","tag_menu"),("📂ارشيف","archive_menu"),("🔙","back")] ]))
    if d=="a": bot.edit_message_text("🤖 الرد التلقائي",call.message.chat.id,call.message.id,reply_markup=kb([ [("➕اضافة","addauto"),("➖حذف","delauto"),("📋قائمة","listauto")], [("🔙","back")] ]))
    if d=="s": bot.answer_callback_query(call.id,f"المستخدمين:{c.execute('SELECT COUNT(*) FROM users').fetchone()[0]}\nالمحظورين:{c.execute('SELECT COUNT(*) FROM users WHERE ban=1').fetchone()[0]}",show_alert=True)
    if d=="sec": bot.answer_callback_query(call.id,"🛡️ حماية: سبام + فلتر كلمات + كابتشا",show_alert=True)
    if d=="f": bot.answer_callback_query(call.id,"🎲 نرد + ❓سؤال + 😂نكتة + حكمة",show_alert=True)
    if d=="vip": bot.answer_callback_query(call.id,"💎 نظام VIP + نقاط + متجر",show_alert=True)
    if d=="set": bot.edit_message_text("⚙️ الاعدادات",call.message.chat.id,call.message.id,reply_markup=kb([ [("⏰مشغول","busy"),("🛠️صيانة","maint"),("💾باك اب","backup")], [("👋ترحيب","welcome"),("🔙","back")] ]))
    if d=="b": bot.send_message(call.message.chat.id,"اكتب رسالة البث الجماعي")
    if d=="back": bot.edit_message_text("👑 200 ميزة",call.message.chat.id,call.message.id,reply_markup=main_menu())

    # افعال
    if d.startswith("ban_"): uid=d.split("_")[1]; c.execute("UPDATE users SET ban=1 WHERE id=?",(uid,)); conn.commit(); bot.send_message(int(uid),"🚫 تم حظرك"); bot.answer_callback_query(call.id,"تم الحظر")
    if d.startswith("unban_"): uid=d.split("_")[1]; c.execute("UPDATE users SET ban=0 WHERE id=?",(uid,)); conn.commit(); bot.send_message(int(uid),"✅ فك الحظر"); bot.answer_callback_query(call.id,"تم")
    if d.startswith("mute_"): uid=d.split("_")[1]; waiting[call.message.chat.id]=("mute",uid); bot.send_message(call.message.chat.id,"اختار المدة: 5 - 10 - 30 - 60")
    if d.startswith("info_"): uid=d.split("_")[1]; c.execute("SELECT * FROM users WHERE id=?",(uid,)); u=c.fetchone(); bot.answer_callback_query(call.id,f"الاسم:{u[1]}\n@{u[2]}\nنقاط:{u[3]}\nVIP:{u[4]}",show_alert=True)
    if d.startswith("reply_"): uid=d.split("_")[1]; waiting[call.message.chat.id]=("reply",uid); bot.send_message(call.message.chat.id,"اكتب الرد هسه")
    if d.startswith("points_"): uid=d.split("_")[1]; waiting[call.message.chat.id]=("points",uid); bot.send_message(call.message.chat.id,"كم نقطة تريد تضيف؟")
    if d.startswith("vip_"): uid=d.split("_")[1]; c.execute("UPDATE users SET vip=1 WHERE id=?",(uid,)); conn.commit(); bot.send_message(int(uid),"👑 تم ترقيتك VIP"); bot.answer_callback_query(call.id,"تم")
    if d.startswith("warn_"): uid=d.split("_")[1]; c.execute("UPDATE users SET warns=warns+1 WHERE id=?",(uid,)); conn.commit(); bot.send_message(int(uid),"⚠️ تحذير من الادمن"); bot.answer_callback_query(call.id,"تم")

    if d=="addauto": waiting[call.message.chat.id]=("addauto","key"); bot.send_message(call.message.chat.id,"دز الكلمة")
    if d=="listauto": c.execute("SELECT * FROM auto"); bot.send_message(call.message.chat.id,"\n".join([f"{x[0]} = {x[1]}" for x in c.fetchall()]) if c.fetchall() else "ماكو ردود")

    if d=="busy": global busy; busy=not busy; bot.answer_callback_query(call.id,f"الحالة: {'مشغول' if busy else 'متاح'}")
    if d=="maint": global maintenance; maintenance=not maintenance; bot.answer_callback_query(call.id,f"الصيانة: {maintenance}")
    if d=="backup": bot.send_document(call.message.chat.id,open('bot.db','rb'))

# كتابة الادمن
@bot.message_handler(func=lambda m: m.from_user.id==ADMIN_ID)
def admin_write(m):
    if m.chat.id in waiting:
        t,v=waiting[m.chat.id]
        if t=="reply": bot.send_message(int(v),f"📨 رد الادمن:\n\n{m.text}"); del waiting[m.chat.id]; bot.reply_to(m,"✅ تم")
        if t=="mute": mins=int(m.text); c.execute("UPDATE users SET mute=? WHERE id=?",(time.time()+mins*60,v)); conn.commit(); bot.send_message(int(v),f"🔇 مكتوم {mins} دقيقة"); del waiting[m.chat.id]; bot.reply_to(m,"✅ تم")
        if t=="points": pts=int(m.text); c.execute("UPDATE users SET points=points+? WHERE id=?",(pts,v)); conn.commit(); del waiting[m.chat.id]; bot.reply_to(m,"✅ تم")
        if t==("addauto","key"): waiting[m.chat.id]=("addauto",m.text); bot.send_message(m.chat.id,"هسه دز الرد")
        if t==("addauto","value"): c.execute("INSERT INTO auto VALUES (?,?)",(v,m.text)); conn.commit(); bot.send_message(m.chat.id,"✅ تم اضافة الرد التلقائي"); del waiting[m.chat.id]

bot.polling(none_stop=True)