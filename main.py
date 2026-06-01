import asyncio
import aiohttp
import os
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
from twilio.twiml.voice_response import VoiceResponse, Gather, Play

app = FastAPI()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("VOICE_ID")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

async def elevenlabs_tts(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            return await resp.read()

@app.post("/incoming-call")
async def incoming_call(request: Request):
    base_url = "https://voice.apsservice.theaifreedom.com"
    greeting = "Thank you for calling APS Service, Florida's mobile ADAS calibration experts. How can I help you today?"
    response = VoiceResponse()
    response.play(f"{base_url}/tts?text={greeting.replace(' ', '+')}")
    gather = Gather(input='speech', action='/handle-speech', method='POST', timeout=5, speech_timeout='auto')
    response.append(gather)
    return Response(content=str(response), media_type="application/xml")

@app.post("/handle-speech")
async def handle_speech(request: Request):
    form = await request.form()
    speech = form.get('SpeechResult', '')
    caller = form.get('From', 'Unknown')
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": f"NEW APS CALL\nFrom: {caller}\nMessage: {speech}"}
        )
    reply = "Thank you! Jason has been notified and will call you back shortly. Have a great day!"
    base_url = "https://voice.apsservice.theaifreedom.com"
    response = VoiceResponse()
    response.play(f"{base_url}/tts?text={reply.replace(' ', '+')}")
    return Response(content=str(response), media_type="application/xml")
