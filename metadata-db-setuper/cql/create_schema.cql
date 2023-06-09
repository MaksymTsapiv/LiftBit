CREATE KEYSPACE IF NOT EXISTS metadata WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};

CREATE TABLE IF NOT EXISTS metadata.files (
    filename text,
    owner text,
    users list<text>,
    PRIMARY KEY ((filename), owner)
);
