## Run Locally

**Prerequisites:** Node.js and Python 3.10+

1. Install frontend dependencies:
   `npm install`

2. Install backend dependencies:
   `pip install -r backend/requirements.txt`

3. Configure environment variables in [.env.local](.env.local):
   - `NEXT_PUBLIC_API_URL=http://localhost:8000`
   - `APP_URL` can stay empty or use your local app URL if needed

4. Start the backend from the project root:
   `python main.py`

5. Start the frontend in a second terminal:
   `npm run dev`

6. Open the app at `http://localhost:3000`