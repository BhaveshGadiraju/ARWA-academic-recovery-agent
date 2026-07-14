'use client';

import { useState, useEffect } from 'react';
import { Menu, X, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TopNavProps {
  onMenuToggle?: () => void;
}

export function TopNav({ onMenuToggle }: TopNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Check current dark mode state from document
    setIsDark(document.documentElement.classList.contains('dark'));
  }, []);

  const handleMenuToggle = () => {
    setIsOpen(!isOpen);
    onMenuToggle?.();
  };

  const toggleTheme = () => {
    const newDarkMode = !isDark;
    setIsDark(newDarkMode);
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Store preference
    localStorage.setItem('arwa-theme', newDarkMode ? 'dark' : 'light');
  };

  if (!mounted) return null;

  return (
    <div className="border-b border-border/30 bg-card/98 backdrop-blur-sm shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <div className="flex items-center justify-between px-8 py-4 sm:px-10">
        <div className="flex items-center gap-5">
          <button
            onClick={handleMenuToggle}
            className="lg:hidden p-2 hover:bg-muted/50 rounded-lg transition-all duration-200 active:scale-95"
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <h1 className="text-xl font-bold text-foreground tracking-tight">ARWA</h1>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="rounded-full hover:bg-muted/50 transition-all duration-200 active:scale-95"
          >
            {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
        </div>
      </div>
    </div>
  );
}
