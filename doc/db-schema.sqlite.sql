BEGIN TRANSACTION;

CREATE TABLE wtf (
    id INTEGER PRIMARY KEY, 
    acronym_i TEXT, 
    acronym TEXT, 
    text TEXT, 
    nick TEXT, 
    chan TEXT, 
    date TEXT, 
    lastused NUMERIC DEFAULT '1'
);

CREATE TABLE score (
    name TEXT PRIMARY KEY,
    value NUMERIC,
    nick TEXT,
    chan TEXT,
    date TEXT
);

CREATE TABLE log (
    id INTEGER PRIMARY KEY,
    nick TEXT,
    chan TEXT,
    text TEXT,
    num NUMERIC,
    type TEXT,
    date TEXT
);

CREATE TABLE hangman (
    chan TEXT,
    state NUMERIC,
    final TEXT,
    phrase TEXT,
    guess TEXT,
    wrong TEXT,
    nick TEXT
);

CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote TEXT,
    nick TEXT,
    date TEXT
);

COMMIT;
