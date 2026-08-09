# Day 4 — Submission kit (Aarogya Saathi)

Day 4 = **memory day.** Give the agent lasting memory so a returning caller is greeted **by name**
and the call continues from last time — with a hard **ask-before-saving** consent rule (mandatory
for Health Access). Then video (two calls back-to-back) → LinkedIn → Discord form.

## What shipped today (for reference while recording)

- **SQLite store** — `backend/src/memory.py`, a tiny repository keyed by the caller's **spoken name**
  (the LiveKit participant identity is random every call, so it can't be a durable key). File-based →
  survives an agent restart. Gitignored — it holds personal data.
- **Three function tools the LLM calls itself** (not driven from the prompt text) —
  `backend/src/agent.py`:
  - `recall_caller(name)` — looked up the moment the caller says their name.
  - `remember_caller(consent_given, language, age_band, conditions, triage_outcome)` — **refuses to
    save unless `consent_given` is true.**
  - `forget_caller()` — the "forget me" / delete-my-data tool (advanced bonus).
  - DB work runs in a worker thread (`asyncio.to_thread`) so the realtime audio loop never blocks
    (covers the "async lookup" advanced bonus).
- **Greets returning callers by name** — on recall, the agent welcomes them back and refers to last
  time ("पिछली बार BP की बात हुई थी, अब कैसा है?").
- **Consent is a hard rule** — the agent asks "क्या मैं आपकी जानकारी याद रख लूँ?" and only saves on a
  clear yes; on refusal it saves nothing and says so. Enforced twice: in the prompt AND in the tool.
- **Privacy by design** — stores only name, language, a rough age band, a couple of condition labels,
  and one short triage line. **Never** Aadhaar/bank/phone/OTP/ID numbers, and no detailed medical
  notes — matching the Health Access track rule.
- **Tests** — `backend/tests/test_memory.py` (16 tests): roundtrip, name normalization, update/merge,
  Devanagari-safe JSON, restart survival, forget, and the consent hard-rule. Full suite: **19 passed**.

## Verify locally (no browser needed)

```bash
cd backend
uv run ruff check .                 # clean
uv run pytest -q                    # 19 passed
```

The DB lands at `backend/aarogya_memory.db` (override with `AAROGYA_DB_PATH`).

## 1) Two-call demo script (~60–75 sec) — the whole point of Day 4

Record on your phone (this machine can't open a headed browser). Do **both calls back-to-back** in
one video so the difference is obvious.

**Call 1 — the agent meets a new caller and remembers her (with consent):**
1. Start the call. Agent: *"नमस्ते! मैं आरोग्य साथी हूँ… आपका नाम क्या है?"*
2. Say your name, e.g. **"मैं सुनीता।"** (agent silently runs `recall_caller` → new caller).
3. Share a symptom: *"BP थोड़ा high रहता है, कमज़ोरी लगती है।"* Let it give safe guidance.
4. Near the end it asks consent: *"क्या मैं आपकी जानकारी याद रख लूँ, ताकि अगली बार दोबारा न बतानी पड़े?"*
   → say **"हाँ"**. It confirms it'll remember.
5. **Hang up.**

**Call 2 — call back; it greets you by name and continues:**
6. Start a fresh call. Give the **same name**: *"सुनीता बोल रही हूँ।"*
7. 💡 **Money shot:** it welcomes you back **by name** and refers to last time —
   *"अरे सुनीता जी, फिर से नमस्ते! पिछली बार BP की बात हुई थी, अब कैसा लग रहा है?"*

**(Optional) show the two bonus rules on camera:**
- **Consent respected:** in a quick call, when it asks to save, say **"नहीं"** → it says
  *"ठीक है, मैं कुछ याद नहीं रखूँगा"* and saves nothing.
- **Forget me:** say *"मेरी जानकारी हटा दीजिए"* → it calls `forget_caller` and confirms.

> Optional flex: mention the data survives a restart — stop the backend, start it again, call back,
> and it still remembers.

---

## 2) LinkedIn caption (copy-paste)

> When you type `@Murf`, pick the real **Murf AI** company page from the dropdown so the tag links.
> Keep the three must-haves: **Murf Falcon** mention, **10 Days of Voice Agents**, and
> **#VoiceForBharat**.

---

Day 4 of **10 Days of AI Voice Agents** 🎙️

Ab tak **Aarogya Saathi** har call ko ajnabi jaisa shuru karti thi. Aaj usko **yaaddaasht** di — ab wo aapko yaad rakhti hai. 🇮🇳

Socho: ek buzurg kaki roz call karti hai. Har baar phir se apna naam, apni BP-sugar ki baat batana — thak jaati hai. Aaj se nahi.

🧠 **Naam se pehchaan** — call back karo, aur wo naam se welcome karti hai: *"अरे सुनीता जी, फिर से नमस्ते! पिछली बार BP की बात हुई थी, अब कैसा है?"* Baat wahin se aage badhti hai jahan chhodi thi.

🔐 **Save karne se pehle poochhti hai** — ye Health Access ke liye hard rule hai. *"क्या मैं आपकी जानकारी याद रख लूँ?"* — sirf "haan" pe save karti hai. "Nahi" bola to kuch nahi rakhti. Aur Aadhaar, bank, ya koi ID number kabhi store nahi — sirf naam, umr ka andaaza, aur do-teen health notes.

🗑️ **"Mujhe bhool jao"** — user kabhi bhi apna data delete karwa sakta hai, ek line me.

⚙️ Andar: LLM khud **do function tools** call karta hai (lookup + save) — memory prompt se nahi, code se aati hai. Data ek chhoti SQLite file me, jo **restart ke baad bhi zinda** rehti hai. Lookup **async** — call ke beech rukawat nahi.

Aur awaaz? Wahi **Murf Falcon** — the fastest TTS API — low-latency native Hindi jo apni si lagti hai.

Stack: LiveKit Agents + Deepgram STT + Murf Falcon (hi-IN) + SQLite.

Bharosa sirf sahi jawaab se nahi banta — yaad rakhne se, aur permission maangne se banta hai. 💛

Building in public — Day 4 done, 6 to go 🚀

@Murf AI
\#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #HealthTech

---

## 3) Submit

Paste the LinkedIn post link into the Discord submission form (from the Day 4 message).
Deadline: **today, 11:59 PM**.

## Done-when checklist (from the task)

- [x] Data survives a full agent restart — file-based SQLite (`aarogya_memory.db`).
- [x] Caller info comes through a **function**, not the prompt — `recall_caller` / `remember_caller`.
- [x] The **second call clearly goes better** than the first — greeted by name, continues from last time.
- [x] The agent **asks before saving** and drops it on refusal — enforced in prompt **and** tool.
- [x] (Bonus) async lookup + "forget me" tool.
