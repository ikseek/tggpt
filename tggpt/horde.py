import asyncio
import base64
from os import environ
from stablehorde_api import StableHordeAPI, GenerationInput
from datetime import timedelta
import json

class StableHorde(StableHordeAPI):
    async def models(self):
        response = await self._request(self.api + '/status/models', "GET", {"type":"image"})
        return await response.content.read()


models_cache = set()
client = StableHorde(environ["STABLEHORDE_API_KEY"])


async def generate_image(prompt: str):
    parts = prompt.split("|", 1)
    model_name = parts[0].strip()
    if model_name in await list_models():
        prompt = parts[1].strip()
    else:
        model_name = "Anything Diffusion"

    params = GenerationInput(prompt, models=[model_name], nsfw=True, censor_nsfw=False, r2=False)
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


async def list_models():
    global models_cache
    if not models_cache:
        res = await client.models()
        models_cache = set(m["name"] for m in json.loads(res))
    return models_cache