import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/DataTable';
import { FormDialog, FormField } from '@/components/Forms/FormDialog';
import { RiskBand, AlertSeverity } from '@/types';
import { AlertTriangle, Settings, Plus, Edit, Trash2, Info } from 'lucide-react';

// API data types
interface RiskThreshold {
  id: string;
  name: string;
  band: string;
  minRisk: number;
  maxRisk: number;
  color: string;
  description?: string;
  autoAlert: boolean;
}

interface GaugeThreshold {
  id: string;
  gaugeId: string;
  gaugeName: string;
  alertThreshold: number;
  criticalThreshold: number;
  unit: string;
  description?: string;
}

interface AlertRule {
  id: string;
  name: string;
  triggerType: string;
  triggerValue: string;
  severity: AlertSeverity;
  enabled: boolean;
  channels: string[];
  cooldownMinutes: number;
  description?: string;
}

export function AdminThresholds() {
  const [riskThresholds, setRiskThresholds] = useState<RiskThreshold[]>([]);
  const [gaugeThresholds, setGaugeThresholds] = useState<GaugeThreshold[]>([]);
  const [alertRules, setAlertRules] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch thresholds data from API
  useEffect(() => {
    const fetchThresholds = async () => {
      try {
        setLoading(true);
        setError(null);

        const [riskResponse, gaugeResponse, alertResponse] = await Promise.all([
          fetch('/api/admin/thresholds/risk'),
          fetch('/api/admin/thresholds/gauges'),
          fetch('/api/admin/alerts/rules')
        ]);

        if (!riskResponse.ok) {
          throw new Error(`Failed to fetch risk thresholds: ${riskResponse.statusText}`);
        }
        if (!gaugeResponse.ok) {
          throw new Error(`Failed to fetch gauge thresholds: ${gaugeResponse.statusText}`);
        }
        if (!alertResponse.ok) {
          throw new Error(`Failed to fetch alert rules: ${alertResponse.statusText}`);
        }

        const riskData: RiskThreshold[] = await riskResponse.json();
        const gaugeData: GaugeThreshold[] = await gaugeResponse.json();
        const alertData: AlertRule[] = await alertResponse.json();

        setRiskThresholds(riskData || []);
        setGaugeThresholds(gaugeData || []);
        setAlertRules(alertData || []);

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load thresholds data';
        setError(errorMessage);
        console.error('Error fetching thresholds:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchThresholds();
  }, []);

  const [isRiskDialogOpen, setIsRiskDialogOpen] = useState(false);
  const [isGaugeDialogOpen, setIsGaugeDialogOpen] = useState(false);
  const [isAlertDialogOpen, setIsAlertDialogOpen] = useState(false);

  const [editingRisk, setEditingRisk] = useState<any>(null);
  const [editingGauge, setEditingGauge] = useState<any>(null);
  const [editingAlert, setEditingAlert] = useState<any>(null);

  // Risk Threshold Form Fields
  const riskFields: FormField[] = [
    {
      key: 'name',
      label: 'Threshold Name',
      type: 'text',
      required: true,
    },
    {
      key: 'band',
      label: 'Risk Band',
      type: 'select',
      required: true,
      options: [
        { value: 'Low', label: 'Low' },
        { value: 'Moderate', label: 'Moderate' },
        { value: 'High', label: 'High' },
        { value: 'Severe', label: 'Severe' },
      ],
    },
    {
      key: 'minRisk',
      label: 'Minimum Risk Value',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0 || num > 1) return 'Must be between 0 and 1';
        return null;
      },
    },
    {
      key: 'maxRisk',
      label: 'Maximum Risk Value',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0 || num > 1) return 'Must be between 0 and 1';
        return null;
      },
    },
    {
      key: 'color',
      label: 'Display Color',
      type: 'text',
      placeholder: '#22c55e',
      validation: (value) => {
        if (!value.match(/^#[0-9A-Fa-f]{6}$/)) {
          return 'Must be a valid hex color (e.g., #22c55e)';
        }
        return null;
      },
    },
    {
      key: 'description',
      label: 'Description',
      type: 'textarea',
    },
    {
      key: 'autoAlert',
      label: 'Generate Automatic Alert',
      type: 'checkbox',
    },
  ];

  // Gauge Threshold Form Fields
  const gaugeFields: FormField[] = [
    {
      key: 'gaugeId',
      label: 'Gauge ID',
      type: 'text',
      required: true,
    },
    {
      key: 'gaugeName',
      label: 'Gauge Name',
      type: 'text',
      required: true,
    },
    {
      key: 'alertThreshold',
      label: 'Alert Threshold',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0) return 'Must be positive';
        return null;
      },
    },
    {
      key: 'criticalThreshold',
      label: 'Critical Threshold',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0) return 'Must be positive';
        return null;
      },
    },
    {
      key: 'unit',
      label: 'Unit',
      type: 'select',
      required: true,
      options: [
        { value: 'meters', label: 'Meters' },
        { value: 'feet', label: 'Feet' },
        { value: 'cfs', label: 'Cubic Feet per Second' },
      ],
    },
    {
      key: 'description',
      label: 'Description',
      type: 'textarea',
    },
  ];

  // Alert Rules Form Fields
  const alertFields: FormField[] = [
    {
      key: 'name',
      label: 'Rule Name',
      type: 'text',
      required: true,
    },
    {
      key: 'triggerType',
      label: 'Trigger Type',
      type: 'select',
      required: true,
      options: [
        { value: 'Risk Threshold', label: 'Risk Threshold' },
        { value: 'Gauge Rate', label: 'Gauge Rate' },
        { value: 'Gauge Level', label: 'Gauge Level' },
        { value: 'Crew Activity', label: 'Crew Activity' },
      ],
    },
    {
      key: 'triggerValue',
      label: 'Trigger Value',
      type: 'text',
      required: true,
    },
    {
      key: 'severity',
      label: 'Alert Severity',
      type: 'select',
      required: true,
      options: [
        { value: 'Low', label: 'Low' },
        { value: 'Moderate', label: 'Moderate' },
        { value: 'High', label: 'High' },
        { value: 'Severe', label: 'Severe' },
        { value: 'Operational', label: 'Operational' },
      ],
    },
    {
      key: 'channels',
      label: 'Notification Channels',
      type: 'tags',
      placeholder: 'Add channel...',
    },
    {
      key: 'cooldownMinutes',
      label: 'Cooldown Period (minutes)',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0) return 'Must be positive';
        return null;
      },
    },
    {
      key: 'description',
      label: 'Description',
      type: 'textarea',
    },
    {
      key: 'enabled',
      label: 'Enable Rule',
      type: 'checkbox',
    },
  ];

  // Risk Threshold Columns
  const riskColumns = [
    {
      key: 'name',
      title: 'Name',
      sortable: true,
      render: (value: string, record: any) => (
        <div className="flex items-center space-x-2">
          <div
            className="w-4 h-4 rounded"
            style={{ backgroundColor: record.color }}
          />
          <span className="font-medium">{value}</span>
        </div>
      ),
    },
    {
      key: 'band',
      title: 'Risk Band',
      sortable: true,
      render: (value: RiskBand) => (
        <Badge variant={value === 'Severe' ? 'destructive' : 'secondary'}>
          {value}
        </Badge>
      ),
    },
    {
      key: 'minRisk',
      title: 'Min Risk',
      sortable: true,
      render: (value: number) => `${(value * 100).toFixed(0)}%`,
    },
    {
      key: 'maxRisk',
      title: 'Max Risk',
      sortable: true,
      render: (value: number) => `${(value * 100).toFixed(0)}%`,
    },
    {
      key: 'autoAlert',
      title: 'Auto Alert',
      render: (value: boolean) => (
        <Badge variant={value ? 'default' : 'outline'}>
          {value ? 'Enabled' : 'Disabled'}
        </Badge>
      ),
    },
  ];

  // Gauge Threshold Columns
  const gaugeColumns = [
    { key: 'gaugeId', title: 'Gauge ID', sortable: true },
    { key: 'gaugeName', title: 'Gauge Name', sortable: true },
    {
      key: 'alertThreshold',
      title: 'Alert Level',
      sortable: true,
      render: (value: number, record: any) => `${value} ${record.unit}`,
    },
    {
      key: 'criticalThreshold',
      title: 'Critical Level',
      sortable: true,
      render: (value: number, record: any) => `${value} ${record.unit}`,
    },
  ];

  // Alert Rules Columns
  const alertColumns = [
    { key: 'name', title: 'Rule Name', sortable: true },
    { key: 'triggerType', title: 'Trigger Type', sortable: true },
    { key: 'triggerValue', title: 'Trigger Value' },
    {
      key: 'severity',
      title: 'Severity',
      sortable: true,
      render: (value: AlertSeverity) => {
        const colors = {
          Low: 'bg-green-100 text-green-800',
          Moderate: 'bg-yellow-100 text-yellow-800',
          High: 'bg-orange-100 text-orange-800',
          Severe: 'bg-red-100 text-red-800',
          Operational: 'bg-blue-100 text-blue-800',
        };
        return (
          <Badge className={colors[value]}>
            {value}
          </Badge>
        );
      },
    },
    {
      key: 'enabled',
      title: 'Status',
      render: (value: boolean) => (
        <Badge variant={value ? 'default' : 'secondary'}>
          {value ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'channels',
      title: 'Channels',
      render: (value: string[]) => (
        <div className="flex flex-wrap gap-1">
          {value?.map((channel) => (
            <Badge key={channel} variant="outline" className="text-xs">
              {channel}
            </Badge>
          ))}
        </div>
      ),
    },
  ];

  const handleSaveRisk = async (data: any) => {
    try {
      const url = editingRisk
        ? `/api/admin/thresholds/risk/${editingRisk.id}`
        : '/api/admin/thresholds/risk';

      const method = editingRisk ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to save risk threshold: ${response.statusText}`);
      }

      const savedThreshold = await response.json();

      if (editingRisk) {
        setRiskThresholds(prev =>
          prev.map(rt => rt.id === editingRisk.id ? savedThreshold : rt)
        );
      } else {
        setRiskThresholds(prev => [...prev, savedThreshold]);
      }

      setIsRiskDialogOpen(false);
      setEditingRisk(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save risk threshold';
      setError(errorMessage);
      console.error('Error saving risk threshold:', err);
    }
  };

  const handleSaveGauge = async (data: any) => {
    try {
      const url = editingGauge
        ? `/api/admin/thresholds/gauges/${editingGauge.id}`
        : '/api/admin/thresholds/gauges';

      const method = editingGauge ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to save gauge threshold: ${response.statusText}`);
      }

      const savedThreshold = await response.json();

      if (editingGauge) {
        setGaugeThresholds(prev =>
          prev.map(gt => gt.id === editingGauge.id ? savedThreshold : gt)
        );
      } else {
        setGaugeThresholds(prev => [...prev, savedThreshold]);
      }

      setIsGaugeDialogOpen(false);
      setEditingGauge(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save gauge threshold';
      setError(errorMessage);
      console.error('Error saving gauge threshold:', err);
    }
  };

  const handleSaveAlert = async (data: any) => {
    try {
      const url = editingAlert
        ? `/api/admin/alerts/rules/${editingAlert.id}`
        : '/api/admin/alerts/rules';

      const method = editingAlert ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`Failed to save alert rule: ${response.statusText}`);
      }

      const savedRule = await response.json();

      if (editingAlert) {
        setAlertRules(prev =>
          prev.map(ar => ar.id === editingAlert.id ? savedRule : ar)
        );
      } else {
        setAlertRules(prev => [...prev, savedRule]);
      }

      setIsAlertDialogOpen(false);
      setEditingAlert(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save alert rule';
      setError(errorMessage);
      console.error('Error saving alert rule:', err);
    }
  };

  const handleDeleteRisk = async (record: any) => {
    try {
      const response = await fetch(`/api/admin/thresholds/risk/${record.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete risk threshold: ${response.statusText}`);
      }

      setRiskThresholds(prev => prev.filter(rt => rt.id !== record.id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete risk threshold';
      setError(errorMessage);
      console.error('Error deleting risk threshold:', err);
    }
  };

  const handleDeleteGauge = async (record: any) => {
    try {
      const response = await fetch(`/api/admin/thresholds/gauges/${record.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete gauge threshold: ${response.statusText}`);
      }

      setGaugeThresholds(prev => prev.filter(gt => gt.id !== record.id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete gauge threshold';
      setError(errorMessage);
      console.error('Error deleting gauge threshold:', err);
    }
  };

  const handleDeleteAlert = async (record: any) => {
    try {
      const response = await fetch(`/api/admin/alerts/rules/${record.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete alert rule: ${response.statusText}`);
      }

      setAlertRules(prev => prev.filter(ar => ar.id !== record.id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete alert rule';
      setError(errorMessage);
      console.error('Error deleting alert rule:', err);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Threshold Configuration</h1>

      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      <Alert className="mb-6">
        <Info className="h-4 w-4" />
        <AlertDescription>
          Configure risk thresholds, gauge monitoring levels, and automated alert rules for the flood prediction system.
          These settings determine when alerts are triggered and how severe events are classified.
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="risk" className="space-y-6">
        <TabsList>
          <TabsTrigger value="risk">Risk Thresholds</TabsTrigger>
          <TabsTrigger value="gauges">Gauge Thresholds</TabsTrigger>
          <TabsTrigger value="alerts">Alert Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="risk">
          <DataTable
            data={riskThresholds}
            columns={riskColumns}
            title="Risk Band Thresholds"
            description="Configure the risk value ranges for each severity band"
            onAdd={() => {
              setEditingRisk(null);
              setIsRiskDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingRisk(record);
              setIsRiskDialogOpen(true);
            }}
            onDelete={handleDeleteRisk}
            emptyMessage="No risk thresholds configured"
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="gauges">
          <DataTable
            data={gaugeThresholds}
            columns={gaugeColumns}
            title="Gauge Monitoring Thresholds"
            description="Set alert and critical thresholds for water level gauges"
            onAdd={() => {
              setEditingGauge(null);
              setIsGaugeDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingGauge(record);
              setIsGaugeDialogOpen(true);
            }}
            onDelete={handleDeleteGauge}
            emptyMessage="No gauge thresholds configured"
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="alerts">
          <DataTable
            data={alertRules}
            columns={alertColumns}
            title="Automated Alert Rules"
            description="Configure rules for automatic alert generation and notification"
            onAdd={() => {
              setEditingAlert(null);
              setIsAlertDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingAlert(record);
              setIsAlertDialogOpen(true);
            }}
            onDelete={handleDeleteAlert}
            emptyMessage="No alert rules configured"
            loading={loading}
          />
        </TabsContent>
      </Tabs>

      {/* Risk Threshold Dialog */}
      <FormDialog
        open={isRiskDialogOpen}
        onOpenChange={setIsRiskDialogOpen}
        title={editingRisk ? "Edit Risk Threshold" : "Add Risk Threshold"}
        fields={riskFields}
        initialData={editingRisk || { autoAlert: false }}
        onSubmit={handleSaveRisk}
      />

      {/* Gauge Threshold Dialog */}
      <FormDialog
        open={isGaugeDialogOpen}
        onOpenChange={setIsGaugeDialogOpen}
        title={editingGauge ? "Edit Gauge Threshold" : "Add Gauge Threshold"}
        fields={gaugeFields}
        initialData={editingGauge || { unit: 'meters' }}
        onSubmit={handleSaveGauge}
      />

      {/* Alert Rules Dialog */}
      <FormDialog
        open={isAlertDialogOpen}
        onOpenChange={setIsAlertDialogOpen}
        title={editingAlert ? "Edit Alert Rule" : "Add Alert Rule"}
        fields={alertFields}
        initialData={editingAlert || { enabled: true, channels: ['Dashboard'] }}
        onSubmit={handleSaveAlert}
      />
    </div>
  );
}