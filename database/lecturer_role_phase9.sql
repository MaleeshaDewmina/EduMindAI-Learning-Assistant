-- Phase 9: run against a BACKED-UP edumind_ai_db with MySQL Workbench.
-- Existing users remain students. Safe to re-run after successful migration.
USE edumind_ai_db;
SET @has_role = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role');
SET @sql = IF(@has_role = 0, CONCAT('ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT ', CHAR(39), 'student', CHAR(39)), 'SELECT 1');
PREPARE role_migration FROM @sql;
EXECUTE role_migration;
DEALLOCATE PREPARE role_migration;

CREATE TABLE IF NOT EXISTS lecturer_access_grants (
    grant_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    lecturer_id INT NOT NULL,
    granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_lecturer_grant (student_id, lecturer_id),
    KEY ix_grants_student_id (student_id),
    KEY ix_grants_lecturer_id (lecturer_id),
    CONSTRAINT fk_grants_student FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_grants_lecturer FOREIGN KEY (lecturer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT ck_lecturer_grant_not_self CHECK (student_id <> lecturer_id)
) ENGINE=InnoDB;

SHOW COLUMNS FROM users LIKE 'role';
SHOW COLUMNS FROM lecturer_access_grants;
