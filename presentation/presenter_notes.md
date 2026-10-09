# AI Defense Arena — presenter notes

Use these as prompts, not as text to read word for word. The eight-slide deck is designed for about **4–5 minutes**, followed by a short live demo.

1. **Title (20 seconds).** “AI Defense Arena helps a team practice defending a project before the real panel. We upload our own source files, so the questions are about our work.” The screenshot is a marked UI preview; the real defense generates questions through the API.
2. **Problem (30 seconds).** “Building software and explaining its tradeoffs under pressure are different skills. Generic interview questions do not know our code, and a team needs a fair way to choose who speaks.”
3. **Experience (40 seconds).** “The host uploads source files or a ZIP and teammates join by room code. Each question shows an exact source line. The team votes for 15 seconds, then the chosen defender gets two minutes to answer while others can use private team chat. The defense ends with a transcript and coaching.”
4. **AI panel (35 seconds).** “Four specialist roles cover architecture, security, product value, and critical assumptions. Each gets at least one question. The AI may ask one follow-up immediately, so a session has four to eight turns.”
5. **Room screen (35 seconds).** Point to the question, file/line citation, and Vote/Answer plus Team Chat tabs. “The server validates the cited line before it is shown. That makes the panel’s question traceable to the uploaded project.”
6. **Architecture (40 seconds).** “The browser uses React and Three.js; FastAPI owns rooms, WebSocket updates, votes and deadlines. The OpenAI Responses API generates questions and qualitative coaching. Uploaded text is numbered and sent as context; the server checks the returned file and line. Rooms are kept in memory for this hackathon prototype.”
7. **What I made (40 seconds).** “I shaped the concept, specified the four panelists and team flow, reviewed the screens and tests, and drove the deployment. I used AI coding agents to accelerate implementation, while I made the product and release decisions.” Adjust this to match exactly what you personally did.
8. **Live demo (20 seconds).** “Let’s try it with a small project.” Open the URL. Have one browser create the room and a second browser join. Show one cited question, vote, answer, and the resulting transcript. If the service has just restarted, create a fresh room because rooms are in memory.

## Demo preparation

- Prepare a small source project or ZIP in advance. Open two browser windows or devices on the same deployed URL.
- Create the room shortly before presenting. Keep the host page open and share **only the room code**.
- Test that the OpenAI API key is configured on Render. Never show it in a slide or screen share.
- For a very short demo, show one question and source line, the vote, and one answer. Use the transcript/coaching slides to explain the complete flow.
- The deployed timed-room UI and assets were verified. A full live AI session on this specific timed release has **not yet been confirmed** in the project log; test it before claiming that validation on stage.

## Likely judge questions

**Are these four different AI models?** No. They are four role-specific panelists orchestrated through one configurable OpenAI model. The different prompts give each role a distinct focus.

**Is there a vector database or RAG index?** No. This prototype sends bounded, numbered project text as context and validates the AI’s cited file and line. A vector index would be a future scaling step for much larger projects.

**How do you prevent made-up code citations?** The server accepts a citation only if the file and numbered line exist in the uploaded project, then displays the exact stored line. The model may still ask a weak question, so this is a grounding check, not a guarantee that every question is perfect.

**What if a defender disconnects or time runs out?** The server reassigns a disconnected speaker without restarting the answer clock. An expired question is saved as unanswered; later AI prompts and coaching must treat it that way.

**What are the prototype limits?** Rooms and chat live in one server process, so a Render restart clears them. The game is text-based; it does not include voice, persistent accounts, or scores.
