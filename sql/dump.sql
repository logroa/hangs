CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    handle VARCHAR(100) NOT NULL,
    ip VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS packs (
    id SERIAL PRIMARY KEY,
    name VARCHAR (100) NOT NULL,
    created_at TIMESTAMP,
    description VARCHAR (200)
);

CREATE TABLE IF NOT EXISTS hangs (
    id SERIAL PRIMARY KEY,
    name VARCHAR (200) NOT NULL,
    created_by INTEGER REFERENCES people (id),
    created_at TIMESTAMP,
    pack INTEGER REFERENCES packs (id)
);

CREATE TABLE IF NOT EXISTS votes (
    voter INTEGER REFERENCES people (id),
    hang INTEGER REFERENCES hangs (id),
    PRIMARY KEY (voter, hang),
    direction INTEGER
);

CREATE TABLE IF NOT EXISTS chat (
    id SERIAL PRIMARY KEY,
    chatter INTEGER REFERENCES people (id),
    about INTEGER REFERENCES packs (id),
    created_at TIMESTAMP,
    content VARCHAR(1048)
);

-- TEST DATA
INSERT INTO people (handle, ip) VALUES ('testguy', '1.1.1.1');
INSERT INTO people (handle, ip) VALUES ('testguy2', '1.1.1.2');

INSERT INTO packs (name) VALUES ('testpack');
INSERT INTO packs (name) VALUES ('testpack2');

INSERT INTO hangs (name, created_by, pack) VALUES ('testhang', 1, 1);
INSERT INTO hangs (name, created_by, pack) VALUES ('testhang2', 1, 1);

INSERT INTO votes (voter, hang, direction) VALUES (1, 1, 1);
INSERT INTO votes (voter, hang, direction) VALUES (2, 1, 1);
INSERT INTO votes (voter, hang, direction) VALUES (1, 2, 0);

drop table chat;
drop table votes;
drop table hangs;
drop table packs;
drop table people;