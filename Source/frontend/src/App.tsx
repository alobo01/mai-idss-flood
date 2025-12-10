import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from 'react-leaflet';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Flood stage data for St. Louis
const FLOOD_STAGES = [
  { name: 'Action Stage', level: 28, color: '#FFEB3B', dasharray: '5 5' },
  { name: 'Flood Stage', level: 30, color: '#FF9800', dasharray: '5 5' },
  { name: 'Moderate Flood', level: 35, color: '#F44336', dasharray: '5 5' },
  { name: 'Major Flood', level: 40, color: '#B71C1C', dasharray: '5 5' },
];

// Sensor data with mock locations and levels
const SENSOR_DATA = [
  { id: 'STL-001', name: 'St. Louis Main', lat: 38.6270, lng: -90.1994, currentLevel: 32.5, isMainGauge: true },
  { id: 'STL-002', name: 'North Station', lat: 38.6800, lng: -90.1500, currentLevel: 28.2, isMainGauge: false },
  { id: 'STL-003', name: 'South Station', lat: 38.5500, lng: -90.2500, currentLevel: 31.8, isMainGauge: false },
  { id: 'STL-004', name: 'West Station', lat: 38.6270, lng: -90.3000, currentLevel: 29.1, isMainGauge: false },
];

// Mock prediction data for the line plot
const generatePredictionData = () => {
  const data = [];
  const now = new Date();
  const currentLevel = 32.5;

  for (let i = 24; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      time: time.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
      actual: i <= 6 ? currentLevel + (Math.random() - 0.5) * 0.5 : null,
      predicted: currentLevel + Math.sin(i / 4) * 3 + Math.random() * 0.5,
      hour: i,
    });
  }

  // Add future predictions
  for (let i = 1; i <= 48; i++) {
    const time = new Date(now.getTime() + i * 60 * 60 * 1000);
    const trend = i > 24 ? -0.3 : 0.2; // Rising then falling
    data.push({
      time: time.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
      actual: null,
      predicted: currentLevel + (Math.sin(i / 4) * 3) + (trend * i) + Math.random() * 0.5,
      hour: -i,
    });
  }

  return data;
};

const WaterLevelWidget: React.FC<{ level: number; name: string; isMainGauge?: boolean }> = ({ level, name, isMainGauge = false }) => {
  const percentage = Math.min((level / 45) * 100, 100);
  const maxHeight = 140;
  const waterHeight = (percentage / 100) * maxHeight;

  const getStageGradient = (level: number) => {
    if (level >= 40) return 'bg-gradient-to-t from-red-700 to-red-500';
    if (level >= 35) return 'bg-gradient-to-t from-orange-600 to-orange-400';
    if (level >= 30) return 'bg-gradient-to-t from-yellow-600 to-yellow-400';
    if (level >= 28) return 'bg-gradient-to-t from-blue-600 to-blue-400';
    return 'bg-gradient-to-t from-green-600 to-green-400';
  };

  const getStageBorderColor = (level: number) => {
    if (level >= 40) return 'border-red-400';
    if (level >= 35) return 'border-orange-400';
    if (level >= 30) return 'border-yellow-400';
    if (level >= 28) return 'border-blue-400';
    return 'border-green-400';
  };

  const getStageGlowColor = (level: number) => {
    if (level >= 40) return 'shadow-red-500/50';
    if (level >= 35) return 'shadow-orange-500/50';
    if (level >= 30) return 'shadow-yellow-500/50';
    if (level >= 28) return 'shadow-blue-500/50';
    return 'shadow-green-500/50';
  };

  return (
    <div className={`relative p-5 rounded-xl transition-all duration-300 hover:scale-105 hover:shadow-xl ${
      isMainGauge
        ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-400 shadow-lg'
        : 'bg-gradient-to-br from-white to-gray-50 border-2 border-gray-200 shadow-md hover:border-blue-300'
    }`}>
      {isMainGauge && (
        <div className="absolute top-2 right-2">
          <div className="flex items-center space-x-1 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span className="font-semibold">Main</span>
          </div>
        </div>
      )}

      <h4 className="font-bold text-sm mb-3 text-gray-800">{name}</h4>

      <div className="flex items-center justify-center mb-3">
        <div className={`relative w-20 h-40 bg-gradient-to-b from-gray-100 to-gray-200 rounded-2xl overflow-hidden border-4 ${getStageBorderColor(level)} shadow-inner`}>
          {/* Glass effect overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>

          {/* Water with multiple animation layers */}
          <div
            className={`absolute bottom-0 w-full ${getStageGradient(level)} transition-all duration-1500 ease-in-out shadow-lg ${getStageGlowColor(level)} shadow-2xl`}
            style={{ height: `${waterHeight}px` }}
          >
            {/* Wave animation */}
            <div className="absolute top-0 w-full h-6">
              <div className="w-full h-full bg-blue-300/30 animate-pulse"></div>
              <div className="w-full h-full bg-blue-200/50 rounded-full transform -translate-y-3 animate-bounce"></div>
            </div>

            {/* Bubbles animation */}
            <div className="absolute bottom-2 left-2 w-2 h-2 bg-white/60 rounded-full animate-ping"></div>
            <div className="absolute bottom-4 right-3 w-1 h-1 bg-white/40 rounded-full animate-ping animation-delay-200"></div>
            <div className="absolute bottom-8 left-4 w-1.5 h-1.5 bg-white/50 rounded-full animate-ping animation-delay-400"></div>
          </div>

          {/* Water level indicator */}
          <div className="absolute top-2 right-2 bg-black/80 text-white text-xs font-bold px-2 py-1 rounded-lg backdrop-blur-sm border border-white/20">
            {level.toFixed(1)}'
          </div>

          {/* Measurement marks */}
          <div className="absolute right-0 top-0 h-full w-2 flex flex-col justify-between py-2">
            {[45, 35, 25, 15, 5].map((mark) => (
              <div key={mark} className="w-full h-px bg-gray-400/50"></div>
            ))}
          </div>
        </div>
      </div>

      <div className="text-center">
        <div className="font-bold text-lg text-gray-800 mb-1">{level.toFixed(1)} ft</div>
        <div className={`text-xs font-semibold px-2 py-1 rounded-full inline-block ${
          level >= 40 ? 'bg-red-100 text-red-700' :
          level >= 35 ? 'bg-orange-100 text-orange-700' :
          level >= 30 ? 'bg-yellow-100 text-yellow-700' :
          level >= 28 ? 'bg-blue-100 text-blue-700' :
          'bg-green-100 text-green-700'
        }`}>
          {level >= 40 ? 'Major Flood' :
           level >= 35 ? 'Moderate Flood' :
           level >= 30 ? 'Flood Stage' :
           level >= 28 ? 'Action Stage' :
           'Normal'}
        </div>
      </div>
    </div>
  );
};

// Mock zone data for demonstration
const MOCK_ZONES: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { id: "downtown", name: "Downtown St. Louis", risk_level: 0.8 },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-90.210, 38.635],
          [-90.190, 38.635],
          [-90.190, 38.620],
          [-90.210, 38.620],
          [-90.210, 38.635]
        ]]
      }
    },
    {
      type: "Feature",
      properties: { id: "north", name: "North City", risk_level: 0.3 },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-90.200, 38.640],
          [-90.180, 38.640],
          [-90.180, 38.655],
          [-90.200, 38.655],
          [-90.200, 38.640]
        ]]
      }
    },
    {
      type: "Feature",
      properties: { id: "south", name: "South City", risk_level: 0.6 },
      geometry: {
        type: "Polygon",
        coordinates: [[
          [-90.200, 38.615],
          [-90.180, 38.615],
          [-90.180, 38.600],
          [-90.200, 38.600],
          [-90.200, 38.615]
        ]]
      }
    }
  ]
};

const PlannerDashboard: React.FC = () => {
  const [predictionData, setPredictionData] = useState(generatePredictionData());
  const [selectedZone, setSelectedZone] = useState<any>(null);

  // Update predictions periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setPredictionData(generatePredictionData());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getZoneStyle = (feature: any) => {
    const riskLevel = feature.properties?.risk_level || 0;

    return {
      fillColor: riskLevel > 0.7 ? '#d32f2f' : riskLevel > 0.4 ? '#f57c00' : '#388e3c',
      weight: 2,
      opacity: 1,
      color: 'white',
      dashArray: '3',
      fillOpacity: 0.6,
    };
  };

  const getStageStatus = (level: number) => {
    if (level >= 40) return { name: 'Major Flood', color: 'text-red-600' };
    if (level >= 35) return { name: 'Moderate Flood', color: 'text-orange-500' };
    if (level >= 30) return { name: 'Flood Stage', color: 'text-yellow-600' };
    if (level >= 28) return { name: 'Action Stage', color: 'text-blue-500' };
    return { name: 'Normal', color: 'text-green-600' };
  };

  const currentStlStatus = getStageStatus(SENSOR_DATA[0].currentLevel);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <div className="absolute inset-0 bg-black/20"></div>

      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/3 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl animate-pulse animation-delay-4000"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto p-6">
        {/* Enhanced Header */}
        <div className="bg-gradient-to-r from-blue-600/90 to-cyan-600/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 mb-6 border border-blue-400/30">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">St. Louis Flood Planner</h1>
              <p className="text-blue-100 text-lg">Real-time Monitoring & Prediction System</p>
            </div>
            <div className="text-right">
              <div className="bg-white/20 backdrop-blur-sm rounded-lg px-6 py-4 border border-white/30">
                <div className="text-blue-100 text-sm mb-1">Current Status</div>
                <div className={`text-2xl font-bold ${currentStlStatus.color === 'text-red-600' ? 'text-red-300' :
                  currentStlStatus.color === 'text-orange-500' ? 'text-orange-300' :
                  currentStlStatus.color === 'text-yellow-600' ? 'text-yellow-300' :
                  currentStlStatus.color === 'text-blue-500' ? 'text-blue-300' : 'text-green-300'}`}>
                  {currentStlStatus.name}
                </div>
                <div className="text-blue-100 text-sm mt-1">Main Gauge: {SENSOR_DATA[0].currentLevel.toFixed(1)} ft</div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Map with Sensors */}
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Sensor Network & Zone Classification</h2>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Live</span>
              </div>
            </div>
            <div className="h-96 rounded-xl overflow-hidden shadow-inner border-2 border-gray-200">
              <MapContainer
                center={[38.6270, -90.1994]}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='© OpenStreetMap contributors'
                />

                {/* Zone GeoJSON Layer */}
                <GeoJSON
                  data={MOCK_ZONES}
                  style={getZoneStyle}
                  onEachFeature={(feature, layer) => {
                    layer.on({
                      click: () => setSelectedZone(feature),
                      mouseover: (e) => {
                        const layer = e.target;
                        layer.setStyle({
                          weight: 3,
                          color: '#666',
                          dashArray: '',
                          fillOpacity: 0.8,
                        });
                      },
                      mouseout: (e) => {
                        const layer = e.target;
                        layer.setStyle(getZoneStyle(feature));
                      },
                    });
                  }}
                />

                {/* Enhanced Sensor Markers */}
                {SENSOR_DATA.map(sensor => (
                  <Marker
                    key={sensor.id}
                    position={[sensor.lat, sensor.lng]}
                  >
                    <Popup className="custom-popup">
                      <div className="p-3 min-w-48">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-bold text-gray-800">{sensor.name}</h3>
                          {sensor.isMainGauge && (
                            <div className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                              Main
                            </div>
                          )}
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Level:</span>
                            <span className="font-semibold">{sensor.currentLevel.toFixed(1)} ft</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Status:</span>
                            <span className={`font-semibold px-2 py-1 rounded text-xs ${
                              sensor.currentLevel >= 40 ? 'bg-red-100 text-red-700' :
                              sensor.currentLevel >= 35 ? 'bg-orange-100 text-orange-700' :
                              sensor.currentLevel >= 30 ? 'bg-yellow-100 text-yellow-700' :
                              sensor.currentLevel >= 28 ? 'bg-blue-100 text-blue-700' :
                              'bg-green-100 text-green-700'
                            }`}>
                              {getStageStatus(sensor.currentLevel).name}
                            </span>
                          </div>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
            {selectedZone && (
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <strong className="text-gray-700">Selected Zone:</strong> {selectedZone.properties?.name || 'Unknown'}
                    <br />
                    <span className="text-sm text-gray-600">Zone ID: {selectedZone.properties?.id || 'N/A'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-4 h-4 rounded-full ${
                      selectedZone.properties?.risk_level > 0.7 ? 'bg-red-500' :
                      selectedZone.properties?.risk_level > 0.4 ? 'bg-orange-500' : 'bg-green-500'
                    }`}></div>
                    <span className="text-sm text-gray-600">
                      Risk: {Math.round((selectedZone.properties?.risk_level || 0) * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Water Level Sensors Panel */}
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Live Water Level Sensors</h2>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">All Systems Online</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {SENSOR_DATA.map(sensor => (
                <WaterLevelWidget
                  key={sensor.id}
                  level={sensor.currentLevel}
                  name={sensor.name}
                  isMainGauge={sensor.isMainGauge}
                />
              ))}
            </div>

            {/* Enhanced Flood Stages Reference */}
            <div className="mt-6 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
              <h3 className="font-bold text-gray-800 mb-3 flex items-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                Flood Stage Reference
              </h3>
              <div className="space-y-2">
                {FLOOD_STAGES.map(stage => (
                  <div key={stage.name} className="flex items-center justify-between p-2 bg-white rounded-lg border border-gray-200">
                    <div className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded-full ${
                        stage.level >= 40 ? 'bg-red-500' :
                        stage.level >= 35 ? 'bg-orange-500' :
                        stage.level >= 30 ? 'bg-yellow-500' : 'bg-blue-500'
                      }`}></div>
                      <span className="font-medium text-gray-700">{stage.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-gray-900">{stage.level}</span>
                      <span className="text-gray-600 text-sm">ft</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Predictions Chart */}
        <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl p-6 border border-white/20">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800">St. Louis River Level Predictions</h2>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Actual</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Predicted</span>
              </div>
              <div className="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full font-semibold">
                48-Hour Forecast
              </div>
            </div>
          </div>
          <div className="w-full overflow-x-auto bg-gradient-to-br from-gray-50 to-white p-4 rounded-xl">
            <LineChart
              width={1000}
              height={350}
              data={predictionData}
              margin={{ top: 10, right: 40, left: 30, bottom: 80 }}
            >
              <defs>
                <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#dc2626" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#dc2626" stopOpacity={0.1}/>
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={12}
                stroke="#6b7280"
              />
              <YAxis
                label={{
                  value: 'River Level (ft)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fontSize: 14, fill: '#374151' }
                }}
                fontSize={12}
                stroke="#6b7280"
                domain={[20, 45]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend
                wrapperStyle={{
                  paddingTop: '20px'
                }}
              />

              {/* Enhanced flood stage reference lines */}
              {FLOOD_STAGES.map(stage => (
                <ReferenceLine
                  key={stage.name}
                  y={stage.level}
                  stroke={stage.color}
                  strokeDasharray={stage.dasharray}
                  strokeWidth={2}
                  label={{
                    value: stage.name,
                    position: 'right',
                    style: {
                      fontSize: 12,
                      fontWeight: 'bold',
                      fill: stage.color
                    }
                  }}
                />
              ))}

              {/* Enhanced actual data line */}
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ fill: '#2563eb', strokeWidth: 2, r: 5 }}
                activeDot={{ r: 7, fill: '#1d4ed8' }}
                name="Actual"
              />

              {/* Enhanced predicted data line */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#dc2626"
                strokeWidth={3}
                strokeDasharray="8 4"
                dot={false}
                activeDot={false}
                name="Predicted"
              />
            </LineChart>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-1 bg-blue-600 rounded"></div>
                <span className="text-sm font-medium text-gray-700">Historical Data</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-6 h-1 bg-red-600 rounded" style={{ borderTop: '2px dashed' }}></div>
                <span className="text-sm font-medium text-gray-700">Predicted Data</span>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return <PlannerDashboard />;
}

export default App;
