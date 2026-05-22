# JobFit Resume Agent Deployment

This project deploys as one online service:

- FastAPI serves the API and the built React frontend from the same domain.
- The LLM key stays on the server as an environment variable.

GitHub Pages can host only static files, so it cannot run the FastAPI backend or protect the LLM API key. Use Render or another service that can run Docker.

## Recommended Setup: Render

1. Push this repo to GitHub.
2. Open Render and create a new Blueprint from this repository.
3. Render will read `render.yaml` and create one web service:
   - `jobfit-resume-agent`
4. Set the required secret environment variable:

```env
OPENAI_API_KEY=your_real_key
```

5. Deploy. The final Render URL is the interviewer-facing URL.

## Smoke Test

Backend:

```text
https://your-render-url.onrender.com/health
```

Frontend:

```text
https://your-render-url.onrender.com
```

In the frontend, run:

1. Paste a JD.
2. Analyze JD.
3. Fill user information.
4. Diagnose match.
5. Generate resume.
6. Export PDF.

## Security

Never put `OPENAI_API_KEY` in frontend environment variables or Git.

Only the backend should have the model key. The frontend must call the backend API.
