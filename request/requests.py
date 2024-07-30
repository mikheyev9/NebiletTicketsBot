import httpx
import asyncio

from logger import logger

MAX_CONCURRENT_REQUESTS = 3
RETRY_LIMIT = 3
headers = httpx.Headers(headers={
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, как Gecko) Chrome/126.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Linux\""
    }, encoding='utf-8')

async def check_events(base_url: str, site_names: list):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with httpx.AsyncClient() as client:
        async def sem_task(site_name):
            async with semaphore:
                try:
                    return await _handle_event_data(client, base_url, site_name), None
                except Exception as e:
                    return None, e

        tasks = [sem_task(site_name) for site_name in site_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_results = (result for result, error in results if error is None)
    errors = (error for result, error in results if error is not None)
    return successful_results, errors

async def _handle_event_data(client, base_url, site_name):
    params = {'site-name': site_name}
    data = await _fetch_event_data(client, base_url, params)
    if data and "total_events_count" in data:
        total_events_count = data["total_events_count"]
        events_with_tickets_count = data["events_with_tickets_count"]
        events_without_tickets_count = data["events_without_tickets_count"]
        return (site_name,
                total_events_count,
                events_with_tickets_count,
                events_without_tickets_count)
    return None

async def _fetch_event_data(client, url, params):
    retries = 0
    while retries < RETRY_LIMIT:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as exc:
            logger.error(f"An error occurred while requesting {url} with params {params}: {exc}")
            retries += 1
            await asyncio.sleep(2 ** retries)

    return None

