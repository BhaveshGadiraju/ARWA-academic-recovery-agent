'use client';

import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Smartphone, TrendingUp, Heart, Moon } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-12">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-5xl font-bold text-foreground tracking-tight">Your Wellness</h1>
          <p className="text-lg text-foreground/60">Welcome back. Here's your recovery summary.</p>
        </div>

        {/* Top Action Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <Button size="lg" className="rounded-full">
            <Plus className="h-5 w-5" />
            Log Workout
          </Button>
          <Button variant="outline" size="lg" className="rounded-full">
            <Smartphone className="h-4 w-4" />
            Connect Device
          </Button>
        </div>

        {/* Main Grid - Premium Card Layout */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
          {/* Left: Wellness Score Ring */}
          <Card className="p-10 md:p-12 md:col-span-1">
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-foreground tracking-tight">Today's Wellness</h2>
                <p className="text-sm text-foreground/60 mt-1">You're on track</p>
              </div>
              
              {/* Animated Circular Progress */}
              <div className="flex justify-center py-4">
                <div className="relative w-56 h-56">
                  <svg 
                    className="w-full h-full transform -rotate-90" 
                    viewBox="0 0 100 100"
                  >
                    <defs>
                      <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="rgb(140, 93, 66)" stopOpacity="1" />
                        <stop offset="100%" stopColor="rgb(179, 117, 79)" stopOpacity="1" />
                      </linearGradient>
                    </defs>
                    {/* Background circle - subtle */}
                    <circle 
                      cx="50" cy="50" r="42" 
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="4.5" 
                      className="text-border/30" 
                    />
                    {/* Gradient progress circle - animated */}
                    <circle 
                      cx="50" cy="50" r="42" 
                      fill="none" 
                      stroke="url(#ringGradient)" 
                      strokeWidth="4.5" 
                      strokeDasharray="131.95 282.74" 
                      strokeLinecap="round"
                      className="drop-shadow-sm transition-all duration-[1500ms] ease-out"
                      style={{
                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.08))'
                      }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-sm font-medium text-foreground/70 tracking-wide">DAILY GOAL</span>
                    <span className="text-5xl font-bold text-foreground mt-1">100</span>
                    <span className="text-xs text-foreground/60 font-medium">minutes</span>
                  </div>
                </div>
              </div>

              {/* Breakdown */}
              <div className="space-y-2.5 pt-2">
                {[
                  { label: 'Daily Goal', value: '40%', color: 'from-primary to-primary/70' },
                  { label: 'Mindfulness', value: '50%', color: 'from-primary/70 to-primary/40' },
                  { label: 'Nutrition', value: '20%', color: 'from-primary/40 to-primary/20' }
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-3 px-2 rounded-lg hover:bg-muted/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-3.5 h-3.5 rounded-full bg-gradient-to-br ${item.color} shadow-sm`}></div>
                      <span className="text-sm font-medium text-foreground/80">{item.label}</span>
                    </div>
                    <span className="font-semibold text-foreground text-sm">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          {/* Middle Column - Activity & Sleep */}
          <div className="space-y-8 md:col-span-1">
            {/* Weekly Activity */}
            <Card className="p-10 md:p-12">
              <h3 className="text-xl font-bold text-foreground mb-8 tracking-tight">Weekly Activity</h3>
              <div className="space-y-6">
                <div className="flex items-end justify-between h-40 gap-1.5">
                  {[45, 62, 38, 71, 58, 80, 65].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-primary to-primary/40 rounded-t-lg hover:from-primary/95 hover:to-primary/30 transition-all duration-300 cursor-pointer hover:shadow-md group"
                      style={{ 
                        height: `${(height / 100) * 160}px`,
                        animation: `slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) ${i * 0.06}s both`
                      }}
                      title={`${height}%`}
                    />
                  ))}
                </div>
                <div className="flex justify-between text-xs font-medium text-foreground/50 px-1">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                    <span key={day} className="flex-1 text-center">{day}</span>
                  ))}
                </div>
              </div>
            </Card>

            {/* Sleep Quality */}
            <Card className="p-10 md:p-12">
              <h3 className="text-xl font-bold text-foreground mb-8 tracking-tight">Sleep Quality</h3>
              <div className="space-y-6">
                <svg 
                  className="w-full h-40" 
                  viewBox="0 0 320 120" 
                  preserveAspectRatio="none"
                >
                  <defs>
                    <linearGradient id="sleepGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="rgb(140, 93, 66)" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="rgb(140, 93, 66)" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <polyline 
                    points="10,70 50,50 90,65 130,40 170,58 210,35 250,52 310,45" 
                    fill="none" 
                    stroke="rgb(140, 93, 66)" 
                    strokeWidth="2.5" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  />
                  <polygon 
                    points="10,70 50,50 90,65 130,40 170,58 210,35 250,52 310,45 310,120 10,120" 
                    fill="url(#sleepGrad)" 
                  />
                </svg>
                <div className="flex justify-between text-xs font-medium text-foreground/50">
                  {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                    <span key={day} className="flex-1 text-center">{day}</span>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* Right Column - Mood & Meditation */}
          <div className="space-y-8 md:col-span-1">
            {/* Mood Tracker */}
            <Card className="p-10 md:p-12">
              <h3 className="text-xl font-bold text-foreground mb-8 tracking-tight">Check Your Mood</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-5 gap-2">
                  {['😄', '😔', '😐', '😐', '😠'].map((emoji, i) => (
                    <button 
                      key={`top-${i}`}
                      className="aspect-square text-4xl flex items-center justify-center rounded-lg hover:bg-muted/50 hover:scale-110 transition-all duration-200 hover:-translate-y-2 active:scale-95 focus:outline-none focus:ring-2 focus:ring-primary/30"
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {['😕', '🥰', '😪', '😢', '😭'].map((emoji, i) => (
                    <button 
                      key={`bottom-${i}`}
                      className="aspect-square text-4xl flex items-center justify-center rounded-lg hover:bg-muted/50 hover:scale-110 transition-all duration-200 hover:-translate-y-2 active:scale-95 focus:outline-none focus:ring-2 focus:ring-primary/30"
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>
              <Button className="w-full mt-6 rounded-full" size="lg">Save Check-in</Button>
            </Card>

            {/* Meditation Card */}
            <Card className="p-10 md:p-12 bg-gradient-to-br from-primary/8 to-primary/3 overflow-hidden relative">
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16"></div>
              <div className="relative z-10 space-y-6">
                <div>
                  <h3 className="text-xl font-bold text-foreground tracking-tight">Daily Meditation</h3>
                  <p className="text-sm text-foreground/60 mt-1">10 minutes</p>
                </div>
                <button className="w-full h-48 rounded-2xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center hover:from-primary/20 hover:to-primary/10 transition-all duration-300 group active:scale-95">
                  <div className="w-20 h-20 rounded-full bg-white shadow-lg flex items-center justify-center group-hover:shadow-2xl transition-shadow duration-300">
                    <Heart className="w-10 h-10 text-primary ml-1" />
                  </div>
                </button>
              </div>
            </Card>
          </div>
        </div>

        {/* CTA Section */}
        <Card className="p-12 md:p-16 text-center">
          <div className="space-y-6">
            <div>
              <h2 className="text-4xl font-bold text-foreground tracking-tight mb-2">Ready for deeper insights?</h2>
              <p className="text-lg text-foreground/70">Start your comprehensive recovery analysis today</p>
            </div>
            <Link href="/analyze">
              <Button size="lg" className="rounded-full shadow-lg hover:shadow-xl">
                <Plus className="h-5 w-5" />
                Create Analysis
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </DashboardLayout>
  );
}
