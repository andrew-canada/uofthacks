const express = require('express');
const cors = require('cors');
const path = require('path');

const healthRoutes = require('./routes/health');
const authRoutes = require('./routes/auth');
const productsRoutes = require('./routes/products');
const suggestionsRoutes = require('./routes/suggestions');
const themesRoutes = require('./routes/themes');

const app = express();

app.use(cors());
app.use(express.json());

app.use(express.static(path.join(__dirname, '..', 'public')));

app.use('/', authRoutes);
app.use('/health', healthRoutes);
app.use('/api', productsRoutes);
app.use('/api/suggestions', suggestionsRoutes);
app.use('/api/themes', themesRoutes);

module.exports = app;
