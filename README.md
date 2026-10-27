# lodgify-ai-coaching-widget

- `index.html`: the SDR roleplay coach (ElevenLabs agent Training_Sparring_Outbound_V1).
- `results.html`: team results. Leaderboard, coaching per rep, personas and every call with a link to the recording.

## How results update

`.github/workflows/update-calls.yml` runs every morning at 07:00 Madrid time (06:00 in winter). It runs `scripts/fetch_calls.py`, which pulls every call on the agent from the ElevenLabs API (EU residency) into `data/calls.json`, commits it and redeploys Pages. Run it any time from **Actions → Update roleplay results → Run workflow**.

Needs one repository secret: **Settings → Secrets and variables → Actions → `ELEVENLABS_API_KEY`** (a key that can read conversations).

## Adding a rep

Calls are matched to reps by ElevenLabs user ID. A new rep shows as "New rep" until you add them to `data/reps.json`:

```json
"883e41df7c4b57ede2c305647128f47a": { "name": "Thomas", "role": "SDR" }
```

The user ID is on each conversation in ElevenLabs under Metadata. One person can have several user IDs (for example when calling from another browser): add each ID with the same name and the page merges them into one rep. Edit `data/reps.json`, never `data/calls.json`, which is rebuilt from ElevenLabs on every refresh. Calls under 20 seconds or without a score are skipped.
