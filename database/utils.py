import os
import json
import aiofiles
from typing import List

filename_default = os.path.join(os.path.dirname(__file__), 'message_ids.json')
async def save_message_ids(message_ids: List[int],
                           filename=filename_default):
    async with aiofiles.open(filename, 'w') as file:
        await file.write(json.dumps(message_ids, indent=2))

async def load_message_ids(filename=filename_default) -> List[int]:
    try:
        async with aiofiles.open(filename, 'r') as file:
            data = json.loads(await file.read())
            return data
    except FileNotFoundError:
        return []
