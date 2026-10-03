'use client';

import { useEffect, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Field, FormError, Input } from '@/components/ui/Field';

type Mode = 'login' | 'signup';

const MIN_PASSWORD = 8;

export function AuthForm({ mode }: { mode: Mode }) {
  const { session, signIn, signUp } = useAuth();
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState(false);

  useEffect(() => {
    if (session) router.replace(mode === 'signup' ? '/onboarding' : '/dashboard');
  }, [session, mode, router]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (mode === 'signup' && password.length < MIN_PASSWORD) {
      setError(`Use at least ${MIN_PASSWORD} characters for your password.`);
      return;
    }
    setSubmitting(true);
    const result = mode === 'login' ? await signIn(email.trim(), password) : await signUp(email.trim(), password, name.trim());
    setSubmitting(false);
    if (result.error) setError(result.error);
    else if ('needsConfirmation' in result && result.needsConfirmation) setConfirmEmail(true);
  };

  if (confirmEmail) {
    return (
      <div className="rounded-3xl border border-line bg-surface p-6 text-center shadow-card">
        <p className="text-[15px] font-medium">Check your inbox</p>
        <p className="mt-2 text-sm text-muted">
          We sent a confirmation link to <span className="font-medium text-ink">{email}</span>. Open it, then come back and log in.
        </p>
        <Link href="/login" className="mt-5 inline-block text-sm font-medium text-ink underline underline-offset-4">
          Go to login
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      {mode === 'signup' && (
        <Field label="Your name">
          <Input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required maxLength={120} />
        </Field>
      )}
      <Field label="Email">
        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
      </Field>
      <Field label="Password" hint={mode === 'signup' ? `At least ${MIN_PASSWORD} characters` : undefined}>
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          required
        />
      </Field>
      <FormError message={error} />
      <Button type="submit" size="lg" className="w-full" loading={submitting} disabled={!email || !password}>
        {mode === 'login' ? 'Log in' : 'Create account'}
      </Button>
      <p className="pt-2 text-center text-sm text-muted">
        {mode === 'login' ? 'New to ARWA? ' : 'Already have an account? '}
        <Link href={mode === 'login' ? '/signup' : '/login'} className="font-medium text-ink underline underline-offset-4">
          {mode === 'login' ? 'Create an account' : 'Log in'}
        </Link>
      </p>
    </form>
  );
}
