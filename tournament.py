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
    The database assigns a unique serial id number for the player.

    Player is registered to the current tournament.
    If you want the player to be registered to a new tournament,
    then a new tournament has to be created first with createTournament().
    Args:
      name: the player's full name (need not be unique).
    """
    # If there is no tournament, create one
    result = execute('select count(*) from tournament')
    result = result[0][0]
    if result == 0:
        createTounament('First tournament')
    current_tournament = getCurrentTournament()
    # Add player to player table
    result = execute('insert into player values (default, %s) returning id',
                     (name,))
    player = result[0][0]
    # Register player in the current tournament
    execute('insert into tournament_player values (%s, %s)',
            (current_tournament, player))


def opponentMatchWins(player_id, tournament_id):
    """Return opponent match wins (OMW) of the player in tournament.
    This is a helper function when calculating playerStandings().
    """
    # Find all the opponents the player with player_id
    # has played against in tournament_id
    r = execute('select * from tournament_match_result where '
                'tournament_id=%s and (winner_id=%s or loser_id=%s)',
                (tournament_id, player_id, player_id))
    opponents = []
    for row in r:
        if row[2] != player_id:
            opponents.append(row[2])
        else:
            opponents.append(row[3])
    # Find opponent match wins (OMW) by iterating the opponents of
    # player_id, and calculate the sum of their wins
    opponent_match_wins = 0
    for opponent in opponents:
        # Find the number of wins of opponent
        r = execute('select count(*) from tournament_match_result where '
                    'tournament_id=%s and winner_id=%s and is_draw=false',
                    (tournament_id, opponent))
        wins = r[0][0]
        opponent_match_wins += wins
    return opponent_match_wins


def playerStandings():
    """Return a list of the players and their win records, sorted by wins.
    When two players have the same number of wins, rank them according to
    OMW (Opponent Match Wins), the total number of wins by players
    they have played against. 

    The first entry in list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    # Get current players who are in the current tournament
    current_players = execute('select * from current_player')
    current_tournament_id = getCurrentTournament()
    # standings_with_omw is a list of tuples holding the player standings
    # with player's id, name, wins, matches,
    # and a facicilating value holding opponent match wins (OMW)
    # that is used for sorting player standings
    standings_with_omw = []
    for player_id, player_name in current_players:
        # Calculate the number of wins of player_id
        r = execute('select count(*) from tournament_match_result where '
                    'tournament_id=%s and winner_id=%s and is_draw=false',
                    (current_tournament_id, player_id))
        wins = r[0][0]
        # Calculate the number of matched player_id has played
        r = execute('select count(*) from tournament_match_result '
                    'where tournament_id=%s and (winner_id=%s or loser_id=%s)',
                    (current_tournament_id, player_id, player_id))
        matches = r[0][0]
        # Calculate opponent match wins (OMW) of player_id
        omw = opponentMatchWins(player_id, current_tournament_id)
        # Add player's id, name, wins, matches, OMW to list
        standings_with_omw.append((player_id, player_name, wins, matches, omw))
    # Sort list first by player's number of wins, if tied,
    # then by player's OMW.
    # This sortig is done in Python, because I don't know how to do it in SQL
    # that is both easy to implement and easy to understand
    # because the sorting has to be done on two values
    standings_with_omw.sort(key=lambda x: (x[2], x[4]), reverse=True)
    standings = []
    # Save the first four values, i.e. id, name, wins, matches to standings
    # since the fifth value OMW is only used for sorting,
    # and is needed in the final result
    for standing in standings_with_omw:
        standings.append(standing[:4])
    return standings


def reportMatch(winner, loser=None, is_draw=False):
    """Record the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
              when None, it means the winner gets a bye (i.e. a free win)
      is_draw: whether the match is a draw. default: False
               when True, winner and loser are assigned arbitrarily
    """
    current_tournament_id = getCurrentTournament()
    if loser is None:
        # When loser is None, it means winner gets a bye
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
        # When there are an odd number of players:
        # find all players who have got a bye,
        # which is determined by playing a match with a null player
        players_with_a_bye = []
        r = execute('select winner_id from tournament_match_result where '
                    'tournament_id=%s and loser_id is null',
                    (current_tournament_id,))
        if r:
            for row in r:
                players_with_a_bye.append(row[0])
        # Get all players
        players = [row[0] for row in standings]
        # Find all players who haven't got a bye,
        # by substracting players_with_a_bye from all players
        players_without_a_bye = set(players) - set(players_with_a_bye)
        # Randomly choose a player from players_without_a_bye,
        # who will receive a bye this round
        player_receiving_bye = random.choice(list(players_without_a_bye))
        # Exclude the player_receiving_bye from standings list.
        # Thus standings list now has an even number of players,
        # which is equivalent to the case when there are an even number
        # of players to start with
        standings = filter(lambda x: x[0] != player_receiving_bye, standings)

    # Now that standings list has an even number of players,
    # we can pair a player with another player who is next in the standings
    pairings = []
    for i in range(0, len(standings), 2):
        id1, name1, _, _ = standings[i]
        id2, name2, _, _ = standings[i+1]
        pairings.append((id1, name1, id2, name2))
    # Please note that the returned pairings do not include the player who
    # receives a bye in this round, when there are an odd number of players.
    # This makes sense, since that player does not pair with anyone.
    return pairings
