-- Table definitions for the tournament project.
--
-- Warning: executing this file will drop the existing tournament database
-- Make sure to back it up if the data are critical

-- start from an empty database
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament;

-- This table is necessary to support more than one tournament per database
-- This table records the tournaments
CREATE TABLE IF NOT EXISTS tournament (
    id serial PRIMARY KEY,
    name text);

-- This table records all the players
CREATE TABLE IF NOT EXISTS player (
    id serial PRIMARY KEY,
    name text);

-- This table is necessary to support more than one tournament per database
-- This table records which player has entered which tournament
CREATE TABLE IF NOT EXISTS tournament_player (
    tournament_id integer REFERENCES tournament(id) ON DELETE CASCADE,
    player_id integer REFERENCES player(id) ON DELETE CASCADE,
    PRIMARY KEY (tournament_id, player_id));

-- tournament_id column is needed to support
-- more than one tournament per database
-- is_draw column is used to denote whether the match result is a draw,
-- to allow a draw (a tied game) as result.
CREATE TABLE IF NOT EXISTS tournament_match_result (
    id serial PRIMARY KEY,
    tournament_id integer REFERENCES tournament(id) ON DELETE CASCADE,
    winner_id integer REFERENCES player(id) ON DELETE CASCADE,
    loser_id integer REFERENCES player(id) ON DELETE CASCADE,
    is_draw boolean DEFAULT false);

-- This view is to get the current tournament conveniently
-- when supporting more than one tournament per database
-- The current tournament is the one with max id
CREATE OR REPLACE VIEW current_tournament AS
    SELECT * FROM tournament WHERE id IN (SELECT max(id) FROM tournament);

-- This view is to get the players in the current tournament conveniently
-- when supporting more than one tournament per database
CREATE OR REPLACE VIEW current_player AS
    SELECT * FROM player WHERE id IN
        (SELECT player_id FROM tournament_player WHERE tournament_id IN
            (SELECT max(id) FROM tournament));

