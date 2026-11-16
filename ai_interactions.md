# AI Interactions Log

## Agentic Workflow Enhancement: Reasoning Traces

My agent (`src/agent.py`) runs a multi-step loop:

1. **PLAN**: Gemini turns the user's sentence into a listener profile (genre, mood, energy), choosing only from genres and moods that exist in `data/songs.csv`.
2. **USE TOOL**: the profile is passed to my Project 3 scoring function `recommend_songs`.
3. **CHECK**: if the top song scores below 3.0 (it does not match both genre and mood), the agent sends Gemini feedback listing the genre/mood pairs that really exist, and tries again (max 2 tries). It keeps the best attempt, not the last one.
4. **ANSWER**: the specialized "DJ Vibe" prompt explains the final songs, using only the retrieved songs.

Below are three real traces captured from `python -m src.ask`. Each shows a different path through the loop.

### Trace 1: strong match on the first try

```
$ python -m src.ask
What kind of music do you want? chill lofi for studying on a rainy night
--- Attempt 1 ---
Step 1 - PLAN: turning your request into a profile...
   Profile: {'favorite_genre': 'lofi', 'favorite_mood': 'chill', 'target_energy': 0.2}
Step 2 - USE TOOL: asking the recommender for songs...
   Library Rain (lofi, chill) score 3.85
   Midnight Coding (lofi, chill) score 3.78
   Focus Flow (lofi, focused) score 2.80
   Spacewalk Thoughts (ambient, chill) score 1.92
   Moonlight Sonata Redux (classical, peaceful) score 1.00
Step 3 - CHECK: is the top song a strong match?
   Yes! Good match found.
Step 4 - ANSWER: asking DJ Vibe to explain the songs...

You're tuned in to DJ Vibe, keeping you company on this rainy night of studying!
🎵 Library Rain - Paper Lanterns | cozy lofi beats for deep focus
🎵 Midnight Coding - LoRoom | smooth late-night rhythms to keep you studying
🎵 Focus Flow - LoRoom | steady instrumental vibes for maximum concentration
Stay tuned, and keep crushing those study goals!
```

### Trace 2: weak plan, retry, then a strong match

"Bachata" is not in my catalog. The first plan (pop/romantic) ranked a workout song second, so the CHECK step rejected it. With feedback, Gemini switched to r&b/romantic and found the romantic song.

```
$ python -m src.ask
What kind of music do you want? bachata vibes for a date night
--- Attempt 1 ---
Step 1 - PLAN: turning your request into a profile...
   Profile: {'favorite_genre': 'pop', 'favorite_mood': 'romantic', 'target_energy': 0.6}
Step 2 - USE TOOL: asking the recommender for songs...
   Sunrise City (pop, happy) score 2.78
   Gym Hero (pop, intense) score 2.67
   Velvet Midnight (r&b, romantic) score 1.90
   Dusty Back Roads (country, nostalgic) score 0.95
   Island Sunday (reggae, laid-back) score 0.88
Step 3 - CHECK: is the top song a strong match?
   No. Best score 2.78 is below 3.0.
--- Attempt 2 ---
Step 1 - PLAN: turning your request into a profile...
   Profile: {'favorite_genre': 'r&b', 'favorite_mood': 'romantic', 'target_energy': 0.6}
Step 2 - USE TOOL: asking the recommender for songs...
   Velvet Midnight (r&b, romantic) score 3.90
   Dusty Back Roads (country, nostalgic) score 0.95
   Island Sunday (reggae, laid-back) score 0.88
   Night Drive Loop (synthwave, moody) score 0.85
   Rooftop Lights (indie pop, happy) score 0.84
Step 3 - CHECK: is the top song a strong match?
   Yes! Good match found.
Step 4 - ANSWER: asking DJ Vibe to explain the songs...

You're tuned in to DJ Vibe, bringing the late-night magic for your date night!
🎵 Velvet Midnight - Solenne | smooth R&B grooves setting a romantic mood
🎵 Night Drive Loop - Neon Echo | moody synthwave beats for the drive
🎵 Rooftop Lights - Indigo Parade | upbeat indie pop to keep the energy glowing
Stay tuned, and keep the good times rolling!
```

### Trace 3: no strong match, so the agent stops and warns the user

K-pop is not in my catalog, and no song is both pop and energetic. Gemini picked the same profile twice, so the agent stopped after 2 tries and honestly said the results are the closest match, not a perfect one.

```
$ python -m src.ask
What kind of music do you want? k-pop dance songs for a party
--- Attempt 1 ---
Step 1 - PLAN: turning your request into a profile...
   Profile: {'favorite_genre': 'pop', 'favorite_mood': 'energetic', 'target_energy': 0.9}
Step 2 - USE TOOL: asking the recommender for songs...
   Gym Hero (pop, intense) score 2.97
   Sunrise City (pop, happy) score 2.92
   Block Party Anthem (hip-hop, energetic) score 1.95
   Storm Runner (rock, intense) score 0.99
   Neon Pulse (edm, euphoric) score 0.95
Step 3 - CHECK: is the top song a strong match?
   No. Best score 2.97 is below 3.0.
--- Attempt 2 ---
Step 1 - PLAN: turning your request into a profile...
   Profile: {'favorite_genre': 'pop', 'favorite_mood': 'energetic', 'target_energy': 0.9}
Step 2 - USE TOOL: asking the recommender for songs...
   Gym Hero (pop, intense) score 2.97
   Sunrise City (pop, happy) score 2.92
   Block Party Anthem (hip-hop, energetic) score 1.95
   Storm Runner (rock, intense) score 0.99
   Neon Pulse (edm, euphoric) score 0.95
Step 3 - CHECK: is the top song a strong match?
   No. Best score 2.97 is below 3.0.
   Out of tries. Note: these are the closest songs I have, not a perfect match.
Step 4 - ANSWER: asking DJ Vibe to explain the songs...

You're tuned in to DJ Vibe, keeping the dancefloor alive with those high-energy beats!
🎵 Gym Hero - Max Pulse | high-intensity workout pop to fuel the dancefloor
🎵 Block Party Anthem - Kid Kairo | booming hip-hop beats made for heavy grooving
🎵 Neon Pulse - DJ Lumen | pure euphoric edm energy for late-night partying
Stay tuned, and keep the dancefloor moving!
```

**What I learned from these traces:** the retry loop fixes plans that pick the wrong genre (Trace 2), but it cannot invent songs that are not in the catalog (Trace 3). Gemini also sometimes ignored the feedback and repeated the same plan, which is why the max-tries limit and the honest warning matter.