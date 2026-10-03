import { ButtonLink } from '@/components/ui/Button';
import { Logo } from '@/components/ui/Logo';
import { ScoreRing } from '@/components/insights/ScoreRing';

const STEPS = [
  { title: 'Add your semester', body: 'Courses, deadlines, grades, and the hours you actually have.' },
  { title: 'See your Recovery Score', body: 'One transparent number built from workload, deadlines, grades, and time.' },
  { title: 'Follow today’s plan', body: 'Real assignments in real time blocks, ranked by what matters most.' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-6">
        <Logo />
        <nav className="flex items-center gap-2">
          <ButtonLink href="/login" variant="ghost" size="sm">
            Log in
          </ButtonLink>
          <ButtonLink href="/signup" size="sm">
            Get started
          </ButtonLink>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-5 sm:px-6">
        <section className="grid items-center gap-12 py-14 md:grid-cols-[1.15fr_1fr] md:py-24">
          <div className="animate-fade-up">
            <p className="mb-5 text-[11px] font-semibold uppercase tracking-[0.18em] text-faint">Academic Recovery & Wellness Agent</p>
            <h1 className="text-[44px] font-semibold leading-[1.05] tracking-tight sm:text-[64px]">Recover your semester.</h1>
            <p className="mt-6 max-w-md text-[17px] leading-relaxed text-muted">
              ARWA turns your courses, deadlines, and study time into a clear plan for today, and tells you honestly when
              something won&apos;t fit.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <ButtonLink href="/signup" size="lg">
                Get started
              </ButtonLink>
              <ButtonLink href="/login" variant="secondary" size="lg">
                I have an account
              </ButtonLink>
            </div>
          </div>

          <div className="flex justify-center">
            <div className="w-full max-w-sm rounded-[32px] border border-line bg-surface p-8 shadow-lift">
              <div className="flex justify-center">
                <ScoreRing score={72} label="Manageable" size={200} />
              </div>
              <p className="mt-6 text-center text-sm text-muted">Your Recovery Score</p>
              <div className="mt-6 space-y-3">
                {[
                  ['Midterm review', '6:00 PM · 50m'],
                  ['Lab report draft', '7:00 PM · 50m'],
                ].map(([title, time]) => (
                  <div key={title} className="flex items-center justify-between rounded-2xl bg-sunken px-4 py-3 text-sm">
                    <span className="font-medium">{title}</span>
                    <span className="text-muted">{time}</span>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-center text-[11px] text-faint">Example preview</p>
            </div>
          </div>
        </section>

        <section className="grid gap-4 pb-24 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <div key={step.title} className="rounded-3xl border border-line bg-surface p-6">
              <span className="text-[13px] font-semibold tabular-nums text-faint">0{i + 1}</span>
              <h2 className="mt-3 text-[17px] font-semibold tracking-tight">{step.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-line py-8 text-center text-xs text-faint">
        ARWA&apos;s Recovery Score is a planning aid, not a clinical or scientifically validated measure.
      </footer>
    </div>
  );
}
