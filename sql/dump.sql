CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    handle VARCHAR(100) NOT NULL,
    code VARCHAR(200) NOT NULL,
    created_at TIMESTAMP,
    access_role INTEGER REFERENCES roles (id)
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
    created_at TIMESTAMP,
    direction INTEGER
);

CREATE TABLE IF NOT EXISTS chat (
    id SERIAL PRIMARY KEY,
    chatter INTEGER REFERENCES people (id),
    about INTEGER REFERENCES packs (id),
    created_at TIMESTAMP,
    content VARCHAR(1048)
);

CREATE TABLE IF NOT EXISTS traffic (
    ip VARCHAR(100) NOT NULL,
    visited_at TIMESTAMP
);

-- TEST DATA
INSERT INTO roles (title) VALUES ('admin');
INSERT INTO roles (title) VALUES ('pleb');

INSERT INTO people (handle, code, access_role) VALUES ('testguy', 'cool', 1);
INSERT INTO people (handle, code, access_role) VALUES ('testguy2', 'dude', 2);

INSERT INTO packs (name) VALUES ('testpack');
INSERT INTO packs (name) VALUES ('testpack2');

INSERT INTO hangs (name, created_by, pack) VALUES ('testhang', 1, 1);
INSERT INTO hangs (name, created_by, pack) VALUES ('testhang2', 1, 1);

INSERT INTO votes (voter, hang, direction) VALUES (1, 1, 1);
INSERT INTO votes (voter, hang, direction) VALUES (2, 1, 1);
INSERT INTO votes (voter, hang, direction) VALUES (1, 2, 0);
-- INSERT INTO votes (voter, hang, direction) VALUES (3, 2, 0);

INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'a', '2016-06-22 19:10:25');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'b', '2016-06-22 19:10:26');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'c', '2016-06-22 19:10:27');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'd', '2016-06-22 19:10:28');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'e', '2016-06-22 19:10:29');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'f', '2016-06-22 19:10:30');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'g', '2016-06-22 19:10:31');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'h', '2016-06-22 19:10:32');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'i', '2016-06-22 19:10:33');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'j', '2016-06-22 19:10:34');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'k', '2016-06-22 19:10:35');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'l', '2016-06-22 19:10:36');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'm', '2016-06-22 19:10:37');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'n', '2016-06-22 19:10:38');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'o', '2016-06-22 19:10:39');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'p', '2016-06-22 19:10:40');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'q', '2016-06-22 19:10:41');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 'r', '2016-06-22 19:10:42');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 's', '2016-06-22 19:10:43');
INSERT INTO chat (chatter, about, content, created_at) VALUES (1, 1, 't', '2016-06-22 19:10:44');

drop table chat;
drop table votes;
drop table hangs;
drop table packs;
drop table people;
drop table traffic;
drop table roles;