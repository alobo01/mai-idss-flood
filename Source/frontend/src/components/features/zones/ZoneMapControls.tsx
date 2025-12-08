import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MapPin, Users, Building, AlertTriangle } from 'lucide-react';
import type { ZoneProperties } from '@/types';

interface ZoneMapControlsProps {
  selectedZone: string | null;
  zonesCount: number;
  selectedZoneProperties?: ZoneProperties;
  onZoneSelect: (zoneId: string | null) => void;
}

const criticalAssetIcons: { [key: string]: React.ReactNode } = {
  hospital: <Building className="h-3 w-3" />,
  school: <Users className="h-3 w-3" />,
  government: <AlertTriangle className="h-3 w-3" />
};

export const ZoneMapControls: React.FC<ZoneMapControlsProps> = ({
  selectedZone,
  zonesCount,
  selectedZoneProperties,
  onZoneSelect
}) => {
  return (
    <div className="absolute top-4 right-4 z-[1000] bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-sm">Zone Controls</h3>
          <Badge variant="secondary" className="text-xs">
            {zonesCount} zones
          </Badge>
        </div>

        {selectedZone ? (
          <div className="space-y-2 border-t pt-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Selected:</span>
              <Badge variant="default" className="text-xs">
                {selectedZone}
              </Badge>
            </div>

            {selectedZoneProperties && (
              <>
                <div className="text-xs space-y-1">
                  <div><strong>Name:</strong> {selectedZoneProperties.name}</div>
                  <div><strong>Population:</strong> {selectedZoneProperties.population.toLocaleString()}</div>
                  <div><strong>Admin Level:</strong> {selectedZoneProperties.admin_level}</div>
                </div>

                {selectedZoneProperties.critical_assets.length > 0 && (
                  <div className="space-y-1">
                    <div className="text-xs font-medium">Critical Assets:</div>
                    <div className="flex flex-wrap gap-1">
                      {selectedZoneProperties.critical_assets.map((asset, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {criticalAssetIcons[asset.toLowerCase()] || <MapPin className="h-3 w-3" />}
                          {asset}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onZoneSelect(null)}
                  className="w-full text-xs"
                >
                  Clear Selection
                </Button>
              </>
            )}
          </div>
        ) : (
          <div className="text-xs text-gray-500 dark:text-gray-400 italic">
            Click on a zone to view details
          </div>
        )}
      </div>
    </div>
  );
};