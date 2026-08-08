# Day 3 — Submission kit (Aarogya Saathi)

Day 3 = **frontend / UX day.** Personalise the agent's UI to the track (Health Access), show all
five agent states clearly, indicate who's speaking, and handle mic-permission errors — then video →
LinkedIn → Discord form.

## What shipped today (for reference while recording)

- **On-brand call screen** — the custom editorial `AarogyaChatView` is now the live session view
  (warm saffron/teal/terracotta/indigo, Hindi copy, tap-to-ask starter chips).
- **Five states, clearly shown:**
  - **Ready** — welcome masthead ("Tabiyat kaisi hai aaj?") + in-call "Taiyaar hun".
  - **Connecting** — start button flips to "Jud rahe hain…" with a spinner.
  - **Listening** — "Sun rahi hun…" + teal pulsing orb/visualizer.
  - **Speaking** — "Bol rahi hun…" + saffron orb/visualizer.
  - **Call ended** — dedicated "Apna khyaal rakhiye" screen with **Phir se baat karein** (restart).
- **Who's speaking** — floating status pill (live visualizer bar + Hindi label) + pulsing `VoiceOrb`.
- **Mic-permission error** — clear Hinglish toast + an inline red strip with a **Dobara koshish
  karein** retry button, telling the user exactly how to Allow the mic.

## 1) One-take demo script (~45–60 sec)

Record on your phone (this machine can't open a headed browser). Join the LiveKit room from the
phone. Narrate lightly so each state is visible on screen.

1. **Ready** — open the app. Show the welcome masthead + the three topic index items.
2. **Connecting** — tap **"Baat shuru karein"**. Point out the button → "Jud rahe hain…" + spinner.
3. **Listening** — once connected, say a line and show the status pill turn teal → "Sun rahi hun…":
   > "Kal se halka fever hai, kya karun?"
4. **Speaking** — as the agent replies, show the pill go saffron → "Bol rahi hun…" (who's speaking).
5. **Mic error (the UX money shot)** — deny/block the mic once (browser mic icon → Block, then tap
   the mic button). Show the red strip + toast, then tap **"Dobara koshish karein"** after Allowing.
6. **Call ended** — tap the end (📞) button. Show the "Apna khyaal rakhiye" screen.
7. **Restart** — tap **"Phir se baat karein"** to prove the full loop works.

> Tip: keep it phone-shot and vertical — it reinforces the "for Bharat, on a real phone" story.

---

## 2) LinkedIn caption (copy-paste)

> When you type `@Murf`, pick the real **Murf AI** company page from the dropdown so the tag links.
> Keep the three must-haves: **Murf Falcon** mention, **10 Days of Voice Agents**, and
> **#VoiceForBharat**.

---

Day 3 of **10 Days of AI Voice Agents** 🎙️

Do din se **Aarogya Saathi** ke andar ki awaaz aur dimaag ban raha tha. Aaj usko ek **chehra** diya — pura user-facing frontend, Bharat ke user ko dhyaan me rakh ke. 🇮🇳

Aaj ka focus: **UX jo bharosa de.** Voice agent tabhi kaam karta hai jab user ko har pal saaf pata ho ki ho kya raha hai.

🟢 **Paanch clear states** — Ready, Connecting ("Jud rahe hain…"), Listening ("Sun rahi hun…"), Speaking ("Bol rahi hun…"), aur Call ended. Har state ka apna colour aur Hindi label — koi guesswork nahi.

🎤 **Kaun bol raha hai** — ek live waveform + pulsing orb batata hai agent sun raha hai ya bol raha hai. Silence me bhi user confuse nahi hota.

🚫 **Mic block ho gaya? Koi tension nahi** — agar browser mic ki permission rok de, to ek saaf Hinglish message aata hai ki kaise Allow karna hai, aur ek "Dobara koshish karein" button — dead-end nahi.

🎨 Design editorial-warm rakha — saffron/teal, badi typography, tap-to-ask health prompts. Generic "AI app" jaisa nahi; ek bharosemand health saathi jaisa.

Aur awaaz? Wahi **Murf Falcon** — the fastest TTS API — low-latency Hindi streaming jo warm lagti hai, robotic nahi.

Stack: Next.js + LiveKit Agents UI + Murf Falcon (hi-IN).

Achhi UX matlab: chhote sheher ka pehli baar app use karne wala user bhi bina sikhaaye chala le. 💛

Building in public — Day 3 done, 7 to go 🚀

@Murf AI
\#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #Murf #BuildInPublic #AIForBharat #UX

---

## 3) Submit

Paste the LinkedIn post link into the Discord submission form (from the Day 3 message).
Deadline: **today, 11:59 PM**. (Day 3 is also the last day to switch tracks — staying on Health Access.)
