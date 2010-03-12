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
COMMIT;
