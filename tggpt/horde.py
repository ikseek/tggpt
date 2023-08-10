import asyncio
import base64
from os import environ
from stablehorde_api import StableHordeAPI, GenerationInput
from datetime import timedelta

client = StableHordeAPI(environ["STABLEHORDE_API_KEY"])


async def generate_image(prompt: str):
    params = GenerationInput(prompt, nsfw=True, censor_nsfw=False, r2=False)
    request_id = (await client.txt2img_request(params)).id

    status = await client.generate_check(request_id)
    while not status.done:
        yield "generating", timedelta(seconds=status.wait_time)
        await asyncio.sleep(max(2, status.wait_time / 100))
        status = await client.generate_check(request_id)

    generate_status = await client.generate_status(request_id)
    for num, generation in enumerate(generate_status.generations):
        img_bytes = base64.b64decode(generation.img)
        yield "done", img_bytes
