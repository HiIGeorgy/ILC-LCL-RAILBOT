from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

TOKEN = '7878760566:AAGwHJGLSnXmHgv9o2tFiw5we1v8XsMSleE'

CHOOSING_ACTION, CHOOSING_REGION, ENTER_PARAMS = range(3)

regions = [
    "Северо-Восточный",  # 1
    "Северный",          # 2
    "Восточный",         # 3
    "Центрально-Южный",  # 4
    "Юго-Западный",      # 5
    "Северо-Западный"    # 6
]

main_menu = [["Расчет тарифа"]]

def calculate_local_delivery(volume):
    if volume < 1:
        return 20
    elif volume < 5:
        return 50
    else:
        return 100

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Здравствуйте! Вас приветствует бот ILC.\n\nПожалуйста, выберите действие:",
        reply_markup=ReplyKeyboardMarkup(main_menu, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Расчет тарифа":
        # Отправляем картинку с регионами
        with open("china_regions.jpg", "rb") as photo:
            await update.message.reply_photo(
                photo,
                caption="Выберите регион на карте и нажмите соответствующую кнопку ниже.\n"
                        "1. Северо-Восточный\n"
                        "2. Северный\n"
                        "3. Восточный\n"
                        "4. Центрально-Южный\n"
                        "5. Юго-Западный\n"
                        "6. Северо-Западный"
            )
        reply_keyboard = [["1", "2", "3"], ["4", "5", "6"]]
        await update.message.reply_text(
            "Пожалуйста, выберите номер региона (1-6):",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_REGION
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите действие из меню.",
            reply_markup=ReplyKeyboardMarkup(main_menu, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_ACTION

async def region_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region_num = update.message.text.strip()
    if region_num in ["1", "2", "3", "4", "5", "6"]:
        region_idx = int(region_num) - 1
        context.user_data['region'] = regions[region_idx]
        await update.message.reply_text(
            "Введите вес (кг) и объем (м3) через запятую (например: 1200, 3.5):",
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTER_PARAMS
    else:
        reply_keyboard = [["1", "2", "3"], ["4", "5", "6"]]
        await update.message.reply_text(
            "Пожалуйста, выберите номер региона от 1 до 6.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_REGION

async def enter_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        weight, volume = text.split(',')
        weight = float(weight.strip())
        volume = float(volume.strip())

        volume_by_weight = weight / 500
        chargeable_volume = max(volume, volume_by_weight)

        base_tariff = 140 * chargeable_volume
        local_delivery = calculate_local_delivery(chargeable_volume)
        total = base_tariff + 150 + 50 + local_delivery
        total_with_fee = round(total * 1.025, 2)

        await update.message.reply_text(
    f"Регион: {context.user_data['region']}\n"
    f"Вес: {weight} кг\n"
    f"Объем: {volume} м³\n"
    f"К расчету принимается: {chargeable_volume:.2f} м³\n"
    f"Тариф: 140 USD x {chargeable_volume:.2f} = {base_tariff:.2f} USD\n"
    f"Сборы: 150 USD + 50 USD\n"
    f"Локальный довоз: {local_delivery} USD\n"
    f"Итого: {total_with_fee:.2f} USD\n\n"
    f"Подошел тариф? Напиши нам sales_ao@interlogcon.com"
        )
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text("Ошибка ввода. Пример: 1200, 3.5")
        return ENTER_PARAMS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
            CHOOSING_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region_chosen)],
            ENTER_PARAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_params)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()