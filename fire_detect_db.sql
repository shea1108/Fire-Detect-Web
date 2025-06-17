
DROP TABLE IF EXISTS NOTIFICATION_PLATFORMs;
DROP TABLE IF EXISTS USER_PLATFORMs;
DROP TABLE IF EXISTS NOTIFICATIONs;
DROP TABLE IF EXISTS LOGs;
DROP TABLE IF EXISTS MODELs;
DROP TABLE IF EXISTS PLATFORMs;
DROP TABLE IF EXISTS DEVICEs;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS log_bboxes;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS roles;



-- ALTER TABLE models DROP COLUMN IF EXISTS model_config;


-- ALTER TABLE models
-- ADD COLUMN model_short_title VARCHAR(100),
-- ADD COLUMN model_tooltip TEXT;



-- TABLE: users  
CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    user_name       VARCHAR(100) NOT NULL,
    user_password   VARCHAR(255) NOT NULL,
    user_email      VARCHAR(100) UNIQUE NOT NULL,
    user_phone_num  VARCHAR(10) UNIQUE,
    user_reset_token VARCHAR(128),
    user_reset_expire_at TIMESTAMP,
    user_status     BOOLEAN      NOT NULL,
    user_avatar TEXT,
    user_create_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: devices
CREATE TABLE devices (
    dev_id         SERIAL PRIMARY KEY,
    user_id        INT NOT NULL,
    dev_name       VARCHAR(100) NOT NULL,
    dev_location   VARCHAR(255),
    dev_ip_address VARCHAR(50),
    dev_status     BOOLEAN      NOT NULL,
	dev_hardware_id VARCHAR(255) NOT NULL,
    dev_create_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: models
CREATE TABLE models (
    model_id        SERIAL PRIMARY KEY,
    model_name      VARCHAR(100) NOT NULL,
    model_path      TEXT         NOT NULL,
    model_short_title VARCHAR(100),
    model_tooltip TEXT,
    model_status    BOOLEAN      NOT NULL,
    model_create_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: logs
CREATE TABLE logs (
    log_id              SERIAL PRIMARY KEY,
    dev_id              INT,
    model_id            INT NOT NULL,
    log_image_path      VARCHAR(255),
    log_create_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (dev_id)   REFERENCES devices(dev_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(model_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: log_bboxes
CREATE TABLE log_bboxes (
    bbox_id SERIAL PRIMARY KEY,
    log_id INT, 
	confidence FLOAT CHECK (confidence BETWEEN 0 AND 1),
    x_center FLOAT,
    y_center FLOAT,
    width FLOAT,
    height FLOAT,
	FOREIGN KEY (log_id) REFERENCES logs(log_id)
		ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: platforms
CREATE TABLE platforms (
    plat_id        SERIAL PRIMARY KEY,
    plat_name      VARCHAR(100) NOT NULL,
    plat_endpoint  TEXT,
    plat_create_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- TABLE: notifications
CREATE TABLE notifications (
    noti_id        SERIAL PRIMARY KEY,
    log_id         INT NOT NULL,
    noti_title     VARCHAR(100) NOT NULL,
    noti_message   TEXT         NOT NULL,
    noti_is_receive BOOLEAN     NOT NULL,
    noti_create_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    FOREIGN KEY (log_id) REFERENCES logs(log_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: notification_platforms
CREATE TABLE notification_platforms (
    noti_id              INT NOT NULL,
    plat_id              INT NOT NULL,
    np_status            BOOLEAN,
    np_sent_at           TIMESTAMP,
    np_error_message     TEXT,
    np_retry_count       INTEGER CHECK (np_retry_count >= 0),
    np_payload           TEXT,
    np_recipient_address VARCHAR(255),
    np_response_data     TEXT,
    PRIMARY KEY (noti_id, plat_id),
    FOREIGN KEY (noti_id) REFERENCES notifications(noti_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (plat_id) REFERENCES platforms(plat_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- TABLE: user_platforms
CREATE TABLE user_platforms (
    user_id INT NOT NULL,
    plat_id INT NOT NULL,
    PRIMARY KEY (user_id, plat_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (plat_id) REFERENCES platforms(plat_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
-- Bảng roles (vai trò)
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL -- ví dụ: admin, guest, police
);

-- Bảng permissions (quyền cụ thể)
CREATE TABLE permissions (
    perm_id SERIAL PRIMARY KEY,
    perm_name VARCHAR(100) UNIQUE NOT NULL,         -- ví dụ: use_v8n, use_v8m
    perm_description TEXT
);

-- Nhiều user có nhiều role
CREATE TABLE user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

-- Nhiều role có nhiều quyền
CREATE TABLE role_permissions (
    role_id INT NOT NULL,
    perm_id INT NOT NULL,
    PRIMARY KEY (role_id, perm_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (perm_id) REFERENCES permissions(perm_id) ON DELETE CASCADE
);
-- Thêm roles
INSERT INTO roles (role_name) VALUES ('admin'), ('guest'), ('user'), ('police');


INSERT INTO models (model_name, model_path, model_config, model_status) VALUES
('Fire_Detect 1.3', 'Yolo/best.pt', '{}', TRUE),
('Fire_Detect 1.2', 'Yolo/best1.pt', '{}', TRUE),
('Fire_Detect 1.1', 'Yolo/best2.pt', '{}', TRUE);

--admin
INSERT INTO user_roles(user_id, role_id)
VALUES (1, 1)


--USER
INSERT INTO user_roles(user_id, role_id)
VALUES (2, 3)
