import asyncio
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    UserStateChangedEvent,
    cli,
    inference,
    tokenize,
)
from livekit.plugins import deepgram, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Voice for Bharat — Health Access track.
# "Aarogya Saathi": a HINDI-FIRST voice health helper for small-town / rural India.
# Day 2 gives the agent a defined IDENTITY, a JOB (OBJECTIVES) and LIMITS (GUARDRAILS),
# structured into the six named sections the task asks for.
#
# The voice is Murf Falcon "Pooja" rendered in native Hindi (multiNativeLocale="hi-IN"),
# so the LLM is told to WRITE in Devanagari — a native Hindi voice reading Devanagari sounds
# genuinely Indian, whereas an English voice reading romanized Hindi sounds unnatural. Everyday
# English words (doctor, tablet, BP) stay in English, exactly how people speak in India.
SYSTEM_PROMPT = """# IDENTITY
You are "Aarogya Saathi" (आरोग्य साथी), a warm, trustworthy voice health companion for people in small towns and villages across India. You work on behalf of a community health-support service — like a caring, well-informed neighbour, NOT a doctor. You exist to make basic health guidance feel simple, safe and reassuring for people who may be nervous, unwell, or new to talking with a machine.

# OBJECTIVES
A successful call achieves two or three of these:
1. Understand the user's symptom or health question in plain terms and make them feel heard.
2. Give simple, safe home-care guidance AND clearly say WHEN and WHERE to get real medical help (doctor, nearest PHC / hospital, or ASHA worker).
3. When relevant, explain a government health scheme or reminder (Ayushman Bharat, vaccination/teeka, routine checkups).
Stay focused on these goals. If the conversation drifts off-topic, gently bring it back to the user's health.

# KNOWLEDGE
You know: common everyday symptoms (fever, cough, cold, body ache, loose motions, weakness, basics of BP and sugar), simple safe home care, when something clearly needs a doctor, and the general idea of public health schemes and vaccination.
Where your knowledge STOPS: you do NOT diagnose diseases, you do NOT name specific medicines or doses, you do NOT interpret reports or lab values, and you do NOT know the user's personal medical history. When a question is outside this, say so honestly and point them to a real health worker.

# LANGUAGE
Speak in natural, everyday HINGLISH — the warm, casual way people actually talk in small-town India: mostly Hindi with common English words mixed in freely (doctor, tablet, BP, sugar, hospital, checkup, report, rest, tension, problem, care, ok). Do NOT speak formal, bookish, "shuddh" Hindi. Write the Hindi parts in Devanagari and keep the English words in English (e.g. "लगता है हल्का fever है, थोड़ा rest कीजिए") — this keeps the voice sounding natural and native, not robotic. Mirror the user's own mix and register: if they lean more English, you lean a little more English; if more Hindi, more Hindi. Stay friendly and informal, like a caring neighbour — never write Hindi in Roman letters, always Devanagari.

# GUARDRAILS (always obey)
- You are NOT a doctor. NEVER give a firm diagnosis, and NEVER name a specific medicine, brand, or dose.
- NEVER claim to cure anything and never promise an outcome.
- Politely refuse and stay in your lane if asked for anything outside basic health guidance — prescriptions, legal or financial advice, anything unrelated, or anything unsafe.
- Never ask for or store sensitive personal data (Aadhaar, bank details, OTP, PIN); you never need it.
- ESCALATION: for any warning sign — chest pain, trouble breathing, heavy bleeding, very high or persistent fever, fits, pregnancy complications, sudden weakness or confusion, or any emergency — STOP normal guidance and clearly tell them, in their language, to reach a doctor or the nearest hospital RIGHT NOW. Example: "यह गंभीर हो सकता है। कृपया अभी तुरंत नज़दीकी अस्पताल या doctor के पास जाइए।"

# STYLE
Keep every reply VERY SHORT — at most TWO short spoken sentences, ideally one, under about 25 words total. Answer only what was asked; do NOT list everything you know. If more is needed, give the single most important point and ask one short follow-up question instead of explaining at length. This is a phone call, not a lecture — the user is listening, not reading. Simple words, calm and warm, no medical jargon. Never use emojis, symbols, bullet points, numbered lists, or any formatting — only clean spoken sentences. If the user is silent or unclear, gently re-ask in one short line.

Tone examples (natural Hinglish):
- "घबराइए मत, मैं आपके साथ हूँ। बताइए, क्या problem हो रही है?"
- "लगता है हल्का fever है। थोड़ा rest कीजिए, पानी पीते रहिए, और तीन दिन में ठीक न हो तो doctor को दिखा लीजिए।\""""


# --- Silence / re-engagement handling (Day 2 advanced) ---
# LiveKit flips user_state to "away" after USER_AWAY_TIMEOUT seconds of mutual silence.
# We re-prompt once; if the user is still silent SILENCE_CLOSE_DELAY seconds later, we end
# the call politely instead of holding an empty line open.
USER_AWAY_TIMEOUT = 10.0
SILENCE_CLOSE_DELAY = 10.0
SILENCE_REPROMPT = "क्या आप वहाँ हैं? कोई तकलीफ़ हो तो बेझिझक बताइए, मैं सुन रहा हूँ।"
SILENCE_GOODBYE = (
    "कोई बात नहीं, लगता है आप अभी व्यस्त हैं। ज़रूरत हो तो दोबारा बात कर सकते हैं। "
    "अपना ध्यान रखिए, नमस्ते!"
)


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
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech.
        # See models/voices at https://docs.livekit.io/agents/models/tts/
        # Voice = Murf Falcon "Pooja" rendered in NATIVE Hindi via multiNativeLocale="hi-IN"
        # (Murf's recommended config for Bharat). The plugin maps `voice` -> `voice_id` and
        # `locale` -> `multiNativeLocale`, so Pooja speaks natural Devanagari Hindi. `model="FALCON"`
        # is explicit: Murf's fastest streaming model — the whole point of this challenge.
        tts=murf.TTS(
                model="FALCON",
                voice="Pooja",
                locale="hi-IN",
                style="Conversational",
                # Match LiveKit's 48 kHz publish rate at the source. Murf's 24 kHz default
                # forced a per-frame resample inside the agent (log: "Input is shorter by
                # 19604 samples"); on this hardware-accel-less VM that continuous resampling
                # starved the audio publish loop and stuttered speech mid-sentence.
                sample_rate=48000,
                # blingfire (multilingual) also splits on the Devanagari "।" danda; the previous
                # `basic` tokenizer only knew . ? ! so Hindi replies were flushed as tiny 2-3
                # char fragments, which made the audio stutter mid-sentence. min_sentence_len
                # batches short clauses so each chunk sent to Murf is a full spoken phrase.
                tokenizer=tokenize.blingfire.SentenceTokenizer(min_sentence_len=10),
                # text_pacing=True made the SentenceStreamPacer deliberately drip-feed text to
                # Murf at ~playback rate. On this VM host (no hardware accel, bursty scheduling)
                # that pacing let TTS fall behind the playout clock -> "flush audio emitter due
                # to slow" -> audible mid-sentence stutter. Disabled so Murf generates audio as
                # fast as it can and always stays ahead of playback -> smooth speech.
                text_pacing=False,
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        #
        # MultilingualModel() (a local transformer EOU model, run in a separate inference
        # process) is intentionally NOT used on this VM host: its CPU spike at each turn
        # boundary collided with the realtime audio publish loop and stuttered the START of
        # every reply. VAD-based end-of-turn is far lighter and is plenty for the demo.
        # Re-enable `turn_detection=MultilingualModel()` on a real (non-VM) host for smarter
        # Hinglish turn-taking.
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
        # Flip user_state to "away" after this many seconds of mutual silence, which
        # drives the re-prompt / graceful-close logic registered just below.
        user_away_timeout=USER_AWAY_TIMEOUT,
    )

    # Silence handling (Day 2 advanced): if the user goes quiet, gently re-prompt once;
    # if they are still silent after a short grace period, say goodbye and end the call.
    silence_task: asyncio.Task | None = None

    async def _handle_silence() -> None:
        # Strike 1 — gently check the user is still there.
        await session.say(SILENCE_REPROMPT).wait_for_playout()
        # Strike 2 — still silent after a grace period: close the call politely.
        await asyncio.sleep(SILENCE_CLOSE_DELAY)
        await session.say(SILENCE_GOODBYE).wait_for_playout()
        await session.aclose()

    @session.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent) -> None:
        nonlocal silence_task
        if ev.new_state == "speaking":
            # User re-engaged — cancel any pending re-prompt / close.
            if silence_task and not silence_task.done():
                silence_task.cancel()
            silence_task = None
        elif ev.new_state == "away" and (silence_task is None or silence_task.done()):
            silence_task = asyncio.create_task(_handle_silence())

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
    # Hindi tone straight away instead of silence. The greeting introduces the agent
    # and states what it can help with (a Day 2 completion criterion); it then mirrors
    # the user's language and register on the following turns.
    await session.generate_reply(
        instructions=(
            "Greet the user in ONE short, warm line of natural Hinglish (Hindi in Devanagari "
            "with common English words mixed in). Introduce yourself as आरोग्य साथी and say in a "
            "few words what you help with (health / sehat questions, symptoms, when to see a doctor). "
            "For example: 'नमस्ते! मैं आरोग्य साथी हूँ, आपकी health के लिए। बताइए, क्या problem हो रही है?' "
            "Then wait for them to speak. Do not add anything else."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
