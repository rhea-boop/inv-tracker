const mysql = require('mysql2/promise');
require('dotenv').config();

const dbConfig = {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD 
};

const DB_NAME = process.env.DB_NAME || 'inventory_tracker';

let pool;

async function initializeDatabase() {
    console.log("Checking database schema...");
    const connection = await mysql.createConnection(dbConfig);
    
    await connection.query(`CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;`);
    await connection.query(`USE \`${DB_NAME}\`;`);

    console.log("Building new schema...");
    // 2. Create the Assets Table
    await connection.query(`
        CREATE TABLE IF NOT EXISTS assets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            epc VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255),
            room VARCHAR(255),
            status ENUM('PRESENT', 'MISSING') DEFAULT 'PRESENT',
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `);

    // 3. Create the Scan Logs Table
    await connection.query(`
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            epc VARCHAR(50) NOT NULL,
            room VARCHAR(255),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    `);

    // 4. Create the Tripwire Trigger
    // We safely drop the trigger first so MariaDB doesn't crash on restarts
    await connection.query(`DROP TRIGGER IF EXISTS update_asset_last_seen;`);
    
    await connection.query(`
        CREATE TRIGGER update_asset_last_seen
        AFTER INSERT ON scan_logs
        FOR EACH ROW
        BEGIN
            UPDATE assets 
            SET last_seen = NEW.timestamp,
                room = COALESCE(NEW.room, room)
            WHERE epc = NEW.epc;
        END;
    `);
    
    console.log("✅ Inventory schema and triggers are armed and ready.");
    await connection.end();

    pool = mysql.createPool({
        ...dbConfig,
        database: DB_NAME,
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
    });

    return pool;
}

module.exports = {
    initializeDatabase,
    getPool: () => pool 
};