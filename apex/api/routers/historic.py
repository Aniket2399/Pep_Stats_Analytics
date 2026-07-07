"""Historic (StatsBomb) read routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from ..db import get_db
from .. import queries

router = APIRouter(prefix="/api", tags=["historic"])

@router.get("/clubs")
def get_clubs(con=Depends(get_db)):
    return queries.clubs(con)

@router.get("/players")
def get_players(club: int | None = None, position: str | None = None,
                limit: int | None = Query(None, ge=1), con=Depends(get_db)):
    return queries.players(con, club=club, position=position, limit=limit)

@router.get("/players/{player_id}")
def get_player(player_id: int, con=Depends(get_db)):
    row = queries.player(con, player_id)
    if row is None:
        raise HTTPException(status_code=404, detail="player not found")
    return row

@router.get("/teams")
def get_teams(con=Depends(get_db)):
    return queries.teams(con)

@router.get("/teams/{team_id}")
def get_team(team_id: int, con=Depends(get_db)):
    row = queries.team(con, team_id)
    if row is None:
        raise HTTPException(status_code=404, detail="team not found")
    return row

@router.get("/standings")
def get_standings(con=Depends(get_db)):
    return queries.standings(con)

@router.get("/shots")
def get_shots(club: int | None = None, player: int | None = None,
              match: int | None = None, con=Depends(get_db)):
    return queries.shots(con, club=club, player=player, match=match)
