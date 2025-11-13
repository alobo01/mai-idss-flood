import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAppContext } from '@/contexts/AppContext';
import { Role } from '@/types';
import {
  MapPin,
  Settings,
  BarChart3,
  Radio,
} from 'lucide-react';

const roleConfig = {
  Administrator: {
    icon: Settings,
    description: 'Configure regions, resources, thresholds, and users',
    color: 'bg-blue-500',
    capabilities: ['Zone Management', 'Resource Configuration', 'Threshold Rules', 'User Management']
  },
  Planner: {
    icon: MapPin,
    description: 'Review predictions, create scenarios, and propose response plans',
    color: 'bg-green-500',
    capabilities: ['Risk Analysis', 'Scenario Planning', 'Plan Drafting', 'Alert Management']
  },
  Coordinator: {
    icon: Radio,
    description: 'Execute approved plans and manage live operations',
    color: 'bg-orange-500',
    capabilities: ['Live Operations', 'Crew Management', 'Communications', 'Resource Allocation']
  },
  'Data Analyst': {
    icon: BarChart3,
    description: 'Analyze model outputs, damage indices, and export data',
    color: 'bg-purple-500',
    capabilities: ['Data Analysis', 'Export Tools', 'Layer Analysis', 'Impact Assessment']
  }
};

export function RoleSelector() {
  const { setCurrentRole, darkMode } = useAppContext();

  const handleRoleSelect = (role: Role) => {
    setCurrentRole(role);
  };

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${
      darkMode ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Flood Prediction System
          </h1>
          <p className="text-xl text-muted-foreground">
            Select your role to continue
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(roleConfig).map(([role, config]) => {
            const Icon = config.icon;
            return (
              <Card key={role} className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${config.color} text-white`}>
                        <Icon className="h-6 w-6" />
                      </div>
                      <CardTitle className="text-xl">{role}</CardTitle>
                    </div>
                  </div>
                  <CardDescription className="text-sm">
                    {config.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2 text-sm">Key Capabilities:</h4>
                    <div className="flex flex-wrap gap-1">
                      {config.capabilities.map((capability) => (
                        <Badge key={capability} variant="secondary" className="text-xs">
                          {capability}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button
                    onClick={() => handleRoleSelect(role as Role)}
                    className="w-full"
                  >
                    Select {role}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            This is a demo application. All data is mocked for demonstration purposes.
          </p>
        </div>
      </div>
    </div>
  );
}