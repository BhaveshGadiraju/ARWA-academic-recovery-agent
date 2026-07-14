'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { StudentForm } from '@/components/analysis/StudentForm';
import { ResultsDisplay } from '@/components/analysis/ResultsDisplay';
import { LoadingState } from '@/components/shared/LoadingState';
import { ErrorState } from '@/components/shared/ErrorState';
import { useAnalysis } from '@/hooks/useAnalysis';
import type { AnalyzeRequest } from '@/lib/types';

export default function AnalyzePage() {
  const { analyze, loading, error, data } = useAnalysis();
  const [studentName, setStudentName] = useState('');

  const handleSubmit = async (formData: AnalyzeRequest) => {
    setStudentName(formData.name);
    try {
      await analyze(formData);
    } catch (err) {
      console.error('[v0] Analysis failed:', err);
    }
  };

  const handleRetry = async () => {
    // This would retry the last request
    // For now, just show the form again
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-10">
        {/* Header */}
        {!data && (
          <div className="space-y-3">
            <h1 className="text-4xl font-bold text-foreground tracking-tight">Academic Analysis</h1>
            <p className="text-lg text-foreground/70">
              Fill out your information to receive a personalized recovery and wellness plan tailored to your unique situation.
            </p>
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="rounded-lg border border-border bg-card p-8">
            <LoadingState />
          </div>
        ) : error ? (
          <ErrorState
            message={error.message}
            onRetry={handleRetry}
          />
        ) : data ? (
          <ResultsDisplay response={data} studentName={studentName} />
        ) : (
          <StudentForm onSubmit={handleSubmit} isLoading={loading} />
        )}
      </div>
    </DashboardLayout>
  );
}
