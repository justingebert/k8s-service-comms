const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8080';

// static files
app.use(express.static(path.join(__dirname, 'public')));

app.get('/healthz', (req, res) => {
  res.send('ok');
});

// forwards to the backend service inside the cluster
app.get('/api/hello', async (req, res) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/hello`);
    const text = await response.text();
    res.status(response.status);
    res.type('application/json').send(text);
  } catch (err) {
    res.status(502).json({ error: 'Failed to reach backend', details: String(err) });
  }
});

// proxy to see how many calls have been logged
app.get('/api/hello/stats', async (req, res) => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/hello/stats`);
    const text = await response.text();
    res.status(response.status);
    res.type('application/json').send(text);
  } catch (err) {
    res.status(502).json({ error: 'Failed to reach backend', details: String(err) });
  }
});

// proxy to list recent call entries
app.get('/api/hello/history', async (req, res) => {
  try {
    const limit = req.query.limit;
    const url = new URL(`${BACKEND_URL}/api/hello/history`);
    if (limit) url.searchParams.set('limit', String(limit));
    const response = await fetch(url);
    const text = await response.text();
    res.status(response.status);
    res.type('application/json').send(text);
  } catch (err) {
    res.status(502).json({ error: 'Failed to reach backend', details: String(err) });
  }
});

app.listen(PORT, () => {
  console.log(`Frontend listening on port ${PORT}. Using BACKEND_URL=${BACKEND_URL}`);
});
