import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DataTable } from '@/components/DataTable';
import { FormDialog, FormField } from '@/components/Forms/FormDialog';
import { EquipmentStatus, CrewStatus } from '@/types';
import { Package, Users, MapPin, Plus, Edit, Trash2, Wrench, Truck, AlertTriangle, Info } from 'lucide-react';
import { buildApiUrl } from '@/lib/apiBase';


// API data types
interface Depot {
  id: string;
  name: string;
  lat: number;
  lng: number;
  address?: string;
  capacity?: number;
  manager?: string;
  phone?: string;
  operatingHours?: string;
  zones?: string[];
  status?: string;
}

interface Equipment {
  id: string;
  type: string;
  subtype?: string;
  capacity_lps?: number;
  units?: number;
  depot: string;
  status: EquipmentStatus;
  serialNumber?: string;
  manufacturer?: string;
  model?: string;
}

interface Crew {
  id: string;
  name: string;
  skills: string[];
  depot: string;
  status: CrewStatus;
  lat?: number;
  lng?: number;
  teamSize?: number;
  leader?: string;
  phone?: string;
  certifications?: string[];
}


export function AdminResources() {
  const [depots, setDepots] = useState<Depot[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [crews, setCrews] = useState<Crew[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch resources data from API
  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch from admin endpoints
        const [depotsResponse, equipmentResponse, crewsResponse] = await Promise.all([
          fetch(buildApiUrl('/admin/resources/depots')),
          fetch(buildApiUrl('/admin/resources/equipment')),
          fetch(buildApiUrl('/admin/resources/crews'))
        ]);

        if (!depotsResponse.ok || !equipmentResponse.ok || !crewsResponse.ok) {
          throw new Error(`Failed to fetch resources`);
        }

        const [depotsData, equipmentData, crewsData] = await Promise.all([
          depotsResponse.json(),
          equipmentResponse.json(),
          crewsResponse.json()
        ]);

        setDepots(depotsData || []);
        setEquipment(equipmentData || []);
        setCrews(crewsData || []);

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load resources data';
        setError(errorMessage);
        console.error('Error fetching resources:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchResources();
  }, []);

  const [isDepotDialogOpen, setIsDepotDialogOpen] = useState(false);
  const [isEquipmentDialogOpen, setIsEquipmentDialogOpen] = useState(false);
  const [isCrewDialogOpen, setIsCrewDialogOpen] = useState(false);

  const [editingDepot, setEditingDepot] = useState<any>(null);
  const [editingEquipment, setEditingEquipment] = useState<any>(null);
  const [editingCrew, setEditingCrew] = useState<any>(null);

  // Form Fields
  const depotFields: FormField[] = [
    { key: 'name', label: 'Depot Name', type: 'text', required: true },
    { key: 'address', label: 'Address', type: 'text', required: true },
    { key: 'manager', label: 'Manager Name', type: 'text', required: true },
    { key: 'phone', label: 'Phone', type: 'text', required: true },
    {
      key: 'capacity',
      label: 'Capacity',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 0) return 'Capacity must be positive';
        return null;
      },
    },
    { key: 'operatingHours', label: 'Operating Hours', type: 'text', placeholder: '24/7 or 06:00-22:00' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'maintenance', label: 'Under Maintenance' },
      ],
    },
    { key: 'zones', label: 'Service Zones', type: 'tags', placeholder: 'Add zone ID...' },
  ];

  const equipmentFields: FormField[] = [
    { key: 'type', label: 'Equipment Type', type: 'text', required: true },
    { key: 'subtype', label: 'Subtype', type: 'text' },
    {
      key: 'depot',
      label: 'Depot',
      type: 'select',
      required: true,
      options: depots.map(d => ({ value: d.id, label: d.name })),
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { value: 'available', label: 'Available' },
        { value: 'deployed', label: 'Deployed' },
        { value: 'maintenance', label: 'Maintenance' },
      ],
    },
    { key: 'serialNumber', label: 'Serial Number', type: 'text' },
    { key: 'manufacturer', label: 'Manufacturer', type: 'text' },
    { key: 'model', label: 'Model', type: 'text' },
    {
      key: 'capacity_lps',
      label: 'Capacity (LPS)',
      type: 'number',
      validation: (value) => {
        const num = Number(value);
        if (num < 0) return 'Capacity must be positive';
        return null;
      },
    },
    { key: 'units', label: 'Units', type: 'number' },
  ];

  const crewFields: FormField[] = [
    { key: 'name', label: 'Crew Name', type: 'text', required: true },
    { key: 'leader', label: 'Crew Leader', type: 'text', required: true },
    { key: 'phone', label: 'Contact Phone', type: 'text', required: true },
    {
      key: 'teamSize',
      label: 'Team Size',
      type: 'number',
      required: true,
      validation: (value) => {
        const num = Number(value);
        if (num < 1 || num > 20) return 'Team size must be between 1 and 20';
        return null;
      },
    },
    {
      key: 'depot',
      label: 'Home Depot',
      type: 'select',
      required: true,
      options: depots.map(d => ({ value: d.id, label: d.name })),
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      required: true,
      options: [
        { value: 'ready', label: 'Ready' },
        { value: 'working', label: 'Working' },
        { value: 'rest', label: 'Rest' },
        { value: 'enroute', label: 'En Route' },
      ],
    },
    { key: 'skills', label: 'Skills', type: 'tags', placeholder: 'Add skill...' },
    { key: 'experience', label: 'Experience', type: 'text', placeholder: '3 years' },
    { key: 'certifications', label: 'Certifications', type: 'tags', placeholder: 'Add certification...' },
  ];

  // Table Columns
  const depotColumns = [
    {
      key: 'name',
      title: 'Depot Name',
      sortable: true,
      render: (value: string, record: any) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-sm text-muted-foreground">{record.id}</div>
        </div>
      ),
    },
    { key: 'address', title: 'Address', sortable: true },
    { key: 'manager', title: 'Manager', sortable: true },
    {
      key: 'capacity',
      title: 'Capacity',
      sortable: true,
      render: (value: number) => `${value} units`,
    },
    {
      key: 'status',
      title: 'Status',
      render: (value: string) => {
        const colors = {
          active: 'bg-green-100 text-green-800',
          inactive: 'bg-gray-100 text-gray-800',
          maintenance: 'bg-orange-100 text-orange-800',
        };
        return (
          <Badge className={colors[value as keyof typeof colors]}>
            {value}
          </Badge>
        );
      },
    },
    {
      key: 'zones',
      title: 'Service Zones',
      render: (value: string[]) => (
        <div className="flex flex-wrap gap-1">
          {value?.map((zone) => (
            <Badge key={zone} variant="outline" className="text-xs">
              {zone}
            </Badge>
          ))}
        </div>
      ),
    },
  ];

  const equipmentColumns = [
    {
      key: 'id',
      title: 'Equipment',
      render: (value: string, record: any) => (
        <div>
          <div className="font-medium">{record.type}</div>
          <div className="text-sm text-muted-foreground">{value}</div>
          {record.subtype && (
            <div className="text-xs text-muted-foreground">{record.subtype}</div>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      render: (value: EquipmentStatus) => {
        const colors = {
          available: 'bg-green-100 text-green-800',
          deployed: 'bg-blue-100 text-blue-800',
          maintenance: 'bg-orange-100 text-orange-800',
        };
        const icons = {
          available: <Package className="h-3 w-3" />,
          deployed: <Truck className="h-3 w-3" />,
          maintenance: <Wrench className="h-3 w-3" />,
        };
        return (
          <Badge className={colors[value]}>
            {icons[value]} <span className="ml-1">{value}</span>
          </Badge>
        );
      },
    },
    {
      key: 'depot',
      title: 'Location',
      render: (value: string) => {
        const depot = depots.find(d => d.id === value);
        return depot ? depot.name : value;
      },
    },
    {
      key: 'capacity_lps',
      title: 'Capacity',
      render: (value: number, record: any) => {
        if (value) return `${value} LPS`;
        if (record.units) return `${record.units} units`;
        return 'N/A';
      },
    },
    { key: 'manufacturer', title: 'Manufacturer' },
    { key: 'model', title: 'Model' },
  ];

  const crewColumns = [
    {
      key: 'name',
      title: 'Crew',
      render: (value: string, record: any) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-sm text-muted-foreground">Leader: {record.leader}</div>
          <div className="text-xs text-muted-foreground">{record.id}</div>
        </div>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      render: (value: CrewStatus) => {
        const colors = {
          ready: 'bg-green-100 text-green-800',
          working: 'bg-blue-100 text-blue-800',
          rest: 'bg-yellow-100 text-yellow-800',
          enroute: 'bg-purple-100 text-purple-800',
        };
        return (
          <Badge className={colors[value]}>
            {value}
          </Badge>
        );
      },
    },
    {
      key: 'teamSize',
      title: 'Team',
      sortable: true,
      render: (value: number) => `${value} members`,
    },
    {
      key: 'depot',
      title: 'Home Depot',
      render: (value: string) => {
        const depot = depots.find(d => d.id === value);
        return depot ? depot.name : value;
      },
    },
    {
      key: 'skills',
      title: 'Skills',
      render: (value: string[]) => (
        <div className="flex flex-wrap gap-1">
          {value?.slice(0, 3).map((skill) => (
            <Badge key={skill} variant="secondary" className="text-xs">
              {skill.replace('_', ' ')}
            </Badge>
          ))}
          {value?.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{value.length - 3} more
            </Badge>
          )}
        </div>
      ),
    },
    {
      key: 'experience',
      title: 'Experience',
      sortable: true,
    },
  ];

  // Event Handlers
  const handleSaveDepot = (data: any) => {
    if (editingDepot) {
      setDepots(prev =>
        prev.map(d => d.id === editingDepot.id ? { ...data, id: editingDepot.id } : d)
      );
    } else {
      const newDepot = { ...data, id: `D-${Date.now()}` };
      setDepots(prev => [...prev, newDepot]);
    }
    setIsDepotDialogOpen(false);
    setEditingDepot(null);
  };

  const handleSaveEquipment = (data: any) => {
    if (editingEquipment) {
      setEquipment(prev =>
        prev.map(e => e.id === editingEquipment.id ? { ...data, id: editingEquipment.id } : e)
      );
    } else {
      const newEquipment = { ...data, id: `${data.type[0]}-${Date.now()}` };
      setEquipment(prev => [...prev, newEquipment]);
    }
    setIsEquipmentDialogOpen(false);
    setEditingEquipment(null);
  };

  const handleSaveCrew = (data: any) => {
    if (editingCrew) {
      setCrews(prev =>
        prev.map(c => c.id === editingCrew.id ? { ...data, id: editingCrew.id } : c)
      );
    } else {
      const newCrew = {
        ...data,
        id: `C-${Date.now()}`,
        lat: 38.6270,
        lng: -90.1994,
      };
      setCrews(prev => [...prev, newCrew]);
    }
    setIsCrewDialogOpen(false);
    setEditingCrew(null);
  };

  // Resource Statistics
  const activeDepots = depots.filter(d => d.status === 'active').length;
  const availableEquipment = equipment.filter(e => e.status === 'available').length;
  const readyCrews = crews.filter(c => c.status === 'ready').length;
  const workingCrews = crews.filter(c => c.status === 'working').length;

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Resource Management</h1>

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
          Manage depots, equipment, and crews for flood response operations. Track availability,
          maintenance schedules, and deployment status of all resources.
        </AlertDescription>
      </Alert>

      {/* Resource Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center">
              <MapPin className="h-4 w-4 mr-2" />
              Active Depots
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{activeDepots}</div>
            <p className="text-xs text-muted-foreground">of {depots.length} total depots</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center">
              <Package className="h-4 w-4 mr-2" />
              Available Equipment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{availableEquipment}</div>
            <p className="text-xs text-muted-foreground">of {equipment.length} total items</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center">
              <Users className="h-4 w-4 mr-2" />
              Ready Crews
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{readyCrews}</div>
            <p className="text-xs text-muted-foreground">available for deployment</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Working Crews
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{workingCrews}</div>
            <p className="text-xs text-muted-foreground">currently deployed</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="depots" className="space-y-6">
        <TabsList>
          <TabsTrigger value="depots">Depots</TabsTrigger>
          <TabsTrigger value="equipment">Equipment</TabsTrigger>
          <TabsTrigger value="crews">Crews</TabsTrigger>
        </TabsList>

        <TabsContent value="depots">
          <DataTable
            data={depots}
            columns={depotColumns}
            title="Depot Locations"
            description="Manage depot locations and their service areas"
            onAdd={() => {
              setEditingDepot(null);
              setIsDepotDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingDepot(record);
              setIsDepotDialogOpen(true);
            }}
            onDelete={(record) => setDepots(prev => prev.filter(d => d.id !== record.id))}
            emptyMessage="No depots configured"
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="equipment">
          <DataTable
            data={equipment}
            columns={equipmentColumns}
            title="Equipment Inventory"
            description="Manage equipment status and maintenance schedules"
            onAdd={() => {
              setEditingEquipment(null);
              setIsEquipmentDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingEquipment(record);
              setIsEquipmentDialogOpen(true);
            }}
            onDelete={(record) => setEquipment(prev => prev.filter(e => e.id !== record.id))}
            emptyMessage="No equipment in inventory"
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="crews">
          <DataTable
            data={crews}
            columns={crewColumns}
            title="Response Crews"
            description="Manage crew assignments, skills, and availability"
            onAdd={() => {
              setEditingCrew(null);
              setIsCrewDialogOpen(true);
            }}
            onEdit={(record) => {
              setEditingCrew(record);
              setIsCrewDialogOpen(true);
            }}
            onDelete={(record) => setCrews(prev => prev.filter(c => c.id !== record.id))}
            emptyMessage="No crews configured"
            loading={loading}
          />
        </TabsContent>
      </Tabs>

      {/* Form Dialogs */}
      <FormDialog
        open={isDepotDialogOpen}
        onOpenChange={setIsDepotDialogOpen}
        title={editingDepot ? "Edit Depot" : "Add New Depot"}
        fields={depotFields}
        initialData={editingDepot || { status: 'active', zones: [] }}
        onSubmit={handleSaveDepot}
      />

      <FormDialog
        open={isEquipmentDialogOpen}
        onOpenChange={setIsEquipmentDialogOpen}
        title={editingEquipment ? "Edit Equipment" : "Add New Equipment"}
        fields={equipmentFields}
        initialData={editingEquipment || { status: 'available' }}
        onSubmit={handleSaveEquipment}
      />

      <FormDialog
        open={isCrewDialogOpen}
        onOpenChange={setIsCrewDialogOpen}
        title={editingCrew ? "Edit Crew" : "Add New Crew"}
        fields={crewFields}
        initialData={editingCrew || { status: 'ready', skills: [], certifications: [] }}
        onSubmit={handleSaveCrew}
      />
    </div>
  );
}
