-- Execute in MySQL Workbench AFTER backing up edumind_ai_db.
-- Current SQLAlchemy model uses db.String(30), but an older MySQL enum can
-- reject new recommendation categories such as 'Consistency'.
USE edumind_ai_db;
SHOW COLUMNS FROM feedback LIKE 'feedback_type';

-- Only proceed when you have reviewed the column and backed up the database.
ALTER TABLE feedback
MODIFY COLUMN feedback_type VARCHAR(30) NOT NULL;

SHOW COLUMNS FROM feedback LIKE 'feedback_type';
SELECT feedback_type, COUNT(*) AS count FROM feedback GROUP BY feedback_type;
