import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { X, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface FormField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'select' | 'textarea' | 'checkbox' | 'tags';
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  required?: boolean;
  disabled?: boolean;
  description?: string;
  validation?: (value: any) => string | null;
}

export interface FormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  fields: FormField[];
  initialData?: Record<string, any>;
  onSubmit: (data: Record<string, any>) => void;
  loading?: boolean;
  submitButtonText?: string;
  cancelButtonText?: string;
}

export function FormDialog({
  open,
  onOpenChange,
  title,
  description,
  fields,
  initialData = {},
  onSubmit,
  loading = false,
  submitButtonText = "Save",
  cancelButtonText = "Cancel",
}: FormDialogProps) {
  const [formData, setFormData] = useState<Record<string, any>>(initialData);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [newTag, setNewTag] = useState('');

  React.useEffect(() => {
    setFormData(initialData);
    setErrors({});
  }, [initialData]);

  const updateField = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));

    // Clear error for this field if it exists
    if (errors[key]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    fields.forEach(field => {
      const value = formData[field.key];

      // Required validation
      if (field.required && (!value || (typeof value === 'string' && !value.trim()))) {
        newErrors[field.key] = `${field.label} is required`;
        return;
      }

      // Custom validation
      if (field.validation && value !== undefined && value !== null && value !== '') {
        const validationError = field.validation(value);
        if (validationError) {
          newErrors[field.key] = validationError;
        }
      }

      // Type validation
      if (field.type === 'number' && value !== undefined && value !== null && value !== '') {
        const numValue = Number(value);
        if (isNaN(numValue)) {
          newErrors[field.key] = `${field.label} must be a valid number`;
        }
      }

      if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
          newErrors[field.key] = `${field.label} must be a valid email address`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Convert number fields
    const processedData = { ...formData };
    fields.forEach(field => {
      if (field.type === 'number' && processedData[field.key] !== undefined && processedData[field.key] !== '') {
        processedData[field.key] = Number(processedData[field.key]);
      }
    });

    onSubmit(processedData);
  };

  const addTag = (fieldKey: string) => {
    if (newTag.trim() && !formData[fieldKey]?.includes(newTag.trim())) {
      updateField(fieldKey, [...(formData[fieldKey] || []), newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (fieldKey: string, tagToRemove: string) => {
    updateField(fieldKey, formData[fieldKey]?.filter((tag: string) => tag !== tagToRemove) || []);
  };

  const renderField = (field: FormField) => {
    const value = formData[field.key];
    const error = errors[field.key];

    switch (field.type) {
      case 'text':
      case 'number':
      case 'email':
        return (
          <div className="space-y-2">
            <Label htmlFor={field.key}>
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            <Input
              id={field.key}
              type={field.type}
              placeholder={field.placeholder}
              value={value || ''}
              onChange={(e) => updateField(field.key, e.target.value)}
              disabled={field.disabled || loading}
              className={cn(error && "border-destructive")}
            />
            {field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-2">
            <Label htmlFor={field.key}>
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            <Textarea
              id={field.key}
              placeholder={field.placeholder}
              value={value || ''}
              onChange={(e) => updateField(field.key, e.target.value)}
              disabled={field.disabled || loading}
              className={cn(error && "border-destructive")}
              rows={3}
            />
            {field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <Label htmlFor={field.key}>
              {field.label}
              {field.required && <span className="text-destructive ml-1">*</span>}
            </Label>
            <Select
              value={value || ''}
              onValueChange={(newValue) => updateField(field.key, newValue)}
              disabled={field.disabled || loading}
            >
              <SelectTrigger className={cn(error && "border-destructive")}>
                <SelectValue placeholder={field.placeholder || `Select ${field.label}`} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        );

      case 'checkbox':
        return (
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id={field.key}
                checked={value || false}
                onCheckedChange={(checked) => updateField(field.key, checked)}
                disabled={field.disabled || loading}
              />
              <Label htmlFor={field.key} className="text-sm font-normal">
                {field.label}
                {field.required && <span className="text-destructive ml-1">*</span>}
              </Label>
            </div>
            {field.description && (
              <p className="text-sm text-muted-foreground ml-6">{field.description}</p>
            )}
            {error && (
              <p className="text-sm text-destructive ml-6">{error}</p>
            )}
          </div>
        );

      case 'tags':
        return (
          <div className="space-y-2">
            <Label>{field.label}</Label>
            <div className="flex space-x-2">
              <Input
                placeholder={field.placeholder || "Add tag..."}
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTag(field.key);
                  }
                }}
                disabled={loading}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => addTag(field.key)}
                disabled={loading}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {value && value.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {value.map((tag: string) => (
                  <Badge key={tag} variant="secondary" className="flex items-center space-x-1">
                    <span>{tag}</span>
                    <X
                      className="h-3 w-3 cursor-pointer hover:text-destructive"
                      onClick={() => removeTag(field.key, tag)}
                    />
                  </Badge>
                ))}
              </div>
            )}
            {field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {fields.map((field) => (
            <div key={field.key}>
              {renderField(field)}
            </div>
          ))}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              {cancelButtonText}
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : submitButtonText}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}