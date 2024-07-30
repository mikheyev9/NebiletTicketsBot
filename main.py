import asyncio
from collections import namedtuple
from dotenv import load_dotenv
import os

from database import (init_db,
                      get_previous_results)
from request import check_events
from telegram import (telegram_bot,
                      SendTask)
from database import (save_site_result_to_db,
                      load_message_ids,
                      save_message_ids,
                      DBConnection)
from logger import logger, EventMessage
from calculate import (calculate_percentage,
                       calculate_average_percentage,
                       calculate_percentage_drop,
                       were_tickets_available)

load_dotenv()

DOMAIN = os.getenv('DOMAIN')
CHECK_INTERVAL = 20
BASE_URL = f"http://{DOMAIN}/react_api/v1/check_ticket_availability"
EventResult = namedtuple('EventResult', ['site_name', 'total_events_count',
                                         'events_with_tickets_count', 'events_without_tickets_count'])


async def scheduled_check():
    await init_db()
    db_connection = DBConnection(logger=logger,
                                 use_json=False)
    message_ids: list = await load_message_ids()
    asyncio.create_task(telegram_bot.start_polling())

    while True:
        try:
            message_for_tg = EventMessage()
            site_names = await db_connection.get_sites()
            successful_requests, errors_requests = await check_events(BASE_URL, site_names)

            for result in successful_requests:
                site_info = EventResult(*result)
                percentage_with_tickets = calculate_percentage(site_info)
                message_for_tg.add(site_info, percentage_with_tickets)
                previous_results = await get_previous_results(site_info.site_name, limit=10)

                if previous_results:
                    average_previous_percentage = calculate_average_percentage(previous_results)
                    percentage_drop = calculate_percentage_drop(average_previous_percentage, percentage_with_tickets)
                    if (percentage_drop > 10 and
                            percentage_with_tickets == 0 and
                            were_tickets_available(previous_results[:1])):
                        message = message_for_tg.add_warning(site_info.site_name,
                                                             percentage_drop,
                                                             need_return=True)
                        await telegram_bot.add_to_queue(
                            SendTask(type='send', message=message, chat_id=telegram_bot.CHANNEL_WARNING)
                        )
                    if percentage_with_tickets > 0 and not were_tickets_available(previous_results[:1]):
                        message = message_for_tg.add_available_ticket(site_info.site_name,
                                                                      percentage_with_tickets,
                                                                      need_return=True)
                        await telegram_bot.add_to_queue(
                            SendTask(type='send', message=message, chat_id=telegram_bot.CHANNEL_WARNING)
                        )

                await save_site_result_to_db(*site_info)

            for error in errors_requests:
                logger.error(f"An error occurred: {error}")

            if message_ids:
                if len(message_for_tg.message_parts) > len(message_ids):
                    # Если частей сообщений больше, чем сохраненных message_id, добавляем новые сообщения
                    for part, message_id in zip(message_for_tg.message_parts, message_ids):
                        edit_message_id = await telegram_bot.tg_edit_message(telegram_bot.CHANNEL_INFO,
                                                                             message_id,
                                                                             part)
                        if edit_message_id:
                            message_ids.remove(message_id)
                            message_ids.append(edit_message_id)
                    for part in message_for_tg.message_parts[len(message_ids):]:
                        message_id = await telegram_bot.tg_send_message(telegram_bot.CHANNEL_INFO, part)
                        message_ids.append(message_id)
                else:
                    if len(message_for_tg.message_parts) < len(message_ids):
                        # Если частей сообщений меньше, чем сохраненных message_id, удаляем лишние сообщения
                        await telegram_bot.tg_delete_messages_by_id(
                            telegram_bot.CHANNEL_INFO,
                            message_ids[len(message_for_tg.message_parts):]
                        )
                        message_ids = message_ids[:len(message_for_tg.message_parts)]
                    # Если частей сообщений меньше или равно количеству сохраненных message_id, обновляем существующие сообщения
                    for message_id, part in zip(message_ids, message_for_tg.message_parts):
                        edit_message_id = await telegram_bot.tg_edit_message(telegram_bot.CHANNEL_INFO,
                                                                             message_id,
                                                                             part)
                        if edit_message_id:
                            message_ids.remove(message_id)
                            message_ids.append(edit_message_id)
            else:
                # Если нет сохраненных message_id, отправляем новые сообщения
                await telegram_bot.tg_delete_messages(telegram_bot.CHANNEL_INFO)
                for part in message_for_tg.message_parts:
                    message_id = await telegram_bot.tg_send_message(telegram_bot.CHANNEL_INFO, part)
                    message_ids.append(message_id)
            await save_message_ids(message_ids)
            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"An error occurred during scheduled check: {e}")
            await asyncio.sleep(CHECK_INTERVAL)


async def main():
    await scheduled_check()


if __name__ == "__main__":
    asyncio.run(main())
