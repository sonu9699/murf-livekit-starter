# Day 7 — Submission kit (Aarogya Saathi)

Day 7 = **Human-in-the-loop Escalation.** Give Aarogya Saathi the maturity to recognize when it cannot solve a problem, seek caller consent, log a structured request persistently, and provide a clear next step.

---

## What shipped today (for reference while recording)

1. **Escalations Database & JSON Sync** (`backend/src/escalation.py`):
   - Exposes SQLite persistence for human help requests (`escalations` table).
   - Generates a unique reference ID (e.g. `ESC-XXXX`) per request.
   - Automatically syncs data to `backend/escalations.json` to allow clean frontend reading.
   - Hooks into `DISCORD_WEBHOOK_URL` to send real-time embeds of new referrals.
2. **Consent-Gated Agent Tool** (`backend/src/agent.py`):
   - **`create_escalation` Tool**: Allows the agent to programmatically file a human referral.
   - **Consent Prompts**: Instructs Pooja to check for red-flag symptoms or diagnoses, request permission in Hinglish, and only call the tool if the caller says yes.
   - **ID Feedback**: Tells Pooja to read out the Reference ID and explain the follow-up timeline.
3. **Frontend referral Dashboard** (`frontend/app/escalations/page.tsx` + `route.ts`):
   - Implements `/escalations` page with search, filters (All, Open, Resolved), and detailed patient cards.
   - Dynamic badges (red pulsating badge for Emergencies, yellow for High, etc.).
   - Interactive action button ("Resolve / Re-open Case") that calls the Node.js Next.js API, which executes a python command to update SQLite and syncs the JSON file.

---

## Verify locally

```bash
cd backend
# Run all unit tests including the new escalation tests
uv run pytest
```

To run the application:
```bash
# From workspace root
./start_app.sh
```
Then visit `http://localhost:3000` and click **Baat shuru karein**.

---

## 1) Demo Script (~60–90 sec)

Follow these steps to record your demo video:

**Path A: Normal Flow (No Escalation)**
1. Connect via browser.
2. Say: *"नमस्ते पूजा, मेरा नाम हरीश है। मुझे कल से हल्की सर्दी है।"*
3. Pooja: *"नमस्ते हरीश जी! कोई बात नहीं, यह mild symptom लग रहा है। आप भरपूर आराम करें, गर्म पानी पीते रहें और आराम न मिलने पर doctor से मिलें।"*
4. Verify Pooja did not mention escalation or ask for permission.

**Path B: Emergency Flow with Consent (Referral Created)**
5. Start a new conversation.
6. Say: *"नमस्ते पूजा, मेरा नाम सोहन है। मेरे सीने में बहुत तेज दर्द है और सांस लेने में भी दिक्कत हो रही है।"*
7. Pooja (stops normal care, alerts caller, and asks permission): *"सोहन जी, यह गंभीर Emergency हो सकती है। आप तुरंत नज़दीकी अस्पताल जाएँ। क्या मैं आपकी ये जानकारी senior doctor को भेजना चाहती हूँ ताकि वे आपसे संपर्क कर सकें? क्या मुझे इसकी अनुमति है?"*
8. Say: *"हाँ, भेज दो।"*
9. Pooja: *"ठीक है, मैंने request भेज दी है। आपका reference ID है ESC-XXXX। एक senior doctor या health worker आपसे जल्द संपर्क करेंगे।"*
10. Click the **Escalations** button in the header (or visit `/escalations`).
11. Show the dashboard card with **Sohan**, Urgency **Emergency** (pulsing red dot), and **Symptoms**.
12. Click **Resolve Case** to show state update.

**Path C: Emergency Flow without Consent (No Referral)**
13. Start a new conversation.
14. Say: *"मेरे बहुत तेज बुखार है और खून की उल्टी हो रही है।"*
15. Pooja will tell you to visit the hospital and ask for permission.
16. Say: *"नहीं, मुझे किसी को जानकारी नहीं भेजनी है।"*
17. Pooja: *"ठीक है, मैं आपकी जानकारी आगे नहीं भेजूँगी। आप अपना ध्यान रखिए और तुरंत डॉक्टर के पास जाइए।"*
18. Go to `/escalations` and verify no referral was logged.

---

## 2) LinkedIn Caption (copy-paste)

Day 7 of **10 Days of AI Voice Agents** 🎙️

Aarogya Saathi ab aur bhi intelligent ho gayi hai! 🏥🤖 Aaj humne isme **Human-in-the-Loop (HITL) Escalation** aur ek responsive **Referrals Dashboard** build kiya. Pooja ko pata hai ki kab use human help ke liye request karni hai!

Highlights:

🚫 **Safety Guardrails & Triage** — Agar user red-flag symptoms (jaise chest pain, severe breathing issues) batata hai ya diagnosis mangta hai, to Pooja aage ki advice stop karke human doctor ko refer karti hai.
🔐 **Consent-First Design** — Pooja patient se warm Hinglish me details share karne ki permission maangti hai. Target tool tabhi call hota hai jab permission "Yes" ho.
📝 **SQLite + JSON + Discord Integration** — Consent milne par Pooja ek unique Reference ID (e.g. ESC-1029) generate karti hai, use SQLite database aur JSON me write karti hai, aur real-time update Discord Webhook par send karti hai!
📊 **Next.js Referral Dashboard** — `/escalations` dashboard par doctors ya ASHA workers patients ki details, symptoms aur urgency check kar sakte hain, aur unhe active se "Resolved" mark kar sakte hain.

Humara low-latency stack:
LiveKit + Next.js App Router + Deepgram Nova-3 + Murf Falcon TTS (Native Pooja voice) + Gemini 2.5 Flash + SQLite3.

Rural health access me human-AI collaboration ab bilkul aasan hai! 🇮🇳

Building in public — Day 7 done, 3 to go! 🚀

@Murf AI
#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #Healthcare #HumanInTheLoop #NextJS #LiveKit
