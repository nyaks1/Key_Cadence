# KeyCadence

Behavioral biometric authentication API — passive fraud detection via keystroke dynamics. Built for South African fintech developers.

---

## What This Is

KeyCadence identifies users by **how** they type, not what they type.

Every person has a unique rhythm when typing — the time between keystrokes, how long each key is held, the patterns between specific key pairs. KeyCadence captures those timings, builds a baseline profile per user, and scores every future login attempt against that baseline using statistical deviation analysis.

If someone steals a password and tries to log in, their typing pattern won't match. KeyCadence catches that — silently, passively, with zero friction added to the user experience.

This is called **behavioral biometrics**. It runs underneath your existing login as a second signal, not instead of it.

---

## Why This Exists

South Africa's dominant fraud vector is SIM-swap — attackers clone a victim's phone number to intercept the OTP (one-time password) sent by a banking app. Once they have the OTP, the bank's standard 2FA is defeated.

Keystroke dynamics doesn't care about your SIM card. It scores the typing pattern of whoever is at the keyboard. A fraudster with the correct password and the correct OTP, but the wrong typing rhythm, gets flagged.

KeyCadence is the shovel. SA fintech developers are the miners. We don't build the bank — we sell the tool that makes the bank safer.

---

## How It Works

### Two endpoints. That's the whole API.

**1. Enroll** — call this when a trusted user logs in for the first time (or re-establishes their baseline). You send their keystroke timing data; we store a statistical profile.

**2. Verify** — call this on every subsequent login. You send new keystroke timings; we compare them to the stored baseline and return a confidence score plus a risk decision.

### The math (simple version)

A keystroke timing sample is just a list of numbers — the gap between each key press in milliseconds.

```
User types "password123":
[120, 95, 110, 88, 130, 102, 98, 115, 90, 105]
  p→a  a→s  s→s  s→w  w→o  o→r  r→d  d→1  1→2  2→3
```

During enrollment, we calculate the **mean** (average gap) and **standard deviation** (how much it varies) for this user. That's their baseline.

During verification, we measure how far the new sample deviates from that baseline. This is a **z-score** — a standard statistical measure of "how unusual is this?"

```
z = (new_value - baseline_mean) / baseline_std_deviation
```

A z-score close to 0 means "this matches the baseline." A high z-score means "this is unusual." We average the z-scores across all keystrokes and produce a single confidence score between 0 and 1.

### The agent

The z-score gives us a number. The **Risk Decision Agent** (powered by Gemini via Google Cloud) turns that number into a decision:

- **ALLOW** — confidence is high, let the user through
- **STEP_UP** — borderline confidence, trigger additional verification (re-enter password, OTP)
- **BLOCK** — low confidence, flag as suspected fraud

The agent also writes a plain-English explanation of the decision that shows in your dashboard. This is what makes it useful for a non-technical business owner — not a raw number, but a reason.

---

## Project Structure

```
keycadence/
├── api/
│   ├── main.py              # FastAPI app — registers all routes
│   ├── routes/
│   │   ├── enroll.py        # POST /enroll — store a user's baseline
│   │   └── verify.py        # POST /verify — score a login attempt
│   ├── core/
│   │   ├── scoring.py       # z-score deviation logic
│   │   └── storage.py       # baseline profile read/write
│   ├── agent/
│   │   └── risk_agent.py    # Gemini ADK risk decision agent
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response shapes
│   └── requirements.txt     # Python dependencies
├── demo/                    # Flutter demo shell (banking login screen)
│   └── lib/
│       └── main.dart
├── Dockerfile               # Packages the API for Cloud Run
├── .env.example             # Required environment variables (no values)
├── .gitignore
└── README.md
```

### Why each layer exists

**`routes/`** — each endpoint is its own file. Separation of concerns: if the enroll logic breaks, you open `enroll.py`. You don't hunt through a 400-line file.

**`core/`** — pure logic, no web framework knowledge. `scoring.py` doesn't know FastAPI exists. `storage.py` doesn't know Gemini exists. This is how you test business logic without spinning up a server.

**`agent/`** — isolated because it's the only file that talks to Google Cloud. When something breaks with the Gemini integration, you know exactly where to look.

**`models/schemas.py`** — every request and response shape lives here. Change a field once, it propagates everywhere. This is Pydantic — Python's data validation library, used by FastAPI natively.

**`Dockerfile`** — Cloud Run doesn't run Python files directly. It runs containers. A container is a sealed, reproducible environment with your code, the right Python version, and all dependencies bundled. Docker builds that container. Without it, Cloud Run has nothing to deploy.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| API framework | FastAPI | Auto-generates docs at `/docs`, fast, Pydantic-native |
| Data validation | Pydantic | Request/response contracts enforced at runtime |
| Scoring logic | NumPy / SciPy | Statistical math — z-score, mean, std deviation |
| AI agent | Google ADK + Gemini | Risk decision layer, Cloud Run eligibility |
| Deployment | Google Cloud Run | Container-based, pay-per-request, free tier available |
| Demo shell | Flutter | Banking login screen for the 90-second demo video |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. Never commit `.env`.

```
GEMINI_API_KEY=
GOOGLE_CLOUD_PROJECT=
STORAGE_PATH=
```

---

## Endpoints

### `POST /enroll`

Store a user's keystroke baseline.

**Request:**
```json
{
  "user_id": "user_abc123",
  "keystroke_timings": [120, 95, 110, 88, 130, 102, 98, 115, 90, 105]
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "status": "enrolled",
  "samples_recorded": 10
}
```

---

### `POST /verify`

Score a login attempt against the stored baseline.

**Request:**
```json
{
  "user_id": "user_abc123",
  "keystroke_timings": [118, 200, 310, 90, 128, 99, 150, 112, 88, 103]
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "match_confidence": 0.43,
  "decision": "STEP_UP",
  "reason": "Timing variance in mid-sequence keystrokes is 2.3 standard deviations above this user's baseline. Recommend secondary verification before granting access.",
  "flagged": true
}
```

---

## Running Locally

```bash
# Install dependencies
cd api
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload

# Open docs
open http://localhost:8000/docs
```

---

## Running with Docker

```bash
docker build -t keycadence .
docker run -p 8080:8080 keycadence
```

---

## POPIA Compliance Note

KeyCadence processes **keystroke timing metadata** — not the content of what users type, only the timing patterns. Under POPIA, behavioral biometrics may qualify as personal information requiring a lawful basis for processing. Integrating developers are responsible for:

- Disclosing keystroke analysis in their privacy notice
- Obtaining informed consent from end users
- Ensuring data is not retained beyond its purpose
- Implementing appropriate security safeguards (Section 19)

KeyCadence does not store passwords, keystrokes content, or any data that identifies what was typed — only when.

---

## Pricing

Usage-based. Per verification call. Free tier available for development.

*(Pricing page coming soon)*

---

## Status

🔨 Active development — Build with Gemini XPRIZE submission, deadline August 17 2026.
