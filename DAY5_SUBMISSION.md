# Day 5 — Submission kit (Aarogya Saathi)

Day 5 = **The Tools.** Connect the voice agent to the real world! Today, Aarogya Saathi gets a comprehensive suite of **4 dynamic health tools** to provide real-world facility lookup, symptom triage, vaccine scheduling, and scheme eligibility checks under August 2026 guidelines.

## What shipped today (for reference while recording)

1. **Nearest Health Facility Lookup** (`lookup_nearest_facility`): 
   - Dynamically geocodes any 6-digit Indian PIN code using the live, public Postal Pincode API.
   - Matches location against a local directory (`facilities.py`) covering Bihar, UP, Rajasthan, MP, Maharashtra, and Jharkhand, returning local PHCs/CHCs/hospitals with phone numbers.
2. **Symptom Triage Classifier** (`classify_triage_level`):
   - Categorizes severity into **RED** (immediate hospital/108 call), **YELLOW** (PHC/clinic checkup in 1-2 days), or **GREEN** (rest and home care advice with ORS).
3. **Ayushman Bharat Eligibility Checker** (`check_ayushman_eligibility`):
   - Computes eligibility based on rural deprivation criteria (landless casual labor, kucha houses).
4. **Teekakaran (Vaccination) Schedule Calculator** (`get_vaccination_schedule`):
   - Determines UIP vaccines due based on a baby's age in months.

*Note: All tools handle failure paths out loud, write Devanagari Hindi for Pooja's native voice, and reference the August 2026 guidelines.*

---

## Verify locally

```bash
cd backend
uv run pytest
```
Output:
```text
tests/test_agent.py ...
tests/test_facilities.py ..........
tests/test_memory.py ................
============================= 29 passed in 11.70s ==============================
```

---

## 1) Demo Script (~60–90 sec)

You can record a single continuous video testing these tools back-to-back:

**Call 1: Symptom Triage + Facility Lookup**
1. Start the call. Agent: *"नमस्ते! मैं आरोग्य साथी हूँ… आपका नाम क्या है?"*
2. Say: *"मेरा नाम राहुल है, और मुझे दो दिन से सीने में बहुत तेज दर्द हो रहा है और सांस लेने में दिक्कत है।"*
3. Agent (runs `classify_triage_level` -> RED): *"August 2026 guidelines के अनुसार, यह गंभीर Emergency हो सकती है। तुरंत नज़दीकी अस्पताल जाएँ या 108 helpline पर call करें।"*
4. Say: *"मैं पटना में हूँ। नज़दीकी अस्पताल का पता बता सकते हो?"*
5. Agent (asks for PIN): *"नज़दीकी अस्पताल या PHC ढूंढने के लिए, कृपया अपना 6-digit का PIN code बताइए।"*
6. Say: *"मेरा PIN code 800001 है"*
7. Agent (runs `lookup_nearest_facility` -> Patna matched): *"August 2026 health directory के अनुसार, Patna में, नज़दीकी local center PHC Phulwari Sharif है और बड़ा अस्पताल PMCH है।"*

**Call 2: Ayushman Bharat Eligibility + Vaccination Schedule**
8. Call back. Say: *"क्या मैं Ayushman card बनवा सकता हूँ? मैं गाँव में रहता हूँ, हमारा घर कच्चा है और मैं मज़दूरी करता हूँ।"*
9. Agent (runs `check_ayushman_eligibility` -> Eligible): *"August 2026 guidelines के अनुसार, आप eligible हो सकते हैं! इसके तहत 5 लाख रुपये तक का मुफ्त इलाज मिलता है। Jan Seva Kendra जाकर Aadhaar से card बनवाएँ।"*
10. Say: *"और मेरे 2 महीने के बच्चे को कौन सा टीका लगेगा?"*
11. Agent (runs `get_vaccination_schedule` -> 2 months): *"August 2026 guidelines के अनुसार, 1.5 months (6 weeks) पर Pentavalent 1, OPV 1, Rotavirus 1, IPV 1, और PCV 1 का टीका लगेगा।"*

---

## 2) LinkedIn Caption (copy-paste)

Day 5 of **10 Days of AI Voice Agents** 🎙️

Aaj **Aarogya Saathi** ko ek poora digital health desk bana diya! Internet and database se connect karke humne **4 dynamic tools** add kiye jo small-town aur rural Bharat me kisi healthcare companion se kam nahi hain. 🏥🇮🇳

Sahi information sahi time pe milna hi healthcare access ka pehla step hai. Ye hain humare 4 tools:

📍 **PIN Code Resolution** — Call pe sirf 6-digit ka pincode bolo, aur hum live public API se unka block aur district fetch karke nearest PHC, CHC ya government hospital aur uske phone numbers batate hain.
🌡️ **Symptom Triage Classifier** — Caller ki physical complaints sunkar use classify karte hain: **RED** (Emergency - direct hospital/108 call), **YELLOW** (PHC visit in 1-2 days), ya **GREEN** (home care with ORS/rest).
💳 **Ayushman Bharat Eligibility** — User ke rural deprivation factors (kucha house, manual labor) se check karte hain ki unka PM-JAY card ban sakta hai ya nahi, aur unhe sahi guides dete hain.
👶 **Teekakaran (Vaccination) Schedule** — Bacche ki age (months) batate hi National Immunization Schedule ke mutabiq next vaccines list kar deta hai.

⚙️ Aur sabse important: **Out-loud Failure Handling**. Agar API down ho ya network slow ho, to agent chup nahi hota. Wo turant natural voice me bolti hai ki *"Lookup server down hai, par emergency me aap 108 dial karein ya naziiki ASHA didi se milen."*

Latency? Bilkul zero, thanks to async processing. Voice quality? **Murf Falcon** (hi-IN) ki native Hindi tone, jo sunne me bilkul local lagti hai.

Stack: LiveKit Agents + Deepgram STT + Murf Falcon + Postal Pincode API + UIP/SECC guidelines.

Technology jab domain knowledge se judti hai, tab asli Bharat ke liye solution banta hai! 💛

Building in public — Day 5 done, halfway mark reached! 🚀

@Murf AI
#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #HealthTech #LiveKit #HealthcareAccess
