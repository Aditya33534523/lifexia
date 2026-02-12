const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5001;

app.use(cors());
app.use(express.json());

// Path to the locations data
const LOCATIONS_PATH = path.join(__dirname, '..', 'frontend', 'static', 'js', 'locations.json');

const DIST_PATH = path.join(__dirname, '..', 'map_frontend_react', 'dist');

// Serve static files from React build
app.use(express.static(DIST_PATH));

app.get('/api/locations', (req, res) => {
    try {
        if (!fs.existsSync(LOCATIONS_PATH)) {
            return res.status(404).json({ error: 'Locations data not found' });
        }
        const data = fs.readFileSync(LOCATIONS_PATH, 'utf8');
        res.json(JSON.parse(data));
    } catch (error) {
        console.error('Error reading locations:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'map-service' });
});

app.listen(PORT, () => {
    console.log(`Map Backend Service running on http://localhost:${PORT}`);
});
