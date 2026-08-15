import asyncio
import json
import logging
import time

import aiohttp
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
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

import calls
import escalation
import facilities
import memory  # flat import: backend is launched as `python src/agent.py`, so src/ is on sys.path
import triage

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Voice for Bharat — Health Access track.
# "Pooja": a HINDI-FIRST voice health helper for small-town / rural India.
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
You are "Pooja" (पूजा), a warm, trustworthy voice health companion for people in small towns and villages across India. You work on behalf of a community health-support service — like a caring, well-informed neighbour, NOT a doctor. You exist to make basic health guidance feel simple, safe and reassuring for people who may be nervous, unwell, or new to talking with a machine.

# OBJECTIVES
A successful call achieves two or three of these:
1. Understand the user's symptom or health question in plain terms and make them feel heard.
2. Give simple, safe home-care guidance AND clearly say WHEN and WHERE to get real medical help (doctor, nearest PHC / hospital, or ASHA worker). You can look up the nearest health facility if they ask and provide their 6-digit PIN code.
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
- Politely refuse and stay in your lane if asked for anything outside basic health guidance — prescriptions, legal or financial advice, anything unrelated, or anything unsafe. If they ask for a diagnosis or prescription, explain that you are an AI companion, not a doctor, but offer to escalate their request to a real doctor or senior health worker.
- Never ask for or store sensitive personal data (Aadhaar, bank details, OTP, PIN); you never need it. Note: A 6-digit postal PIN code is NOT sensitive personal data; you may ask for it to find the nearest health facility.
- ESCALATION (Day 7): for any warning sign — chest pain, trouble breathing, heavy bleeding, very high or persistent fever, fits, pregnancy complications, sudden weakness or confusion, or any emergency — STOP normal guidance immediately. You MUST tell them to reach a doctor or hospital immediately, AND ask for permission to escalate using these exact words: "क्या मैं आपकी ये जानकारी senior doctor को भेजना चाहती हूँ ताकि वे आपसे संपर्क कर सकें? क्या मुझे इसकी अनुमति है?". If they say yes, call the `create_escalation` tool. If they say no, respect it: "ठीक है, मैं नहीं भेजूँगी।" and continue with standard care guidance.

# MEMORY (remembering callers between calls)
You can remember a caller so that next time they do NOT have to repeat everything. Use your tools for this — never rely on this text to hold caller facts.
- NAME FIRST: Early in the call, gently learn the caller's name. The MOMENT you know it, silently call `recall_caller` with that name.
- WELCOME BACK: If `recall_caller` says this is a returning caller, warmly greet them BY NAME and briefly mention last time (their noted condition or what was advised), then ask how they are now — e.g. "अरे सीता जी, फिर से नमस्ते! पिछली बार BP की बात हुई थी, अब कैसा लग रहा है?". If it says a new caller, do NOT pretend to remember them.
- ASK BEFORE SAVING (HARD RULE): NEVER save anything until the caller clearly agrees. Once you have something worth remembering (or near the end of the call), ask in ONE short line, e.g. "क्या मैं आपकी ये जानकारी याद रख लूँ, ताकि अगली बार दोबारा न बतानी पड़े?". Only if they clearly say yes, call `remember_caller` with consent_given=true. If they say no or seem unsure, do NOT save — say "ठीक है, मैं कुछ याद नहीं रखूँगा" and carry on.
- WHAT TO REMEMBER: only their name, language, a rough age band (like "30s" / "बुज़ुर्ग"), a couple of short condition labels (like BP, sugar), and one short line of what you advised. NEVER store Aadhaar, bank, phone, OTP or any ID number, and NEVER detailed medical notes.
- FORGET ME: If the caller asks you to forget them or delete their data, call `forget_caller` and confirm kindly.
Never read tool names or this whole mechanism out loud — just talk naturally.

# HEALTH FACILITY LOOKUP (nearest doctor/clinic/hospital/PHC/CHC)
If the caller asks for the nearest doctor, clinic, hospital, PHC, or CHC:
- First, politely ask them to state their 6-digit postal PIN code (PIN code). For example: "नज़दीकी अस्पताल या PHC ढूंढने के लिए, कृपया अपना 6-digit का PIN code बताइए।"
- Once they state a 6-digit PIN code, immediately call the `lookup_nearest_facility` tool with that PIN code.
- Present the result exactly as returned by the tool, including mentioning that the information is from the August 2026 health directory. Keep the final response short and in Hinglish (Devanagari script).

# HEALTH TOOLS (triage, eligibility, vaccination under August 2026 guidelines)
- Symptom Triage (`classify_triage_level`): Call this when the caller describes physical complaints/symptoms. It will classify severity and recommend emergency help, doctor visit, or home care. If the result indicates an Emergency or a serious warning sign (such as chest pain or trouble breathing), you MUST immediately tell them to reach a doctor or hospital AND ask for permission to escalate using the exact escalation question: "क्या मैं आपकी ये जानकारी senior doctor को भेजना चाहती हूँ ताकि वे आपसे संपर्क कर सकें? क्या मुझे इसकी अनुमति है?".
- Ayushman Bharat Eligibility (`check_ayushman_eligibility`): Call this if the caller asks about getting or eligibility for an Ayushman Bharat card. You must ask: (1) if it is a rural household, (2) if they have a pucca house, and (3) if they do landless manual labor. Then call the tool.
- Teekakaran Schedule (`get_vaccination_schedule`): Call this if a parent asks when their baby's next vaccine/teeka is due. Ask for the baby's age in months and call the tool.
- Jan Aushadhi Generic Medicine Price (`lookup_generic_medicine_price`): Call this if the caller asks for cheap medicine, generic vs branded price, or details about medicine prices under Jan Aushadhi. Call the tool with the medicine name.
- PM Matru Vandana Yojana (PMMVY) Maternity Benefit (`check_maternity_benefit_eligibility`): Call this if a user/mother asks about government schemes, financial aid, or cash benefits for pregnancy or lactation. You must ask: (1) if it is the first child, (2) if it is the second child and is a girl child, and (3) if the mother has a government job.
- Human Help Escalation (`create_escalation`): Call this when the caller reports a red-flag symptom or asks for a diagnosis/prescription AND explicitly consents to sharing their info. You must pass caller_name, language, symptoms, urgency level (Low/Medium/High/Emergency), follow-up method (e.g. phone call), and a short summary of the check. Once called, say the reference ID (e.g. ESC-XXXX) to the caller.
- Clinic and Appointment Booking (transfer_to_appointments): Call this immediately if the caller wants to book, schedule, reschedule, or cancel a doctor, clinic, PHC, or hospital appointment. You do not handle appointments yourself; you must transfer the user to the specialist agent. When calling this tool, you must tell the user that you are transferring them to the clinic and appointment specialist (in Hinglish Devanagari script). Do not say that the appointment will be booked soon or that you are booking it yourself.

# TELEPHONY / CALL CONTROL
- If the caller says they are not free, do not want to talk, say no, or want to hang up, immediately say a short friendly goodbye in Hinglish and use the `end_call` tool to hang up the phone call.

# STYLE
Keep every reply VERY SHORT — at most TWO short spoken sentences, ideally one, under about 25 words total. (Exception: When warning the user about an emergency/warning sign and asking for escalation consent, you can use up to 4 sentences and 50 words to ensure safety and collect clear consent). Answer only what was asked; do NOT list everything you know. If more is needed, give the single most important point and ask one short follow-up question instead of explaining at length. This is a phone call, not a lecture — the user is listening, not reading. Simple words, calm and warm, no medical jargon. Never use emojis, symbols, bullet points, numbered lists, or any formatting — only clean spoken sentences. If the user is silent or unclear, gently re-ask in one short line.

Tone examples (natural Hinglish):
- "घबराइए मत, मैं आपके साथ हूँ। बताइए, क्या problem हो रही है?"
- "लगता है हल्का fever है। थोड़ा rest कीजिए, पानी पीते रहिए, और तीन दिन में ठीक न हो तो doctor को दिखा लीजिए।"""


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


APPOINTMENT_PROMPT = """# IDENTITY
You are "Abhinav" (अभिनव), the Clinic and Appointment Specialist helper for Aarogya Saathi. Your ONLY job is to help users schedule and book appointments at their preferred health facility (like a Primary Health Center - PHC, Community Health Center - CHC, district hospital, or doctor's clinic).

# OBJECTIVES
1. Help the user book an appointment by asking for:
   - Patient's name (मरीज़ का नाम)
   - Preferred health facility name (अस्पताल या क्लिनिक का नाम)
   - Appointment date (तारीख)
   - Appointment time slot (समय)
2. If they don't know which facility to book at, guide them that you can book at any clinic/PHC they prefer. If they want to search for the nearest facility, tell them they can do that, but you can only book if they tell you the name of the facility they want.
3. Once you have all the booking details (patient's name, facility, date, and time), call the `book_appointment` tool to book the appointment.
4. Confirm the booking details (date, time, patient name, facility name, and the generated booking ID) with them.
5. If the caller asks about symptoms, medicines, government schemes, or anything outside booking appointments in their CURRENT/LATEST turn, politely inform them that you cannot help with those topics and that you are transferring them back to Pooja (the main assistant), and immediately call the `transfer_to_main` tool. Do NOT look at past messages in the history to trigger this; only transfer if they are asking about these topics right now in their current turn.

# LANGUAGE
Speak in natural, everyday HINGLISH — Devanagari script for Hindi parts, English for English terms (patient, doctor, appointment, book, time, date, confirm, success). Keep replies short (at most 2 sentences, under 25 words). Never write Hindi in Roman letters, always Devanagari. Since you are "Abhinav" (a male companion), use appropriate masculine Hindi verb forms (e.g. "रहा हूँ" instead of "रही हूँ").

# GUARDRAILS
- You ONLY handle appointments. Refuse to diagnose, triage symptoms, suggest medicines, or check schemes.
- Always transfer back to the main assistant using the `transfer_to_main` tool if the user asks non-appointment questions.
- Never ask for or store sensitive personal data (Aadhaar, bank details, OTP).
"""


class AppointmentAgent(Agent):
    def __init__(
        self, chat_ctx: ChatContext | None = None, ctx: JobContext | None = None
    ) -> None:
        self.ctx = ctx
        super().__init__(
            instructions=APPOINTMENT_PROMPT,
            chat_ctx=chat_ctx,
            tts=murf.TTS(
                model="FALCON",
                voice="Abhinav",
                locale="hi-IN",
                style="Conversational",
                sample_rate=48000,
                tokenizer=tokenize.blingfire.SentenceTokenizer(min_sentence_len=10),
                text_pacing=False,
            ),
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply(
            instructions="Introduce yourself in Hinglish (Devanagari) as the clinic and appointment specialist for Aarogya Saathi, and ask how you can help them book their appointment."
        )

    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        patient_name: str,
        facility_name: str,
        appointment_date: str,
        appointment_time: str,
    ) -> str:
        """Book a clinic or hospital appointment for the user.

        Call this once you have the patient name, facility name, appointment date, and time.

        Args:
            patient_name: The name of the patient.
            facility_name: The name of the health facility or clinic (e.g. 'Rampur PHC').
            appointment_date: The date for the appointment (e.g. '15 August 2026').
            appointment_time: The time slot (e.g. '10:00 AM').
        """
        import random

        apt_id = f"APT-{random.randint(1000, 9999)}"
        logger.info(
            "Appointment booked: ID=%s, patient=%s, facility=%s",
            apt_id,
            patient_name,
            facility_name,
        )
        return (
            f"Successfully booked appointment at {facility_name} for {patient_name} on {appointment_date} at {appointment_time}. "
            f"Appointment ID is {apt_id}. Inform the user about the booking ID and details."
        )

    @function_tool
    async def transfer_to_main(self, context: RunContext) -> tuple[Agent, str]:
        """Transfer the user back to the main health assistant for general health advice, symptoms, or schemes."""
        logger.info("Transferring back to main assistant")
        chat_ctx = self.chat_ctx.copy(exclude_instructions=True)
        chat_ctx.add_message(
            role="system",
            content="[SYSTEM: The user has returned to you (Pooja, the main assistant) from the specialist. Do NOT transfer them back to the specialist unless they explicitly ask for appointment booking again in a new turn.]"
        )
        main_assistant = Assistant(
            chat_ctx=chat_ctx, ctx=self.ctx
        )
        return main_assistant, "ठीक है, मैं आपको वापस मुख्य सहायक पूजा के पास भेज रहा हूँ।"


class Assistant(Agent):
    def __init__(
        self, chat_ctx: ChatContext | None = None, ctx: JobContext | None = None
    ) -> None:
        super().__init__(instructions=SYSTEM_PROMPT, chat_ctx=chat_ctx)
        self.ctx = ctx
        # Per-call memory state. A fresh Assistant is created for every call
        # (see session.start below), so this safely holds only the current caller.
        self._caller_id: str = ""
        self._caller_name: str = ""
        self._profile: memory.CallerProfile | None = None
        self._consent_given: bool = False

        # Day 8 Analytics Metrics
        self.start_time: float = time.time()
        self.user_engaged: bool = False
        self.triage_performed: bool = False
        self.facility_lookup_performed: bool = False
        self.scheme_checked: bool = False
        self.escalated: bool = False

    async def on_enter(self) -> None:
        has_history = any(
            m.role in ("user", "assistant") for m in self.chat_ctx.messages()
        )
        if has_history:
            logger.info(
                "Assistant: returning from specialist handoff, generating reply"
            )
            await self.session.generate_reply(
                instructions="Warmly welcome the user back in Hinglish (Devanagari) as Pooja the main health assistant, and ask how you can help them now."
            )

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        caller_name: str,
        language: str,
        symptoms: str,
        urgency: str,
        followup_method: str,
        summary: str,
    ) -> str:
        """Create a human help escalation request when the caller consents to it.

        Call this only when the caller has given clear permission to share their info.
        This records the request and generates a unique reference ID.

        Args:
            caller_name: The caller's display name.
            language: The language preference, e.g. 'Hinglish' or 'Hindi'.
            symptoms: The symptoms or problem they reported (e.g. 'chest pain').
            urgency: How urgent the issue is ('Low', 'Medium', 'High', or 'Emergency').
            followup_method: How they want to be contacted (e.g. 'phone call').
            summary: A brief summary of what happened and what the agent checked.
        """
        logger.info("create_escalation tool called for %s", caller_name)
        self.escalated = True
        ref_id = await escalation.save_escalation(
            caller_name=caller_name,
            language=language,
            symptoms=symptoms,
            urgency=urgency,
            followup_method=followup_method,
            summary=summary,
        )
        return f"Successfully created escalation request. Reference ID is: {ref_id}. Tell the user the reference ID and inform them that a doctor/health worker will call them soon."

    @function_tool
    async def end_call(self, context: RunContext) -> str:
        """Hang up or end the phone call.

        Use this once the conversation is finished and you have said goodbye.
        """
        await context.session.generate_reply(
            instructions="Thank them for their time and say a short goodbye in Hinglish."
        )

        logger.info("Ending call")
        if self.ctx and self.ctx.api:
            try:
                from livekit import api

                await self.ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=self.ctx.room.name)
                )
            except Exception as e:
                logger.error("Failed to delete room: %s", e)
        return "Call ended."

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
            return (
                "No usable name was given. Gently ask the caller for their name first."
            )

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

    @function_tool
    async def lookup_nearest_facility(self, context: RunContext, pincode: str) -> str:
        """Lookup the nearest Primary Health Center (PHC), Community Health Center (CHC), or district hospital for a given 6-digit Indian PIN code.

        Call this when the user asks for the nearest hospital, doctor, clinic, PHC, or CHC, and provides a 6-digit PIN code.

        Args:
            pincode: A 6-digit Indian postal code (PIN code) as a string (e.g. "110001").
        """
        # Validate PIN code format: exactly 6 digits
        pincode = pincode.strip()
        if not pincode.isdigit() or len(pincode) != 6:
            logger.info("lookup_nearest_facility: invalid pincode '%s'", pincode)
            return "गलत PIN code है। कृपया एक valid 6-digit का PIN code बताइए।"

        url = f"https://api.postalpincode.in/pincode/{pincode}"
        logger.info("lookup_nearest_facility: querying API for '%s'", pincode)

        try:
            async with aiohttp.ClientSession() as session:
                # 5 second timeout to handle API timeouts/delays out loud
                async with session.get(url, timeout=5.0) as response:
                    if response.status != 200:
                        logger.error(
                            "lookup_nearest_facility: API returned status %s",
                            response.status,
                        )
                        return (
                            "Pincode lookup server response me issue ho raha hai. "
                            "Lekin chinta mat kijiye, aam taur par har block me ek Primary Health Center (PHC) hota hai. "
                            "Aap emergency ke liye 108 ya 102 helpline par call kar sakte hain ya naziiki ASHA worker se poonch sakte hain."
                        )
                    data = await response.json()
        except asyncio.TimeoutError:
            logger.error("lookup_nearest_facility: API timeout for pincode %s", pincode)
            return (
                "Pincode lookup server response me time lag raha hai ya connection down hai. "
                "Aam taur par har block me ek Primary Health Center (PHC) hota hai. "
                "Aap emergency ke liye 108 ya 102 helpline par call kar sakte hain ya local ASHA worker se help le sakte hain."
            )
        except Exception as e:
            logger.error(
                "lookup_nearest_facility: API connection error for pincode %s: %s",
                pincode,
                e,
            )
            return (
                "Internet lookup connection me temporary dikkat hai. "
                "Aam taur par har block me ek Primary Health Center (PHC) hota hai. "
                "Aap emergency ke liye 108 ya 102 helpline par call kar sakte hain ya local ASHA worker se contact kar sakte hain."
            )

        if not data or not isinstance(data, list) or data[0].get("Status") != "Success":
            logger.info(
                "lookup_nearest_facility: API returned non-success status for '%s'",
                pincode,
            )
            return f"PIN code {pincode} के लिए कोई record नहीं मिला। कृपया correct 6-digit PIN code बताइए।"

        post_offices = data[0].get("PostOffice", [])
        if not post_offices:
            logger.info(
                "lookup_nearest_facility: no post offices found for '%s'", pincode
            )
            return f"PIN code {pincode} के लिए कोई record नहीं मिला। कृपया correct 6-digit PIN code बताइए।"

        # Get location names
        po = post_offices[0]
        district = po.get("District", "")
        state = po.get("State", "")
        block = po.get("Block", "")

        # Look up in our local directory
        self.facility_lookup_performed = True
        facilities_result = facilities.lookup_facilities_by_district(
            district, state, block
        )

        # Include data version statement as required by Day 5 Step 5
        version_prefix = "August 2026 health directory के अनुसार, "
        return f"{version_prefix}{facilities_result}"

    @function_tool
    async def classify_triage_level(
        self, context: RunContext, symptoms: str, duration_days: int = 1
    ) -> str:
        """Classify symptom severity into home care, doctor visit, or emergency visit.

        Call this when the user shares physical complaints or symptoms.

        Args:
            symptoms: A description of the physical complaints/symptoms (e.g. "bukhar aur khansi").
            duration_days: How many days the symptoms have lasted. Default is 1.
        """
        logger.info(
            "classify_triage_level: symptoms='%s', duration=%s", symptoms, duration_days
        )
        self.triage_performed = True
        return triage.classify_triage(symptoms, duration_days)

    @function_tool
    async def check_ayushman_eligibility(
        self,
        context: RunContext,
        rural_household: bool,
        has_pucca_house: bool,
        landless_manual_labor: bool,
    ) -> str:
        """Check if the caller qualifies for the Ayushman Bharat PM-JAY health scheme.

        Call this if the caller asks about getting or eligibility for an Ayushman Bharat card.

        Args:
            rural_household: True if the household is in a village/rural area, False otherwise.
            has_pucca_house: True if the house is a pucca house (brick/concrete walls/roof), False otherwise.
            landless_manual_labor: True if the household is landless and depends on manual casual labor, False otherwise.
        """
        logger.info(
            "check_ayushman_eligibility: rural=%s, pucca=%s, labor=%s",
            rural_household,
            has_pucca_house,
            landless_manual_labor,
        )
        self.scheme_checked = True
        return triage.check_ayushman(
            rural_household, has_pucca_house, landless_manual_labor
        )

    @function_tool
    async def get_vaccination_schedule(
        self, context: RunContext, baby_age_months: int
    ) -> str:
        """Retrieve the immunization schedule and upcoming vaccines based on the baby's age in months.

        Call this if a parent asks when their child's next vaccine/teeka is due or which one to get.

        Args:
            baby_age_months: The age of the baby in months (e.g. 0 for newborn, 2 for 2-month old baby).
        """
        logger.info("get_vaccination_schedule: age=%s", baby_age_months)
        self.scheme_checked = True
        return triage.get_vaccination_schedule(baby_age_months)

    @function_tool
    async def lookup_generic_medicine_price(
        self, context: RunContext, medicine_name: str
    ) -> str:
        """Lookup the generic price of a medicine under the Jan Aushadhi (PMBJP) scheme and compare it with the branded price.

        Call this if the user asks for cheaper medicine alternatives, price of generic/branded medicine, or prices under the Jan Aushadhi Scheme.

        Args:
            medicine_name: The name of the medicine (e.g., 'Paracetamol', 'Pantoprazole').
        """
        logger.info("lookup_generic_medicine_price: med=%s", medicine_name)
        self.scheme_checked = True
        return triage.lookup_generic_medicine(medicine_name)

    @function_tool
    async def check_maternity_benefit_eligibility(
        self,
        context: RunContext,
        is_first_child: bool,
        is_second_child_girl: bool,
        is_govt_employee: bool,
    ) -> str:
        """Check eligibility for PM Matru Vandana Yojana (PMMVY) maternity cash benefit.

        Call this if a user asks about government benefits, financial help, or schemes for pregnant/lactating mothers.

        Args:
            is_first_child: True if this is the first child, False otherwise.
            is_second_child_girl: True if this is the second child and the baby is a girl, False otherwise.
            is_govt_employee: True if the mother is central/state government or PSU employed, False otherwise.
        """
        logger.info(
            "check_maternity_benefit_eligibility: first=%s, second_girl=%s, govt=%s",
            is_first_child,
            is_second_child_girl,
            is_govt_employee,
        )
        self.scheme_checked = True
        return triage.check_maternity_benefit(
            is_first_child, is_second_child_girl, is_govt_employee
        )

    @function_tool
    async def transfer_to_appointments(self, context: RunContext) -> tuple[Agent, str]:
        """Transfer the user to the clinic and appointment specialist for booking clinic/hospital appointments, scheduling doctor visits, or changing appointment details."""
        logger.info("Transferring to appointment specialist")
        chat_ctx = self.chat_ctx.copy(exclude_instructions=True)
        chat_ctx.add_message(
            role="system",
            content="[SYSTEM: The user has been transferred to you (Abhinav, the appointment specialist) for booking/scheduling an appointment. Ignore any past medical symptoms or health scheme queries when deciding if you need to transfer back. Only transfer the user back to Pooja (main assistant) if they ask a new health symptom or medical query in their next turns.]"
        )
        appointment_agent = AppointmentAgent(
            chat_ctx=chat_ctx, ctx=self.ctx
        )
        return (
            appointment_agent,
            "ठीक है, मैं आपको क्लिनिक और अपॉइंटमेंट स्पेशलिस्ट के पास ट्रांसफर कर रही हूँ।",
        )

    async def save_on_disconnect(self, session: AgentSession) -> None:
        """Automatically summarize dialogue and persist/update caller profile on call end, and log call analytics."""
        # 1. Save Call Analytics (Always log every call)
        duration = int(time.time() - self.start_time)
        is_success = self.user_engaged and (
            self.triage_performed
            or self.facility_lookup_performed
            or self.scheme_checked
            or self.escalated
        )

        status = "success" if is_success else "failed"
        reason = ""
        if not is_success:
            if not self.user_engaged:
                reason = "Caller was silent / did not engage"
            else:
                reason = "Caller hung up before receiving guidance or completing a triage/scheme check"
        else:
            reasons = []
            if self.triage_performed:
                reasons.append("Triage performed")
            if self.facility_lookup_performed:
                reasons.append("Facility lookup performed")
            if self.scheme_checked:
                reasons.append("Scheme eligibility checked")
            if self.escalated:
                reasons.append("Escalation request created")
            reason = "Completed: " + ", ".join(reasons)

        room_name = self.ctx.room.name if (self.ctx and self.ctx.room) else "test_room"
        try:
            calls.save_call(
                call_id=room_name,
                caller_name=self._caller_name or None,
                status=status,
                reason=reason,
                duration=duration,
            )
        except Exception as e:
            logger.error("Failed to save call analytics on disconnect: %s", e)

        # 2. Extract and Save Caller Profile (Only if name known and consent given)
        if not self._caller_id or not self._consent_given:
            return

        logger.info("save_on_disconnect: extracting profile for %s", self._caller_id)

        # Build chat history string
        history_str = ""
        for msg in session.history.messages():
            if msg.role in ("user", "assistant"):
                text = msg.text_content
                if text:
                    role_lbl = "User" if msg.role == "user" else "Pooja"
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
                if lines[0].startswith("```json") or lines[0].startswith("```"):
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
                last_triage=data.get("triage_outcome")
                or (prev.last_triage if prev else ""),
            )

            self._profile = await asyncio.to_thread(memory.upsert_caller, profile)
            logger.info(
                "save_on_disconnect: successfully saved profile for %s", self._caller_id
            )
        except Exception as e:
            logger.error("save_on_disconnect error: %s", e)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # Day 4: make sure the caller-memory DB + table exist before any call lands.
    db_path = memory.init_db()
    logger.info("caller memory ready at %s", db_path)
    # Day 7: init escalations table
    escalation.init_db(db_path)
    # Day 8: init calls table
    calls.init_db(db_path)


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
                "bukhar",
                "khansi",
                "zukaam",
                "sardi",
                "dard",
                "sir dard",
                "pet dard",
                "saans",
                "chakkar",
                "ulti",
                "dast",
                "kamzori",
                "BP",
                "blood pressure",
                "sugar",
                "diabetes",
                "pregnancy",
                "garbhavastha",
                "dawai",
                "tablet",
                "injection",
                "teeka",
                "vaccine",
                "Ayushman Bharat",
                "PHC",
                "ASHA",
                "doctor",
                "chest pain",
                "seene me dard",
                "seene",
                "chest",
                "pain",
                "saans lene me takleef",
                "trouble breathing",
                "heavy bleeding",
                "khoon ki ulti",
                "vomiting blood",
                "emergency",
                "fever",
                "cough",
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
        # Increase endpointing delay so the agent doesn't interrupt the user too quickly.
        # 1.5 seconds is ideal for natural rural conversational pacing.
        min_endpointing_delay=1.5,
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
    user_has_spoken = False

    async def _handle_silence() -> None:
        # Strike 1 — gently check the user is still there.
        await session.say(SILENCE_REPROMPT).wait_for_playout()
        # Strike 2 — still silent after a grace period: close the call politely.
        await asyncio.sleep(SILENCE_CLOSE_DELAY)
        await session.say(SILENCE_GOODBYE).wait_for_playout()
        await session.aclose()

    @session.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent) -> None:
        nonlocal silence_task, user_has_spoken
        if ev.new_state == "speaking":
            user_has_spoken = True
            agent.user_engaged = True
            # User re-engaged — cancel any pending re-prompt / close.
            if silence_task and not silence_task.done():
                silence_task.cancel()
            silence_task = None
        elif ev.new_state == "away" and (silence_task is None or silence_task.done()):
            if not is_outbound or user_has_spoken:
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

    agent = Assistant(ctx=ctx)

    # Check if room or job metadata indicates this is an outbound call
    is_outbound = False
    outbound_meta = {}
    meta_str = ctx.room.metadata or ctx.job.metadata
    if meta_str:
        try:
            outbound_meta = json.loads(meta_str)
            if outbound_meta.get("is_outbound"):
                is_outbound = True
        except Exception as e:
            logger.error("Failed to parse room/job metadata: %s", e)

    if is_outbound:
        caller_name = outbound_meta.get("caller_name", "user")
        # Pre-load profile if caller is returning
        if caller_name:
            caller_id = memory.normalize_name(caller_name)
            if caller_id:
                profile = await asyncio.to_thread(memory.get_caller, caller_id)
                agent._caller_id = caller_id
                agent._caller_name = caller_name
                agent._profile = profile
                if profile:
                    agent._consent_given = True
                    logger.info("Outbound: pre-loaded profile for '%s'", caller_id)

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

        # Build greeting instructions based on inbound/outbound context
        if is_outbound:
            scenario = outbound_meta.get("scenario", "vaccination_reminder")

            if scenario == "vaccination_reminder" or scenario == "triage_followup":
                greeting_instructions = (
                    "This is an OUTBOUND follow-up call. "
                    "Start the call by saying EXACTLY: 'नमस्ते! मैं आरोग्य साथी से पूजा बोल रही हूँ। क्या अभी आपसे बात करने का सही समय है?' "
                    "Do not add anything else in the first turn. Wait for their reply. "
                    "If they say they are not free or say no, politely say goodbye and use the end_call tool to hang up. "
                    "If they say yes, you must say: 'तीन दिन पहले आपको बुखार था। क्या आप डेली सुबह 9 बजे दवा ले रहे हैं या अब आपकी सेहत बिल्कुल सही हो गई है? और हाँ, आप आयुष्मान कार्ड के बारे में पूछ रहे थे, तो क्या मैं आपको बताऊँ कि इसका फायदा कैसे उठा सकते हैं?' "
                    "Wait for their reply. If they say yes/haan, explain the Ayushman Bharat card benefits in detail and accurately (e.g. 5 lakh rupees free treatment per family per year, cashless hospital care, apply at Jan Seva Kendra / CSC using Aadhaar)."
                )
            else:
                greeting_instructions = (
                    "This is an OUTBOUND call. "
                    "Start the call by saying EXACTLY: 'नमस्ते! मैं आरोग्य साथी से पूजा बोल रही हूँ। क्या अभी आपसे बात करने का सही समय है?' "
                    "Do not add anything else in the first turn. Wait for their reply. "
                    "If they say they are not free or say no, politely say goodbye and use the end_call tool to hang up. "
                    "If they say yes, ask for their name, and continue the conversation normally."
                )
        else:
            greeting_instructions = (
                "Greet the user in ONE short, warm line of natural Hinglish (Hindi in Devanagari "
                "with common English words mixed in). Introduce yourself as पूजा, say in a few "
                "words what you help with (health / sehat, symptoms, when to see a doctor), and gently "
                "ask their name so you can help better. "
                "For example: 'नमस्ते! मैं पूजा हूँ, आपकी health के लिए। पहले बताइए, आपका नाम क्या है?' "
                "Then wait for them to speak. Do not add anything else. When they tell you their name, "
                "quietly use your recall_caller tool."
            )

        # Kick things off with a short, warm greeting so the user hears the natural
        # Hindi tone straight away instead of silence.
        await session.generate_reply(instructions=greeting_instructions)

        # Keep running until the room is disconnected
        while ctx.room.isconnected():
            await asyncio.sleep(0.5)

    finally:
        # Shield the disconnect handler to ensure database write completes
        await asyncio.shield(agent.save_on_disconnect(session))


if __name__ == "__main__":
    cli.run_app(server)
