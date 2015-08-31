#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#
import psycopg2
import random


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def execute(query, params=()):
    """Connect to the database. Execute query. Commit.
    Return returned value from database."""
    db = connect()
    c = db.cursor()
    c.execute(query, params)
    try:
        result = c.fetchall()
    except psycopg2.ProgrammingError:
        result = None
    db.commit()
    db.close()
    return result


def deleteMatches():
    """Remove all the match records from the database."""
    execute('delete from tournament_match_result')


def deletePlayers():
    """Remove all the player records from the database."""
    execute('delete from player')


def countPlayers():
    """Return the number of players currently registered."""
    result = execute('select count(*) from current_player')
    return result[0][0]


def createTounament(name):
    """Create a new tournament.
    This is to support the feature that more than one tournament
    can be in the database."""
    execute('insert into tournament values (default, %s)', (name,))


def getCurrentTournament():
    """Return current tournament, i.e. the one with the max id.
    See database view current_tournament for details."""
    result = execute('select * from current_tournament')
    return result[0][0]


def registerPlayer(name):
    """Add a player to the tournament database.
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Player is registered to the current tournament.
    If you want the player to be registered to a new tournament,
    then a new tournament has to be created first with createTournament().
    Args:
      name: the player's full name (need not be unique).
    """
    # if there is no tournament, create one
    result = execute('select count(*) from tournament')
    result = result[0][0]
    if result == 0:
        createTounament('First tournament')
    current_tournament = getCurrentTournament()
    result = execute('insert into player values (default, %s) returning id',
                     (name,))
    player = result[0][0]
    execute('insert into tournament_player values (%s, %s)',
            (current_tournament, player))


def opponentMatchWins(player_id, tournament_id):
    """Return opponent match wins (OMW) of the player in tournament."""
    r = execute('select * from tournament_match_result where '
                'tournament_id=%s and (winner_id=%s or loser_id=%s)',
                (tournament_id, player_id, player_id))
    opponents = []
    for row in r:
        if row[2] != player_id:
            opponents.append(row[2])
        else:
            opponents.append(row[3])
    opponent_match_wins = 0
    for opponent in opponents:
        r = execute('select count(*) from tournament_match_result where '
                    'tournament_id=%s and winner_id=%s and is_draw=false',
                    (tournament_id, opponent))
        wins = r[0][0]
        opponent_match_wins += wins
    return opponent_match_wins


def playerStandings():
    """Return a list of the players and their win records, sorted by wins.

    The first entry in list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    current_players = execute('select * from current_player')
    current_tournament_id = getCurrentTournament()
    standings_with_omw = []
    for player_id, player_name in current_players:
        r = execute('select count(*) from tournament_match_result where '
                    'tournament_id=%s and winner_id=%s and is_draw=false',
                    (current_tournament_id, player_id))
        wins = r[0][0]
        r = execute('select count(*) from tournament_match_result '
                    'where tournament_id=%s and (winner_id=%s or loser_id=%s)',
                    (current_tournament_id, player_id, player_id))
        matches = r[0][0]
        omw = opponentMatchWins(player_id, current_tournament_id)
        standings_with_omw.append((player_id, player_name, wins, matches, omw))
    standings_with_omw.sort(key=lambda x: (x[2], x[4]), reverse=True)
    standings = []
    for standing in standings_with_omw:
        standings.append(standing[:4])
    return standings


def reportMatch(winner, loser=None, is_draw=False):
    """Record the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      is_draw: whether the match is a draw. default: False
    """
    current_tournament_id = getCurrentTournament()
    if loser is None:
        # winner gets a bye
        execute('insert into tournament_match_result values (default, %s, %s)',
                (current_tournament_id, winner))
    else:
        execute('insert into tournament_match_result values '
                '(default, %s, %s, %s)',
                (current_tournament_id, winner, loser))


def swissPairings():
    """Return a list of pairs of players for the next round of a match.
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    standings = playerStandings()
    current_tournament_id = getCurrentTournament()
    if len(standings) % 2 != 0:
        # odd number of players
        # find all player who have got a bye,
        # determined by pairing with a null player
        players_with_a_bye = []
        r = execute('select winner_id from tournament_match_result where '
                    'tournament_id=%s and loser_id is null',
                    (current_tournament_id,))
        if r:
            for row in r:
                players_with_a_bye.append(row[0])
        players = [row[0] for row in standings]
        players_without_a_bye = set(players) - set(players_with_a_bye)
        # randomly choose a player from players_without_a_bye
        # who will receive a bye this round
        player_receiving_bye = random.choice(list(players_without_a_bye))
        standings = filter(lambda x: x[0] != player_receiving_bye, standings)

    pairings = []
    for i in range(0, len(standings), 2):
        id1, name1, _, _ = standings[i]
        id2, name2, _, _ = standings[i+1]
        pairings.append((id1, name1, id2, name2))
    return pairings
