import React, { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Save,
  Download,
  Upload,
  Trash2,
  Edit,
  Plus,
  MapPin,
  Users,
  Building,
  AlertTriangle,
  Square
} from 'lucide-react';
import type { GeoJSON as GeoJSONType, ZoneProperties, GeoJSONFeature } from '@/types';
import { fixLeafletIcons } from '@/lib/leaflet-config';

// Initialize Leaflet icons (CSS is imported in main.tsx)
import 'leaflet-draw/dist/leaflet.draw.css';
fixLeafletIcons();

// Validation functions
const validateZoneId = (id: string, existingIds: string[]): string[] => {
  const errors: string[] = [];

  if (!id || id.trim() === '') {
    errors.push('Zone ID is required');
  }

  if (!/^[A-Za-z][A-Za-z0-9_-]*$/.test(id)) {
    errors.push('Zone ID must start with a letter and contain only letters, numbers, underscores, and hyphens');
  }

  if (existingIds.includes(id)) {
    errors.push('Zone ID must be unique');
  }

  return errors;
};

const validateZoneProperties = (properties: ZoneProperties): string[] => {
  const errors: string[] = [];

  if (!properties.name || properties.name.trim() === '') {
    errors.push('Zone name is required');
  }

  if (properties.population < 0) {
    errors.push('Population must be a non-negative number');
  }

  if (properties.admin_level < 1 || properties.admin_level > 15) {
    errors.push('Admin level must be between 1 and 15');
  }

  if (properties.critical_assets.some(asset => !asset || asset.trim() === '')) {
    errors.push('Critical asset names cannot be empty');
  }

  return errors;
};

const validateGeoJSONFeature = (feature: any): string[] => {
  const errors: string[] = [];

  if (feature.type !== 'Feature') {
    errors.push('Invalid GeoJSON feature type');
  }

  if (!feature.properties) {
    errors.push('Feature properties are required');
  }

  if (!feature.geometry) {
    errors.push('Feature geometry is required');
  }

  if (feature.geometry.type !== 'Polygon') {
    errors.push('Only Polygon geometry is supported');
  }

  if (!feature.geometry.coordinates || !Array.isArray(feature.geometry.coordinates)) {
    errors.push('Invalid polygon coordinates');
  }

  return errors;
};

interface ZoneEditorProps {
  initialZones?: GeoJSONType;
  onZonesChange?: (zones: GeoJSONType) => void;
  onValidationError?: (errors: string[]) => void;
  className?: string;
}

interface EditingZone {
  id: string;
  properties: ZoneProperties;
  isNew?: boolean;
}

export function ZoneEditor({
  initialZones,
  onZonesChange,
  onValidationError,
  className = ''
}: ZoneEditorProps) {
  const [zones, setZones] = useState<GeoJSONType>(initialZones || {
    type: "FeatureCollection",
    features: []
  });

  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [editingZone, setEditingZone] = useState<EditingZone | null>(null);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const mapRef = useRef<L.Map | null>(null);
  const drawnItemsRef = useRef<L.FeatureGroup | null>(null);
  const drawControlRef = useRef<L.Control.Draw | null>(null);

  // Update zones when initialZones prop changes
  useEffect(() => {
    if (initialZones) {
      setZones(initialZones);
    }
  }, [initialZones]);

  // Notify parent of zone changes
  useEffect(() => {
    if (onZonesChange) {
      onZonesChange(zones);
    }
  }, [zones, onZonesChange]);

  // Initialize drawing controls when map is ready
  useEffect(() => {
    if (!mapRef.current || drawnItemsRef.current) return;

    const map = mapRef.current;
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    drawnItemsRef.current = drawnItems;

    // Add existing zones to drawn items for editing
    zones.features.forEach(feature => {
      const layer = L.geoJSON(feature.geometry as any, {
        style: {
          color: '#3388ff',
          weight: 2,
          fillOpacity: 0.2
        }
      });

      layer.eachLayer((l) => {
        (l as any).feature = feature;
        drawnItems.addLayer(l);
      });
    });

    return () => {
      if (map && drawnItems) {
        map.removeLayer(drawnItems);
      }
    };
  }, [mapRef.current, zones]);

  // Generate unique zone ID
  const generateZoneId = (): string => {
    const existingIds = zones.features.map(f => f.properties.id);
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let counter = 0;

    while (counter < 26) {
      const id = `Z-${letters[counter]}`;
      if (!existingIds.includes(id)) {
        return id;
      }
      counter++;
    }

    // If all single letters are used, use double letters
    let suffix = 1;
    while (true) {
      const id = `Z-${letters[0]}${suffix}`;
      if (!existingIds.includes(id)) {
        return id;
      }
      suffix++;
    }
  };

  // Toggle drawing mode
  const toggleDrawingMode = () => {
    if (!mapRef.current) return;

    if (isDrawingMode) {
      // Exit drawing mode
      setIsDrawingMode(false);
      if (drawControlRef.current) {
        mapRef.current.removeControl(drawControlRef.current);
        drawControlRef.current = null;
      }
    } else {
      // Enter drawing mode
      setIsDrawingMode(true);

      if (drawnItemsRef.current) {
        const drawControl = new L.Control.Draw({
          draw: {
            polygon: {
              allowIntersection: false,
              showArea: true,
              drawError: {
                color: '#e1e100',
                message: '<strong>Error:</strong> Shape edges cannot cross!'
              },
              shapeOptions: {
                color: '#3b82f6',
                weight: 3,
                fillOpacity: 0.3,
                fillColor: '#3b82f6'
              }
            },
            polyline: false,
            circle: false,
            circlemarker: false,
            rectangle: {
              showArea: true,
              shapeOptions: {
                color: '#10b981',
                weight: 3,
                fillOpacity: 0.3,
                fillColor: '#10b981'
              }
            },
            marker: false
          },
          edit: {
            featureGroup: drawnItemsRef.current,
            remove: true,
            edit: {
              selectedPathOptions: {
                color: '#f59e0b',
                weight: 3,
                fillOpacity: 0.4,
                fillColor: '#f59e0b'
              }
            }
          }
        });

        mapRef.current.addControl(drawControl);
        drawControlRef.current = drawControl;

        // Handle draw events
        mapRef.current.on(L.Draw.Event.CREATED, handleCreated);
        mapRef.current.on(L.Draw.Event.EDITED, handleEdited);
        mapRef.current.on(L.Draw.Event.DELETED, handleDeleted);
      }
    }
  };

  // Handle feature creation from drawing
  const handleCreated = (e: any) => {
    if (!mapRef.current || !drawnItemsRef.current) return;

    const { layerType, layer } = e;

    if (layerType === 'polygon' || layerType === 'rectangle') {
      const geojson = layer.toGeoJSON();
      const newZoneId = generateZoneId();

      const newFeature: any = {
        type: "Feature",
        properties: {
          id: newZoneId,
          name: `New Zone ${newZoneId}`,
          population: 0,
          critical_assets: [],
          admin_level: 10
        },
        geometry: geojson.geometry
      };

      // Add feature to layer for identification
      (layer as any).feature = newFeature;

      drawnItemsRef.current.addLayer(layer);

      const updatedZones = {
        ...zones,
        features: [...zones.features, newFeature]
      };

      setZones(updatedZones);
      setSelectedZoneId(newZoneId);
      setEditingZone({
        id: newZoneId,
        properties: newFeature.properties,
        isNew: true
      });

      // Exit drawing mode after creating a zone
      toggleDrawingMode();
    }
  };

  // Handle feature editing
  const handleEdited = (e: any) => {
    if (!drawnItemsRef.current) return;

    const { layers } = e;
    const updatedFeatures = [...zones.features];

    layers.eachLayer((layer: any) => {
      if (layer.feature) {
        const geojson = layer.toGeoJSON();
        const featureIndex = updatedFeatures.findIndex(
          f => f.properties.id === layer.feature.properties.id
        );

        if (featureIndex !== -1) {
          updatedFeatures[featureIndex] = {
            ...updatedFeatures[featureIndex],
            geometry: geojson.geometry
          };
        }
      }
    });

    setZones({
      ...zones,
      features: updatedFeatures
    });
  };

  // Handle feature deletion
  const handleDeleted = (e: any) => {
    if (!drawnItemsRef.current) return;

    const { layers } = e;
    const deletedIds: string[] = [];

    layers.eachLayer((layer: any) => {
      if (layer.feature?.properties?.id) {
        deletedIds.push(layer.feature.properties.id);
      }
    });

    const updatedFeatures = zones.features.filter(
      f => !deletedIds.includes(f.properties.id)
    );

    setZones({
      ...zones,
      features: updatedFeatures
    });

    if (selectedZoneId && deletedIds.includes(selectedZoneId)) {
      setSelectedZoneId(null);
      setEditingZone(null);
    }
  };

  // Save zone properties
  const saveZoneProperties = () => {
    if (!editingZone) return;

    // Validate zone properties
    const existingIds = zones.features
      .filter(f => f.properties.id !== editingZone.id)
      .map(f => f.properties.id);

    const errors = [
      ...validateZoneId(editingZone.properties.id, existingIds),
      ...validateZoneProperties(editingZone.properties)
    ];

    if (errors.length > 0) {
      setValidationErrors(errors);
      if (onValidationError) {
        onValidationError(errors);
      }
      return;
    }

    const updatedFeatures = zones.features.map(feature => {
      if (feature.properties.id === editingZone.id) {
        return {
          ...feature,
          properties: editingZone.properties
        };
      }
      return feature;
    });

    // Update the feature in the drawn layers as well
    if (drawnItemsRef.current) {
      drawnItemsRef.current.eachLayer((layer: any) => {
        if (layer.feature?.properties?.id === editingZone.id) {
          layer.feature.properties = editingZone.properties;
        }
      });
    }

    setZones({
      ...zones,
      features: updatedFeatures
    });

    setEditingZone(null);
    setValidationErrors([]);
  };

  // Delete zone
  const deleteZone = (zoneId: string) => {
    const updatedFeatures = zones.features.filter(f => f.properties.id !== zoneId);

    // Remove from drawn layers
    if (drawnItemsRef.current) {
      drawnItemsRef.current.eachLayer((layer: any) => {
        if (layer.feature?.properties?.id === zoneId) {
          drawnItemsRef.current?.removeLayer(layer);
        }
      });
    }

    setZones({
      ...zones,
      features: updatedFeatures
    });

    if (selectedZoneId === zoneId) {
      setSelectedZoneId(null);
      setEditingZone(null);
    }
  };

  // Handle file import
  const handleImport = async () => {
    if (!importFile) return;

    try {
      const text = await importFile.text();
      const importedData = JSON.parse(text);

      if (importedData.type !== "FeatureCollection") {
        throw new Error('Invalid GeoJSON: must be a FeatureCollection');
      }

      if (!importedData.features || !Array.isArray(importedData.features)) {
        throw new Error('Invalid GeoJSON: features array is required');
      }

      // Validate all features
      const errors: string[] = [];
      const zoneIds: string[] = [];

      importedData.features.forEach((feature: any, index: number) => {
        const featureErrors = validateGeoJSONFeature(feature);
        featureErrors.forEach(error => {
          errors.push(`Feature ${index + 1}: ${error}`);
        });

        if (feature.properties && feature.properties.id) {
          if (zoneIds.includes(feature.properties.id)) {
            errors.push(`Feature ${index + 1}: Duplicate zone ID '${feature.properties.id}'`);
          }
          zoneIds.push(feature.properties.id);
        }

        if (feature.properties) {
          const propErrors = validateZoneProperties(feature.properties);
          propErrors.forEach(error => {
            errors.push(`Feature ${index + 1}: ${error}`);
          });
        }
      });

      if (errors.length > 0) {
        setValidationErrors(errors);
        if (onValidationError) {
          onValidationError(errors);
        }
        return;
      }

      setZones(importedData);
      setIsImportDialogOpen(false);
      setImportFile(null);
      setValidationErrors([]);

      // Update drawn layers
      if (drawnItemsRef.current && mapRef.current) {
        drawnItemsRef.current.clearLayers();

        importedData.features.forEach(feature => {
          const layer = L.geoJSON(feature.geometry as any, {
            style: {
              color: '#3388ff',
              weight: 2,
              fillOpacity: 0.2
            }
          });

          layer.eachLayer((l) => {
            (l as any).feature = feature;
            drawnItemsRef.current?.addLayer(l);
          });
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error importing GeoJSON file';
      setValidationErrors([errorMessage]);
      if (onValidationError) {
        onValidationError([errorMessage]);
      }
      console.error('Import error:', error);
    }
  };

  // Handle file export
  const handleExport = () => {
    const dataStr = JSON.stringify(zones, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `zones-${new Date().toISOString().split('T')[0]}.geojson`;
    link.click();

    URL.revokeObjectURL(url);
    setIsExportDialogOpen(false);
  };

  // Get zone by ID
  const getZone = (zoneId: string) => {
    return zones.features.find(f => f.properties.id === zoneId);
  };

  // Zone style
  const getZoneStyle = (feature: any) => {
    const isSelected = feature.properties.id === selectedZoneId;
    return {
      fillColor: isSelected ? '#3b82f6' : '#6b7280',
      weight: isSelected ? 3 : 2,
      opacity: 1,
      color: isSelected ? '#1e40af' : 'white',
      fillOpacity: isSelected ? 0.5 : 0.3,
    };
  };

  // Handle zone click
  const handleZoneClick = (feature: any, layer: any) => {
    const zoneId = feature.properties.id;
    setSelectedZoneId(zoneId);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <h3 className="font-semibold text-red-900">Validation Errors</h3>
            </div>
            <ul className="text-sm text-red-800 space-y-1">
              {validationErrors.map((error, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {error}
                </li>
              ))}
            </ul>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setValidationErrors([])}
              className="mt-3"
            >
              Dismiss
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Zone List Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Zones ({zones.features.length})
                <div className="flex space-x-1">
                  <Dialog open={isImportDialogOpen} onOpenChange={setIsImportDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Upload className="h-4 w-4 mr-1" />
                        Import
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Import GeoJSON</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="file">Select GeoJSON file</Label>
                          <Input
                            id="file"
                            type="file"
                            accept=".json,.geojson"
                            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                          />
                        </div>
                        <div className="flex justify-end space-x-2">
                          <Button variant="outline" onClick={() => setIsImportDialogOpen(false)}>
                            Cancel
                          </Button>
                          <Button onClick={handleImport} disabled={!importFile}>
                            Import
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Dialog open={isExportDialogOpen} onOpenChange={setIsExportDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-1" />
                        Export
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Export GeoJSON</DialogTitle>
                      </DialogHeader>
                      <p className="text-sm text-muted-foreground">
                        Export {zones.features.length} zones to GeoJSON file
                      </p>
                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={() => setIsExportDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleExport}>
                          <Download className="h-4 w-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-2">
                  {zones.features.map((zone) => (
                    <div
                      key={zone.properties.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedZoneId === zone.properties.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedZoneId(zone.properties.id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{zone.properties.name}</span>
                        <Badge variant="secondary">{zone.properties.id}</Badge>
                      </div>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex items-center">
                          <Users className="h-3 w-3 mr-1" />
                          {zone.properties.population.toLocaleString()}
                        </div>
                        <div className="flex items-center">
                          <Building className="h-3 w-3 mr-1" />
                          {zone.properties.critical_assets.length} assets
                        </div>
                      </div>
                      <div className="flex space-x-1 mt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingZone({
                              id: zone.properties.id,
                              properties: { ...zone.properties }
                            });
                          }}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteZone(zone.properties.id);
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Map Area */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div>
                  Zone Map
                  {isDrawingMode && (
                    <p className="text-sm text-muted-foreground font-normal mt-1">
                      Click the rectangle tool and drag to draw a new zone
                    </p>
                  )}
                </div>
                <Button
                  onClick={toggleDrawingMode}
                  variant={isDrawingMode ? "default" : "outline"}
                  className={isDrawingMode ? "bg-green-600 hover:bg-green-700" : ""}
                >
                  <Square className="h-4 w-4 mr-2" />
                  {isDrawingMode ? "Exit Drawing" : "Draw Zone"}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-[600px]">
                <MapContainer
                  ref={mapRef}
                  center={[40.4167, -3.7033]}
                  zoom={12}
                  className="h-full w-full"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />

                  {/* Render existing zones */}
                  <GeoJSON
                    data={zones as any}
                    style={getZoneStyle}
                    onEachFeature={(feature, layer) => {
                      layer.on({
                        click: () => handleZoneClick(feature, layer)
                      });

                      if (feature.properties.id === selectedZoneId) {
                        layer.bindPopup(`
                          <div class="p-2">
                            <h3 class="font-semibold">${feature.properties.name}</h3>
                            <p class="text-sm">ID: ${feature.properties.id}</p>
                            <p class="text-sm">Population: ${feature.properties.population.toLocaleString()}</p>
                          </div>
                        `).openPopup();
                      }
                    }}
                  />
                </MapContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Properties Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <MapPin className="h-5 w-5 mr-2" />
                Zone Properties
              </CardTitle>
            </CardHeader>
            <CardContent>
              {editingZone ? (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="zone-name">Zone Name</Label>
                    <Input
                      id="zone-name"
                      value={editingZone.properties.name}
                      onChange={(e) => setEditingZone({
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
                      onChange={(e) => setEditingZone({
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
                      onChange={(e) => setEditingZone({
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
                      onChange={(e) => setEditingZone({
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
                              setEditingZone({
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
                              setEditingZone({
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
                          setEditingZone({
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
                    <Button onClick={saveZoneProperties}>
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setEditingZone(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : selectedZoneId ? (
                <div className="space-y-4">
                  {(() => {
                    const zone = getZone(selectedZoneId);
                    if (!zone) return null;

                    return (
                      <>
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
                          onClick={() => setEditingZone({
                            id: zone.properties.id,
                            properties: { ...zone.properties }
                          })}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit Zone
                        </Button>
                      </>
                    );
                  })()}
                </div>
              ) : (
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
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}