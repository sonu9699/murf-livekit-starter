# Day 6 — Submission kit (Aarogya Saathi)

Day 6 = **Telephony & Outbound Calling.** Integrate Aarogya Saathi with real-world SIP trunking so it can dial outbound numbers directly and handle call control (like hanging up when a call is finished) dynamically.

## What shipped today (for reference while recording)

1. **Outbound Call Integration** (`backend/src/dial_outbound.py`):
   - Initiates outbound SIP calls using the LiveKit SIP participant service (`create_sip_participant`).
   - Dynamically dispatches the agent (`my-agent`) into the generated room on call startup.
   - Passes structured session metadata (caller name, scenario, baby's age) to personalize the greeting.
2. **SIP Outbound Trunk Setup** (`backend/src/setup_outbound_trunk.py`):
   - Registers a reusable SIP outbound trunk with LiveKit pointing at Linphone or Twilio Elastic SIP.
3. **Outbound Agent Call Control** (`backend/src/agent.py`):
   - **`end_call()` Tool**: Allows the agent to programmatically hang up the phone and clean up the LiveKit room.
   - **Scenario Greetings**: Tailors the first prompt dynamically based on the outbound scenario (e.g., vaccination follow-ups).
   - **Outbound Silence Handling**: Adapts VAD silence detection to only trigger silence re-engagement after the user has spoken at least once.

---

## Verify locally

```bash
cd backend
# Run unit tests to verify agent functionality and memory
uv run pytest
```

To dial an outbound call:
```bash
# Dial your registered Linphone client
uv run python src/dial_outbound.py --to sonu9699
```

---

## 1) Outbound Demo Script (~60–90 sec)

Test the outbound call flow using Linphone:

**Call 1: Busy Caller Flow (Quick Hangup)**
1. Register your Linphone client as `sonu9699`. Set **Media Encryption** to **None** in Linphone settings.
2. Run the dial command: `uv run python src/dial_outbound.py --to sonu9699`
3. Answer the call on Linphone.
4. Agent: *"नमस्ते! मैं आरोग्य साथी से पूजा बोल रही हूँ। क्या अभी आपसे बात करने का सही समय है?"*
5. Say: *"नहीं, मैं अभी व्यस्त हूँ।"* (No, I am busy right now).
6. Agent (hangs up call): *"ठीक है, मैं बाद में बात करूँगी। अपना ध्यान रखिएगा। नमस्ते!"* (Room deletes and call cuts automatically).

**Call 2: Follow-up & Triage Flow**
7. Run the dial command again.
8. Answer the call.
9. Agent: *"नमस्ते! मैं आरोग्य साथी से पूजा बोल रही हूँ। क्या अभी आपसे बात करने का सही समय है?"*
10. Say: *"हाँ, बोलिए।"*
11. Agent: *"तीन दिन पहले आपको बुखार था। क्या आप डेली सुबह 9 बजे दवा ले रहे हैं या अब आपकी सेहत बिल्कुल सही हो गई है? और हाँ, आप आयुष्मान कार्ड के बारे में पूछ रहे थे, तो क्या मैं आपको बताऊँ कि इसका फायदा कैसे उठा सकते हैं?"*
12. Continue conversation or say thank you and let the call end.

---

## 2) LinkedIn Caption (copy-paste)

Day 6 of **10 Days of AI Voice Agents** 🎙️

Aarogya Saathi ab web app se nikal kar sidhe phone calls par aa gayi hai! 🏥📱 Aaj humne LiveKit aur SIP trunking use karke **Outbound Dialing** aur **Telephony Call Control** add kiya.

Ab humara agent health campaigns ke liye sidhe patients ko dial kar sakta hai:

📞 **Outbound Dialing** — Ek single script se LiveKit room create hota hai, agent dispatch hota hai, aur patient ke SIP client (jaise Linphone/Twilio) par call chali jaati hai.
⚡ **Dynamic Scenario Greetings** — Call ke context ke hisab se (jaise vaccination reminder ya triage follow-up) Pooja ka greeting message change ho jata hai.
🚪 **Graceful Hangup (`end_call`)** — Agar patient busy hai ya call khatam ho gayi hai, to agent programmatically call disconnect (`end_call` tool) karke resources release kar deta hai.
🤫 **Smart Silence Handling** — Outbound calls par background noise/silence ko handle karne ke liye smart silence timing use ki, jo patient ke baat shuru karne ke baad hi trigger hoti hai.

Aur sabse best part: Wahi super-fast **Murf Falcon** (hi-IN) voice low latency aur natural dialect ke sath. 

Stack: LiveKit SIP + Linphone + Deepgram STT + Murf Falcon (hi-IN) + Gemini.

Ab health reminders aur rural follow-ups sirf ek phone call ki doori par hain! 🇮🇳

Building in public — Day 6 done, 4 to go! 🚀

@Murf AI
#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #Telephony #LiveKit #SIP
