CREATE TABLE task_item (
    id UUID PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX idx_task_item_status ON task_item(status);
CREATE INDEX idx_task_item_priority ON task_item(priority);
CREATE INDEX idx_task_item_created_at ON task_item(created_at DESC);
