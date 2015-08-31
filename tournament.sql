-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.


create database tournament;
\c tournament;

create table if not exists tournament (
    id serial primary key,
    name text);

create table if not exists player (
    id serial primary key,
    name text);

create table if not exists tournament_player (
    tournament_id integer references tournament(id) on delete cascade,
    player_id integer references player(id) on delete cascade,
    primary key (tournament_id, player_id));

create table if not exists tournament_match_result (
    id serial primary key,
    tournament_id integer references tournament(id) on delete cascade,
    winner_id integer references player(id) on delete cascade,
    loser_id integer references player(id) on delete cascade,
    is_draw boolean default false);

create or replace view current_tournament as select * from tournament where id in (select max(id) from tournament);

create or replace view current_player as select * from player where id in (select player_id from tournament_player where tournament_id in (select max(id) from tournament)); 

 
