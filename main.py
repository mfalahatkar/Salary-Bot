import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("❌ خطا: توکن ربات تنظیم نشده است! لطفاً متغیر TOKEN را در تنظیمات Railway تنظیم کنید.")
    exit(1)
KM_PER_MISSION = 52
PER_KM = 18524

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

SELECT_CAR, SELECT_MODEL, GET_MISSIONS, GET_NORMAL_HOURS, GET_OVERTIME = range(5)

def start(update: Update, context: CallbackContext) -> int:
            car_types = list(CAR_SALARIES.keys())
            reply_keyboard = [car_types[i:i+2] for i in range(0, len(car_types), 2)]

            update.message.reply_text(
                "🚗 لطفاً نوع خودرو را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return SELECT_CAR

def select_car(update: Update, context: CallbackContext) -> int:
            car_type = update.message.text
            if car_type not in CAR_SALARIES:
                update.message.reply_text("⚠️ نوع خودرو نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
                return SELECT_CAR

            context.user_data['car_type'] = car_type
            models = list(CAR_SALARIES[car_type].keys())
            reply_keyboard = [models[i:i+2] for i in range(0, len(models), 2)]

            update.message.reply_text(
                f"🔧 خودرو انتخاب شده: {car_type}\n\n"
                "📅 لطفاً مدل خودرو را انتخاب کنید:",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            return SELECT_MODEL

def select_model(update: Update, context: CallbackContext) -> int:
            model = update.message.text
            car_type = context.user_data['car_type']

            if model not in CAR_SALARIES[car_type]:
                update.message.reply_text("⚠️ مدل خودرو نامعتبر است! لطفاً از کیبورد انتخاب کنید.")
                return SELECT_MODEL

            context.user_data['model'] = model
            context.user_data['hourly_wage'] = CAR_SALARIES[car_type][model]

            update.message.reply_text(
                f"✅ اطلاعات خودرو:\n"
                f"• نوع: {car_type}\n"
                f"• مدل: {model}\n\n"
                "لطفاً تعداد ماموریت‌های رشت را وارد کنید (عدد صحیح):"
            )
            return GET_MISSIONS

def get_missions(update: Update, context: CallbackContext) -> int:
            try:
                missions = int(update.message.text)
                if missions < 0:
                    update.message.reply_text("❌ تعداد ماموریت نمی‌تواند منفی باشد! دوباره وارد کنید:")
                    return GET_MISSIONS

                context.user_data['missions'] = missions
                update.message.reply_text(
                    "✅ لطفاً ساعت کارکرد عادی را وارد کنید (میتوانید از اعشار استفاده کنید، مثلاً 138.5):"
                )
                return GET_NORMAL_HOURS
            except ValueError:
                update.message.reply_text("❌ لطفاً یک عدد صحیح وارد کنید!")
                return GET_MISSIONS

def get_normal_hours(update: Update, context: CallbackContext) -> int:
            try:
                normal_hours = float(update.message.text)
                if normal_hours < 0:
                    update.message.reply_text("❌ ساعت کار نمی‌تواند منفی باشد! دوباره وارد کنید:")
                    return GET_NORMAL_HOURS

                context.user_data['normal_hours'] = normal_hours
                update.message.reply_text(
                    "✅ لطفاً ساعت اضافه کار را وارد کنید (میتوانید از اعشار استفاده کنید، مثلاً 45.75):"
                )
                return GET_OVERTIME
            except ValueError:
                update.message.reply_text("❌ لطفاً یک عدد وارد کنید (مثال: 138.5):")
                return GET_NORMAL_HOURS

def get_overtime(update: Update, context: CallbackContext) -> int:
            try:
                overtime = float(update.message.text)
                if overtime < 0:
                    update.message.reply_text("❌ ساعت اضافه کار نمی‌تواند منفی باشد! دوباره وارد کنید:")
                    return GET_OVERTIME

                data = context.user_data
                mission_cost = data['missions'] * KM_PER_MISSION * PER_KM
                normal_salary = data['normal_hours'] * data['hourly_wage']
                overtime_salary = overtime * data['hourly_wage'] * 1.4
                total = mission_cost + normal_salary + overtime_salary

                update.message.reply_text(
                    f"📊 نتیجه محاسبات:\n\n"
                    f"🚗 اطلاعات خودرو:\n"
                    f"• نوع: {data['car_type']}\n"
                    f"• مدل: {data['model']}\n"
                    f"• حقوق ساعتی: {data['hourly_wage']:,} ریال\n\n"
                    f"📌 جزئیات محاسبه:\n"
                    f"• تعداد ماموریت: {data['missions']} بار\n"
                    f"• کیلومتر هر ماموریت: {KM_PER_MISSION} کیلومتر\n"
                    f"• هزینه ماموریت: {mission_cost:,} ریال\n"
                    f"• ساعت کار عادی: {data['normal_hours']:.2f} ساعت\n"
                    f"• حقوق پایه: {normal_salary:,} ریال\n"
                    f"• ساعت اضافه کار: {overtime:.2f} ساعت\n"
                    f"• اضافه کار: {overtime_salary:,} ریال\n\n"
                    f"💰 مجموع حقوق: {total:,} ریال\n\n"
                    "برای محاسبه مجدد /start را بزنید."
                )
                return ConversationHandler.END
            except ValueError:
                update.message.reply_text("❌ لطفاً یک عدد وارد کنید (مثال: 45.5):")
                return GET_OVERTIME

def cancel(update: Update, context: CallbackContext) -> int:
            update.message.reply_text('عملیات لغو شد. برای شروع مجدد /start را بزنید.')
            return ConversationHandler.END

def main():
            updater = Updater(TOKEN)
            dispatcher = updater.dispatcher

            conv_handler = ConversationHandler(
                entry_points=[CommandHandler('start', start)],
                states={
                    SELECT_CAR: [MessageHandler(Filters.text & ~Filters.command, select_car)],
                    SELECT_MODEL: [MessageHandler(Filters.text & ~Filters.command, select_model)],
                    GET_MISSIONS: [MessageHandler(Filters.text & ~Filters.command, get_missions)],
                    GET_NORMAL_HOURS: [MessageHandler(Filters.text & ~Filters.command, get_normal_hours)],
                    GET_OVERTIME: [MessageHandler(Filters.text & ~Filters.command, get_overtime)],
                },
                fallbacks=[CommandHandler('cancel', cancel)]
            )

            dispatcher.add_handler(conv_handler)
            updater.start_polling()
            print("✅ ربات فعال شد و آماده دریافت درخواست‌هاست!")
            updater.idle()

if __name__ == '__main__':
            main()
