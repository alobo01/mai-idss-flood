import { useState } from 'react';

type ToastProps = {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
};

export function useToast() {
  const toast = ({ title, description, variant }: ToastProps) => {
    // Simple console implementation for now
    // Can be replaced with a proper toast library later
    const prefix = variant === 'destructive' ? '❌' : '✓';
    console.log(`${prefix} ${title}${description ? `: ${description}` : ''}`);
    
    // You could also use native browser notifications or a toast library
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body: description });
    }
  };

  return { toast };
}
