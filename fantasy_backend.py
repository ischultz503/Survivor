from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/fantasy_survivor.db")

LEAGUE_CONFIG = {
    "NE Portland": {
        "Season 49": {"scores": "data/PointsScored_Survivor_49.xlsx", "point_values": "data/PointValues_Survivor.csv"},
        "Season 48": {"scores": "data/PointsScored_Survivor_48.xlsx", "point_values": "data/PointValues_Survivor.csv"},
        "Season 47": {"scores": "data/PointsScored_Survivor_47.xlsx", "point_values": "data/PointValues_Survivor.csv"},
    },
    "Bi-coastal Elites": {
        "Season 49": {"scores": "data/east/Survivor_49_East.xlsx", "point_values": "data/east/Survivor_49_East.xlsx"}
    },
}

ROSTERS = {
    ("NE Portland", "Season 49"): {
        "Picasso": ["Savannah", "Steven", "Jawan", "Sage"],
        "Brackie": ["MC", "Rizo", "Matt", "Shannon"],
        "Polron": ["Sophie S", "Nate", "Jason", "Kristina"],
        "Kanna": ["Alex", "Jeremiah", "Sophi B", "Jake"],
    },
    ("Bi-coastal Elites", "Season 49"): {
        "Jena": ["Matt", "Sophie S", "Rizo"],
        "Schultz & Big P": ["Kristina", "Alex", "Savannah"],
        "Isaac": ["Jawan", "Jeremiah", "Steven"],
        "Mike": ["Nate", "Jake", "Sage"],
        "Nick": ["MC", "Nicole", "Annie"],
        "Eric": ["Jason", "Sophi B", "Shannon"],
    },
    ("NE Portland", "Season 48"): {
        "Picasso": ["Eva", "Mitch", "Mary", "Sai"],
        "Brackie": ["Kamilla", "Kyle", "Chrissy", "Cedrek"],
        "Polron": ["Joe", "Thomas", "Bianca", "Charity"],
        "Kanna": ["Shauhin", "Justin", "Star", "David"],
    },
    ("NE Portland", "Season 47"): {
        "Picasso": ["Sam", "Sierra", "Genevieve", "Sue", "Caroline"],
        "Brackie": ["Kyle", "Rome", "Sol", "Anika", "Kishan"],
        "Polron": ["Teeny", "Rachel", "Andy", "Gabe", "Tiyana"],
    },
}




def load_point_values(path: str, league_name: str) -> pd.DataFrame:
    if league_name == "Bi-coastal Elites":
        df = pd.read_excel(path, "PointValues_Survivor")[["Event", "Points"]]
    else:
        df = pd.read_csv(path)[["Event", "Points"]]
    df["Event"] = df["Event"].astype(str).str.strip()
    return df.dropna(subset=["Event", "Points"]).drop_duplicates("Event")

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{salt.hex()}:{digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, hash_hex = stored_hash.split(":", 1)
    recomputed = _hash_password(password, bytes.fromhex(salt_hex)).split(":", 1)[1]
    return hash_hex == recomputed


def init_db(force_seed: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league_id INTEGER NOT NULL,
                season_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(league_id, season_id, name),
                FOREIGN KEY (league_id) REFERENCES leagues(id),
                FOREIGN KEY (season_id) REFERENCES seasons(id)
            );
            CREATE TABLE IF NOT EXISTS roster_players (
                team_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                PRIMARY KEY(team_id, player_name),
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
            CREATE TABLE IF NOT EXISTS user_teams (
                user_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                PRIMARY KEY(user_id, team_id),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
            CREATE TABLE IF NOT EXISTS point_values (
                season_id INTEGER NOT NULL,
                event_name TEXT NOT NULL,
                points REAL NOT NULL,
                PRIMARY KEY(season_id, event_name),
                FOREIGN KEY(season_id) REFERENCES seasons(id)
            );
            CREATE TABLE IF NOT EXISTS player_event_scores (
                season_id INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                event_name TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY(season_id, week_number, player_name, event_name),
                FOREIGN KEY(season_id) REFERENCES seasons(id)
            );
            CREATE TABLE IF NOT EXISTS weekly_question_scores (
                team_id INTEGER NOT NULL,
                week_number INTEGER NOT NULL,
                points REAL NOT NULL,
                PRIMARY KEY(team_id, week_number),
                FOREIGN KEY(team_id) REFERENCES teams(id)
            );
            """
        )
    if force_seed:
        seed_from_legacy()


def seed_from_legacy() -> None:
    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM teams").fetchone()["c"]
        if existing:
            return
        for league_name, seasons in LEAGUE_CONFIG.items():
            conn.execute("INSERT INTO leagues(name) VALUES (?)", (league_name,))
            for season_label in seasons:
                conn.execute("INSERT OR IGNORE INTO seasons(label) VALUES (?)", (season_label,))

        conn.execute(
            "INSERT OR IGNORE INTO users(username,password_hash,is_admin) VALUES (?,?,1)",
            ("admin", _hash_password("admin123")),
        )

        for (league_name, season_label), teams in ROSTERS.items():
            league_id = _id_for(conn, "leagues", "name", league_name)
            season_id = _id_for(conn, "seasons", "label", season_label)
            for team_name, players in teams.items():
                conn.execute(
                    "INSERT INTO teams(league_id,season_id,name) VALUES (?,?,?)",
                    (league_id, season_id, team_name),
                )
                team_id = conn.execute(
                    "SELECT id FROM teams WHERE league_id=? AND season_id=? AND name=?",
                    (league_id, season_id, team_name),
                ).fetchone()["id"]
                for player in players:
                    conn.execute(
                        "INSERT INTO roster_players(team_id, player_name) VALUES (?,?)",
                        (team_id, player),
                    )

        for league_name, seasons in LEAGUE_CONFIG.items():
            for season_label, paths in seasons.items():
                season_id = _id_for(conn, "seasons", "label", season_label)
                point_values = load_point_values(paths["point_values"], league_name)
                for _, row in point_values.iterrows():
                    conn.execute(
                        "INSERT OR REPLACE INTO point_values(season_id,event_name,points) VALUES (?,?,?)",
                        (season_id, row["Event"], float(row["Points"])),
                    )

                raw_scores = pd.read_excel(paths["scores"], "PointsScored_Survivor")
                event_cols = [e for e in point_values["Event"].tolist() if e in raw_scores.columns]
                melted = raw_scores[["Player", "Week", *event_cols]].melt(
                    id_vars=["Player", "Week"], var_name="event_name", value_name="value"
                )
                melted["value"] = melted["value"].fillna(0)
                melted = melted[melted["value"] != 0]
                for _, row in melted.iterrows():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO player_event_scores(season_id,week_number,player_name,event_name,value)
                        VALUES (?,?,?,?,?)
                        """,
                        (season_id, int(row["Week"]), row["Player"], row["event_name"], float(row["value"])),
                    )

                weekly_bonus = pd.read_excel(paths["scores"], "Weekly_Pick_Scores")
                for _, row in weekly_bonus.iterrows():
                    week = int(row["Week"])
                    for col in weekly_bonus.columns:
                        if col == "Week" or pd.isna(row[col]):
                            continue
                        team_lookup = "Schultz & Big P" if col.strip() == "Schultz  & Big P" else col
                        team_id = team_id_for(conn, league_name, season_label, team_lookup)
                        if team_id:
                            conn.execute(
                                "INSERT OR REPLACE INTO weekly_question_scores(team_id,week_number,points) VALUES (?,?,?)",
                                (team_id, week, float(row[col])),
                            )


def _id_for(conn: sqlite3.Connection, table: str, col: str, value: str) -> int:
    row = conn.execute(f"SELECT id FROM {table} WHERE {col}=?", (value,)).fetchone()
    if row is None:
        raise ValueError(f"No row in {table} for {value}")
    return row["id"]


def register_user(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required."
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users(username,password_hash,is_admin) VALUES (?,?,0)",
                (username.strip(), _hash_password(password)),
            )
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "Username already exists."


def authenticate_user(username: str, password: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    if row and _verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def list_league_season_options_for_user(user_id: int) -> pd.DataFrame:
    query = """
    SELECT t.id AS team_id, t.name AS team_name, l.name AS league_name, s.label AS season_label
    FROM user_teams ut
    JOIN teams t ON ut.team_id=t.id
    JOIN leagues l ON t.league_id=l.id
    JOIN seasons s ON t.season_id=s.id
    WHERE ut.user_id=?
    ORDER BY s.label DESC, l.name, t.name
    """
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=[user_id])


def assign_team(username: str, league_name: str, season_label: str, team_name: str) -> tuple[bool, str]:
    with get_conn() as conn:
        user = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        team_id = team_id_for(conn, league_name, season_label, team_name)
        if not user or not team_id:
            return False, "User or team not found."
        conn.execute("INSERT OR IGNORE INTO user_teams(user_id,team_id) VALUES (?,?)", (user["id"], team_id))
    return True, "Team linked."


def team_id_for(conn: sqlite3.Connection, league_name: str, season_label: str, team_name: str) -> int | None:
    row = conn.execute(
        """
        SELECT t.id FROM teams t
        JOIN leagues l ON t.league_id=l.id
        JOIN seasons s ON t.season_id=s.id
        WHERE l.name=? AND s.label=? AND t.name=?
        """,
        (league_name, season_label, team_name),
    ).fetchone()
    return row["id"] if row else None


def list_all_teams() -> pd.DataFrame:
    query = """
    SELECT l.name AS league_name, s.label AS season_label, t.name AS team_name
    FROM teams t JOIN leagues l ON t.league_id=l.id JOIN seasons s ON t.season_id=s.id
    ORDER BY s.label DESC, l.name, t.name
    """
    with get_conn() as conn:
        return pd.read_sql_query(query, conn)


def _team_weekly_points(conn: sqlite3.Connection, team_id: int) -> pd.DataFrame:
    query = """
    WITH team_info AS (
      SELECT t.id AS team_id, t.season_id
      FROM teams t WHERE t.id=?
    ), player_points AS (
      SELECT pes.week_number, SUM(pes.value * pv.points) AS player_points
      FROM player_event_scores pes
      JOIN team_info ti ON pes.season_id=ti.season_id
      JOIN roster_players rp ON rp.player_name=pes.player_name AND rp.team_id=ti.team_id
      JOIN point_values pv ON pv.season_id=pes.season_id AND pv.event_name=pes.event_name
      GROUP BY pes.week_number
    )
    SELECT pp.week_number,
           pp.player_points,
           COALESCE(wqs.points, 0) AS bonus_points,
           pp.player_points + COALESCE(wqs.points,0) AS week_total
    FROM player_points pp
    LEFT JOIN weekly_question_scores wqs ON wqs.team_id=? AND wqs.week_number=pp.week_number
    ORDER BY pp.week_number
    """
    df = pd.read_sql_query(query, conn, params=[team_id, team_id])
    if df.empty:
        return df
    df["cumulative_total"] = df["week_total"].cumsum()
    return df


def build_team_dashboard(team_id: int) -> dict[str, pd.DataFrame | float | int]:
    with get_conn() as conn:
        weekly = _team_weekly_points(conn, team_id)
        row = conn.execute(
            """
            SELECT t.name AS team_name, l.name AS league_name, s.label AS season_label
            FROM teams t JOIN leagues l ON t.league_id=l.id JOIN seasons s ON t.season_id=s.id
            WHERE t.id=?
            """,
            (team_id,),
        ).fetchone()
        standings = pd.read_sql_query(
            """
            SELECT t.id AS team_id, t.name AS team_name,
                   COALESCE(SUM(pes.value * pv.points),0) + COALESCE(SUM(wqs.points),0) AS total_points
            FROM teams t
            JOIN leagues l ON l.id=t.league_id
            JOIN seasons s ON s.id=t.season_id
            LEFT JOIN roster_players rp ON rp.team_id=t.id
            LEFT JOIN player_event_scores pes ON pes.player_name=rp.player_name AND pes.season_id=t.season_id
            LEFT JOIN point_values pv ON pv.season_id=pes.season_id AND pv.event_name=pes.event_name
            LEFT JOIN weekly_question_scores wqs ON wqs.team_id=t.id
            WHERE l.name=? AND s.label=?
            GROUP BY t.id, t.name
            ORDER BY total_points DESC
            """,
            conn,
            params=[row["league_name"], row["season_label"]],
        )

        player_weekly = pd.read_sql_query(
            """
            SELECT pes.week_number,
                   rp.player_name,
                   SUM(pes.value * pv.points) AS points
            FROM roster_players rp
            JOIN teams t ON t.id=rp.team_id
            JOIN player_event_scores pes ON pes.player_name=rp.player_name AND pes.season_id=t.season_id
            JOIN point_values pv ON pv.season_id=pes.season_id AND pv.event_name=pes.event_name
            WHERE rp.team_id=?
            GROUP BY pes.week_number, rp.player_name
            ORDER BY pes.week_number, points DESC, rp.player_name
            """,
            conn,
            params=[team_id],
        )

        event_breakdown = pd.read_sql_query(
            """
            SELECT pes.week_number,
                   rp.player_name,
                   pes.event_name,
                   pes.value,
                   pv.points,
                   (pes.value * pv.points) AS event_points
            FROM roster_players rp
            JOIN teams t ON t.id=rp.team_id
            JOIN player_event_scores pes ON pes.player_name=rp.player_name AND pes.season_id=t.season_id
            JOIN point_values pv ON pv.season_id=pes.season_id AND pv.event_name=pes.event_name
            WHERE rp.team_id=?
            ORDER BY pes.week_number DESC, event_points DESC, rp.player_name
            """,
            conn,
            params=[team_id],
        )

        bonus_weekly = pd.read_sql_query(
            """
            SELECT week_number, points
            FROM weekly_question_scores
            WHERE team_id=?
            ORDER BY week_number
            """,
            conn,
            params=[team_id],
        )
    total = float(weekly["week_total"].sum()) if not weekly.empty else 0.0
    current_week = int(weekly["week_number"].max()) if not weekly.empty else 0
    player_totals = (
        player_weekly.groupby("player_name", as_index=False)["points"]
        .sum()
        .sort_values("points", ascending=False)
        .rename(columns={"player_name": "Player", "points": "Total Points"})
    )

    elimination_events = event_breakdown[
        event_breakdown["event_name"].str.contains(
            "eliminat|exits|kicked off|fire making|rocks|voluntar", case=False, regex=True
        )
    ].copy()
    return {
        "meta": pd.DataFrame([dict(row)]),
        "weekly": weekly,
        "standings": standings,
        "player_weekly": player_weekly,
        "player_totals": player_totals,
        "event_breakdown": event_breakdown,
        "bonus_weekly": bonus_weekly,
        "eliminations": elimination_events,
        "total": total,
        "current_week": current_week,
    }


def upsert_player_event(season_label: str, week_number: int, player_name: str, event_name: str, value: float) -> None:
    with get_conn() as conn:
        season_id = _id_for(conn, "seasons", "label", season_label)
        conn.execute(
            "INSERT OR REPLACE INTO player_event_scores(season_id,week_number,player_name,event_name,value) VALUES (?,?,?,?,?)",
            (season_id, week_number, player_name, event_name, value),
        )


def upsert_weekly_bonus(league_name: str, season_label: str, team_name: str, week_number: int, points: float) -> None:
    with get_conn() as conn:
        team_id = team_id_for(conn, league_name, season_label, team_name)
        if team_id is None:
            raise ValueError("Team not found")
        conn.execute(
            "INSERT OR REPLACE INTO weekly_question_scores(team_id,week_number,points) VALUES (?,?,?)",
            (team_id, week_number, points),
        )


def list_seasons() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT label FROM seasons ORDER BY label DESC").fetchall()
    return [r["label"] for r in rows]


def list_events_for_season(season_label: str) -> list[str]:
    with get_conn() as conn:
        season_id = _id_for(conn, "seasons", "label", season_label)
        rows = conn.execute(
            "SELECT event_name FROM point_values WHERE season_id=? ORDER BY event_name", (season_id,)
        ).fetchall()
    return [r["event_name"] for r in rows]


def list_players_for_season(season_label: str) -> list[str]:
    with get_conn() as conn:
        season_id = _id_for(conn, "seasons", "label", season_label)
        rows = conn.execute(
            "SELECT DISTINCT player_name FROM player_event_scores WHERE season_id=? ORDER BY player_name",
            (season_id,),
        ).fetchall()
    return [r["player_name"] for r in rows]


def list_leagues() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM leagues ORDER BY name").fetchall()
    return [r["name"] for r in rows]


def list_teams_for_league_season(league_name: str, season_label: str) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT t.name FROM teams t JOIN leagues l ON t.league_id=l.id JOIN seasons s ON t.season_id=s.id
            WHERE l.name=? AND s.label=? ORDER BY t.name
            """,
            (league_name, season_label),
        ).fetchall()
    return [r["name"] for r in rows]
