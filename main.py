from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException, Response

LICHESS_USER_URL = "https://lichess.org/api/user/{username}"
LICHESS_STATUS_URL = "https://lichess.org/api/users/status"
SHIELDS_BADGE_URL = "https://img.shields.io/badge/{label}-{message}-{color}"

# Lichess logo, base64-encoded SVG, for the shields.io `logo` query param.
LICHESS_LOGO_BASE64 = (
    "PHN2ZyB2aWV3Qm94PSItMC42OTIgMC41IDUxLjU3MyA1NS4yODUiIHhtbG5zPSJodHRwOi8vd3d3"
    "LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjIzODUiIGhlaWdodD0iMjUwMCI+PHBhdGggZD0iTTM4"
    "Ljk1Ni41Yy0zLjUzLjQxOC02LjQ1Mi45MDItOS4yODYgMi45ODRDNS41MzQgMS43ODYtLjY5MiAx"
    "OC41MzMuNjggMjkuMzY0IDMuNDkzIDUwLjIxNCAzMS45MTggNTUuNzg1IDQxLjMyOSA0MS43Yy03"
    "LjQ0NCA3LjY5Ni0xOS4yNzYgOC43NTItMjguMzIzIDMuMDg0Uy0uNTA2IDI3LjM5MiA0LjY4MyAx"
    "Ny41NjdDOS44NzMgNy43NDIgMTguOTk2IDQuNTM1IDI5LjAzIDYuNDA1YzIuNDMtMS40MTggNS4y"
    "MjUtMy4yMiA3LjY1NS0zLjE4N2wtMS42OTQgNC44NiAxMi43NTIgMjEuMzdjLS40MzkgNS42NTQt"
    "NS40NTkgNi4xMTItNS40NTkgNi4xMTItLjU3NC0xLjQ3LTEuNjM0LTIuOTQyLTQuODQyLTYuMDM2"
    "LTMuMjA3LTMuMDk0LTE3LjQ2NS0xMC4xNzctMTUuNzg4LTE2LjIwNy0yLjAwMSA2Ljk2NyAxMC4z"
    "MTEgMTQuMTUyIDE0LjA0IDE3LjY2MyAzLjczIDMuNTEgNS40MjYgNi4wNCA1Ljc5NSA2Ljc1NiAw"
    "IDAgOS4zOTItMi41MDQgNy44MzgtOC45MjdMMzcuNCA3LjE3MXoiIHN0cm9rZT0iI2ZmZiIgZmls"
    "bD0iI2ZmZiIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPgo="
)

app = FastAPI(
    title="Lichess Badges",
    description="Generates shields.io SVG badges for Lichess.org ratings.",
)


class TimeControl(str, Enum):
    ultra_bullet = "ultraBullet"
    bullet = "bullet"
    blitz = "blitz"
    rapid = "rapid"
    classical = "classical"
    correspondence = "correspondence"
    chess960 = "chess960"
    crazyhouse = "crazyhouse"
    antichess = "antichess"
    atomic = "atomic"
    horde = "horde"
    king_of_the_hill = "kingOfTheHill"
    racing_kings = "racingKings"
    three_check = "threeCheck"
    puzzle = "puzzle"


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/api/rating/{username}/{time_control}")
async def badge(username: str, time_control: TimeControl):
    async with httpx.AsyncClient() as client:
        user_response = await client.get(LICHESS_USER_URL.format(username=username))

        if user_response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Lichess user '{username}' not found")
        user_response.raise_for_status()

        data = user_response.json()
        perf = data.get("perfs", {}).get(time_control.value)
        if perf is None:
            raise HTTPException(
                status_code=404,
                detail=f"No {time_control.value} rating found for '{username}'",
            )

        rating = perf["rating"]
        label = f"Lichess {time_control.value[0].upper()}{time_control.value[1:]}"

        shield_response = await client.get(
            SHIELDS_BADGE_URL.format(label=label, message=rating, color="blue"),
            params={
                "logo": f"data:image/svg+xml;base64,{LICHESS_LOGO_BASE64}",
                "style": "for-the-badge",
            },
        )
        shield_response.raise_for_status()

    return Response(content=shield_response.content, media_type="image/svg+xml")


@app.get("/api/status/{username}")
async def status(username: str):
    async with httpx.AsyncClient() as client:
        status_response = await client.get(LICHESS_STATUS_URL, params={"ids": username})
        status_response.raise_for_status()

        users = status_response.json()
        if not users:
            raise HTTPException(status_code=404, detail=f"Lichess user '{username}' not found")

        online = users[0].get("online", False)
        message = "online" if online else "offline"
        color = "brightgreen" if online else "lightgrey"

        shield_response = await client.get(
            SHIELDS_BADGE_URL.format(label="Lichess", message=message, color=color),
            params={
                "logo": f"data:image/svg+xml;base64,{LICHESS_LOGO_BASE64}",
                "style": "for-the-badge",
            },
        )
        shield_response.raise_for_status()

    return Response(content=shield_response.content, media_type="image/svg+xml")
