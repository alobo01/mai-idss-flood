
import { useState, useEffect } from 'react';
import { ZoneEditor } from '@/components/ZoneEditor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Info } from 'lucide-react';
import type { GeoJSON } from '@/types';

export function AdminRegions() {
  const [zones, setZones] = useState<GeoJSON | null>(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  // Load initial zones data
  useEffect(() => {
    const loadZones = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/zones');

        if (!response.ok) {
          throw new Error(`Failed to load zones: ${response.statusText}`);
        }

        const zonesData = await response.json();
        setZones(zonesData);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to load zones data';
        setErrors([errorMessage]);
        console.error('Error loading zones:', error);
      } finally {
        setLoading(false);
      }
    };

    loadZones();
  }, []);

  // Handle zone changes
  const handleZonesChange = (updatedZones: GeoJSON) => {
    setZones(updatedZones);
    // Here you could implement saving to backend
    console.log('Zones updated:', updatedZones);
  };

  // Handle validation errors
  const handleValidationErrors = (validationErrors: string[]) => {
    setErrors(validationErrors);
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Regions Manager</h1>

      {/* Information Card */}
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Zone Management</h3>
              <p className="text-sm text-blue-800">
                Use the interactive map editor to create, edit, and manage flood prediction zones.
                Draw new zones, edit existing boundaries, and configure zone properties like population
                and critical infrastructure assets.
              </p>
              <div className="mt-2 text-xs text-blue-700">
                <strong>Features:</strong> Drawing tools • Zone property editing • Import/Export GeoJSON • Real-time validation
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {errors.length > 0 && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 mb-2">Error</h3>
                <ul className="text-sm text-red-800 space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Zone Editor */}
      {loading ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading zones data...</p>
            </div>
          </CardContent>
        </Card>
      ) : zones ? (
        <ZoneEditor
          initialZones={zones}
          onZonesChange={handleZonesChange}
          onValidationError={handleValidationErrors}
        />
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Failed to load zones data</p>
              <p className="text-sm mt-2">Please refresh the page to try again</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}