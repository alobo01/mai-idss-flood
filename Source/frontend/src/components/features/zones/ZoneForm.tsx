import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, X } from 'lucide-react';
import { useZoneFormData } from './ZoneFormData';
import { validateZoneId, validateZoneProperties } from './ZoneValidation';

interface ZoneFormProps {
  existingZoneIds: string[];
  onSubmit: (zoneId: string, properties: any) => void;
  onCancel: () => void;
  initialData?: { id: string; properties: any };
}

export const ZoneForm: React.FC<ZoneFormProps> = ({
  existingZoneIds,
  onSubmit,
  onCancel,
  initialData
}) => {
  const [newAsset, setNewAsset] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    formData,
    editingZone,
    isFormDirty,
    updateFormData,
    resetFormData,
    addCriticalAsset,
    removeCriticalAsset
  } = useZoneFormData();

  // Load initial data if provided
  React.useEffect(() => {
    if (initialData) {
      updateFormData({
        id: initialData.id,
        ...initialData.properties
      });
    }
  }, [initialData, updateFormData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const validationErrors = [
      ...validateZoneId(formData.id, existingZoneIds.filter(id => id !== editingZone)),
      ...validateZoneProperties(formData)
    ];

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors([]);

    try {
      const { id, ...properties } = formData;
      await onSubmit(id, properties);
      resetFormData();
    } catch (error) {
      setErrors(['Failed to save zone']);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddAsset = () => {
    if (newAsset.trim()) {
      addCriticalAsset(newAsset.trim());
      setNewAsset('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3">
          {errors.map((error, index) => (
            <div key={index} className="text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="zone-id">Zone ID</Label>
          <Input
            id="zone-id"
            value={formData.id}
            onChange={(e) => updateFormData({ id: e.target.value })}
            placeholder="e.g., zone_a"
            disabled={!!editingZone}
          />
        </div>

        <div>
          <Label htmlFor="zone-name">Zone Name</Label>
          <Input
            id="zone-name"
            value={formData.name}
            onChange={(e) => updateFormData({ name: e.target.value })}
            placeholder="e.g., Downtown District"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="population">Population</Label>
          <Input
            id="population"
            type="number"
            value={formData.population}
            onChange={(e) => updateFormData({ population: parseInt(e.target.value) || 0 })}
            min="0"
          />
        </div>

        <div>
          <Label htmlFor="admin-level">Admin Level</Label>
          <Input
            id="admin-level"
            type="number"
            value={formData.admin_level}
            onChange={(e) => updateFormData({ admin_level: parseInt(e.target.value) || 1 })}
            min="1"
            max="15"
          />
        </div>
      </div>

  
      <div>
        <Label>Critical Assets</Label>
        <div className="flex gap-2 mb-2">
          <Input
            value={newAsset}
            onChange={(e) => setNewAsset(e.target.value)}
            placeholder="Add critical asset"
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAsset())}
          />
          <Button type="button" onClick={handleAddAsset} size="sm">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {formData.critical_assets.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {formData.critical_assets.map((asset, index) => (
              <Badge key={index} variant="secondary" className="flex items-center gap-1">
                {asset}
                <X
                  className="h-3 w-3 cursor-pointer hover:text-red-500"
                  onClick={() => removeCriticalAsset(index)}
                />
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={!isFormDirty || isSubmitting}
          className="flex-1"
        >
          {isSubmitting ? 'Saving...' : (editingZone ? 'Update Zone' : 'Add Zone')}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
};