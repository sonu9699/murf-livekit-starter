🚀 Day 10: Aarogya Saathi - The Journey of Building a Voice AI Assistant for Bharat 🇮🇳🎙️

Over the last 10 days, I took on the 10 Days of Voice Agents — #VoiceForBharat Edition challenge by @Murf AI. Today, I'm proud to share the final milestone of my health access voice assistant: Aarogya Saathi (आरोग्य साथी)! 

Aarogya Saathi is designed for rural and semi-urban India, where language and app complexity are major barriers to healthcare. Users can speak naturally in everyday Hinglish to get symptom triaging, look up nearest facilities, check government scheme eligibility, and book clinic appointments.

Here’s a summary of what was built and shipped:
1️⃣ Fast Voice Pipeline: Powered by Murf Falcon (the fastest TTS model on the market with a record-breaking 55ms model latency) + LiveKit + Deepgram Nova-2 + Google Gemini.
2️⃣ Consent-Gated Long-Term Memory: SQL-backed memory that recalls returning users by name and references their last visit, with strict, mandatory consent checks for data privacy.
3️⃣ Multi-Agent Specialist Handoff: Pooja (general health helper in a conversational female voice) transfering seamlessly to Abhinav (appointment specialist in a conversational male voice) with 100% conversation context preserved.
4️⃣ Postal PIN Geocoding & Scheme Eligibility: Geocoding 6-digit Indian PIN codes via API to lookup matching facilities in an August 2026 directory, plus calculators for Ayushman Bharat & PMMVY.
5️⃣ Outbound Telephony: Full SIP trunking integration to dial real phone numbers and programmatic agent-led hang-up control (end_call()).
6️⃣ Web Dashboards: Operational dashboards for /analytics (call durations, success rates) and /escalations (human referrals with real-time Discord notifications webhook).

💡 Key Takeaways & Lessons Learned:
- VAD tuning is critical for Hinglish speakers who naturally pause while translating or thinking mid-sentence.
- Devanagari outputs sound vastly superior to romanized Hindi when synthesized with native Indian voices.

Check out the full technical writeup, including code snippets and system architecture diagram, in my blog post here:
🔗 https://github.com/sonu9699/murf-livekit-starter/blob/main/DAY10_BLOG_POST.md

Source Code: 
📂 https://github.com/sonu9699/murf-livekit-starter

A huge thank you to the @Murf AI team for designing such a challenging and rewarding developer journey! It’s been an incredible 10 days of building in public.

#VoiceForBharat #10DaysOfVoiceAgents #VoiceAI #MurfAI #BuildInPublic #AIForBharat #Healthcare #MultiAgent #LiveKit #Handoff #NextJS #Telephony
