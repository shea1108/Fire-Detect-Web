DROP TABLE IF EXISTS NOTIFICATION_PLATFORM;
DROP TABLE IF EXISTS USER_PLATFORM;
DROP TABLE IF EXISTS NOTIFICATION;
DROP TABLE IF EXISTS LOG;
DROP TABLE IF EXISTS MODEL;
DROP TABLE IF EXISTS PLATFORM;
DROP TABLE IF EXISTS DEVICE;
DROP TABLE IF EXISTS "user";
DROP TABLE IF EXISTS "users";




-- TABLE: users  
CREATE TABLE users (
    user_id         VARCHAR(50)  PRIMARY KEY,
    user_name       VARCHAR(100) NOT NULL,
    user_password   VARCHAR(255) NOT NULL,
    user_role       VARCHAR(20)  NOT NULL,
    user_email      VARCHAR(100) UNIQUE NOT NULL,
    user_phone_num  VARCHAR(10),
    user_status     BOOLEAN      NOT NULL,
    user_create_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: devices
CREATE TABLE devices (
    dev_id         VARCHAR(50)  PRIMARY KEY,
    user_id        VARCHAR(50),
    dev_name       VARCHAR(100) NOT NULL,
    dev_location   VARCHAR(255),
    dev_ip_address VARCHAR(50),
    dev_status     BOOLEAN      NOT NULL,
    dev_create_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: models
CREATE TABLE models (
    model_id        VARCHAR(50)  PRIMARY KEY,
    model_name      VARCHAR(100) NOT NULL,
    model_path      TEXT         NOT NULL,
    model_config    TEXT,
    model_status    BOOLEAN      NOT NULL,
    model_create_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: logs
CREATE TABLE logs (
    log_id              VARCHAR(50)  PRIMARY KEY,
    dev_id              VARCHAR(50),
    model_id            VARCHAR(50),
    log_fire_confidence FLOAT        CHECK (log_fire_confidence BETWEEN 0 AND 1),
    log_image_path      VARCHAR(255),
    log_create_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (dev_id)   REFERENCES devices(dev_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(model_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: platforms
CREATE TABLE platforms (
    plat_id        VARCHAR(50)  PRIMARY KEY,
    plat_name      VARCHAR(100) NOT NULL,
    plat_endpoint  TEXT,
    plat_create_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: notifications
CREATE TABLE notifications (
    noti_id        VARCHAR(50)  PRIMARY KEY,
    log_id         VARCHAR(50),
    noti_title     VARCHAR(100) NOT NULL,
    noti_message   TEXT         NOT NULL,
    noti_is_receive BOOLEAN     NOT NULL,
    noti_create_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (log_id) REFERENCES logs(log_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: notification_platforms   (quan hệ N-N giữa notifications và platforms)
CREATE TABLE notification_platforms (
    noti_id            VARCHAR(50),
    plat_id            VARCHAR(50),
    np_status          BOOLEAN,
    np_sent_at         TIMESTAMP,
    np_error_message   TEXT,
    np_retry_count     INTEGER      CHECK (np_retry_count >= 0),
    np_payload         TEXT,
    np_recipient_address VARCHAR(255),
    np_response_data   TEXT,
    PRIMARY KEY (noti_id, plat_id),
    FOREIGN KEY (noti_id) REFERENCES notifications(noti_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (plat_id) REFERENCES platforms(plat_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: user_platforms   (quan hệ N-N giữa users và platforms)
CREATE TABLE user_platforms (
    user_id VARCHAR(50),
    plat_id VARCHAR(50),
    PRIMARY KEY (user_id, plat_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (plat_id) REFERENCES platforms(plat_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
