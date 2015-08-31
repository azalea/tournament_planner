# Tournament Results

This is Project 2 of Full Stack Web Developer Nanodegree.

Database schema is designed and implemented in tournament.sql. Two database views are used to store query results which can then be retrieved easily.

APIs to access the database are implemented in tournament.py. 

Tests are in tournament_test.py which have been implemented beforehand to facilitate test-driven development.

## Features:

tournament.py has the following functions (modified from the original project description):

* registerPlayer(name)

  > Adds a player to the tournament by putting an entry in the database. The database assigns an ID number to the player. Different players may have the same names but will receive different ID numbers.

* countPlayers()

  > Returns the number of currently registered players. This function uses the database operations to count the players.

* deletePlayers()

  > Clear out all the player records from the database.

* reportMatch(winner, loser)

  > Stores the outcome of a single match between two players in the database.

* deleteMatches()

  > Clear out all the match records from the database.

* playerStandings()

  > Returns a list of (id, name, wins, matches) for each player, sorted by the number of wins each player has.

* swissPairings()

  > Given the existing set of registered players and the matches they have played, generates and returns a list of pairings according to the Swiss system. Each pairing is a tuple (id1, name1, id2, name2), giving the ID and name of the paired players. For instance, if there are eight registered players, this function will return four pairings. This function uses playerStandings to find the ranking of players.

## Additional features:

* Support more than one tournament in the database. This is achieved by having a player table that stores players in general, a tournament table that stores each tournament, and a tournament_player table that stores which player has entered which tournament.
* Support even or odd number of players per tournament. If there is an odd number of players, assign one player a "bye" which is considered a free win. A player will not receive more than one bye in a tournament. This is achieved in swissPairings() function which randomly selects a player among those who haven't got a "bye" and grants that player a "bye, when there are an odd number of players. In the tournament_match_result table, loser_id is stored as NULL when winner with winner_id receives a "bye".
* Support games where a draw (tied game) is possible. This is achieved by having a tournament_match_result table with a column is_draw that stores whether the match is a draw. The function reportMatch takes an optional parameter is_draw which defaults to False to support this feature.
* When two players have the same number of wins, rank them according to OMW (Opponent Match Wins), the total number of wins by players they have played against. OMW is calculated by opponentMatchWins(), which is then used by playerStandings() to rank the players.
