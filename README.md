# JobFit Resume Agent

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/dileonardoliebel813-jpg/jobfit-resume-agent1)

JobFit Resume Agent generates role-fit resume JSON from a job description and a candidate profile. The project currently uses a modular FastAPI agent backend and a React/Vite/Tailwind workspace UI. In real mode, model-backed agents call an OpenAI-compatible Responses API through a single backend LLM client; the frontend never calls the model directly.

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/v1/              # FastAPI route modules
|   |   |-- agents/              # Modular agents
|   |   |-- core/                # config, prompts, LLM client
|   |   |-- db/                  # SQLAlchemy session/base
|   |   |-- models/              # persistence models placeholder
|   |   |-- schemas/             # Pydantic request/response schemas
|   |   |-- services/            # resume pipeline orchestration
|   |   `-- main.py
|   `-- tests/
`-- frontend/
    `-- src/
        |-- components/
        `-- pages/
```

The backend paths requested in the brief are under `backend/app/...`; the frontend paths are under `frontend/src/...`.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn app.main:app --reload
```

Backend health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Vite will serve the app at:

```text
http://localhost:5173
```

For local frontend-only development, create `frontend/.env` and set:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

In the one-service cloud deployment, the frontend and backend share the same domain, so `VITE_API_BASE_URL` can be omitted.

## Mock vs Real LLM

`LLM_MODE=mock` is the default. In this mode no model API is called, tests stay deterministic, and `JDProfilerAgent` returns a valid mock `JDProfile`.

`LLM_MODE=real` calls the configured OpenAI-compatible Responses API through `backend/app/core/llm_client.py`. The frontend never calls the model directly.

## How To Connect A Real Model

1. Copy the example environment file:

```powershell
cd backend
Copy-Item ..\.env.example .env
```

2. Edit `.env`:

```env
LLM_MODE=real
OPENAI_API_KEY=你的中转站key
OPENAI_BASE_URL=https://mx.free.codesonline.dev
OPENAI_MODEL=gpt-5.4
MODEL_REASONING_EFFORT=xhigh
JD_REASONING_EFFORT=medium
PROFILE_REASONING_EFFORT=medium
RESUME_REASONING_EFFORT=xhigh
REVIEW_REASONING_EFFORT=xhigh
DISABLE_RESPONSE_STORAGE=true
LLM_MAX_RETRIES=0
```

`MODEL_REASONING_EFFORT` remains the default fallback. The phase-three stability setup uses lighter reasoning for extraction tasks (`JD_REASONING_EFFORT`, `PROFILE_REASONING_EFFORT`) and keeps high reasoning for resume generation and review tasks (`RESUME_REASONING_EFFORT`, `REVIEW_REASONING_EFFORT`).

3. Start the backend:

```powershell
uvicorn app.main:app --reload
```

4. Open:

```text
http://127.0.0.1:8000/docs
```

5. Test `POST /api/v1/jd/analyze` with:

```json
{
  "raw_jd": "这里粘贴岗位 JD 文本"
}
```

If `DISABLE_RESPONSE_STORAGE=true`, the Responses API request is sent with `store=false`.

### DeepSeek-compatible setup

DeepSeek uses an OpenAI-compatible Chat Completions API. Use `chat_completions` instead of `responses`:

```env
LLM_MODE=real
LLM_PROVIDER=deepseek
OPENAI_API_KEY=你的 DeepSeek key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
OPENAI_REVIEW_MODEL=deepseek-v4-pro
OPENAI_WIRE_API=chat_completions
LLM_MAX_OUTPUT_TOKENS=4096
LLM_TEMPERATURE=0
JD_REASONING_EFFORT=medium
PROFILE_REASONING_EFFORT=medium
RESUME_REASONING_EFFORT=xhigh
REVIEW_REASONING_EFFORT=xhigh
LLM_MAX_RETRIES=0
```

For `chat_completions`, `LLMClient` asks the provider for JSON output and then validates the result with Pydantic schemas. Invalid or unsupported JSON still fails loudly; the app does not fall back to mock data in real mode. DeepSeek's Chat Completions API does not use OpenAI Responses `reasoning.effort`; the effort variables are kept for Responses-compatible providers.

## Tests

```powershell
cd backend
python -m pytest
```

Current test coverage checks:

- `/health` starts and responds.
- `POST /api/v1/jd/analyze` returns a mock structured JD profile.
- Empty or missing `raw_jd` is rejected.
- `JDProfilerAgent` returns a valid mock `JDProfile`.
- `POST /api/v1/profile/parse` returns a mock structured user profile.
- `POST /api/v1/resume/generate` runs the mock pipeline.
- `POST /api/v1/resume/ats-review` and `POST /api/v1/resume/fact-check` accept the generated resume JSON.

## API

```text
POST /api/v1/jd/analyze
POST /api/v1/profile/parse
POST /api/v1/resume/generate
POST /api/v1/resume/ats-review
POST /api/v1/resume/fact-check
```

Supporting mock routes are also present:

```text
POST /api/v1/match/diagnose
POST /api/v1/ats/review
POST /api/v1/export/resume
```

## Online Deployment

This repository includes a root `Dockerfile` and `render.yaml` for a real one-URL deployment:

- React is built during the Docker build.
- FastAPI serves both the API and the built frontend.
- The model API key is stored only in the cloud service environment variables.

On Render, click the Deploy button above or create a Blueprint from this GitHub repository, then set:

```env
OPENAI_API_KEY=your_real_provider_key
```

The final Render URL opens the usable product directly. See `DEPLOYMENT.md` for the full checklist.

## Agent Pipeline

`ResumePipeline` currently runs:

```text
EvidenceBuilderAgent
HybridMatchAgent
StrategyAgent
ResumeWriterAgent
```

All model-backed agents use `LLMClient`. In real mode, JD/profile extraction uses lighter reasoning for stability, while resume writing, ATS review, and fact checking use higher reasoning. In mock mode, tests remain deterministic and do not consume API calls.
