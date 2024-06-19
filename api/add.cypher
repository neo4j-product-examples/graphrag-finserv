//get rid of NER doc nodes
MATCH (n:Document)  WHERE n.createdAt IS NULL SET n:Doc REMOVE n:Document;
//Set common node label for all NER nodes
MATCH (n) WHERE NOT n:Document AND NOT n:Chunk SET n:__Entity__;
//create full text index
CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id];