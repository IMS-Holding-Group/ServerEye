CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'soc_analyst', 'it_manager')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    os_type TEXT NOT NULL CHECK(os_type IN ('Linux', 'Windows Server')),
    host_address TEXT NOT NULL,
    agent_token TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    is_in_baseline INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    cpu_percent REAL NOT NULL,
    ram_percent REAL NOT NULL,
    disk_percent REAL NOT NULL,
    response_time_ms REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_server_recorded
    ON metrics(server_id, recorded_at);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('منخفضة', 'متوسطة', 'حرجة')),
    message TEXT NOT NULL,
    is_resolved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_by INTEGER,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
