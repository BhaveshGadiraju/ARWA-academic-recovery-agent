'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BarChart3, History, Settings, LogOut, Plus, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen?: boolean;
}

export function Sidebar({ isOpen = true }: SidebarProps) {
  const pathname = usePathname();

  const navigation = [
    { href: '/dashboard', label: 'Overview', icon: BarChart3 },
    { href: '/analyze', label: 'Recovery Plan', icon: Plus },
    { href: '/history', label: 'Progress', icon: History },
    { href: '/settings', label: 'Resources', icon: Settings },
  ];

  return (
    <aside
      className={cn(
        'border-r border-border/30 bg-sidebar shadow-[0_2px_8px_rgba(0,0,0,0.04)]',
        'fixed inset-y-0 left-0 top-16 w-64 transform transition-transform duration-300 lg:static lg:translate-x-0 lg:top-0',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}
    >
      <nav className="flex h-full flex-col px-6 py-8 space-y-8">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3 px-0.5">
          <div className="h-12 w-12 rounded-[14px] bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shadow-sm border border-primary/10">
            <Zap className="h-6 w-6 text-primary" />
          </div>
          <span className="text-base font-bold text-foreground tracking-tight">ARWA</span>
        </div>

        {/* Navigation */}
        <div className="flex-1 space-y-2">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}>
              <Button
                variant={pathname === href ? 'default' : 'ghost'}
                className={cn(
                  'w-full justify-start gap-3 rounded-full px-4 py-2.5 text-sm font-medium transition-all duration-200',
                  pathname === href 
                    ? 'bg-primary text-primary-foreground shadow-md hover:shadow-lg' 
                    : 'text-foreground/70 hover:text-foreground hover:bg-muted/60'
                )}
                asChild
              >
                <span>
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  <span>{label}</span>
                </span>
              </Button>
            </Link>
          ))}
        </div>

        {/* Logout */}
        <Button 
          variant="ghost" 
          className="w-full justify-start gap-3 rounded-full px-4 py-2.5 text-sm font-medium text-foreground/70 hover:text-foreground hover:bg-muted/60 transition-all duration-200" 
          onClick={() => {}}
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          <span>Logout</span>
        </Button>
      </nav>
    </aside>
  );
}
