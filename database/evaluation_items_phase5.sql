-- Phase 5: run once AFTER backing up edumind_ai_db and BEFORE applying the Phase 5 Python files.
-- Preserves every row in evaluation_responses. Adds a new table for item-level v2 ratings.
-- Use MySQL Workbench and confirm the database name matches your actual local configuration.
USE edumind_ai_db;

CREATE TABLE IF NOT EXISTS evaluation_item_responses (
    item_response_id INT NOT NULL AUTO_INCREMENT,
    response_id INT NOT NULL,
    item_code VARCHAR(12) NOT NULL,
    instrument_version VARCHAR(24) NOT NULL,
    rating INT NOT NULL,
    PRIMARY KEY (item_response_id),
    UNIQUE KEY uq_eval_response_item (response_id, item_code),
    INDEX ix_evaluation_item_responses_response_id (response_id),
    CONSTRAINT fk_eval_items_response
        FOREIGN KEY (response_id) REFERENCES evaluation_responses (response_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SHOW COLUMNS FROM evaluation_item_responses;
