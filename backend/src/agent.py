import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
)
from livekit.plugins import deepgram, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Voice for Bharat — Health Access track.
# "Aarogya Saathi": a voice health helper for small-town / rural India that speaks
# in a natural Hindi + English (Hinglish) mix.
SYSTEM_PROMPT = """You are "Aarogya Saathi", a warm, friendly voice health helper for people in small towns and villages across India. You help users understand common health symptoms, guide them on simple home care and when to see a doctor or go to the nearest Primary Health Centre (PHC), explain government schemes like Ayushman Bharat, and remind them about medicines and vaccinations.

HOW YOU TALK — this is the MOST important thing:
Speak in simple, warm, natural Indian ENGLISH. Your warmth must come from your TONE, NOT from inserted Hindi words. Do NOT use "beta", and do NOT lean on any filler word. Keep replies as clean plain English. A single light Hindi touch (like "thoda" or "theek hai?") is allowed only RARELY — at most once in a few replies, and never the same word repeatedly. ONLY if the user clearly speaks in Hindi, then fully switch and reply in natural romanized HINGLISH, matching them. NEVER use Devanagari script, and do NOT use heavy/literary Hindi. Keep medical and common English words as English (doctor, tablet, checkup, BP, sugar, hospital, vaccine).

Tone examples:
- "Don't worry, I'm here with you. Tell me — what's been troubling you?"
- "Sounds like a mild fever. Take some rest, keep sipping water, and if it's not better in three days, please see a doctor."
- If the user speaks Hindi: "Are koi baat nahi, main hun na. Bukhaar hai to thoda aaram kijiye, paani peete rahiye, aur teen din me theek na ho to doctor ko dikha lijiye."

Keep every answer SHORT — just two or three small sentences, because the user is listening, not reading. Simple words, no heavy medical jargon. Stay warm, calm and encouraging.

SAFETY (always follow): You are NOT a doctor. Never give a firm diagnosis and never name a specific medicine or dose. For anything serious — chest pain, trouble breathing, heavy bleeding, very high fever, pregnancy problems, or any emergency — clearly and immediately tell the user (in their own language) to see a doctor or reach the nearest hospital right away.

Never use emojis, symbols, bullet points, or any formatting — only clean, spoken sentences."""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        # language="multi" is REQUIRED for Hinglish: Nova-3 handles live Hindi<->English
        # code-switching only through the "multi" model (no dedicated hi-EN model exists).
        # keyterms bias recognition toward this app's health/scheme vocabulary so mixed
        # speech like "bukhar", "Ayushman", "PHC" is captured cleanly.
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            keyterms=[
                "bukhar", "khansi", "zukaam", "sardi", "dard", "sir dard",
                "pet dard", "saans", "chakkar", "ulti", "dast", "kamzori",
                "BP", "blood pressure", "sugar", "diabetes", "pregnancy",
                "garbhavastha", "dawai", "tablet", "injection", "teeka",
                "vaccine", "Ayushman Bharat", "PHC", "ASHA", "doctor",
            ],
        ),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # LLM via LiveKit Inference gateway — authenticates with LIVEKIT_API_KEY/SECRET,
        # so no separate Gemini/OpenAI key is needed (billed to LiveKit Build inference credits).
        llm=inference.LLM(model="google/gemini-2.5-flash"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        # Voice on Murf Falcon — Indian ENGLISH voice, because English is the agent's
        # default language (it mirrors into romanized Hinglish when the user speaks Hindi).
        # "en-IN-anisha" speaks native Indian English and reads romanized Hinglish with a
        # natural Indian accent. If you want NATIVE Hindi audio instead, switch the prompt
        # back to Devanagari and use a hi-IN voice (hi-IN-khyati / hi-IN-namrita / hi-IN-aman;
        # samples in ~/voice-for-bharat/voice-samples/).
        tts=murf.TTS(
                voice="en-IN-anisha",
                locale="en-IN",
                style="Conversational",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    #
    # NOTE: LiveKit's noise cancellation (Krisp BVC) is intentionally NOT enabled here.
    # Its native lib (liblivekit_nc_plugin.dylib) bundles Intel MKL, which segfaults on
    # this AMD Ryzen host ("Intel MKL ERROR: CPU 0 is not supported") the moment mic audio
    # is processed, killing the agent job. VAD/STT/LLM/TTS do not use MKL and run fine.
    # To re-enable BVC, run the backend on an Intel CPU (or a host that exposes AVX2).
    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Kick things off with a short, warm greeting so the user hears the natural
    # tone straight away instead of silence. Default is English; the agent then
    # mirrors the user's language on the next turns.
    await session.generate_reply(
        instructions=(
            "Greet the user in ONE short, warm, natural line in simple Indian English "
            "— for example: 'Namaste! I'm Aarogya Saathi, here for your health. "
            "Tell me, what's been troubling you?' — then wait for them to speak. "
            "Do not add anything else."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
