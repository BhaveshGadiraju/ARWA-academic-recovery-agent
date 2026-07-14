'use client';

import Link from 'next/link';
import { ArrowRight, TrendingUp, Zap, BookMarked } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Page() {
  return (
    <main className="min-h-screen bg-background">
      {/* Navigation */}
      <div className="border-b border-border/30 bg-card/98 shadow-[0_1px_3px_rgba(0,0,0,0.04)] backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-8 py-4 sm:px-10 lg:px-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-[12px] bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shadow-sm border border-primary/10">
                <Zap className="h-5 w-5 text-primary" />
              </div>
              <h1 className="text-lg font-bold text-foreground tracking-tight">ARWA</h1>
            </div>
            <Link href="/dashboard">
              <Button size="lg" className="rounded-full font-medium">Dashboard</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="mx-auto max-w-5xl px-8 py-36 sm:px-10 lg:px-12">
        <div className="text-center space-y-12">
          <div className="space-y-8">
            <h2 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-foreground leading-[1.15]">
              Recover academically.<br />
              <span className="text-primary">Without burning out.</span>
            </h2>
            <p className="mx-auto max-w-2xl text-lg sm:text-xl text-foreground/70 leading-relaxed font-light">
              ARWA uses AI to create personalized recovery plans based on your workload, goals, and habits. Designed for your long-term success and wellbeing.
            </p>
          </div>
          <div className="flex justify-center">
            <Link href="/analyze">
              <Button size="lg" className="rounded-full px-10 py-3 gap-2 font-semibold shadow-md hover:shadow-lg">
                Create Your Recovery Plan <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-36 grid gap-8 sm:grid-cols-1 md:grid-cols-3">
          <div className="group rounded-2xl bg-card p-10 shadow-[0_1px_3px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300">
            <div className="mb-6 h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors duration-200">
              <TrendingUp className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-3 text-lg font-bold text-foreground tracking-tight">
              Health Score
            </h3>
            <p className="text-sm text-foreground/70 leading-relaxed">
              Real-time wellness metric that tracks your academic and personal recovery progress.
            </p>
          </div>

          <div className="group rounded-2xl bg-card p-10 shadow-[0_1px_3px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300">
            <div className="mb-6 h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors duration-200">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-3 text-lg font-bold text-foreground tracking-tight">
              Smart Plans
            </h3>
            <p className="text-sm text-foreground/70 leading-relaxed">
              AI-generated weekly breakdown with specific actions, study blocks, and wellness breaks.
            </p>
          </div>

          <div className="group rounded-2xl bg-card p-10 shadow-[0_1px_3px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300">
            <div className="mb-6 h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors duration-200">
              <BookMarked className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-3 text-lg font-bold text-foreground tracking-tight">
              Actionable Tips
            </h3>
            <p className="text-sm text-foreground/70 leading-relaxed">
              Sleep optimization, study techniques, and wellness recommendations personalized for you.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
