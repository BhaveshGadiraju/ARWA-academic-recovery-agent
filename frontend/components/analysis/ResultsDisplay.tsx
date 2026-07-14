'use client';

import type { AnalyzeResponse } from '@/lib/types';
import { Card } from '@/components/ui/card';
import { AlertCircle, CheckCircle, Zap, BookOpen, Heart, Award, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface ResultsDisplayProps {
  response: AnalyzeResponse;
  studentName: string;
}

export function ResultsDisplay({ response, studentName }: ResultsDisplayProps) {
  const riskLevelColor = {
    low: 'bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-900',
    medium: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-900',
    high: 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-900',
  };

  const riskLevelBg = {
    low: 'bg-green-500/20',
    medium: 'bg-yellow-500/20',
    high: 'bg-red-500/20',
  };

  return (
    <div className="space-y-7">
      {/* Header */}
      <div className="rounded-2xl border border-border/40 bg-gradient-to-br from-card to-card/80 p-8">
        <h2 className="text-3xl font-bold text-foreground">
          Your Personalized Recovery Plan
        </h2>
        <p className="mt-3 text-foreground/60">
          Analysis for <span className="font-semibold text-foreground">{studentName}</span> • {new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
      </div>

      {/* Summary */}
      <Card className="border-primary/20 bg-gradient-to-br from-primary/8 to-primary/3 p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <Zap className="h-5 w-5 text-primary" />
          </div>
          Executive Summary
        </h3>
        <p className="mt-5 whitespace-pre-wrap leading-relaxed text-foreground/80 font-medium">
          {response.summary}
        </p>
      </Card>

      {/* Risk Assessment */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-red-500/20 flex items-center justify-center">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
          </div>
          Risk Assessment
        </h3>
        <div className="mt-4 space-y-4">
          <div className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 ${riskLevelColor[response.risk_assessment.overall_risk_level]}`}>
            <span className="font-semibold capitalize">
              {response.risk_assessment.overall_risk_level} Risk
            </span>
            <span className="text-sm">
              ({response.risk_assessment.risk_score}%)
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Key Risks:</p>
            <ul className="mt-2 space-y-1">
              {response.risk_assessment.key_risks.map((risk, index) => (
                <li key={index} className="text-sm text-foreground">
                  • {risk}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* Strengths */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <CheckCircle className="h-5 w-5 text-primary" />
          </div>
          Your Strengths
        </h3>
        <ul className="mt-4 space-y-2">
          {response.strengths.map((strength, index) => (
            <li key={index} className="flex items-start gap-2 text-sm">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary flex-shrink-0" />
              <span>{strength}</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Weaknesses */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-yellow-500/20 flex items-center justify-center">
            <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
          </div>
          Areas for Improvement
        </h3>
        <ul className="mt-4 space-y-2">
          {response.weaknesses.map((weakness, index) => (
            <li key={index} className="flex items-start gap-2 text-sm">
              <span className="mt-1 h-2 w-2 rounded-full bg-destructive flex-shrink-0" />
              <span>{weakness}</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Recovery Plan */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
          <Award className="h-5 w-5" />
          </div>
          Recovery Plan
        </h3>
        <div className="mt-4 space-y-3">
          {response.recovery_plan.map((suggestion, index) => (
            <div
              key={index}
              className="rounded-lg border border-border bg-muted/50 p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-medium text-foreground">{suggestion.title}</h4>
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                  suggestion.priority === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                  suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                  'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                }`}>
                  {suggestion.priority}
                </span>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                {suggestion.description}
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Study Schedule */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
          <BookOpen className="h-5 w-5" />
          </div>
          Study Schedule
        </h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Day</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Time</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Subject</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Activity</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Duration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {response.study_schedule.map((session, index) => (
                <tr key={index} className="hover:bg-muted/50">
                  <td className="px-4 py-2">{session.day}</td>
                  <td className="px-4 py-2">{session.time}</td>
                  <td className="px-4 py-2">{session.subject}</td>
                  <td className="px-4 py-2">{session.activity}</td>
                  <td className="px-4 py-2">{session.duration}m</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Mental Wellness */}
      <Card className="p-8">
        <h3 className="flex items-center gap-3 text-lg font-semibold text-foreground">
          <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
          <Heart className="h-5 w-5" />
          </div>
          Mental Wellness Suggestions
        </h3>
        <ul className="mt-4 space-y-2">
          {response.mental_wellness_suggestions.map((suggestion, index) => (
            <li key={index} className="flex items-start gap-2 text-sm">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary flex-shrink-0" />
              <span>{suggestion}</span>
            </li>
          ))}
        </ul>
      </Card>

      {/* Confidence Score */}
      <Card className={`p-6 ${riskLevelBg[response.risk_assessment.overall_risk_level]}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Confidence Score</p>
            <p className="mt-1 text-3xl font-bold text-foreground">
              {(response.confidence_score * 100).toFixed(0)}%
            </p>
          </div>
          <div className="h-24 w-24 rounded-full border-4 border-primary/30 flex items-center justify-center">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">
                {(response.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Next Steps */}
      <Card className="border-primary/20 bg-primary/5 p-6">
        <h3 className="font-semibold text-foreground">Next Steps</h3>
        <ol className="mt-4 space-y-2">
          {response.next_steps.map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-sm">
              <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary">
                {index + 1}
              </span>
              <span className="pt-0.5">{step}</span>
            </li>
          ))}
        </ol>
      </Card>

      {/* Resources */}
      {response.recommended_resources.length > 0 && (
        <Card className="p-8">
          <h3 className="font-semibold text-foreground">Recommended Resources</h3>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {response.recommended_resources.map((resource, index) => (
              <div key={index} className="rounded-lg border border-border p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-foreground">{resource.title}</p>
                    <p className="text-xs text-muted-foreground">{resource.type}</p>
                  </div>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{resource.description}</p>
                {resource.url && (
                  <a
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-2 text-sm text-primary hover:text-primary/80"
                  >
                    Visit <ArrowRight className="h-3 w-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Link href="/analyze" className="flex-1">
          <Button variant="outline" className="w-full">
            New Analysis
          </Button>
        </Link>
        <Link href="/dashboard" className="flex-1">
          <Button className="w-full">
            Back to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
