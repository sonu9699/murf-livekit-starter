# Day 9 — Submission (Aarogya Saathi - Hand Off to a Specialist Agent)

Day 9 = **Hand Off to a Specialist Agent.** Create a specialist agent (Clinic and Appointment Specialist) for the Health Access track, implement seamless bidirectional handoff between the main assistant and the specialist, and preserve conversation context across transfers.

---

## What shipped today

1. **Clinic and Appointment Specialist Agent** (`backend/src/agent.py`):
   - Created `APPOINTMENT_PROMPT` giving the specialist a smaller, focused job: booking health facility appointments.
   - Built the `AppointmentAgent` class using the distinct **Murf Falcon Abhinav** (male) voice with the same low-latency configuration (`hi-IN`, `48000Hz`, no text pacing, blingfire sentence tokenizer) to provide a clear role distinction when handoff occurs.
   - Implemented `on_enter` to introduce the specialist and ask for booking details (patient name, facility, date, time).
2. **Bidirectional Transfer Tools** (`backend/src/agent.py`):
   - **`transfer_to_appointments`**: Added to the main assistant (`Assistant`) to hand off to the specialist when a user wants to book an appointment.
   - **`book_appointment`**: Added to the specialist (`AppointmentAgent`) to finalize booking and output a confirmation ID (`APT-XXXX`).
   - **`transfer_to_main`**: Added to the specialist (`AppointmentAgent`) to route the user back to the main assistant when they ask general medical or symptom questions.
   - **Context Preservation**: Seamlessly copies conversation history (`chat_ctx`) across all transfers.
   - **`on_enter` Welcome Back**: The main assistant now detects if a user is returning from a specialist transfer to greet them back dynamically.
3. **Automated Handoff Verification Tests** (`backend/tests/test_agent.py`):
   - Added robust tests validating routing from main to specialist, booking completion, and routing from specialist back to main.
   - Fixed linter/imports and reformatted using `ruff`.

---

## Verify locally

```bash
cd backend
# Run the test suite (all 44 tests pass)
uv run pytest
```

To run the application:
```bash
# From workspace root
./start_app.sh
```

---

## 1) Demo Script (~60 sec)

Follow these steps to record your demo video:

1. Open your browser and navigate to `http://localhost:3000`.
2. Connect to Aarogya Saathi ("Baat shuru karein").
3. Say: *"नमस्ते पूजा, मेरा नाम हरीश कुमार है। मुझे रामपुर PHC में डॉक्टर के साथ अपॉइंटमेंट बुक करना है।"*
4. Pooja (main assistant) answers: *"Transferring you to our clinic and appointment specialist."* and hands off to the specialist.
5. The specialist (Appointment Agent) takes over in Abhinav's voice: *"नमस्ते! मैं क्लिनिक और अपॉइंटमेंट स्पेशलिस्ट हूँ। क्या आप हरीश कुमार के लिए 15 अगस्त को सुबह 10 बजे रामपुर PHC में अपॉइंटमेंट बुक करना चाहते हैं?"*
6. Answer: *"हाँ, बुक कर दीजिए।"*
7. Specialist answers: *"आपका अपॉइंटमेंट रामपुर PHC में 15 अगस्त सुबह 10 बजे बुक हो गया है। बुकिंग ID है APT-1234।"*
8. Ask a general query: *"मुझे कल से बहुत तेज बुखार है, क्या मुझे कोई दवा लेनी चाहिए?"*
9. Specialist answers: *"मैं सिर्फ अपॉइंटमेंट बुकिंग में मदद करती हूँ। दवाई और इलाज के लिए मैं आपको वापस मुख्य सहायक पूजा के पास भेज रही हूँ।"*
10. Pooja (main assistant) takes over: *"लगता है तेज बुखार है। कितना तेज बुखार है और साथ में कोई और symptoms हैं?"*
11. Disconnect the call.

---

## 2) LinkedIn Caption (copy-paste)

Day 9 of **10 Days of AI Voice Agents** 🎙️

Aarogya Saathi goes multi-agent! 🤝🏥 Today, we split responsibilities by creating a dedicated **Clinic and Appointment Specialist** agent and implemented a seamless bidirectional handoff between the main health assistant and the specialist.

Highlights:
🎯 **Focused Specialist Agent** — Built a separate `AppointmentAgent` with its own instructions, guardrails, and limits to handle clinic and hospital bookings.
🔄 **Seamless Handoff** — The main agent hands off to the specialist when booking is requested. If the user asks general medical queries while talking to the specialist, they get routed back to Pooja/main assistant.
💾 **Context Retention** — The user's entire conversation context and history are copied and preserved during transfers, so they never have to repeat themselves.
🗣️ **Clear Voice Distinction** — Used the distinct **Murf Falcon Abhinav** voice for the specialist to make the handoff clear and distinguishable, while keeping the same configuration (`hi-IN` locale, 48kHz, blingfire sentence tokenizer) for optimal quality.

All 44 evaluation tests are passing successfully! 🚀

Our tech stack:
LiveKit Agents + Next.js App Router + SQLite3 + Murf Falcon TTS (Pooja and Abhinav voices) + Gemini 2.5 Flash.

AI is most effective when agents work as a team! 🇮🇳

Building in public — Day 9 done, 1 to go! 🚀

@Murf AI
#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #Healthcare #MultiAgent #LiveKit #Handoff #NextJS
