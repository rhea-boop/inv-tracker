const express = require('express');
const { spawn } = require('child_process');
const http = require('http');
const { Server } = require("socket.io");
const cors = require('cors');
const dbModule = require('./database'); 

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// --- API ENDPOINTS ---

// Fetch all known assets
app.get('/api/assets', async (req, res) => {
    try {
        const [rows] = await dbModule.getPool().query("SELECT * FROM assets ORDER BY last_seen DESC");
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" }); 
    }
});

// Fetch the 50 most recent scan events
app.get('/api/events', async (req, res) => {
    try {
        const query = `
            SELECT scan_logs.id, scan_logs.epc, scan_logs.room, scan_logs.timestamp, assets.name 
            FROM scan_logs 
            LEFT JOIN assets ON scan_logs.epc = assets.epc 
            ORDER BY scan_logs.timestamp DESC LIMIT 50
        `;
        const [rows] = await dbModule.getPool().query(query);
        res.json(rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Database error" });
    }
});

// Search for an asset by exact EPC or partial Name
// Search for an asset by exact EPC or partial Name
// Search for an asset by exact EPC or partial Name
app.get('/api/search', async (req, res) => {
    const q = req.query.q?.trim();
    
    // TRACER ROUND 1: Did the backend even hear the request?
    console.log(`\n🔍 [BACKEND] Search requested for: "${q}"`); 

    if (!q) {
        console.log("⚠️ [BACKEND] Query was empty. Aborting.");
        return res.json([]);
    }

    try {
        const query = `
            SELECT * FROM assets 
            WHERE epc = ? OR name LIKE ? 
            ORDER BY last_seen DESC
        `;
        const [rows] = await dbModule.getPool().query(query, [q, `%${q}%`]);
        
        // TRACER ROUND 2: Did the database find anything?
        console.log(`✅ [BACKEND] Found ${rows.length} results in the database.`);
        res.json(rows);
        
    } catch (err) {
        console.error("❌ [BACKEND] Database crash:", err);
        res.status(500).json({ error: "Database error" });
    }
});
// --- END API ENDPOINTS ---

async function startApp() {
    try {
        await dbModule.initializeDatabase();
        
        server.listen(3000, () => {
            console.log('🚀 Backend running on http://localhost:3000');
            console.log('📡 Starting hardware tracker...');
            
// Passing it as a single string clears the Node deprecation warning
// We also force Python to use UTF-8 so it stops crashing on emojis!
            const tracker = spawn('py -u tracker.py', { 
                shell: true, 
                env: { ...process.env, PYTHONIOENCODING: 'utf-8' } 
            });

            tracker.stdout.on('data', (data) => {
                const output = data.toString().trim();
                console.log(`🐍 [TRACKER]: ${output}`);
                
                if (output.includes("Database Updated Successfully")) {
                    io.emit('new_scan_event');
                }
            });
            
            tracker.stderr.on('data', (data) => {
                console.error(`🚨 [TRACKER ERROR]: ${data.toString().trim()}`);
            });

            tracker.on('close', (code) => {
                console.log(`⚠️ [TRACKER] Process exited with code ${code}`);
            });
        });
        
    } catch (error) {
        console.error("❌ CRITICAL FAILURE: Could not start app.", error);
        process.exit(1);
    }
}

startApp();