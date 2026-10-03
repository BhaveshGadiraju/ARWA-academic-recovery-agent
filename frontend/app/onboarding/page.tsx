'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { RequireAuth } from '@/components/shell/RequireAuth';
import { Logo } from '@/components/ui/Logo';
import { ErrorState, LoadingState } from '@/components/ui/States';
import { useApi } from '@/hooks/useApi';
import type { Assignment, AvailabilityDay, Course, Profile, Semester } from '@/lib/types';
import type { OnboardingData } from '@/components/onboarding/types';
import { ProfileStep } from '@/components/onboarding/ProfileStep';
import { CoursesStep } from '@/components/onboarding/CoursesStep';
import { AssignmentsStep } from '@/components/onboarding/AssignmentsStep';
import { StudyTimeStep } from '@/components/onboarding/StudyTimeStep';
import { WellnessStep } from '@/components/onboarding/WellnessStep';

export default function OnboardingPage() {
  return (
    <RequireAuth>
      <div className="min-h-screen px-5">
        <header className="mx-auto flex h-16 max-w-xl items-center">
          <Logo href="/onboarding" />
        </header>
        <main className="mx-auto max-w-xl pb-16 pt-4">
          <Onboarding />
        </main>
      </div>
    </RequireAuth>
  );
}

function Onboarding() {
  const request = useApi();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [data, setData] = useState<OnboardingData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [profile, semesters, courses, assignments, availability] = await Promise.all([
        request<Profile>('GET', '/profile'),
        request<Semester[]>('GET', '/semesters'),
        request<Course[]>('GET', '/courses'),
        request<Assignment[]>('GET', '/assignments'),
        request<AvailabilityDay[]>('GET', '/availability'),
      ]);
      if (profile.onboarding_completed) {
        router.replace('/dashboard');
        return;
      }
      setData({ profile, semester: semesters.find((s) => s.is_current) ?? null, courses, assignments, availability });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your account.');
    }
  }, [request, router]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading" />;

  const update = (patch: Partial<OnboardingData>) => setData({ ...data, ...patch });
  const next = () => setStep((s) => s + 1);
  const back = () => setStep((s) => s - 1);

  const finish = async () => {
    await request('PATCH', '/profile', { onboarding_completed: true });
    router.replace('/dashboard');
  };

  switch (step) {
    case 1:
      return <ProfileStep data={data} onSaved={(patch) => { update(patch); next(); }} />;
    case 2:
      return <CoursesStep courses={data.courses} onChange={(courses) => update({ courses })} onBack={back} onNext={next} />;
    case 3:
      return (
        <AssignmentsStep
          courses={data.courses}
          assignments={data.assignments}
          onChange={(assignments) => update({ assignments })}
          onBack={back}
          onNext={next}
        />
      );
    case 4:
      return <StudyTimeStep initial={data.availability} onSaved={(availability) => { update({ availability }); next(); }} onBack={back} />;
    default:
      return <WellnessStep onBack={back} onFinish={finish} />;
  }
}
