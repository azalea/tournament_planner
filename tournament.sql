-- Table definitions for the tournament project.
--
-- Warning: executing this file will drop the existing tournament database
-- Make sure to back it up if the data are critical

-- start from an empty database
drop database if exists tournament;
create database tournament;
\c tournament;

-- This table is necessary to support more than one tournament per database
-- This table records the tournaments
create table if not exists tournament (
    id serial primary key,
    name text);

-- This table records all the players
create table if not exists player (
    id serial primary key,
    name text);

-- This table is necessary to support more than one tournament per database
-- This table records which player has entered which tournament
create table if not exists tournament_player (
    tournament_id integer references tournament(id) on delete cascade,
    player_id integer references player(id) on delete cascade,
    primary key (tournament_id, player_id));

-- tournament_id column is needed to support
-- more than one tournament per database
-- is_draw column is used to denote whether the match result is a draw,
-- to allow a draw (a tied game) as result.
create table if not exists tournament_match_result (
    id serial primary key,
    tournament_id integer references tournament(id) on delete cascade,
    winner_id integer references player(id) on delete cascade,
    loser_id integer references player(id) on delete cascade,
    is_draw boolean default false);

-- This view is to get the current tournament conveniently
-- when supporting more than one tournament per database
-- The current tournament is the one with max id
create or replace view current_tournament as
    select * from tournament where id in (select max(id) from tournament);

-- This view is to get the players in the current tournament conveniently
-- when supporting more than one tournament per database
create or replace view current_player as
    select * from player where id in
        (select player_id from tournament_player where tournament_id in
            (select max(id) from tournament));

