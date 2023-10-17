CREATE TABLE User (
    username VARCHAR(255),
    password VARCHAR(255),
    PRIMARY KEY (username)
);

CREATE TABLE Roles (
    r_username VARCHAR(255),
    role VARCHAR(255),
    PRIMARY KEY (r_username, role),
    FOREIGN KEY (r_username) REFERENCES User(username)
);