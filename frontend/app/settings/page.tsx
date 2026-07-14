'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Moon, Sun, Monitor } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function SettingsPage() {
  const [mounted, setMounted] = useState(false);
  const [theme, setThemeState] = useState<'light' | 'dark' | 'system'>('system');

  useEffect(() => {
    setMounted(true);
    const savedTheme = localStorage.getItem('arwa-theme') as 'light' | 'dark' | 'system' | null;
    setThemeState(savedTheme || 'system');
  }, []);

  const handleSetTheme = (newTheme: 'light' | 'dark' | 'system') => {
    setThemeState(newTheme);
    localStorage.setItem('arwa-theme', newTheme);
    
    if (newTheme === 'system') {
      document.documentElement.classList.remove('dark');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        document.documentElement.classList.add('dark');
      }
    } else if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  if (!mounted) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
            <p className="mt-2 text-muted-foreground">
              Manage your preferences and account settings
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="mt-2 text-muted-foreground">
            Manage your preferences and account settings
          </p>
        </div>

        {/* Theme Settings */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground">Theme</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Choose how ARWA looks on your device
          </p>

          <div className="mt-6 grid grid-cols-3 gap-4">
            <button
              onClick={() => handleSetTheme('light')}
              className={`rounded-lg border-2 p-4 text-center transition-all ${
                theme === 'light'
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-muted-foreground'
              }`}
            >
              <Sun className="mx-auto h-6 w-6 mb-2" />
              <p className="text-sm font-medium">Light</p>
            </button>

            <button
              onClick={() => handleSetTheme('dark')}
              className={`rounded-lg border-2 p-4 text-center transition-all ${
                theme === 'dark'
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-muted-foreground'
              }`}
            >
              <Moon className="mx-auto h-6 w-6 mb-2" />
              <p className="text-sm font-medium">Dark</p>
            </button>

            <button
              onClick={() => handleSetTheme('system')}
              className={`rounded-lg border-2 p-4 text-center transition-all ${
                theme === 'system'
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-muted-foreground'
              }`}
            >
              <Monitor className="mx-auto h-6 w-6 mb-2" />
              <p className="text-sm font-medium">System</p>
            </button>
          </div>
        </Card>

        {/* Account Section (Placeholder) */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground">Account</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Manage your account settings
          </p>
          <div className="mt-6 space-y-4">
            <Button variant="outline" className="w-full justify-start">
              Change Password
            </Button>
            <Button variant="outline" className="w-full justify-start text-destructive hover:text-destructive">
              Logout
            </Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
