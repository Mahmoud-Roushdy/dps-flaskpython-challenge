from flask import Flask, jsonify, request
import sqlite3
import os

# Define the path to your database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app = Flask(__name__)


def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    Enforces foreign key constraints and allows row-based access.
    """
    # This creates the connection to the .db file
    conn = sqlite3.connect(DB_PATH)
    # This allows you to access columns by name (e.g., player['name'])
    conn.row_factory = sqlite3.Row
    # This ensures your Table Relationships (Foreign Keys) are active
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.route("/init", methods=["GET"])
def init_db():
    """
    Initializes the SQLite database.
    Creates the necessary tables (tournaments, players, matches) if they do not exist.
    """
    conn = get_db_connection()

    # 1. Create the Tournaments table (Parent table)
    # Tracks the overall status of the competition
    conn.execute(
        """ 
        CREATE TABLE IF NOT EXISTS tournaments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'Planning' -- Valid states: Planning, Started, Completed
        )
        """
    )

    # 2. Create the Players table (Parent table)
    # Stores the participants
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS players(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        ) 
        """
    )

    # 3. Create the Matches table (Child table)
    # Links players to a specific tournament and records their scores
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS matches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            player1_id INTEGER NOT NULL,
            player2_id INTEGER NOT NULL,
            score1 INTEGER DEFAULT NULL,
            score2 INTEGER DEFAULT NULL,
            FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
            FOREIGN KEY (player1_id) REFERENCES players (id),
            FOREIGN KEY (player2_id) REFERENCES players (id)
        ) 
        """
    )

    # Save the changes and close the connection
    conn.commit()
    conn.close()

    # Return a success response with an explicit 200 OK status
    return jsonify({"message": "Database initialized successfully!"}), 200


@app.route("/players", methods=["GET"])
def get_all_players():
    """
    Retrieves a list of all players in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all rows from the players table
    players = cursor.execute("SELECT * FROM players").fetchall()

    # Note: conn.commit() is removed here because we are only reading data, not changing it.
    conn.close()

    # Convert SQLite Row objects to standard Python dictionaries for JSON serialization
    return jsonify([dict(player) for player in players]), 200


@app.route("/matches", methods=["GET"])
def get_all_matches():
    """
    Retrieves a list of all matches in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all rows from the matches table
    matches = cursor.execute("SELECT * FROM matches").fetchall()

    conn.close()

    return jsonify([dict(match) for match in matches]), 200


@app.route("/players", methods=["POST"])
def add_player():
    """
    Adds a new player to the database.
    Expects JSON payload: {"name": "Player Name"}
    """
    # Use force=True to prevent the 'str object has no attribute get' error
    data = request.get_json(force=True)
    name = data.get("name")

    # VALIDATION: Prevent the app from crashing if the user forgets to send a name
    if not name or str(name).strip() == "":
        return jsonify({"error": "Player name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert the new player into the database
    cursor.execute("INSERT INTO players(name) VALUES(?)", (name,))

    # Commit is required here because we are writing new data
    conn.commit()

    # Get the ID of the player we just inserted
    player_id = cursor.lastrowid
    conn.close()

    new_player = {"id": player_id, "name": name}

    return jsonify({"message": "Player added successfully!", "player": new_player}), 201


@app.route("/start", methods=["POST"])
def start_play():
    """
    Starts a new tournament by creating a tournament record
    and generating all possible match pairings between players.
    """
    # Use force=True to ensure JSON parsing works regardless of headers
    data = request.get_json(force=True)
    tournament_name = data.get("tour_name", "Unnamed Tournament")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all registered players
    players = cursor.execute("SELECT id FROM players").fetchall()
    # Check if a tournament is already in progress
    existing_matches = cursor.execute("SELECT id FROM matches").fetchall()

    players_size = len(players)

    # VALIDATION 1: Ensure enough players are present
    if players_size < 2 or players_size > 5:
        return (
            jsonify({"message": "The number of players should be in the range 2-5!"}),
            400,
        )

    # VALIDATION 2: Prevent starting a new tournament if one exists
    if len(existing_matches) > 0:
        return (
            jsonify(
                {
                    "message": "You should finish the current tournament or cancel it first!"
                }
            ),
            400,
        )

    # 1. Create the Tournament entry
    cursor.execute(
        "INSERT INTO tournaments (name, status) VALUES (?, ?)",
        (tournament_name, "Started"),
    )
    tournament_id = cursor.lastrowid

    # 2. Match Generation Logic (Round Robin)
    matches_size = 0
    # The outer loop picks Player A
    for i in range(players_size):
        # The inner loop picks Player B (starting from the player after A)
        # This prevents a player from playing themselves or playing the same person twice
        for j in range(i + 1, players_size):
            player1_id = players[i]["id"]
            player2_id = players[j]["id"]

            cursor.execute(
                "INSERT INTO matches(tournament_id, player1_id, player2_id) VALUES(?,?,?)",
                (tournament_id, player1_id, player2_id),
            )
            matches_size += 1

    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": f"Successfully created {matches_size} matches for tournament: {tournament_name}!",
                "tournament_id": tournament_id,
            }
        ),
        201,
    )


@app.route("/matches/<int:match_id>", methods=["PATCH"])
def update_scores(match_id):
    """
    Updates the scores for a specific match.
    Expects JSON: {"score1": int, "score2": int}
    """
    data = request.get_json(force=True)
    score1 = data.get("score1")
    score2 = data.get("score2")

    # VALIDATION: Ensure both scores are provided
    if score1 is None or score2 is None:
        return jsonify({"error": "Please provide both score1 and score2"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the match actually exists
    match = cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,)).fetchone()
    if not match:
        conn.close()
        return jsonify({"message": "Match not found"}), 404

    # Update scores in the database
    cursor.execute(
        "UPDATE matches SET score1 = ?, score2 = ? WHERE id = ?",
        (score1, score2, match_id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": f"Match {match_id} updated successfully",
                "result": {"score1": score1, "score2": score2},
            }
        ),
        200,
    )


@app.route("/result", methods=["GET"])
def get_result():
    """
    Calculates and returns the leaderboard for the most recent tournament.
    Includes points, wins, draws, losses, and overall ranking.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Identify the most recent tournament
    latest_tour = cursor.execute(
        "SELECT * FROM tournaments ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if not latest_tour:
        conn.close()
        return jsonify({"message": "No tournament found"}), 404

    # 2. Fetch all matches and players for this specific tournament
    matches = cursor.execute(
        "SELECT * FROM matches WHERE tournament_id = ?", (latest_tour["id"],)
    ).fetchall()
    players = cursor.execute("SELECT * FROM players").fetchall()

    # 3. Initialize a dictionary to store stats for each player
    results = {
        p["id"]: {
            "player_id": p["id"],
            "name": p["name"],
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,  # Note: capitalized consistency is better (Losses)
            "points": 0,
        }
        for p in players
    }

    completed_count = 0
    # 4. Iterate through matches to calculate points
    for m in matches:
        p1_id, p2_id = m["player1_id"], m["player2_id"]
        s1, s2 = m["score1"], m["score2"]

        # Only count matches where scores have been submitted
        if s1 is not None and s2 is not None:
            completed_count += 1
            results[p1_id]["played"] += 1
            results[p2_id]["played"] += 1

            if s1 > s2:
                results[p1_id]["wins"] += 1
                results[p1_id]["points"] += 2
                results[p2_id]["losses"] += 1
            elif s2 > s1:
                results[p2_id]["wins"] += 1
                results[p2_id]["points"] += 2
                results[p1_id]["losses"] += 1
            else:
                results[p1_id]["draws"] += 1
                results[p1_id]["points"] += 1
                results[p2_id]["draws"] += 1
                results[p2_id]["points"] += 1

    # 5. Sort the results list by points (highest first)
    leaderboard = sorted(results.values(), key=lambda p: p["points"], reverse=True)

    # 6. Assign visual rank based on sorted position
    for index, player in enumerate(leaderboard):
        player["rank"] = index + 1

    conn.close()

    # 7. Final JSON response structure matching the requirements
    return (
        jsonify(
            {
                "tournament_id": latest_tour["id"],
                "tournament_name": latest_tour["name"],
                "status": latest_tour["status"],
                "total_matches": len(matches),
                "completed_matches": completed_count,
                "leaderboard": leaderboard,
            }
        ),
        200,
    )


@app.route("/reset", methods=["DELETE"])
def reset_tournament():
    """
    Clears all matches and resets the tournament status.
    Keeps the players list intact so you don't have to re-add them.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Delete all matches
        cursor.execute("DELETE FROM matches")

        # 2. Delete all tournaments
        cursor.execute("DELETE FROM tournaments")

        # (This makes your IDs start from 1 again)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='matches'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tournaments'")

        conn.commit()
        message = "Tournament data cleared. You can now start a new one!"
        status_code = 200
    except Exception as e:
        conn.rollback()
        message = f"An error occurred: {str(e)}"
        status_code = 500
    finally:
        conn.close()

    return jsonify({"message": message}), status_code


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
