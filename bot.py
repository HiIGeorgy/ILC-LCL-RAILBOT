from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

TOKEN = '7878760566:AAGwHJGLSnXmHgv9o2tFiw5we1v8XsMSleE'

CHOOSING_ACTION, CHOOSING_REGION, ENTER_PARAMS = range(3)

def calculate_local_delivery(volume):
    # Пример функции для расчёта локального довоза, замени на свою логику
    if volume < 1:
        return 20
    elif volume < 5:
        return 50
    else:
        return 100

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Выбери действие.")
    return CHOOSING_ACTION

def choose_action(update: Update, context: CallbackContext):
    update.message.reply_text("Выбери регион.")
    return CHOOSING_REGION

def region_chosen(update: Update, context: CallbackContext):
    region = update.message.text
    context.user_data['region'] = region
    update.message.reply_text(f"Выбран регион: {region}. Введи вес и объем через запятую, например: 1200, 3.5")
    return ENTER_PARAMS

def enter_params(update: Update, context: CallbackContext):
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

        update.message.reply_text(
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
        update.message.reply_text("Ошибка ввода. Пример: 1200, 3.5")
        return ENTER_PARAMS

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [MessageHandler(Filters.text & ~Filters.command, choose_action)],
            CHOOSING_REGION: [MessageHandler(Filters.text & ~Filters.command, region_chosen)],
            ENTER_PARAMS: [MessageHandler(Filters.text & ~Filters.command, enter_params)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if name == "__main__":
    main()