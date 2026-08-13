# Day 8 — Submission kit (Aarogya Saathi - Call Analytics Dashboard)

Day 8 = **Call Analytics Dashboard.** Define what a successful call means for the health access voice agent, log call outcomes persistently on disconnect, and build a beautiful real-time analytics web dashboard showing total calls, successful calls, and failed calls.

---

## What shipped today

1. **Call Outcome Logging** (`backend/src/calls.py` & `backend/src/agent.py`):
   - Exposes SQLite persistence for call outcomes (`calls` table).
   - Tracks metrics: duration, user engagement, and health actions taken.
   - Saves whether the call was a **Success** (caller engaged and received health guidance/escalation) or **Failed** (caller went silent or hung up early).
   - Automatically syncs data to `backend/calls.json` to allow clean frontend reading.
2. **Call Logs API Endpoint** (`frontend/app/api/calls/route.ts`):
   - Serves logs from `backend/calls.json` to the frontend via GET `/api/calls`.
3. **Analytics Web Dashboard** (`frontend/app/analytics/page.tsx`):
   - Renders statistics: **Total Calls**, **Successful**, **Failed**, **Success Rate (%)**, and **Average Duration**.
   - Includes real-time search, status filter tabs (All, Success, Failed), and a manual **Refresh Stats** button.
4. **Header Navigation** (`frontend/app/layout.tsx`):
   - Adds an **Analytics** link to the global layout header next to Escalations.

---

## Verify locally

```bash
cd backend
# Run all unit tests including the new calls tests
uv run pytest
```

To run the application:
```bash
# From workspace root
./start_app.sh
```
Then visit `http://localhost:3000/analytics` to view the Call Analytics Dashboard.

---

## 1) Demo Script (~60 sec)

Follow these steps to record your demo video:

1. Open your browser and navigate to `http://localhost:3000`.
2. Click the **Analytics** link in the top-right header.
3. Show the empty/initial state of the dashboard (if you have no calls recorded yet).
4. Go back to Home and start a call ("Baat shuru karein").
5. Say: *"नमस्ते पूजा, मेरा नाम हरीश है। मुझे कल से हल्की सर्दी है।"*
6. Let Pooja answer, then close/disconnect the call.
7. Go to `/analytics` and hit **Refresh Stats**. Show the stats update: **Total Calls: 1**, **Successful: 1**, and the recent log details ("Triage performed").
8. Start another call, connect, and disconnect immediately without saying anything.
9. Go to `/analytics` and hit **Refresh Stats**. Show the stats update: **Total Calls: 2**, **Successful: 1**, **Failed: 1**, and the second log detail ("Caller was silent / did not engage").

---

## 2) LinkedIn Caption (copy-paste)

Day 8 of **10 Days of AI Voice Agents** 🎙️

Aarogya Saathi now has a professional **Call Analytics Dashboard**! 📊🏥 In this update, we defined clear success metrics for our rural health assistant, tracked outcome states for every call, and built a beautiful, real-time dashboard.

Highlights:

🎯 **Defining 'Success' for Health Access** — A successful call means the caller actually received health guidance (symptom triage, health scheme details, facility lookup) or got safely escalated. Hanging up early or staying silent is logged as a failed call.
💾 **Automatic Call Recording** — We instrumented our LiveKit agent to calculate duration, user speaking events, and tool actions, persistently saving the outcome to SQLite and JSON on session disconnect.
📈 **Premium Next.js Dashboard** — `/analytics` displays real-time statistics including **Total Calls**, **Successful**, **Failed**, **Success Rate (%)**, and **Average Duration** with fully searchable and filterable logs.

Our tech stack:
LiveKit + Next.js App Router + SQLite3 + Tailwind CSS + Murf Falcon TTS (Native Pooja voice) + Gemini 2.5 Flash.

AI is powerful, but visibility is what makes it reliable in the field! 🇮🇳

Building in public — Day 8 done, 2 to go! 🚀

@Murf AI
#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #Healthcare #CallAnalytics #NextJS #LiveKit #SQLite
