import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, Download, Edit, Trash2, Users, Building } from 'lucide-react';
import type { GeoJSON } from '@/types';

interface ZoneListProps {
  zones: GeoJSON;
  selectedZoneId: string | null;
  onZoneSelect: (zoneId: string) => void;
  onZoneEdit: (zoneId: string) => void;
  onZoneDelete: (zoneId: string) => void;
  onImport: (file: File) => void;
  onExport: () => void;
}

export function ZoneList({
  zones,
  selectedZoneId,
  onZoneSelect,
  onZoneEdit,
  onZoneDelete,
  onImport,
  onExport
}: ZoneListProps) {
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);

  const handleImport = () => {
    if (importFile) {
      onImport(importFile);
      setIsImportDialogOpen(false);
      setImportFile(null);
    }
  };

  return (
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
                  <Button onClick={onExport}>
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
                onClick={() => onZoneSelect(zone.properties.id)}
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
                      onZoneEdit(zone.properties.id);
                    }}
                  >
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onZoneDelete(zone.properties.id);
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
  );
}