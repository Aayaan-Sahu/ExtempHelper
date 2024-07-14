const express = require('express');
const Mercury = require('@postlight/mercury-parser');
const app = express();
const port = 3000;

app.get('/parse', async (req, res) => {
  const { url } = req.query;
  try {
    const result = await Mercury.parse(url);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
