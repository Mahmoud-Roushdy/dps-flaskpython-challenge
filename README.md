🏆 **Tournament Manager API**
A lightweight, RESTful Flask API designed to manage a Round Robin tournament. This application allows users to register players, automatically generate match pairings, record scores, and view a dynamically calculated leaderboard.

Developed by: Mahmoud Roushdy

🚀 **Features**
Automated Matchmaking: Automatically generates Round Robin pairings (everyone plays everyone) for 2 to 5 players.

Dynamic Leaderboard: Calculates points (2 for a win, 1 for a draw, 0 for a loss) and ranks players on the fly.

Relational Database: Uses SQLite with strictly enforced Foreign Key constraints to maintain data integrity.

Defensive Programming: Includes validation to prevent starting tournaments with insufficient players or missing data.

🛠 **Installation & Setup**
Prerequisites
Python 3.8+ installed on your machine.

1. Set up the Environment
Open your terminal, navigate to the project directory, and create a virtual environment:

Windows:

Bash
python -m venv venv
venv\Scripts\activate
macOS/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
2. Install Dependencies
Install Flask and other required packages using the requirements file:

Bash
pip install -r requirements.txt
3. Run the Application
Start the Flask development server:

Bash
python app.py
The API will be available at http://127.0.0.1:5000

🧪 **Step-by-Step Testing Guide (The "Happy Path")**
To easily test the core functionality, use a tool like Postman, Insomnia, or cURL to follow these exact steps in order:

Step 1: Initialize the Database
Before doing anything, you must create the database tables.

Endpoint: POST http://127.0.0.1:5000/init

Response: 200 OK (Database initialized successfully!)

Step 2: Add Players
You need between 2 and 5 players to start a tournament. Send this request multiple times with different names.

Endpoint: POST http://127.0.0.1:5000/players

Body (JSON):

JSON
{
  "name": "Mahmoud"
}
Step 3: Start the Tournament
This will take the players you just created and generate all the match pairings.

Endpoint: POST http://127.0.0.1:5000/start

Body (JSON):

JSON
{
  "tour_name": "DPS Summer Cup"
}
Take note of the match_ids created in the database or returned in your matches list to use in the next step.

Step 4: Update Match Scores
Submit the results for a specific match.

Endpoint: PATCH http://127.0.0.1:5000/matches/1 (Replace '1' with the actual match ID)

Body (JSON):

JSON
{
  "score1": 3,
  "score2": 1
}
Step 5: View the Leaderboard
Check the status of the tournament and see who is winning.

Endpoint: GET http://127.0.0.1:5000/result/1 (Replace '1' with the actual Tournament ID)

Response: Returns the tournament status (Started or Finished), total matches, completed matches, and the sorted leaderboard with detailed stats (Wins, Draws, Losses, Points, Rank).

Step 6: (Optional) Reset Data
If you want to clear the current tournament and matches to start a new one (without deleting your players).

Endpoint: DELETE http://127.0.0.1:5000/reset

📁** Project Structure**
Plaintext
dps-tournament/
├── app.py                  # Main application logic and API routes
├── requirements.txt        # Python dependencies
├── AI_TRANSPARENCY.md      # Documentation of AI tools used for assistance
├── README.md               # Project documentation

🤖 **AI Transparency**
As per the challenge guidelines, AI tools (Gemini) were used to assist in refactoring code, writing Google-style docstrings, and debugging SQLite behavior. For a full breakdown of the workflow and decisions made, please refer to the AI_TRANSPARENCY.md file included in this repository.
