import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter, TelegramBadRequest
from dotenv import load_dotenv
import html
from telethon import TelegramClient
from collections import namedtuple

from logger import logger

load_dotenv()

SendTask = namedtuple('SendTask', ['type', 'message', 'chat_id'])
DeleteTask = namedtuple('DeleteTask', ['type', 'chat_id', 'limit'])
EditMessageTask = namedtuple('EditMessageTask', ['type', 'chat_id', 'message_id', 'message'])

# Initialize the bot
api_token = os.getenv('TELEGRAM_BOT_API_TOKEN')
CHANNEL_INFO = int(os.getenv('TELEGRAM_CHANNEL_INFO'))
CHANNEL_WARNING = int(os.getenv('TELEGRAM_CHANNEL_WARNING'))
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('TELEPHONE_NUMBER')
session_file = os.path.join(os.path.dirname(__file__), 'user.session')


class TelegramBot:
    def __init__(self, token, CHANNEL_INFO, CHANNEL_WARNING, initial_delay=1):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.CHANNEL_INFO = CHANNEL_INFO
        self.CHANNEL_WARNING = CHANNEL_WARNING
        self.message_queue: asyncio.Queue[dict] = asyncio.Queue()

        self.delay = initial_delay

    async def start_polling(self):
        asyncio.create_task(self.process_queue(self.message_queue))
        await self.dp.start_polling(self.bot)

    async def add_to_queue(self, tg_task):
        await self.message_queue.put(tg_task)

    async def process_queue(self, queue):
        while True:
            tg_task = await queue.get()
            if tg_task.type == 'send':
                await self.tg_send_message(tg_task.chat_id,
                                           tg_task.message)
            elif tg_task.type == 'edit':
                await self.tg_edit_message(tg_task.chat_id,
                                           tg_task.message_id,
                                           tg_task.message)
            elif tg_task.type == 'delete':
                await self.tg_delete_messages(tg_task.chat_id,
                                              tg_task.limit)
            await asyncio.sleep(self.delay)

    async def tg_send_message(self, chat_id, message):
        try:
            sent_message = await self.bot.send_message(chat_id=chat_id,
                                                       text=html.escape(message))
            self.delay = 1
            return sent_message.message_id
        except TelegramRetryAfter as e:
            logger.warning(f"Rate limit exceeded. Sleeping for {e.retry_after} seconds.")
            self.delay = e.retry_after + 2
            await self.add_to_queue(chat_id, {'type': 'send', 'message': message})
        except TelegramAPIError as e:
            logger.error(f"Telegram API error occurred: {e}")
            await self.add_to_queue(chat_id, {'type': 'send', 'message': message})

    async def tg_edit_message(self, chat_id, message_id, message):
        try:
            await self.bot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text=message)
            self.delay = 1
        except TelegramRetryAfter as e:
            logger.warning(f"Rate limit exceeded. Sleeping for {e.retry_after} seconds.")
            self.delay = e.retry_after + 2
            await self.add_to_queue(
                EditMessageTask(type='edit', chat_id=telegram_bot.CHANNEL_INFO,
                                message_id=message_id,
                                message=message)
            )
        except TelegramBadRequest as e:
            if 'message is not modified' in str(e):
                logger.warning(f"Message not modified. Skipping update.")
                return
            elif ('message to edit not found' in str(e) or
                  'MESSAGE_ID_INVALID' in str(e)):
                logger.warning(f"{str(e)} {message}")
                new_message_id = await self.tg_send_message(chat_id, message)
                return new_message_id
        except TelegramAPIError as e:
            logger.error(f"Telegram API error occurred: {e}")
            await self.add_to_queue(
                EditMessageTask(type='edit', chat_id=telegram_bot.CHANNEL_INFO,
                                message_id=message_id,
                                message=message)
            )

    async def tg_delete_messages(self, chat_id, limit=None):
        client = TelegramClient(session_file, api_id, api_hash)
        await client.start(phone=phone_number)
        try:
            peer = await client.get_input_entity(chat_id)
            async for message in client.iter_messages(peer, limit=limit):
                try:
                    await client.delete_messages(chat_id, message.id)
                    logger.info(f"Удалено сообщение с ID {message.id} из чата {chat_id}")
                except Exception as e:
                    logger.error(f"Не удалось удалить сообщение с ID {message.id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении истории сообщений: {e}")
        finally:
            await client.disconnect()

    async def tg_delete_messages_by_id(self, chat_id, message_ids):
        client = TelegramClient(session_file, api_id, api_hash)
        await client.start(phone=phone_number)
        try:
            peer = await client.get_input_entity(chat_id)
            for message_id in message_ids:
                try:
                    await client.delete_messages(peer, message_id)
                    logger.info(f"Удалено сообщение с ID {message_id} из чата {chat_id}")
                except Exception as e:
                    logger.error(f"Не удалось удалить сообщение с ID {message_id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении истории сообщений: {e}")
        finally:
            await client.disconnect()


telegram_bot = TelegramBot(api_token, CHANNEL_INFO, CHANNEL_WARNING)


# Example usage
async def main():
    asyncio.create_task(telegram_bot.start_polling())
    await telegram_bot.add_to_queue(SendTask(type='send',
                                             message='Hello Group 1!',
                                             chat_id=telegram_bot.CHANNEL_INFO))
    await telegram_bot.add_to_queue(
        SendTask(type='send', message='Hello Group 2!', chat_id=telegram_bot.CHANNEL_WARNING)
    )
    await telegram_bot.add_to_queue(
        DeleteTask(type='delete', chat_id=telegram_bot.CHANNEL_INFO, limit=None)
    )
    # await telegram_bot.add_to_queue(
    #     DeleteTask(type='delete', chat_id=telegram_bot.CHANNEL_WARNING, limit=None)
    # )
    # await telegram_bot.tg_edit_message(chat_id=telegram_bot.CHANNEL_WARNING,
    #                                    message_id=1183,
    #                                    message='message')
    # await telegram_bot.add_to_queue(
    #     SendTask(type='send', message='Hello Group 1!', chat_id=telegram_bot.CHANNEL_INFO)
    # )
    await asyncio.sleep(111)


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
