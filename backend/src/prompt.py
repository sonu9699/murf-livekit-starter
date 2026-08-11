# =============================================================================
# Aarogya Saathi — Voice AI Telephony & Prompt Guide (Hindi/Hinglish)
# =============================================================================
# Ye file aapko basic guide degi ki Pooja Voice Agent kaise kaam karta hai,
# servers ko kaise run karna hai, aur calls ko kaise test karna hai.
# =============================================================================

"""
-----------------------------------------------------------------------------
1. SERVERS KAISE START KAREIN (Start Backend & Frontend)
-----------------------------------------------------------------------------
Pooja voice agent ko test karne ke liye dono servers ka running hona zaroori hai:

[STEP A] Backend Agent (LiveKit + Murf Falcon TTS):
1. Terminal open karein aur backend directory mein jayein:
   $ cd murf-livekit-starter/backend
2. Agent dev server run karein:
   $ uv run python src/agent.py dev

[STEP B] Frontend Next.js Web App:
1. Ek aur naya terminal tab/window open karein:
   $ cd murf-livekit-starter/frontend
2. Web dev server run karein:
   $ pnpm dev
3. Web interface use karne ke liye browser mein open karein: http://localhost:3000


-----------------------------------------------------------------------------
2. OUTBOUND PHONE CALL TEST KAISE KAREIN (Outbound Calling)
-----------------------------------------------------------------------------
Aap apne phone par voice agent ki call receive karne ke liye ye steps follow karein:

1. Apne phone par "Linphone" App open karein.
2. Check karein ki aap 'sonu9699' account se logged in hain aur status green/Connected hai.
3. [IMPORTANT] Linphone Settings -> Call -> Media Encryption ko "None" par set karein
   (mandatory encryption/ZRTP ki wajah se call auto-cut ho jati hai).
4. Terminal mein ye command run karke call lagayein:
   $ cd murf-livekit-starter/backend
   $ uv run python src/dial_outbound.py --to sonu9699


-----------------------------------------------------------------------------
3. CONVERSATIONAL FLOW (Pooja Agent behavior)
-----------------------------------------------------------------------------
Jab aap outbound call pick up karenge, tab conversation is tarah chalegi:

[A] Name & Status Verification:
- Pooja call par aakar aapse direct "Rahul" nahi bolegi.
- Wo aapse aapka shubh naam (name) confirm karegi.
- Wo aapse poochhegi: "क्या मेरी बात आपसे हो सकती है, क्या अभी बात करने का सही समय है?"

[B] If you say NO (Nahi / Busy Hoon):
- Pooja politely bolegi "Theek hai, main baat baad mein karungi, apna dhyan rakhiyega, Namaste!"
- Pooja immediately `end_call` tool call karke call ko hang up (auto-cut) kar degi.

[C] If you say YES (Haan / Free Hoon):
- Pooja aapse baat aage badhayegi.
- Aap usse health problems, nearest hospital lookup (PIN code bolkar), ya vaccination details pooch sakte hain.


-----------------------------------------------------------------------------
4. KEY TOOLS USED BY AGENT (Code Integration)
-----------------------------------------------------------------------------
- recall_caller(name): Purane callers ko database se naam se retrieve karta hai.
- remember_caller(consent): User ki permission lene ke baad hi memory save karta hai.
- end_call(): Outbound call ko hang up/delete room karne ke liye use hota hai.
- lookup_nearest_facility(pin): PIN code search karke nearest health center batata hai.
"""

# Identity configuration reference for Pooja
IDENTITY = {
    "name": "Pooja (पूजा)",
    "role": "Warm and trustworthy community health support companion",
    "style": "Hinglish (Devanagari script + common English words)",
    "rules": [
        "Never prescribe specific medicines or give medical diagnoses.",
        "Always ask for consent before saving user memory.",
        "Hang up immediately using end_call if the user is busy or says no."
    ]
}
