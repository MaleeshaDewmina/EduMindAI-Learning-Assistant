-- Phase 10: Select the EXISTING Aiven/MySQL database first and back it up.
-- Do not run DROP, DELETE, TRUNCATE, or rebuild any research table.
-- This script adds one audit/token table and a non-destructive consent flag.
SELECT DATABASE() AS selected_database;
CREATE TABLE IF NOT EXISTS email_action_events (
  event_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  purpose VARCHAR(32) NOT NULL,
  address_digest VARCHAR(64) NOT NULL,
  ip_digest VARCHAR(64) NOT NULL,
  token_digest VARCHAR(64) NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NULL,
  consumed_at DATETIME NULL,
  KEY ix_email_action_user_id (user_id),
  KEY ix_email_action_purpose (purpose),
  KEY ix_email_action_address_digest (address_digest),
  KEY ix_email_action_ip_digest (ip_digest),
  KEY ix_email_action_created_at (created_at),
  CONSTRAINT fk_email_action_user FOREIGN KEY (user_id)
    REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;

SET @has_email_allowed = (
 SELECT COUNT(*) FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = DATABASE()
 AND TABLE_NAME = 'lecturer_access_grants'
 AND COLUMN_NAME = 'email_allowed'
);
SET @sql_email_allowed = IF(@has_email_allowed = 0,
 'ALTER TABLE lecturer_access_grants ADD COLUMN email_allowed BOOLEAN NOT NULL DEFAULT FALSE',
 'SELECT 1');
PREPARE phase10_statement FROM @sql_email_allowed;
EXECUTE phase10_statement;
DEALLOCATE PREPARE phase10_statement;

SHOW TABLES LIKE 'email_action_events';
SHOW COLUMNS FROM lecturer_access_grants LIKE 'email_allowed';
SELECT COUNT(*) AS preserved_evaluation_count FROM evaluation_responses;
