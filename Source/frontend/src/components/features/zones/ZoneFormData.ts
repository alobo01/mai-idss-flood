import { useState } from 'react';
import type { ZoneProperties } from '@/types';

export interface ZoneFormData extends ZoneProperties {
  id: string;
}

const createEmptyZoneProperties = (): ZoneProperties => ({
  name: '',
  population: 0,
  admin_level: 1,
  critical_assets: []
});

export const useZoneFormData = () => {
  const [formData, setFormData] = useState<ZoneFormData>({
    id: '',
    ...createEmptyZoneProperties()
  });

  const [editingZone, setEditingZone] = useState<string | null>(null);
  const [isFormDirty, setIsFormDirty] = useState(false);

  const updateFormData = (updates: Partial<ZoneFormData>) => {
    setFormData(prev => ({ ...prev, ...updates }));
    setIsFormDirty(true);
  };

  const resetFormData = () => {
    setFormData({
      id: '',
      ...createEmptyZoneProperties()
    });
    setEditingZone(null);
    setIsFormDirty(false);
  };

  const loadZoneIntoForm = (zoneId: string, properties: ZoneProperties) => {
    setFormData({
      id: zoneId,
      ...properties
    });
    setEditingZone(zoneId);
    setIsFormDirty(false);
  };

  const addCriticalAsset = (asset: string) => {
    if (asset.trim()) {
      updateFormData({
        critical_assets: [...formData.critical_assets, asset.trim()]
      });
    }
  };

  const removeCriticalAsset = (index: number) => {
    updateFormData({
      critical_assets: formData.critical_assets.filter((_, i) => i !== index)
    });
  };

  return {
    formData,
    editingZone,
    isFormDirty,
    updateFormData,
    resetFormData,
    loadZoneIntoForm,
    addCriticalAsset,
    removeCriticalAsset
  };
};