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
)

CREATE TABLE products (
)

CREATE TABLE orders (
)

CREATE TABLE points (
)

CREATE TABLE driver_logs (
)

CREATE TABLE sponsor_logs (
)

CREATE TABLE admin_logs (
)

CREATE TABLE audit_logs (
)

CREATE TABLE notifications (
)