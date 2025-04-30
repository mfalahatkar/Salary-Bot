import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# تنظیمات اولیه
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("❌ خطا: توکن ربات تنظیم نشده است!")
    exit(1)

KM_PER_MISSION = 52  # کیلومتر هر ماموریت
PER_KM = 12596  # قیمت هر کیلومتر (اصلاح شده)
MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]
YEARS = ["1403", "1404"]

# ساختار داده‌ای حقوق خودروها (ریال)
CAR_SALARIES = {
    "ساینا و تیبا": {
        "1395-1397": 511062,
        "98 به بالا": 580124
    },
    "سمند، پژو 405، پژو پارس، رانا، پژو 206، MVM": {
        "1390-1392": 436474,
        "1393-1394": 519350,
        "1395-1397": 607750,
        "98 به بالا": 676812
    },
    "دنا، شاهین، ال 90، برلیانس، لیفان": {
        "1390-1392": 483436,
        "1393-1394": 566312,
        "1395-1397": 663000,
        "98 به بالا": 732062
    }
}

# مراحل گفتگو
SELECT_YEAR, SELECT_MONTH, SELECT_CAR, SELECT_MODEL, GET_MISSIONS, GET_NORMAL_HOURS, GET_HOURLY_MISSIONS, SELECT_FINAL_ACTION = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [YEARS]
    await update.message.reply_text(
        "📅 لطفاً سال مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_YEAR

async def select_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    year = update.message.text
    if year not in YEARS:
        await update.message.reply_text("⚠️ سال نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
        return SELECT_YEAR

    context.user_data['year'] = year

    reply_keyboard = [MONTHS[i:i+3] for i in range(0, len(MONTHS), 3)]
    await update.message.reply_text(
        "📅 لطفاً ماه مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MONTH

async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    month = update.message.text
    if month not in MONTHS:
        await update.message.reply_text("⚠️ ماه نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
        return SELECT_MONTH

    context.user_data['month'] = month

    car_types = list(CAR_SALARIES.keys())
    reply_keyboard = [car_types[i:i+2] for i in range(0, len(car_types), 2)]
    await update.message.reply_text(
        "🚗 لطفاً نوع خودرو را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_CAR

async def select_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    car_type = update.message.text
    if car_type not in CAR_SALARIES:
        await update.message.reply_text("⚠️ نوع خودرو نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
        return SELECT_CAR

    context.user_data['car_type'] = car_type

    models = list(CAR_SALARIES[car_type].keys())
    reply_keyboard = [models[i:i+2] for i in range(0, len(models), 2)]
    await update.message.reply_text(
        "📅 لطفاً مدل خودرو را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MODEL

async def select_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    model = update.message.text
    car_type = context.user_data['car_type']

    if model not in CAR_SALARIES[car_type]:
        await update.message.reply_text("⚠️ مدل خودرو نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
        return SELECT_MODEL

    context.user_data['model'] = model
    context.user_data['hourly_wage'] = CAR_SALARIES[car_type][model]

    await update.message.reply_text(
        f"✅ اطلاعات خودرو:\n"
        f"• نوع: {car_type}\n"
        f"• مدل: {model}\n",
        reply_markup=ReplyKeyboardRemove()
    )

    await update.message.reply_text(
        "لطفاً تعداد ماموریت‌های رشت را وارد کنید (عدد صحیح):"
    )
    return GET_MISSIONS

async def get_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        missions = int(update.message.text)
        if missions < 0:
            await update.message.reply_text("❌ تعداد ماموریت نمی‌تواند منفی باشد! دوباره وارد کنید:")
            return GET_MISSIONS

        context.user_data['missions'] = missions
        await update.message.reply_text(
            "✅ لطفاً ساعت کارکرد عادی را وارد کنید (میتوانید از اعشار استفاده کنید، مثلاً 138.5):"
        )
        return GET_NORMAL_HOURS
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد صحیح وارد کنید!")
        return GET_MISSIONS

async def get_normal_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        normal_hours = float(update.message.text)
        if normal_hours < 0:
            await update.message.reply_text("❌ ساعت کار نمی‌تواند منفی باشد! دوباره وارد کنید:")
            return GET_NORMAL_HOURS

        context.user_data['normal_hours'] = normal_hours
        await update.message.reply_text(
            "⏰ لطفاً تعداد ساعت‌های ماموریت ساعتی را وارد کنید (مثال: 20 یا 15.5):"
        )
        return GET_HOURLY_MISSIONS
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد وارد کنید (مثال: 138.5):")
        return GET_NORMAL_HOURS

async def get_hourly_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        hourly_missions = float(update.message.text)
        if hourly_missions < 0:
            await update.message.reply_text("❌ مقدار وارد شده نمی‌تواند منفی باشد! دوباره وارد کنید:")
            return GET_HOURLY_MISSIONS

        data = context.user_data

        # محاسبه ماموریت رشت
        mission_cost = data['missions'] * KM_PER_MISSION * PER_KM

        # حقوق سایر قسمت‌ها
        normal_salary = data['normal_hours'] * data['hourly_wage']
        hourly_mission_cost = hourly_missions * data['hourly_wage']

        # مجموع
        total = mission_cost + normal_salary + hourly_mission_cost

        # فرمت اعداد با جداکننده سه‌رقمی
        def format_currency(amount):
            return "{:,.0f}".format(amount).replace(",", "٬")

        await update.message.reply_text(
            f"📊 **نتایج محاسبات حقوق - {data['month']} {data['year']}**\n\n"
            f"🚗 **مشخصات خودرو:**\n"
            f"• نوع: {data['car_type']}\n"
            f"• مدل: {data['model']}\n"
            f"• حقوق ساعتی: {format_currency(data['hourly_wage'])} ریال\n\n"
            f"📝 **جزئیات محاسبه:**\n"
            f"• تعداد ماموریت رشت: {data['missions']} بار\n"
            f"• کیلومتر هر ماموریت: {KM_PER_MISSION} کیلومتر\n"
            f"• هزینه ماموریت رشت: {format_currency(mission_cost)} ریال\n"
            f"• ساعت کار عادی: {data['normal_hours']:.2f} ساعت\n"
            f"• حقوق پایه: {format_currency(normal_salary)} ریال\n"
            f"• تعداد ماموریت ساعتی: {hourly_missions:.2f} ساعت\n"
            f"• هزینه ماموریت ساعتی: {format_currency(hourly_mission_cost)} ریال\n\n"
            f"💰 مجموع حقوق قابل پرداخت: {format_currency(total)} ریال\n\n"
            "🟢 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        reply_keyboard = [["شروع دوباره", "ریست ربات", "خروج"]]
        await update.message.reply_text(
            "انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SELECT_FINAL_ACTION

    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد وارد کنید (مثال: 15.5):")
        return GET_HOURLY_MISSIONS

async def handle_final_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    action = update.message.text

    if action == "شروع دوباره":
        await update.message.reply_text("🔄 عملیات از ابتدا آغاز می‌شود.", reply_markup=ReplyKeyboardRemove())
        return await start(update, context)
    
    elif action == "ریست ربات":
        await update.message.reply_text("🔄 ربات ریست شد. برای شروع مجدد /start را بزنید.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    elif action == "خروج":
        await update.message.reply_text("👋 خروج انجام شد. برای شروع مجدد /start را بزنید.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    else:
        await update.message.reply_text("⚠️ گزینه نامعتبر است! لطفاً یکی از گزینه‌های موجود را انتخاب کنید.")
        return SELECT_FINAL_ACTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('عملیات لغو شد. برای شروع مجدد /start را بزنید.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_year)],
            SELECT_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_month)],
            SELECT_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_car)],
            SELECT_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_model)],
            GET_MISSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_missions)],
            GET_NORMAL_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_normal_hours)],
            GET_HOURLY_MISSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hourly_missions)],
            SELECT_FINAL_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_action)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    print("✅ ربات فعال شد و آماده دریافت درخواست‌هاست!")
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
