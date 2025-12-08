import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { MapPin, Save, Edit, Plus, Trash2 } from 'lucide-react';
import type { GeoJSON, ZoneProperties } from '@/types';

interface EditingZone {
  id: string;
  properties: ZoneProperties;
  isNew?: boolean;
}

interface ZonePropertiesProps {
  selectedZoneId: string | null;
  editingZone: EditingZone | null;
  zones: GeoJSON;
  onZoneEdit: (zone: EditingZone) => void;
  onZoneSave: () => void;
  onZoneCancel: () => void;
  onZoneDelete: (zoneId: string) => void;
}

export function ZoneProperties({
  selectedZoneId,
  editingZone,
  zones,
  onZoneEdit,
  onZoneSave,
  onZoneCancel,
  onZoneDelete
}: ZonePropertiesProps) {
  const getZone = (zoneId: string) => {
    return zones.features.find(f => f.properties.id === zoneId);
  };

  if (editingZone) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MapPin className="h-5 w-5 mr-2" />
            Zone Properties
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="zone-name">Zone Name</Label>
              <Input
                id="zone-name"
                value={editingZone.properties.name}
                onChange={(e) => onZoneEdit({
                  ...editingZone,
                  properties: {
                    ...editingZone.properties,
                    name: e.target.value
                  }
                })}
              />
            </div>

            <div>
              <Label htmlFor="zone-id">Zone ID</Label>
              <Input
                id="zone-id"
                value={editingZone.properties.id}
                disabled={!editingZone.isNew}
                onChange={(e) => onZoneEdit({
                  ...editingZone,
                  properties: {
                    ...editingZone.properties,
                    id: e.target.value
                  }
                })}
              />
              {editingZone.isNew && (
                <p className="text-xs text-muted-foreground mt-1">
                  You can edit the ID only for new zones
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="zone-population">Population</Label>
              <Input
                id="zone-population"
                type="number"
                value={editingZone.properties.population}
                onChange={(e) => onZoneEdit({
                  ...editingZone,
                  properties: {
                    ...editingZone.properties,
                    population: parseInt(e.target.value) || 0
                  }
                })}
              />
            </div>

            <div>
              <Label htmlFor="zone-admin-level">Admin Level</Label>
              <Input
                id="zone-admin-level"
                type="number"
                value={editingZone.properties.admin_level}
                onChange={(e) => onZoneEdit({
                  ...editingZone,
                  properties: {
                    ...editingZone.properties,
                    admin_level: parseInt(e.target.value) || 10
                  }
                })}
              />
            </div>

            <div>
              <Label>Critical Assets</Label>
              <div className="space-y-2">
                {editingZone.properties.critical_assets.map((asset, index) => (
                  <div key={index} className="flex space-x-2">
                    <Input
                      value={asset}
                      onChange={(e) => {
                        const newAssets = [...editingZone.properties.critical_assets];
                        newAssets[index] = e.target.value;
                        onZoneEdit({
                          ...editingZone,
                          properties: {
                            ...editingZone.properties,
                            critical_assets: newAssets
                          }
                        });
                      }}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newAssets = editingZone.properties.critical_assets.filter((_, i) => i !== index);
                        onZoneEdit({
                          ...editingZone,
                          properties: {
                            ...editingZone.properties,
                            critical_assets: newAssets
                          }
                        });
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    onZoneEdit({
                      ...editingZone,
                      properties: {
                        ...editingZone.properties,
                        critical_assets: [...editingZone.properties.critical_assets, '']
                      }
                    });
                  }}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add Asset
                </Button>
              </div>
            </div>

            <div className="flex space-x-2">
              <Button onClick={onZoneSave}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
              <Button
                variant="outline"
                onClick={onZoneCancel}
              >
                Cancel
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (selectedZoneId) {
    const zone = getZone(selectedZoneId);
    if (!zone) return null;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MapPin className="h-5 w-5 mr-2" />
            Zone Properties
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium">Name</Label>
              <p className="text-lg">{zone.properties.name}</p>
            </div>

            <div>
              <Label className="text-sm font-medium">Zone ID</Label>
              <p className="font-mono">{zone.properties.id}</p>
            </div>

            <div>
              <Label className="text-sm font-medium">Population</Label>
              <p className="text-lg">{zone.properties.population.toLocaleString()}</p>
            </div>

            <div>
              <Label className="text-sm font-medium">Critical Assets</Label>
              <div className="space-y-1">
                {zone.properties.critical_assets.map((asset, index) => (
                  <Badge key={index} variant="secondary" className="mr-1">
                    {asset}
                  </Badge>
                ))}
              </div>
            </div>

            <Button
              onClick={() => onZoneEdit({
                id: zone.properties.id,
                properties: { ...zone.properties }
              })}
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit Zone
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <MapPin className="h-5 w-5 mr-2" />
          Zone Properties
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center text-muted-foreground py-8">
          <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select a zone to view its properties</p>
          <p className="text-sm mt-2">Or click "Draw Zone" and use the rectangle tool to create a new zone</p>
          <div className="mt-4 p-3 bg-muted rounded-lg text-left max-w-xs mx-auto">
            <p className="text-xs font-medium mb-2">How to create a zone:</p>
            <ol className="text-xs space-y-1 list-decimal list-inside">
              <li>Click "Draw Zone" button</li>
              <li>Select the rectangle tool from the toolbar</li>
              <li>Click and drag on the map to draw a rectangle</li>
              <li>Double-click to finish drawing</li>
              <li>Edit zone properties in this panel</li>
            </ol>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}