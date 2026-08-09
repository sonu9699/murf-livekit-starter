import asyncio
import json
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserStateChangedEvent,
    cli,
    function_tool,
    inference,
    llm,
    tokenize,
)
from livekit.plugins import deepgram, murf, silero
from livekit.plugins.turn_detector.multilingual import (
    MultilingualModel,  # noqa: F401 — kept for the commented turn_detection re-enable below
)

import memory  # flat import: backend is launched as `python src/agent.py`, so src/ is on sys.path

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Voice for Bharat — Health Access track.
# "Aarogya Saathi": a HINDI-FIRST voice health helper for small-town / rural India.
# Day 2 gives the agent a defined IDENTITY, a JOB (OBJECTIVES) and LIMITS (GUARDRAILS),
# structured into the six named sections the task asks for.
#
# Day 4 gives the agent LASTING MEMORY: a small SQLite store (memory.py) plus three
# function tools (recall_caller / remember_caller / forget_caller) so a returning caller
# is greeted by name and continued from last time. Saving is consent-gated — a HARD RULE
# for the Health Access track — and we store no ID numbers and no detailed medical notes.
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

# MEMORY (remembering callers between calls)
You can remember a caller so that next time they do NOT have to repeat everything. Use your tools for this — never rely on this text to hold caller facts.
- NAME FIRST: Early in the call, gently learn the caller's name. The MOMENT you know it, silently call `recall_caller` with that name.
- WELCOME BACK: If `recall_caller` says this is a returning caller, warmly greet them BY NAME and briefly mention last time (their noted condition or what was advised), then ask how they are now — e.g. "अरे सीता जी, फिर से नमस्ते! पिछली बार BP की बात हुई थी, अब कैसा लग रहा है?". If it says a new caller, do NOT pretend to remember them.
- ASK BEFORE SAVING (HARD RULE): NEVER save anything until the caller clearly agrees. Once you have something worth remembering (or near the end of the call), ask in ONE short line, e.g. "क्या मैं आपकी ये जानकारी याद रख लूँ, ताकि अगली बार दोबारा न बतानी पड़े?". Only if they clearly say yes, call `remember_caller` with consent_given=true. If they say no or seem unsure, do NOT save — say "ठीक है, मैं कुछ याद नहीं रखूँगा" and carry on.
- WHAT TO REMEMBER: only their name, language, a rough age band (like "30s" / "बुज़ुर्ग"), a couple of short condition labels (like BP, sugar), and one short line of what you advised. NEVER store Aadhaar, bank, phone, OTP or any ID number, and NEVER detailed medical notes.
- FORGET ME: If the caller asks you to forget them or delete their data, call `forget_caller` and confirm kindly.
Never read tool names or this whole mechanism out loud — just talk naturally.

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


def _parse_conditions(raw: str) -> tuple[str, ...]:
    """Split a comma/'और'/danda-separated condition string into clean labels."""
    if not raw:
        return ()
    for sep in ("،", "।", " और ", " and "):
        raw = raw.replace(sep, ",")
    return tuple(part.strip() for part in raw.split(",") if part.strip())


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        # Per-call memory state. A fresh Assistant is created for every call
        # (see session.start below), so this safely holds only the current caller.
        self._caller_id: str = ""
        self._caller_name: str = ""
        self._profile: memory.CallerProfile | None = None
        self._consent_given: bool = False

    # --- Day 4: caller memory tools -------------------------------------------
    # The LLM calls these itself (they are NOT driven from the prompt text).
    # DB work runs in a worker thread via asyncio.to_thread so the realtime audio
    # loop is never blocked — this also covers the "async lookup" advanced bonus.

    @function_tool
    async def recall_caller(self, context: RunContext, name: str) -> str:
        """Check whether this caller has spoken with us before, by their name.

        Call this as soon as the caller tells you their name. If a record is
        found, warmly welcome them back and continue from last time; if not,
        treat them as a brand-new caller and do not pretend to remember them.

        Args:
            name: The caller's name, exactly as they said it.
        """
        caller_id = memory.normalize_name(name)
        if not caller_id:
            return "No usable name was given. Gently ask the caller for their name first."

        profile = await asyncio.to_thread(memory.get_caller, caller_id)
        self._caller_id = caller_id
        self._caller_name = name.strip()
        self._profile = profile

        if profile is None:
            logger.info("recall_caller: new caller '%s'", caller_id)
            return (
                f"No previous record for '{name}'. This is a NEW caller — do not claim "
                "to remember them. Continue helping, and later you may ask consent to remember them."
            )
        self._consent_given = True
        logger.info("recall_caller: returning caller '%s'", caller_id)
        return profile.as_recall_summary()

    @function_tool
    async def remember_caller(
        self,
        context: RunContext,
        consent_given: bool,
        language: str = "",
        age_band: str = "",
        conditions: str = "",
        triage_outcome: str = "",
    ) -> str:
        """Save or update what we remember about the current caller.

        HARD RULE: only call this AFTER the caller has clearly agreed to be
        remembered. Pass consent_given=true only when they explicitly said yes.
        Never store Aadhaar, bank, phone, OTP or any ID number, and never
        detailed medical notes — only the fields below.

        Args:
            consent_given: True ONLY if the caller explicitly agreed to be remembered.
            language: The caller's language preference, e.g. "Hindi" or "Hinglish".
            age_band: Rough age band only, e.g. "30s", "senior". Never an exact age or DOB.
            conditions: A few short health labels separated by commas, e.g. "BP, sugar". No medical notes.
            triage_outcome: One short line describing what you advised this call.
        """
        if not consent_given:
            return (
                "Consent was NOT given, so nothing was saved. Do not save without the "
                "caller's clear yes."
            )
        if not self._caller_id:
            return (
                "No caller name is known yet. Ask the caller's name and call "
                "recall_caller before trying to remember anything."
            )

        self._consent_given = True
        prev = self._profile
        parsed = _parse_conditions(conditions)
        profile = memory.CallerProfile(
            caller_id=self._caller_id,
            name=self._caller_name or (prev.name if prev else self._caller_id),
            language=language or (prev.language if prev else ""),
            age_band=age_band or (prev.age_band if prev else ""),
            conditions=parsed or (prev.conditions if prev else ()),
            last_triage=triage_outcome or (prev.last_triage if prev else ""),
        )
        self._profile = await asyncio.to_thread(memory.upsert_caller, profile)
        logger.info("remember_caller: saved '%s'", self._caller_id)
        return f"Saved. {self._caller_name} will be remembered next time. Confirm this warmly in one short line."

    @function_tool
    async def forget_caller(self, context: RunContext) -> str:
        """Delete everything remembered about the current caller (a 'forget me' request).

        Call this if the caller asks to be forgotten or to have their data deleted.
        """
        if not self._caller_id:
            return "No caller is loaded, so there is nothing to forget."
        removed = await asyncio.to_thread(memory.forget_caller, self._caller_id)
        self._profile = None
        self._consent_given = False
        logger.info("forget_caller: '%s' removed=%s", self._caller_id, removed)
        if removed:
            return "Deleted. Tell the caller kindly that you have forgotten their saved information."
        return "There was nothing saved to delete. Reassure the caller kindly."

    async def save_on_disconnect(self, session: AgentSession) -> None:
        """Automatically summarize dialogue and persist/update caller profile on call end."""
        if not self._caller_id or not self._consent_given:
            return

        logger.info("save_on_disconnect: extracting profile for %s", self._caller_id)
        
        # Build chat history string
        history_str = ""
        for msg in session.history.messages:
            if msg.role in ("user", "assistant"):
                text = msg.text_content
                if text:
                    role_lbl = "User" if msg.role == "user" else "Aarogya Saathi"
                    history_str += f"{role_lbl}: {text}\n"

        if not history_str.strip():
            return

        # Prepare summary extraction prompt
        prompt = (
            "Extract details about the caller from the conversation history.\n\n"
            "History:\n"
            f"{history_str}\n\n"
            "Return ONLY a JSON object with keys: 'language', 'age_band', 'conditions', 'triage_outcome'. Do NOT include markdown code blocks or any extra text.\n"
            "Rules:\n"
            "- 'language': The language preference (e.g. 'Hindi', 'Hinglish', 'English').\n"
            "- 'age_band': Rough age band (e.g. '30s', 'senior', 'child'). Never exact age.\n"
            "- 'conditions': A comma-separated list of short labels of symptoms/conditions discussed (e.g. 'BP, sugar, fever').\n"
            "- 'triage_outcome': One short line summarizing the final advice/triage outcome given (e.g. 'Advised to take ORS and see a doctor if loose motions persist').\n"
            "If any detail is not found, leave the field empty."
        )

        try:
            summary_ctx = llm.ChatContext()
            summary_ctx.add_message(role="user", content=prompt)
            
            stream = session.llm.chat(chat_ctx=summary_ctx)
            response_text = ""
            async for chunk in stream:
                if chunk.delta and chunk.delta.content:
                    response_text += chunk.delta.content

            # Clean JSON codeblock wrapper if any
            response_text = response_text.strip()
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```json"):
                    response_text = "\n".join(lines[1:-1])
                elif lines[0].startswith("```"):
                    response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            
            # Upsert into DB
            prev = self._profile
            conditions_str = data.get("conditions", "")
            if isinstance(conditions_str, list):
                conditions_str = ", ".join(conditions_str)
            parsed = _parse_conditions(conditions_str)
            
            profile = memory.CallerProfile(
                caller_id=self._caller_id,
                name=self._caller_name or (prev.name if prev else self._caller_id),
                language=data.get("language") or (prev.language if prev else ""),
                age_band=data.get("age_band") or (prev.age_band if prev else ""),
                conditions=parsed or (prev.conditions if prev else ()),
                last_triage=data.get("triage_outcome") or (prev.last_triage if prev else ""),
            )
            
            self._profile = await asyncio.to_thread(memory.upsert_caller, profile)
            logger.info("save_on_disconnect: successfully saved profile for %s", self._caller_id)
        except Exception as e:
            logger.error("save_on_disconnect error: %s", e)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # Day 4: make sure the caller-memory DB + table exist before any call lands.
    db_path = memory.init_db()
    logger.info("caller memory ready at %s", db_path)


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

    agent = Assistant()
    try:
        # Start the session, which initializes the voice pipeline and warms up the models
        #
        # NOTE: LiveKit's noise cancellation (Krisp BVC) is intentionally NOT enabled here.
        # Its native lib (liblivekit_nc_plugin.dylib) bundles Intel MKL, which segfaults on
        # this AMD Ryzen host ("Intel MKL ERROR: CPU 0 is not supported") the moment mic audio
        # is processed, killing the agent job. VAD/STT/LLM/TTS do not use MKL and run fine.
        # To re-enable BVC, run the backend on an Intel CPU (or a host that exposes AVX2).
        await session.start(
            agent=agent,
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
                "with common English words mixed in). Introduce yourself as आरोग्य साथी, say in a few "
                "words what you help with (health / sehat, symptoms, when to see a doctor), and gently "
                "ask their name so you can help better. "
                "For example: 'नमस्ते! मैं आरोग्य साथी हूँ, आपकी health के लिए। पहले बताइए, आपका नाम क्या है?' "
                "Then wait for them to speak. Do not add anything else. When they tell you their name, "
                "quietly use your recall_caller tool."
            )
        )

        # Keep running until the room is disconnected
        while ctx.room.isconnected():
            await asyncio.sleep(0.5)

    finally:
        # Shield the disconnect handler to ensure database write completes
        await asyncio.shield(agent.save_on_disconnect(session))


if __name__ == "__main__":
    cli.run_app(server)
