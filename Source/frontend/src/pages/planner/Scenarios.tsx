
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
// import { Slider } from '@/components/ui/slider';
// import { Switch } from '@/components/ui/switch';
// import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  TrendingUp,
  TrendingDown,
  Droplets,
  Wind,
  AlertTriangle,
  Users,
  MapPin,
  Play,
  Save,
  Download,
  Settings,
  Target,
  Shield,
  Activity,
  Clock,
  BarChart3
} from 'lucide-react';
import { useZones, useRiskData, useResources, useAlerts } from '@/hooks/useApiData';
import { useAppContext } from '@/contexts/AppContext';
import type { RiskPoint, Resources, TimeHorizon } from '@/types';
import { format } from 'date-fns';

interface ScenarioParameters {
  rainfallIncrease: number;
  windSpeed: number;
  temperature: number;
  riverLevel: number;
  infrastructureFailure: boolean;
  evacuationEnabled: boolean;
  resourceDeployment: number;
  warningTime: number;
}

interface ScenarioResult {
  zoneId: string;
  baselineRisk: number;
  scenarioRisk: number;
  riskChange: number;
  impactLevel: 'Low' | 'Moderate' | 'High' | 'Critical';
  recommendations: string[];
}

export function PlannerScenarios() {
  const { selectedZone, timeHorizon } = useAppContext();
  const { data: zones } = useZones();
  const { data: currentRiskData } = useRiskData();
  const { data: resources } = useResources();
  const { data: alerts } = useAlerts();

  const [activeScenario, setActiveScenario] = useState<string>('rainfall');
  const [scenarioParams, setScenarioParams] = useState<ScenarioParameters>({
    rainfallIncrease: 50,
    windSpeed: 25,
    temperature: 20,
    riverLevel: 2,
    infrastructureFailure: false,
    evacuationEnabled: false,
    resourceDeployment: 75,
    warningTime: 6
  });

  const [isRunning, setIsRunning] = useState(false);
  const [scenarioResults, setScenarioResults] = useState<ScenarioResult[]>([]);
  const [savedScenarios, setSavedScenarios] = useState<any[]>([]);

  // Predefined scenario templates
  const scenarioTemplates = [
    {
      id: 'rainfall',
      name: 'Extreme Rainfall',
      description: 'Simulate 50% increase in precipitation',
      icon: Droplets,
      params: { rainfallIncrease: 50, windSpeed: 15 }
    },
    {
      id: 'storm',
      name: 'Storm Surge',
      description: 'Combined wind and rainfall event',
      icon: Wind,
      params: { rainfallIncrease: 75, windSpeed: 45 }
    },
    {
      id: 'failure',
      name: 'Infrastructure Failure',
      description: 'Critical infrastructure outage during event',
      icon: AlertTriangle,
      params: { infrastructureFailure: true, rainfallIncrease: 25 }
    },
    {
      id: 'mitigation',
      name: 'Enhanced Response',
      description: 'Optimized resource deployment and early warning',
      icon: Shield,
      params: { resourceDeployment: 100, warningTime: 12, evacuationEnabled: true }
    }
  ];

  const runScenarioSimulation = async () => {
    setIsRunning(true);

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 2000));

    const results: ScenarioResult[] = zones?.features.map(zone => {
      const baselineRisk = currentRiskData?.find(r => r.zoneId === zone.properties.id)?.risk || 0;

      // Calculate scenario impact based on parameters
      let riskMultiplier = 1;

      // Environmental factors
      riskMultiplier += (scenarioParams.rainfallIncrease / 100) * 0.8;
      riskMultiplier += (scenarioParams.windSpeed / 50) * 0.3;
      riskMultiplier += (scenarioParams.riverLevel - 1) * 0.4;

      // Infrastructure impact
      if (scenarioParams.infrastructureFailure) {
        riskMultiplier += 0.5;
      }

      // Mitigation factors
      riskMultiplier -= (scenarioParams.resourceDeployment / 100) * 0.3;
      riskMultiplier -= (scenarioParams.warningTime / 24) * 0.2;
      if (scenarioParams.evacuationEnabled) {
        riskMultiplier -= 0.2;
      }

      const scenarioRisk = Math.min(Math.max(baselineRisk * riskMultiplier, 0), 1);
      const riskChange = scenarioRisk - baselineRisk;

      let impactLevel: 'Low' | 'Moderate' | 'High' | 'Critical' = 'Low';
      if (Math.abs(riskChange) > 0.4) impactLevel = 'Critical';
      else if (Math.abs(riskChange) > 0.25) impactLevel = 'High';
      else if (Math.abs(riskChange) > 0.1) impactLevel = 'Moderate';

      const recommendations = generateRecommendations(zone.properties.id, riskChange, scenarioParams);

      return {
        zoneId: zone.properties.id,
        baselineRisk,
        scenarioRisk,
        riskChange,
        impactLevel,
        recommendations
      };
    }) || [];

    setScenarioResults(results);
    setIsRunning(false);
  };

  const generateRecommendations = (zoneId: string, riskChange: number, params: ScenarioParameters): string[] => {
    const recommendations: string[] = [];
    const zone = zones?.features.find(z => z.properties.id === zoneId);
    const population = zone?.properties.population || 0;

    if (riskChange > 0.3) {
      recommendations.push('Immediate evacuation preparation recommended');
      recommendations.push('Deploy all available resources to this zone');
    } else if (riskChange > 0.15) {
      recommendations.push('Consider partial evacuation of vulnerable areas');
      recommendations.push('Pre-position emergency resources');
    }

    if (params.rainfallIncrease > 60) {
      recommendations.push('Prepare for flash flooding - clear drainage systems');
    }

    if (params.windSpeed > 40) {
      recommendations.push('Secure loose objects and outdoor equipment');
      recommendations.push('Prepare for power outages');
    }

    if (params.infrastructureFailure && population > 10000) {
      recommendations.push('Establish temporary communication systems');
      recommendations.push('Prepare alternative water sources');
    }

    if (params.resourceDeployment < 50) {
      recommendations.push('Resource shortage anticipated - request external assistance');
    }

    return recommendations;
  };

  const getImpactColor = (impactLevel: string) => {
    switch (impactLevel) {
      case 'Critical': return 'text-red-600 bg-red-50';
      case 'High': return 'text-orange-600 bg-orange-50';
      case 'Moderate': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  const loadScenarioTemplate = (template: any) => {
    setActiveScenario(template.id);
    setScenarioParams(prev => ({ ...prev, ...template.params }));
  };

  const saveScenario = () => {
    const scenario = {
      id: Date.now().toString(),
      name: `Scenario ${savedScenarios.length + 1}`,
      params: scenarioParams,
      results: scenarioResults,
      timestamp: new Date().toISOString()
    };
    setSavedScenarios(prev => [...prev, scenario]);
  };

  const exportResults = () => {
    const data = {
      scenario: activeScenario,
      parameters: scenarioParams,
      results: scenarioResults,
      timestamp: new Date().toISOString(),
      zones: zones?.features.map(z => ({
        id: z.properties.id,
        name: z.properties.name,
        population: z.properties.population
      }))
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario-${activeScenario}-${format(new Date(), 'yyyy-MM-dd-HHmm')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scenario Workbench</h1>
          <p className="text-muted-foreground">Advanced what-if analysis and impact simulation</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={saveScenario} disabled={scenarioResults.length === 0}>
            <Save className="h-4 w-4 mr-2" />
            Save Scenario
          </Button>
          <Button variant="outline" onClick={exportResults} disabled={scenarioResults.length === 0}>
            <Download className="h-4 w-4 mr-2" />
            Export Results
          </Button>
        </div>
      </div>

      <Tabs defaultValue="configure" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configure">Configure Scenario</TabsTrigger>
          <TabsTrigger value="results">Results & Analysis</TabsTrigger>
          <TabsTrigger value="library">Scenario Library</TabsTrigger>
        </TabsList>

        <TabsContent value="configure" className="space-y-6">
          {/* Scenario Templates */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Scenario Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {scenarioTemplates.map(template => {
                const Icon = template.icon;
                const isActive = activeScenario === template.id;

                return (
                  <Card
                    key={template.id}
                    className={`cursor-pointer transition-all ${isActive ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
                    onClick={() => loadScenarioTemplate(template)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3">
                        <Icon className="h-6 w-6 text-primary" />
                        <div>
                          <h4 className="font-medium">{template.name}</h4>
                          <p className="text-xs text-muted-foreground">{template.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Environmental Parameters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>Environmental Parameters</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Rainfall Increase: {scenarioParams.rainfallIncrease}%</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="200"
                    step="5"
                    value={scenarioParams.rainfallIncrease}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, rainfallIncrease: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Wind Speed: {scenarioParams.windSpeed} km/h</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={scenarioParams.windSpeed}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, windSpeed: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">River Level Increase: +{scenarioParams.riverLevel}m</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.5"
                    value={scenarioParams.riverLevel}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, riverLevel: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Temperature: {scenarioParams.temperature}°C</label>
                  </div>
                  <input
                    type="range"
                    min="-10"
                    max="45"
                    step="1"
                    value={scenarioParams.temperature}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, temperature: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Response Parameters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Response Parameters</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Resource Deployment Level: {scenarioParams.resourceDeployment}%</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={scenarioParams.resourceDeployment}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, resourceDeployment: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Warning Time: {scenarioParams.warningTime} hours</label>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="48"
                    step="1"
                    value={scenarioParams.warningTime}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, warningTime: Number(e.target.value) }))}
                    className="w-full"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Infrastructure Failure</label>
                    <p className="text-xs text-muted-foreground">Simulate critical systems outage</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={scenarioParams.infrastructureFailure}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, infrastructureFailure: e.target.checked }))}
                    className="h-4 w-4"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium">Evacuation Protocol</label>
                    <p className="text-xs text-muted-foreground">Enable preemptive evacuation</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={scenarioParams.evacuationEnabled}
                    onChange={(e) => setScenarioParams(prev => ({ ...prev, evacuationEnabled: e.target.checked }))}
                    className="h-4 w-4"
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Run Simulation */}
          <div className="flex justify-center">
            <Button
              onClick={runScenarioSimulation}
              disabled={isRunning}
              size="lg"
              className="h-12 px-8"
            >
              {isRunning ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Running Simulation...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 mr-2" />
                  Run Scenario Simulation
                </>
              )}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="results">
          {scenarioResults.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No Scenario Results</h3>
                <p className="text-muted-foreground mb-4">
                  Configure and run a scenario simulation to see results here
                </p>
                <Button onClick={() => setActiveScenario('configure')}>
                  Go to Configuration
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Executive Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Scenario Impact Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {scenarioResults.filter(r => r.impactLevel === 'Critical').length}
                      </div>
                      <div className="text-sm text-muted-foreground">Critical Impact Zones</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {scenarioResults.filter(r => r.impactLevel === 'High').length}
                      </div>
                      <div className="text-sm text-muted-foreground">High Impact Zones</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {(scenarioResults.reduce((sum, r) => sum + Math.abs(r.riskChange), 0) / scenarioResults.length * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Average Risk Change</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {scenarioResults.filter(r => r.riskChange < 0).length}
                      </div>
                      <div className="text-sm text-muted-foreground">Mitigated Zones</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Results */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {scenarioResults.map(result => {
                  const zone = zones?.features.find(z => z.properties.id === result.zoneId);
                  const isPositive = result.riskChange < 0;

                  return (
                    <Card key={result.zoneId} className="relative">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{zone?.properties.name || result.zoneId}</CardTitle>
                          <Badge className={getImpactColor(result.impactLevel)}>
                            {result.impactLevel}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Baseline Risk</span>
                            <span className="font-medium">{(result.baselineRisk * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Scenario Risk</span>
                            <span className="font-medium">{(result.scenarioRisk * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Change</span>
                            <div className="flex items-center space-x-1">
                              {isPositive ? (
                                <TrendingDown className="h-4 w-4 text-green-500" />
                              ) : (
                                <TrendingUp className="h-4 w-4 text-red-500" />
                              )}
                              <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                                {isPositive ? '' : '+'}{(result.riskChange * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${result.scenarioRisk * 100}%` }}
                            />
                          </div>

                          {result.recommendations.length > 0 && (
                            <div className="pt-2 border-t">
                              <div className="text-sm font-medium mb-2">Recommendations</div>
                              <div className="space-y-1">
                                {result.recommendations.slice(0, 2).map((rec, index) => (
                                  <div key={index} className="text-xs text-muted-foreground flex items-start">
                                    <Target className="h-3 w-3 mr-1 mt-0.5 flex-shrink-0" />
                                    {rec}
                                  </div>
                                ))}
                                {result.recommendations.length > 2 && (
                                  <div className="text-xs text-muted-foreground">
                                    +{result.recommendations.length - 2} more...
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="library">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Saved Scenarios</CardTitle>
              </CardHeader>
              <CardContent>
                {savedScenarios.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Save className="h-8 w-8 mx-auto mb-2" />
                    <p>No saved scenarios</p>
                    <p className="text-sm">Save your scenarios to build a library for quick access</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {savedScenarios.map(scenario => (
                      <div key={scenario.id} className="p-3 border rounded-lg hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium">{scenario.name}</h4>
                            <p className="text-xs text-muted-foreground">
                              {format(new Date(scenario.timestamp), 'MMM d, yyyy HH:mm')}
                            </p>
                          </div>
                          <Button variant="outline" size="sm">Load</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Historical Event Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <h4 className="font-medium">2024 River Flood Event</h4>
                    <p className="text-xs text-muted-foreground mb-2">
                      Historical rainfall patterns and response data
                    </p>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">Rainfall: 85%</Badge>
                      <Badge variant="outline">Duration: 72h</Badge>
                    </div>
                  </div>

                  <div className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <h4 className="font-medium">Storm Surge 2023</h4>
                    <p className="text-xs text-muted-foreground mb-2">
                      Combined wind and flooding event
                    </p>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">Wind: 65km/h</Badge>
                      <Badge variant="outline">Rainfall: 120%</Badge>
                    </div>
                  </div>

                  <div className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                    <h4 className="font-medium">Infrastructure Outage</h4>
                    <p className="text-xs text-muted-foreground mb-2">
                      Critical systems failure scenario
                    </p>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">Duration: 24h</Badge>
                      <Badge variant="outline">Impact: High</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}