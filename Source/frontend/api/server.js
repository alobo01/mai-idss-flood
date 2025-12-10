const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const { parse } = require('csv-parse/sync');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));
app.use((req, res, next) => {
  res.header('access-control-allow-origin', '*');
  res.header('access-control-allow-methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('access-control-allow-headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(204);
  }
  next();
});
app.use(express.json());

// Data storage paths - allow override for local dev
const containerDataPath = path.join('/srv', 'public', 'mock');
const localDataPath = path.join(__dirname, '..', 'public', 'mock');
const dataPath = process.env.MOCK_DATA_PATH
  ? path.resolve(process.env.MOCK_DATA_PATH)
  : (fs.existsSync(containerDataPath) ? containerDataPath : localDataPath);

console.log(`[API] Using data directory: ${dataPath}`);

const repoRoot = path.join(__dirname, '..', '..', '..');
const pipelineResultsPath = process.env.PIPELINE_RESULTS_PATH
  ? path.resolve(process.env.PIPELINE_RESULTS_PATH)
  : path.join(repoRoot, 'Results', 'v2');
const pipelineConfigPath = process.env.PIPELINE_CONFIG_PATH
  ? path.resolve(process.env.PIPELINE_CONFIG_PATH)
  : path.join(repoRoot, 'pipeline_v2', 'config.yaml');
const pipelineStatusPath = process.env.PIPELINE_STATUS_PATH
  ? path.resolve(process.env.PIPELINE_STATUS_PATH)
  : path.join(pipelineResultsPath, 'pipeline_status.json');

console.log(`[API] Using pipeline results directory: ${pipelineResultsPath}`);

// Helper functions
const readJsonFile = (filename) => {
  try {
    const filePath = path.join(dataPath, filename);
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    console.error(`Error reading ${filename} from ${dataPath}:`, error);
    return null;
  }
};

const writeJsonFile = (filename, data) => {
  try {
    const filePath = path.join(dataPath, filename);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    return true;
  } catch (error) {
    console.error(`Error writing ${filename} to ${dataPath}:`, error);
    return false;
  }
};

// Pipeline helper utilities
const fileExists = (filePath) => {
  try {
    fs.accessSync(filePath, fs.constants.F_OK);
    return true;
  } catch (_) {
    return false;
  }
};

const loadPipelineConfig = () => {
  if (!fileExists(pipelineConfigPath)) {
    return null;
  }

  try {
    const raw = fs.readFileSync(pipelineConfigPath, 'utf8');
    return yaml.load(raw);
  } catch (error) {
    console.error(`[API] Failed to parse pipeline config at ${pipelineConfigPath}`, error);
    return null;
  }
};

const getScenarioDir = (scenarioName) => path.join(pipelineResultsPath, scenarioName);

const findLatestFile = (scenarioDir, prefix) => {
  if (!fileExists(scenarioDir)) {
    return null;
  }

  const files = fs
    .readdirSync(scenarioDir)
    .filter((file) => file.startsWith(prefix))
    .sort();

  if (!files.length) {
    return null;
  }

  return path.join(scenarioDir, files[files.length - 1]);
};

const loadScenarioSummary = (scenarioName) => {
  const summaryPath = findLatestFile(getScenarioDir(scenarioName), 'summary_');

  if (!summaryPath) {
    return null;
  }

  try {
    const raw = fs.readFileSync(summaryPath, 'utf8');
    const summary = yaml.load(raw);
    return {
      ...summary,
      file: path.basename(summaryPath),
    };
  } catch (error) {
    console.error(`[API] Failed to read summary for ${scenarioName}`, error);
    return null;
  }
};

const getScenarioConfig = (scenarioName) => {
  const config = loadPipelineConfig();
  if (!config?.scenarios) {
    return null;
  }

  return config.scenarios.find((scenario) => scenario.name === scenarioName) || null;
};

const parseBoolean = (value) => {
  if (typeof value === 'boolean') {
    return value;
  }

  if (value === null || value === undefined) {
    return false;
  }

  return ['true', '1', 'yes', 'y'].includes(String(value).toLowerCase());
};

const toNumber = (value) => {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
};

const normalizeAllocationRow = (row) => ({
  timestamp: row.timestamp,
  scenario: row.scenario,
  zone_id: row.zone_id,
  zone_name: row.zone_name,
  impact_level: row.impact_level,
  allocation_mode: row.allocation_mode,
  river_level_pred: toNumber(row.river_level_pred),
  global_pf: toNumber(row.global_pf),
  pf_zone: toNumber(row.pf_zone),
  vulnerability: toNumber(row.vulnerability),
  is_critical_infra: parseBoolean(row.is_critical_infra),
  units_allocated: toNumber(row.units_allocated) ?? 0,
});

const loadAllocationsCsv = (scenarioName) => {
  const csvPath = findLatestFile(getScenarioDir(scenarioName), 'allocations_');

  if (!csvPath) {
    return null;
  }

  try {
    const raw = fs.readFileSync(csvPath, 'utf8');
    const rows = parse(raw, {
      columns: true,
      skip_empty_lines: true,
    }).map(normalizeAllocationRow);

    return { file: csvPath, rows };
  } catch (error) {
    console.error(`[API] Failed to parse allocations csv for ${scenarioName}`, error);
    return null;
  }
};

const summarizeAllocations = (rows) => {
  const summaryMap = new Map();
  let totalUnits = 0;
  let criticalUnits = 0;

  rows.forEach((row) => {
    const units = row.units_allocated || 0;
    totalUnits += units;
    if (row.is_critical_infra) {
      criticalUnits += units;
    }

    if (!summaryMap.has(row.zone_id)) {
      summaryMap.set(row.zone_id, {
        zone_id: row.zone_id,
        zone_name: row.zone_name,
        is_critical_infra: row.is_critical_infra,
        total_units: 0,
        entries: 0,
        latest_timestamp: row.timestamp,
        latest_units: units,
        last_impact: row.impact_level,
      });
    }

    const zoneSummary = summaryMap.get(row.zone_id);
    zoneSummary.total_units += units;
    zoneSummary.entries += 1;

    if (!zoneSummary.latest_timestamp || row.timestamp >= zoneSummary.latest_timestamp) {
      zoneSummary.latest_timestamp = row.timestamp;
      zoneSummary.latest_units = units;
      zoneSummary.last_impact = row.impact_level;
      zoneSummary.is_critical_infra = zoneSummary.is_critical_infra || row.is_critical_infra;
    }
  });

  return {
    totals: {
      total_units: totalUnits,
      critical_units: criticalUnits,
      zone_count: summaryMap.size,
    },
    zones: Array.from(summaryMap.values()).sort((a, b) => (b.total_units || 0) - (a.total_units || 0)),
  };
};

// Load initial data
let zones = readJsonFile('zones.geojson');
let resources = readJsonFile('resources.json');
let alerts = readJsonFile('alerts.json');
let gauges = readJsonFile('gauges.json');

// In-memory storage for new admin-managed data
let adminData = {
  users: [
    {
      id: 'USR-001',
      username: 'admin.flood',
      email: 'admin@floodsystem.gov',
      firstName: 'Sarah',
      lastName: 'Johnson',
      role: 'Administrator',
      department: 'System Administration',
      phone: '+1-555-0101',
      location: 'Central Office',
      status: 'active',
      lastLogin: new Date().toISOString(),
      zones: ['Z1N', 'Z1S', 'Z2', 'Z3', 'Z4', 'ZC'],
      permissions: ['system_config', 'user_management', 'threshold_management', 'zone_management'],
      createdAt: '2024-01-15T10:00:00Z',
    },
  ],
  riskThresholds: [
    {
      id: 'RT-001',
      name: 'Low Risk',
      band: 'Low',
      minRisk: 0,
      maxRisk: 0.25,
      color: '#22c55e',
      description: 'Normal operating conditions',
      autoAlert: false,
    },
    {
      id: 'RT-002',
      name: 'Moderate Risk',
      band: 'Moderate',
      minRisk: 0.25,
      maxRisk: 0.5,
      color: '#f59e0b',
      description: 'Monitor closely, prepare for potential action',
      autoAlert: false,
    },
    {
      id: 'RT-003',
      name: 'High Risk',
      band: 'High',
      minRisk: 0.5,
      maxRisk: 0.75,
      color: '#ef4444',
      description: 'Take precautionary measures',
      autoAlert: true,
    },
    {
      id: 'RT-004',
      name: 'Severe Risk',
      band: 'Severe',
      minRisk: 0.75,
      maxRisk: 1.0,
      color: '#991b1b',
      description: 'Immediate action required',
      autoAlert: true,
    },
  ],
  gaugeThresholds: [
    {
      id: 'GT-001',
      gaugeId: 'G-RIV-12',
      gaugeName: 'Main River Gauge',
      alertThreshold: 3.5,
      criticalThreshold: 4.2,
      unit: 'meters',
      description: 'Primary river level monitoring',
    },
  ],
  alertRules: [
    {
      id: 'AR-001',
      name: 'Flood Probability Alert',
      triggerType: 'Risk Threshold',
      triggerValue: 'Severe',
      severity: 'Severe',
      enabled: true,
      channels: ['SMS', 'Email', 'Dashboard'],
      cooldownMinutes: 60,
      description: 'Alert when flood probability exceeds severe threshold',
    },
  ],
  depots: resources?.depots || [],
  equipment: resources?.equipment || [],
  crews: resources?.crews || [],
};

// Utility function to generate IDs
const generateId = (prefix) => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Utility function to validate required fields
const validateRequired = (data, requiredFields) => {
  const missing = requiredFields.filter(field => !data[field]);
  return missing.length === 0 ? null : missing;
};

// Existing API endpoints
app.get('/api/zones', (req, res) => {
  res.json(zones);
});

app.get('/api/risk', (req, res) => {
  const timestamp = req.query.at || new Date().toISOString();

  // Try to match specific timestamp format in files
  try {
    const files = fs.readdirSync(dataPath).filter(f => f.startsWith('risk_') && f.endsWith('.json'));

    if (files.length > 0) {
      // Try to find exact match first
      const normalizedTimestamp = timestamp.replace(/[:]/g, '-');
      const exactMatch = files.find(f => f.includes(normalizedTimestamp));

      if (exactMatch) {
        const riskData = readJsonFile(exactMatch);
        return res.json(riskData);
      }

      // Fallback to first available file
      const riskData = readJsonFile(files[0]);
      res.json(riskData);
    } else {
      res.status(404).json({ error: 'No risk data available' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to load risk data' });
  }
});

app.get('/api/resources', (req, res) => {
  res.json(resources);
});

app.get('/api/alerts', (req, res) => {
  res.json(alerts);
});

app.post('/api/alerts/:id/ack', (req, res) => {
  const alertId = req.params.id;
  const alert = alerts.find(a => a.id === alertId);

  if (!alert) {
    return res.status(404).json({ error: 'Alert not found' });
  }

  // Mark alert as acknowledged
  alert.acknowledged = true;
  alert.acknowledgedAt = new Date().toISOString();
  alert.acknowledgedBy = 'current_user';

  res.json({ success: true, alert });
});

app.get('/api/gauges', (req, res) => {
  res.json(gauges);
});

app.get('/api/damage-index', (req, res) => {
  const damageData = readJsonFile('damage_index.json');
  res.json(damageData);
});

app.get('/api/plan', (req, res) => {
  const planData = readJsonFile('plan_draft.json');
  res.json(planData);
});

app.get('/api/comms', (req, res) => {
  const commsData = readJsonFile('comms.json');
  res.json(commsData);
});

app.post('/api/comms', (req, res) => {
  const { channel, from, text } = req.body;

  if (!channel || !from || !text) {
    return res.status(400).json({ error: 'channel, from, and text are required' });
  }

  const commsData = readJsonFile('comms.json') || [];
  const newMessage = {
    id: generateId('COMM'),
    channel,
    from,
    text,
    timestamp: new Date().toISOString(),
  };

  commsData.push(newMessage);
  writeJsonFile('comms.json', commsData);

  res.json({ success: true, ...newMessage });
});

// Pipeline API endpoints
app.get('/api/pipeline/scenarios', (req, res) => {
  const config = loadPipelineConfig();

  if (!config?.scenarios) {
    return res.json({ scenarios: [] });
  }

  const scenarios = config.scenarios.map((scenario) => {
    const summary = loadScenarioSummary(scenario.name);
    const allocationPath = findLatestFile(getScenarioDir(scenario.name), 'allocations_');

    return {
      name: scenario.name,
      source_file: scenario.source_file,
      total_units: scenario.total_units ?? summary?.total_units ?? null,
      max_units_per_zone: scenario.max_units_per_zone ?? null,
      last_run_at: summary?.generated_at || null,
      latest_summary: summary,
      latest_allocation_file: allocationPath ? path.basename(allocationPath) : null,
      result_path: fileExists(getScenarioDir(scenario.name))
        ? path.relative(repoRoot, getScenarioDir(scenario.name))
        : null,
    };
  });

  res.json({ scenarios });
});

app.get('/api/pipeline/scenarios/:scenario/summary', (req, res) => {
  const scenarioName = req.params.scenario;
  const scenarioConfig = getScenarioConfig(scenarioName);

  if (!scenarioConfig) {
    return res.status(404).json({ error: `Scenario ${scenarioName} not found` });
  }

  const summary = loadScenarioSummary(scenarioName);

  if (!summary) {
    return res.status(404).json({ error: 'No summary available for scenario' });
  }

  res.json({ scenario: scenarioName, summary });
});

app.get('/api/pipeline/scenarios/:scenario/allocations', (req, res) => {
  const scenarioName = req.params.scenario;
  const scenarioConfig = getScenarioConfig(scenarioName);

  if (!scenarioConfig) {
    return res.status(404).json({ error: `Scenario ${scenarioName} not found` });
  }

  const allocationData = loadAllocationsCsv(scenarioName);

  if (!allocationData) {
    return res.status(404).json({ error: 'No allocation file available for scenario' });
  }

  const {
    latest = 'false',
    timestamp,
    zone,
    impact,
    criticalOnly = 'false',
    limit,
  } = req.query;

  let rows = allocationData.rows;

  if (latest === 'true' && rows.length) {
    const targetTimestamp = rows[rows.length - 1].timestamp;
    rows = rows.filter((row) => row.timestamp === targetTimestamp);
  }

  if (timestamp) {
    rows = rows.filter((row) => row.timestamp === timestamp);
  }

  if (zone) {
    const zoneLower = zone.toString().toLowerCase();
    rows = rows.filter((row) =>
      row.zone_id?.toLowerCase() === zoneLower ||
      row.zone_name?.toLowerCase().includes(zoneLower)
    );
  }

  if (impact) {
    const impactLower = impact.toString().toLowerCase();
    rows = rows.filter((row) => row.impact_level?.toLowerCase().includes(impactLower));
  }

  if (criticalOnly === 'true') {
    rows = rows.filter((row) => row.is_critical_infra);
  }

  const limitNumber = limit ? Number(limit) : null;
  let limitedRows = rows;

  if (limitNumber && Number.isFinite(limitNumber) && limitNumber > 0) {
    limitedRows = rows.slice(-limitNumber);
  }

  const summary = summarizeAllocations(limitedRows);
  const meta = {
    scenario: scenarioName,
    file: path.basename(allocationData.file),
    total_rows: allocationData.rows.length,
    returned_rows: limitedRows.length,
    filters: {
      latest: latest === 'true',
      timestamp: timestamp || null,
      zone: zone || null,
      impact: impact || null,
      criticalOnly: criticalOnly === 'true',
      limit: limitNumber,
    },
    time_range: {
      start: limitedRows[0]?.timestamp || null,
      end: limitedRows[limitedRows.length - 1]?.timestamp || null,
    },
  };

  res.json({ meta, summary, data: limitedRows });
});

app.get('/api/pipeline/status', (req, res) => {
  if (!fileExists(pipelineStatusPath)) {
    return res.status(404).json({ error: 'Pipeline status file not found' });
  }

  try {
    const raw = fs.readFileSync(pipelineStatusPath, 'utf8');
    const status = JSON.parse(raw);
    res.json(status);
  } catch (error) {
    console.error('[API] Failed to read pipeline status file', error);
    res.status(500).json({ error: 'Failed to parse pipeline status file' });
  }
});

// Administrator API endpoints

// Users Management
app.get('/api/admin/users', (req, res) => {
  res.json(adminData.users);
});

app.post('/api/admin/users', (req, res) => {
  const requiredFields = ['username', 'email', 'firstName', 'lastName', 'role', 'department', 'status'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  // Check for duplicate username or email
  const existingUser = adminData.users.find(u =>
    u.username === req.body.username || u.email === req.body.email
  );

  if (existingUser) {
    return res.status(409).json({ error: 'Username or email already exists' });
  }

  const newUser = {
    id: generateId('USR'),
    ...req.body,
    permissions: getRolePermissions(req.body.role),
    zones: req.body.role === 'Administrator' ? ['Z1N', 'Z1S', 'Z2', 'Z3', 'Z4', 'ZC'] : [],
    createdAt: new Date().toISOString(),
    lastLogin: null,
  };

  adminData.users.push(newUser);
  res.status(201).json(newUser);
});

app.put('/api/admin/users/:id', (req, res) => {
  const userIndex = adminData.users.findIndex(u => u.id === req.params.id);

  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  // Check for duplicate username or email (excluding current user)
  const existingUser = adminData.users.find(u =>
    (u.username === req.body.username || u.email === req.body.email) && u.id !== req.params.id
  );

  if (existingUser) {
    return res.status(409).json({ error: 'Username or email already exists' });
  }

  adminData.users[userIndex] = {
    ...adminData.users[userIndex],
    ...req.body,
    permissions: getRolePermissions(req.body.role),
    updatedAt: new Date().toISOString(),
  };

  res.json(adminData.users[userIndex]);
});

app.delete('/api/admin/users/:id', (req, res) => {
  const userIndex = adminData.users.findIndex(u => u.id === req.params.id);

  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  const user = adminData.users[userIndex];

  // Prevent deletion of the last administrator
  if (user.role === 'Administrator') {
    const adminCount = adminData.users.filter(u => u.role === 'Administrator').length;
    if (adminCount <= 1) {
      return res.status(400).json({ error: 'Cannot delete the last administrator' });
    }
  }

  adminData.users.splice(userIndex, 1);
  res.status(204).send();
});

// Thresholds Management
app.get('/api/admin/thresholds/risk', (req, res) => {
  res.json(adminData.riskThresholds);
});

app.post('/api/admin/thresholds/risk', (req, res) => {
  const requiredFields = ['name', 'band', 'minRisk', 'maxRisk', 'color'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  // Validate risk values
  if (req.body.minRisk < 0 || req.body.maxRisk > 1 || req.body.minRisk >= req.body.maxRisk) {
    return res.status(400).json({ error: 'Invalid risk values' });
  }

  const newThreshold = {
    id: generateId('RT'),
    ...req.body,
    minRisk: Number(req.body.minRisk),
    maxRisk: Number(req.body.maxRisk),
  };

  adminData.riskThresholds.push(newThreshold);
  res.status(201).json(newThreshold);
});

app.put('/api/admin/thresholds/risk/:id', (req, res) => {
  const thresholdIndex = adminData.riskThresholds.findIndex(t => t.id === req.params.id);

  if (thresholdIndex === -1) {
    return res.status(404).json({ error: 'Threshold not found' });
  }

  adminData.riskThresholds[thresholdIndex] = {
    ...adminData.riskThresholds[thresholdIndex],
    ...req.body,
    minRisk: Number(req.body.minRisk),
    maxRisk: Number(req.body.maxRisk),
  };

  res.json(adminData.riskThresholds[thresholdIndex]);
});

app.delete('/api/admin/thresholds/risk/:id', (req, res) => {
  const thresholdIndex = adminData.riskThresholds.findIndex(t => t.id === req.params.id);

  if (thresholdIndex === -1) {
    return res.status(404).json({ error: 'Threshold not found' });
  }

  adminData.riskThresholds.splice(thresholdIndex, 1);
  res.status(204).send();
});

// Gauge Thresholds
app.get('/api/admin/thresholds/gauges', (req, res) => {
  res.json(adminData.gaugeThresholds);
});

app.post('/api/admin/thresholds/gauges', (req, res) => {
  const requiredFields = ['gaugeId', 'gaugeName', 'alertThreshold', 'criticalThreshold', 'unit'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  const newThreshold = {
    id: generateId('GT'),
    ...req.body,
    alertThreshold: Number(req.body.alertThreshold),
    criticalThreshold: Number(req.body.criticalThreshold),
  };

  adminData.gaugeThresholds.push(newThreshold);
  res.status(201).json(newThreshold);
});

app.put('/api/admin/thresholds/gauges/:id', (req, res) => {
  const thresholdIndex = adminData.gaugeThresholds.findIndex(t => t.id === req.params.id);

  if (thresholdIndex === -1) {
    return res.status(404).json({ error: 'Gauge threshold not found' });
  }

  adminData.gaugeThresholds[thresholdIndex] = {
    ...adminData.gaugeThresholds[thresholdIndex],
    ...req.body,
    alertThreshold: Number(req.body.alertThreshold),
    criticalThreshold: Number(req.body.criticalThreshold),
  };

  res.json(adminData.gaugeThresholds[thresholdIndex]);
});

app.delete('/api/admin/thresholds/gauges/:id', (req, res) => {
  const thresholdIndex = adminData.gaugeThresholds.findIndex(t => t.id === req.params.id);

  if (thresholdIndex === -1) {
    return res.status(404).json({ error: 'Gauge threshold not found' });
  }

  adminData.gaugeThresholds.splice(thresholdIndex, 1);
  res.status(204).send();
});

// Alert Rules
app.get('/api/admin/alerts/rules', (req, res) => {
  res.json(adminData.alertRules);
});

app.post('/api/admin/alerts/rules', (req, res) => {
  const requiredFields = ['name', 'triggerType', 'triggerValue', 'severity', 'cooldownMinutes'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  const newRule = {
    id: generateId('AR'),
    ...req.body,
    enabled: req.body.enabled !== undefined ? req.body.enabled : true,
    channels: req.body.channels || ['Dashboard'],
    cooldownMinutes: Number(req.body.cooldownMinutes),
  };

  adminData.alertRules.push(newRule);
  res.status(201).json(newRule);
});

app.put('/api/admin/alerts/rules/:id', (req, res) => {
  const ruleIndex = adminData.alertRules.findIndex(r => r.id === req.params.id);

  if (ruleIndex === -1) {
    return res.status(404).json({ error: 'Alert rule not found' });
  }

  adminData.alertRules[ruleIndex] = {
    ...adminData.alertRules[ruleIndex],
    ...req.body,
    cooldownMinutes: Number(req.body.cooldownMinutes),
  };

  res.json(adminData.alertRules[ruleIndex]);
});

app.delete('/api/admin/alerts/rules/:id', (req, res) => {
  const ruleIndex = adminData.alertRules.findIndex(r => r.id === req.params.id);

  if (ruleIndex === -1) {
    return res.status(404).json({ error: 'Alert rule not found' });
  }

  adminData.alertRules.splice(ruleIndex, 1);
  res.status(204).send();
});

// Resource Management - Depots
app.get('/api/admin/resources/depots', (req, res) => {
  res.json(adminData.depots);
});

app.post('/api/admin/resources/depots', (req, res) => {
  const requiredFields = ['name', 'address', 'manager', 'phone', 'capacity', 'status'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  const newDepot = {
    id: generateId('D'),
    lat: 0,
    lng: 0,
    ...req.body,
    capacity: Number(req.body.capacity),
    zones: req.body.zones || [],
  };

  adminData.depots.push(newDepot);
  res.status(201).json(newDepot);
});

app.put('/api/admin/resources/depots/:id', (req, res) => {
  const depotIndex = adminData.depots.findIndex(d => d.id === req.params.id);

  if (depotIndex === -1) {
    return res.status(404).json({ error: 'Depot not found' });
  }

  adminData.depots[depotIndex] = {
    ...adminData.depots[depotIndex],
    ...req.body,
    capacity: Number(req.body.capacity),
  };

  res.json(adminData.depots[depotIndex]);
});

app.delete('/api/admin/resources/depots/:id', (req, res) => {
  const depotIndex = adminData.depots.findIndex(d => d.id === req.params.id);

  if (depotIndex === -1) {
    return res.status(404).json({ error: 'Depot not found' });
  }

  // Check if depot has equipment or crews
  const hasEquipment = adminData.equipment.some(e => e.depot === req.params.id);
  const hasCrews = adminData.crews.some(c => c.depot === req.params.id);

  if (hasEquipment || hasCrews) {
    return res.status(400).json({ error: 'Cannot delete depot with assigned equipment or crews' });
  }

  adminData.depots.splice(depotIndex, 1);
  res.status(204).send();
});

// Resource Management - Equipment
app.get('/api/admin/resources/equipment', (req, res) => {
  res.json(adminData.equipment);
});

app.post('/api/admin/resources/equipment', (req, res) => {
  const requiredFields = ['type', 'depot', 'status'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  const newEquipment = {
    id: generateId(req.body.type[0]),
    ...req.body,
    capacity_lps: req.body.capacity_lps ? Number(req.body.capacity_lps) : undefined,
    units: req.body.units ? Number(req.body.units) : undefined,
  };

  adminData.equipment.push(newEquipment);
  res.status(201).json(newEquipment);
});

app.put('/api/admin/resources/equipment/:id', (req, res) => {
  const equipmentIndex = adminData.equipment.findIndex(e => e.id === req.params.id);

  if (equipmentIndex === -1) {
    return res.status(404).json({ error: 'Equipment not found' });
  }

  adminData.equipment[equipmentIndex] = {
    ...adminData.equipment[equipmentIndex],
    ...req.body,
    capacity_lps: req.body.capacity_lps ? Number(req.body.capacity_lps) : adminData.equipment[equipmentIndex].capacity_lps,
    units: req.body.units ? Number(req.body.units) : adminData.equipment[equipmentIndex].units,
  };

  res.json(adminData.equipment[equipmentIndex]);
});

app.delete('/api/admin/resources/equipment/:id', (req, res) => {
  const equipmentIndex = adminData.equipment.findIndex(e => e.id === req.params.id);

  if (equipmentIndex === -1) {
    return res.status(404).json({ error: 'Equipment not found' });
  }

  adminData.equipment.splice(equipmentIndex, 1);
  res.status(204).send();
});

// Resource Management - Crews
app.get('/api/admin/resources/crews', (req, res) => {
  res.json(adminData.crews);
});

app.post('/api/admin/resources/crews', (req, res) => {
  const requiredFields = ['name', 'leader', 'phone', 'teamSize', 'depot', 'status'];
  const missing = validateRequired(req.body, requiredFields);

  if (missing) {
    return res.status(400).json({ error: 'Missing required fields', missing });
  }

  const newCrew = {
    id: generateId('C'),
    lat: 40.4167,
    lng: -3.7033,
    skills: req.body.skills || [],
    ...req.body,
    teamSize: Number(req.body.teamSize),
  };

  adminData.crews.push(newCrew);
  res.status(201).json(newCrew);
});

app.put('/api/admin/resources/crews/:id', (req, res) => {
  const crewIndex = adminData.crews.findIndex(c => c.id === req.params.id);

  if (crewIndex === -1) {
    return res.status(404).json({ error: 'Crew not found' });
  }

  adminData.crews[crewIndex] = {
    ...adminData.crews[crewIndex],
    ...req.body,
    teamSize: Number(req.body.teamSize),
  };

  res.json(adminData.crews[crewIndex]);
});

app.delete('/api/admin/resources/crews/:id', (req, res) => {
  const crewIndex = adminData.crews.findIndex(c => c.id === req.params.id);

  if (crewIndex === -1) {
    return res.status(404).json({ error: 'Crew not found' });
  }

  adminData.crews.splice(crewIndex, 1);
  res.status(204).send();
});

// Zone Management
app.put('/api/admin/zones', (req, res) => {
  const { geojson } = req.body;

  if (!geojson || geojson.type !== 'FeatureCollection') {
    return res.status(400).json({ error: 'Invalid GeoJSON format' });
  }

  // Validate zones
  for (const feature of geojson.features) {
    if (!feature.properties || !feature.properties.id || !feature.properties.name) {
      return res.status(400).json({ error: 'Each zone must have id and name properties' });
    }
  }

  zones = geojson;

  // Also save to file
  if (writeJsonFile('zones.geojson', zones)) {
    res.json({ success: true, zones });
  } else {
    res.status(500).json({ error: 'Failed to save zones' });
  }
});

// Export endpoints
app.get('/api/admin/export/:type', (req, res) => {
  const { type } = req.params;

  let data;
  let filename;

  switch (type) {
    case 'users':
      data = adminData.users;
      filename = 'users.json';
      break;
    case 'thresholds':
      data = {
        risk: adminData.riskThresholds,
        gauges: adminData.gaugeThresholds,
        alerts: adminData.alertRules,
      };
      filename = 'thresholds.json';
      break;
    case 'resources':
      data = {
        depots: adminData.depots,
        equipment: adminData.equipment,
        crews: adminData.crews,
      };
      filename = 'resources.json';
      break;
    case 'zones':
      data = zones;
      filename = 'zones.geojson';
      break;
    default:
      return res.status(400).json({ error: 'Invalid export type' });
  }

  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.json(data);
});

// Helper function to get role permissions
function getRolePermissions(role) {
  const permissions = {
    Administrator: ['system_config', 'user_management', 'threshold_management', 'zone_management', 'risk_assessment', 'resource_deployment'],
    Planner: ['risk_assessment', 'scenario_planning', 'alert_management', 'zone_viewing', 'reporting'],
    Coordinator: ['resource_deployment', 'crew_management', 'communications', 'alert_management', 'zone_viewing'],
    'Data Analyst': ['data_export', 'reporting', 'analytics', 'zone_viewing'],
  };

  return permissions[role] || [];
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

app.listen(PORT, () => {
  console.log(`🚀 API server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🔧 Admin endpoints available at /api/admin/`);
});
