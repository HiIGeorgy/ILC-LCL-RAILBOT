from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
TOKEN = '7878760566:AAGwHJGLSnXmHgv9o2tFiw5we1v8XsMSleE'

CHOOSING_ACTION, CHOOSING_REGION, ENTER_PARAMS = range(3)

def calculate_local_delivery(volume):
    if volume < 1:
        return 20
    elif volume < 5:
        return 50
    else:
        return 100

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери действие.")
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выбери регион.")
    return CHOOSING_REGION

async def region_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text
    context.user_data['region'] = region
    await update.message.reply_text(f"Выбран регион: {region}. Введи вес и объем через запятую, например: 1200, 3.5")
    return ENTER_PARAMS

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
    await update.message.reply_text("Отменено.")
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