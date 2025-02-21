CREATE TABLE IF NOT EXISTS processed_images (
    id UUID PRIMARY KEY,
    original_data BYTEA,
    processed_data BYTEA,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(20)
);
