# Setting up Gemini API for PlayDex

To enable advanced natural language understanding in PlayDex, you need to set up a Gemini API key.

## Steps:

1. **Get a Gemini API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the generated API key

2. **Add the API Key to PlayDex**:
   - Open the file `/backend/.env`
   - Find the line `GEMINI_API_KEY=`
   - Paste your API key after the equals sign:
     ```
     GEMINI_API_KEY=your-api-key-here
     ```

3. **Restart the Backend**:
   - Stop the backend server (Ctrl+C)
   - Start it again: `uvicorn app.main:app --reload`

## What Gemini Enables:

With Gemini API configured, PlayDex can understand:
- Complex queries: "steph curry step back three in the clutch"
- Natural language: "that amazing lebron dunk from last night"
- Multiple actions: "giannis block then dunk on the fast break"
- Context: "curry's shot when they were down by 5"
- Variations: "the greek freak's nasty poster" (recognizes Giannis)

## Fallback Mode:

If you don't configure a Gemini API key, PlayDex will still work using basic keyword matching, but with limited understanding of complex queries.