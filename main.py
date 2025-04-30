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

KM_PER_MISSION = 52
PER_KM = 12596
MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
YEARS = ["1403", "1404"]

CAR_SALARIES = {
    "ساینا و تیبا": {"1395-1397": 511062, "98 به بالا": 580124},
    "سمند، پژو 405، پژو پارس، رانا، پژو 206، MVM": {
        "1390-1392": 436474, "1393-1394": 519350, "1395-1397": 607750, "98 به بالا": 676812},
    "دنا، شاهین، ال 90، برلیانس، لیفان": {
        "1390-1392": 483436, "1393-1394": 566312, "1395-1397": 663000, "98 به بالا": 732062}
}

(SELECT_YEAR, SELECT_MONTH, SELECT_CAR, SELECT_MODEL, GET_MISSIONS, 
 GET_NORMAL_HOURS, GET_HOURLY_MISSIONS, SELECT_FINAL_ACTION) = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📅 سال مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup([YEARS], one_time_keyboard=True)
    )
    return SELECT_YEAR

async def select_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['year'] = update.message.text
    reply_keyboard = [MONTHS[i:i+3] for i in range(0, len(MONTHS), 3)]
    await update.message.reply_text(
        "📅 ماه مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MONTH

async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['month'] = update.message.text
    car_types = list(CAR_SALARIES.keys())
    reply_keyboard = [car_types[i:i+2] for i in range(0, len(car_types), 2)]
    await update.message.reply_text(
        "🚗 نوع خودرو را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_CAR

async def select_car(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    car_type = update.message.text
    if car_type not in CAR_SALARIES:
        await update.message.reply_text("⚠️ مدل نامعتبر است!", reply_markup=ReplyKeyboardRemove())
        return SELECT_CAR

    context.user_data['car_type'] = car_type
    models = list(CAR_SALARIES[car_type].keys())
    reply_keyboard = [[model] for model in models]
    await update.message.reply_text(
        "🔧 مدل خودرو را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SELECT_MODEL

async def select_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    car_type = context.user_data['car_type']
    model = update.message.text
    
    if model not in CAR_SALARIES[car_type]:
        await update.message.reply_text("⚠️ مدل نامعتبر است!", reply_markup=ReplyKeyboardRemove())
        return SELECT_MODEL

    context.user_data['model'] = model
    context.user_data['hourly_wage'] = CAR_SALARIES[car_type][model]
    await update.message.reply_text("✅ اطلاعات خودرو ثبت شد.", reply_markup=ReplyKeyboardRemove())
    
    await update.message.reply_text(
        "🔢 تعداد ماموریت‌های رشت را وارد کنید:",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_MISSIONS

async def get_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        missions = int(update.message.text)
        if missions < 0:
            await update.message.reply_text("❌ عدد منفی نمی‌تواند باشد!")
            return GET_MISSIONS
            
        context.user_data['missions'] = missions
        await update.message.reply_text("⏰ ساعت کار عادی:")
        return GET_NORMAL_HOURS
        
    except ValueError:
        await update.message.reply_text("❌ عدد وارد کنید!")
        return GET_MISSIONS

async def get_normal_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        normal_hours = float(update.message.text)
        if normal_hours < 0:
            await update.message.reply_text("❌ عدد منفی نمی‌تواند باشد!")
            return GET_NORMAL_HOURS
            
        context.user_data['normal_hours'] = normal_hours
        await update.message.reply_text("⏱️ ساعت ماموریت:")
        return GET_HOURLY_MISSIONS
        
    except ValueError:
        await update.message.reply_text("❌ عدد وارد کنید!")
        return GET_NORMAL_HOURS

async def get_hourly_missions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        hourly_missions = float(update.message.text)
        if hourly_missions < 0:
            await update.message.reply_text("❌ عدد منفی نمی‌تواند باشد!")
            return GET_HOURLY_MISSIONS

        data = context.user_data
        mission_cost = data['missions'] * KM_PER_MISSION * PER_KM
        normal_salary = data['normal_hours'] * data['hourly_wage']
        hourly_mission_cost = hourly_missions * data['hourly_wage']
        total = mission_cost + normal_salary + hourly_mission_cost

        def format_currency(amount):
            return "{:,.0f}".format(amount).replace(",", "٬")

        result = f"📊 حقوق {data['month']} {data['year']}\n\n"
        result += f"🚗 {data['car_type']} - {data['model']}\n"
        result += f"• ماموریت رشت: {data['missions']}×{KM_PER_MISSION}={format_currency(mission_cost)}\n"
        result += f"• کار عادی: {data['normal_hours']:.1f}h → {format_currency(normal_salary)}\n"
        result += f"• ماموریت ساعتی: {hourly_missions:.1f}h → {format_currency(hourly_mission_cost)}\n"
        result += f"\n💰 جمع کل: {format_currency(total)}"

        await update.message.reply_text(result)

        reply_keyboard = [["🔄 شروع دوباره", "♻️ ریست"]]
        await update.message.reply_text(
            "انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return SELECT_FINAL_ACTION

    except ValueError:
        await update.message.reply_text("❌ عدد وارد کنید!")
        return GET_HOURLY_MISSIONS

async def handle_final_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    action = update.message.text

    if action == "🔄 شروع دوباره":
        await update.message.reply_text("🔁 دوباره شروع می‌کنیم.")
        return await start(update, context)
        
    elif action == "♻️ ریست":
        await update.message.reply_text("🧹 کل داده‌ها پاک شد.", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('⛔ عملیات لغو شد.', reply_markup=ReplyKeyboardRemove())
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
    print("✅ ربات آماده شد!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
