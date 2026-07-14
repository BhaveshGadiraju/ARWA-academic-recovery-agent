'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { EmptyState } from '@/components/shared/EmptyState';
import { History } from 'lucide-react';

export default function HistoryPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-10">
        <div className="space-y-3">
          <h1 className="text-4xl font-bold text-foreground tracking-tight">Analysis History</h1>
          <p className="text-lg text-foreground/70">
            View and compare your previous recovery analyses and track your progress over time.
          </p>
        </div>

        <EmptyState
          title="No Analyses Yet"
          description="Complete your first analysis to see it here"
          icon={<History className="h-12 w-12" />}
        />
      </div>
    </DashboardLayout>
  );
}
