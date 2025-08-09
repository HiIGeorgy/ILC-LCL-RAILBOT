import logging
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = "7878760566:AAGJbJv3-xV87ILGZSaz5bAVgoHDQqGXLdY"

CHOOSING_ACTION, CHOOSING_REGION, ENTER_PARAMS = range(3)

regions = [
    "Северо-Восточный",  # 1
    "Северный",  # 2
    "Восточный",  # 3
    "Центрально-Южный",  # 4
    "Юго-Западный",  # 5
    "Северо-Западный",  # 6
]

main_menu = [["Расчет тарифа"]]


def calculate_local_delivery(volume):
    logging.info(f"Calculating local delivery for volume: {volume}")
    if volume < 1:
        result = 20
    elif volume < 5:
        result = 50
    else:
        result = 100
    logging.info(f"Local delivery calculated: {result} USD")
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    logging.info(f"User {user_id} (@{username}) started the bot")

    await update.message.reply_text(
        "Здравствуйте! Вас приветствует бот ILC.\n\nПожалуйста, выберите действие:",
        reply_markup=ReplyKeyboardMarkup(
            main_menu, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    logging.info(f"User {user_id} sent to CHOOSING_ACTION state")
    return CHOOSING_ACTION


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_choice = update.message.text
    logging.info(f"User {user_id} chose action: {user_choice}")

    if user_choice == "Расчет тарифа":
        logging.info(f"User {user_id} requested tariff calculation")
        # Отправляем картинку с регионами
        file_path = Path(__file__).parent / "china_regions.jpg"
        try:
            with open(file_path, "rb") as photo:
                await update.message.reply_photo(
                    photo,
                    caption=(
                        "Выберите регион на карте и нажмите соответствующую кнопку ниже.\n"
                        "1. Северо-Восточный\n"
                        "2. Северный\n"
                        "3. Восточный\n"
                        "4. Центрально-Южный\n"
                        "5. Юго-Западный\n"
                        "6. Северо-Западный"
                    ),
                )
            logging.info(f"Regions image sent to user {user_id}")
        except FileNotFoundError:
            logging.error(f"Regions image not found at {file_path}")
            await update.message.reply_text("Ошибка загрузки изображения регионов.")
            return CHOOSING_ACTION

        reply_keyboard = [["1", "2", "3"], ["4", "5", "6"]]
        await update.message.reply_text(
            "Пожалуйста, выберите номер региона (1-6):",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        logging.info(f"User {user_id} sent to CHOOSING_REGION state")
        return CHOOSING_REGION
    else:
        logging.warning(f"User {user_id} sent invalid action: {user_choice}")
        await update.message.reply_text(
            "Пожалуйста, выберите действие из меню.",
            reply_markup=ReplyKeyboardMarkup(
                main_menu, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return CHOOSING_ACTION


async def region_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    region_num = update.message.text.strip()
    logging.info(f"User {user_id} selected region: {region_num}")

    if region_num in ["1", "2", "3", "4", "5", "6"]:
        region_idx = int(region_num) - 1
        selected_region = regions[region_idx]
        context.user_data["region"] = selected_region
        logging.info(f"User {user_id} confirmed region: {selected_region}")

        await update.message.reply_text(
            "Введите вес (кг) и объем (м3) через запятую (например: 1200, 3.5):",
            reply_markup=ReplyKeyboardRemove(),
        )
        logging.info(f"User {user_id} sent to ENTER_PARAMS state")
        return ENTER_PARAMS
    else:
        logging.warning(f"User {user_id} sent invalid region number: {region_num}")
        reply_keyboard = [["1", "2", "3"], ["4", "5", "6"]]
        await update.message.reply_text(
            "Пожалуйста, выберите номер региона от 1 до 6.",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, resize_keyboard=True
            ),
        )
        return CHOOSING_REGION


async def enter_params(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    logging.info(f"User {user_id} entered parameters: {text}")

    try:
        weight, volume = text.split(",")
        weight = float(weight.strip())
        volume = float(volume.strip())

        logging.info(f"User {user_id} - Weight: {weight} kg, Volume: {volume} m³")

        volume_by_weight = weight / 500
        chargeable_volume = max(volume, volume_by_weight)

        base_tariff = 140 * chargeable_volume
        local_delivery = calculate_local_delivery(chargeable_volume)
        total = base_tariff + 150 + 50 + local_delivery
        total_with_fee = round(total * 1.025, 2)

        logging.info(
            f"User {user_id} - Calculation completed: Total: {total_with_fee} USD"
        )

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

        logging.info(f"User {user_id} completed tariff calculation successfully")
        return ConversationHandler.END

    except Exception as e:
        logging.error(
            f"User {user_id} - Error parsing parameters: {text}, Error: {str(e)}"
        )
        await update.message.reply_text("Ошибка ввода. Пример: 1200, 3.5")
        return ENTER_PARAMS


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(f"User {user_id} cancelled the conversation")
    await update.message.reply_text(
        "Диалог отменён.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    logging.info("Starting ILC bot...")
    logging.info(f"Bot token: {TOKEN[:10]}...{TOKEN[-10:]}")

    try:
        app = ApplicationBuilder().token(TOKEN).build()
        logging.info("Telegram application built successfully")

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                CHOOSING_ACTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)
                ],
                CHOOSING_REGION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, region_chosen)
                ],
                ENTER_PARAMS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_params)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        app.add_handler(conv_handler)
        logging.info("Conversation handler added successfully")

        logging.info("Starting bot polling...")
        app.run_polling()

    except Exception as e:
        logging.error(f"Error starting bot: {str(e)}")
        raise


if __name__ == "__main__":
    main()
