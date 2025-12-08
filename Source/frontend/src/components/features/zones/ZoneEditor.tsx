import React, { useState, useRef, useEffect } from 'react';
import L from 'leaflet';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';
import type { GeoJSON as GeoJSONType, ZoneProperties, GeoJSONFeature } from '@/types';

import { ZoneList } from './ZoneList';
import { ZoneMap } from './ZoneMap';
import { ZoneProperties as ZonePropertiesPanel } from './ZoneProperties';
import {
  validateZoneId,
  validateZoneProperties,
  validateGeoJSONFeature
} from './ZoneValidation';
import { setupDrawControls, generateZoneId } from './ZoneDrawControls';
import { handleExport, validateImportedData } from './ZoneImportExport';

import 'leaflet-draw/dist/leaflet.draw.css';

interface ZoneEditorProps {
  initialZones?: GeoJSONType;
  onZonesChange?: (zones: GeoJSONType) => void;
  onValidationError?: (errors: string[]) => void;
  className?: string;
}

export interface EditingZone {
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

  // Toggle drawing mode
  const toggleDrawingMode = () => {
    if (!mapRef.current || !drawnItemsRef.current) return;

    setupDrawControls({
      map: mapRef.current,
      isDrawingMode,
      setIsDrawingMode,
      drawnItems: drawnItemsRef.current,
      onDrawCreated: handleCreated,
      onDrawEdited: handleEdited,
      onDrawDeleted: handleDeleted,
      drawControlRef
    });
  };

  // Handle feature creation from drawing
  const handleCreated = (e: any) => {
    if (!mapRef.current || !drawnItemsRef.current) return;

    const { layerType, layer } = e;

    if (layerType === 'polygon' || layerType === 'rectangle') {
      const geojson = layer.toGeoJSON();
      const newZoneId = generateZoneId(zones);

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
      setIsDrawingMode(false);
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
  const handleImport = async (file: File) => {
    try {
      const text = await file.text();
      const importedData = JSON.parse(text);

      const validatedData = validateImportedData(
        importedData,
        validateGeoJSONFeature,
        validateZoneProperties
      );

      setZones(validatedData);
      setValidationErrors([]);

      // Update drawn layers
      if (drawnItemsRef.current && mapRef.current) {
        drawnItemsRef.current.clearLayers();

        validatedData.features.forEach(feature => {
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
      const errors = errorMessage.split('\n');
      setValidationErrors(errors);
      if (onValidationError) {
        onValidationError(errors);
      }
      console.error('Import error:', error);
    }
  };

  // Handle zone click
  const handleZoneClick = (feature: any, layer: any) => {
    const zoneId = feature.properties.id;
    setSelectedZoneId(zoneId);
  };

  // Handle zone edit
  const handleZoneEdit = (zoneId: string) => {
    const zone = zones.features.find(f => f.properties.id === zoneId);
    if (zone) {
      setEditingZone({
        id: zone.properties.id,
        properties: { ...zone.properties }
      });
    }
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
          <ZoneList
            zones={zones}
            selectedZoneId={selectedZoneId}
            onZoneSelect={setSelectedZoneId}
            onZoneEdit={handleZoneEdit}
            onZoneDelete={deleteZone}
            onImport={handleImport}
            onExport={() => handleExport(zones)}
          />
        </div>

        {/* Map Area */}
        <div className="lg:col-span-2">
          <ZoneMap
            zones={zones}
            selectedZoneId={selectedZoneId}
            isDrawingMode={isDrawingMode}
            onZoneClick={handleZoneClick}
            onDrawingModeToggle={toggleDrawingMode}
            onDrawCreated={handleCreated}
            onDrawEdited={handleEdited}
            onDrawDeleted={handleDeleted}
            drawnItemsRef={drawnItemsRef}
            drawControlRef={drawControlRef}
          />
        </div>

        {/* Properties Panel */}
        <div className="lg:col-span-1">
          <ZonePropertiesPanel
            selectedZoneId={selectedZoneId}
            editingZone={editingZone}
            zones={zones}
            onZoneEdit={setEditingZone}
            onZoneSave={saveZoneProperties}
            onZoneCancel={() => setEditingZone(null)}
            onZoneDelete={deleteZone}
          />
        </div>
      </div>
    </div>
  );
}