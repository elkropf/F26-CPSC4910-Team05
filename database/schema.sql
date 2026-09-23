USE Team05_DB;

/* stores login and account info for all users
includes:
    - username
    - hashed password
    - user type (driver, sponsor, admin)
    - account status (active/inactive)
    - timestamps for account creation and last update for audit logging purposes
*/
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_pass VARCHAR(255) NOT NULL,
    user_type ENUM('driver', 'sponsor', 'admin') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE sponsors (
    sponsor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE drivers (
    driver_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE admins (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    sponsor_id INT NOT NULL,
    application_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    application_message TEXT,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_date TIMESTAMP NULL,
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id) ON DELETE CASCADE
    unique (driver_id, sponsor_id)
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    sponsor_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_description TEXT,
    points_value INT NOT NULL,
    instock_quantity INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id) ON DELETE CASCADE
    CHECK (points_value >= 0),
    CHECK (instock_quantity >= 0)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    sponsor_id INT NOT NULL,
    total_points INT NOT NULL,
    order_status ENUM(
        'pending',
        'approved',
        'processing',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (sponsor_id)
        REFERENCES sponsors(sponsor_id)
        ON DELETE RESTRICT,

    CHECK (total_points >= 0)
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    points_cost INT NOT NULL,

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE RESTRICT,

    CHECK (quantity > 0),
    CHECK (points_cost >= 0),

    UNIQUE (order_id, product_id)
);

CREATE TABLE points_logs (
    points_log_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    sponsor_id INT NOT NULL,
    order_id INT NULL,
    created_by_user_id INT NULL,
    transaction_type ENUM(
        'earned',
        'spent',
        'refunded',
        'adjusted'
    ) NOT NULL,
    points_change INT NOT NULL,
    transaction_description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (sponsor_id)
        REFERENCES sponsors(sponsor_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE SET NULL,

    FOREIGN KEY (created_by_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL,

    CHECK (points_change != 0)

);

CREATE TABLE driver_logs (
    driver_log_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    sponsor_id INT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_description VARCHAR(255),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (sponsor_id)
        REFERENCES sponsors(sponsor_id)
        ON DELETE SET NULL
);

CREATE TABLE sponsor_logs (
    sponsor_log_id INT PRIMARY KEY AUTO_INCREMENT,
    sponsor_id INT NOT NULL,
    driver_id INT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_description VARCHAR(255),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sponsor_id)
        REFERENCES sponsors(sponsor_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
        ON DELETE SET NULL
);

CREATE TABLE admin_logs (
    admin_log_id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    affected_user_id INT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_description VARCHAR(255),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (admin_id)
        REFERENCES admins(admin_id)
        ON DELETE RESTRICT,

    FOREIGN KEY (affected_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE audit_logs (
     audit_log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    action_type VARCHAR(50) NOT NULL,
    affected_table VARCHAR(100) NOT NULL,
    affected_record_id INT NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    recipient_user_id INT NOT NULL,
    sender_user_id INT NULL,
    notification_type VARCHAR(50) NOT NULL,
    notification_title VARCHAR(150) NOT NULL,
    notification_message TEXT NOT NULL,
    related_table VARCHAR(100) NULL,
    related_record_id INT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,

    FOREIGN KEY (recipient_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (sender_user_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);