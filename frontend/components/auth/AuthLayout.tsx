import type { ReactNode } from 'react';
import { Logo } from '@/components/ui/Logo';

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col px-5">
      <header className="mx-auto flex h-16 w-full max-w-6xl items-center">
        <Logo />
      </header>
      <div className="flex flex-1 items-center justify-center pb-16">
        <div className="w-full max-w-sm animate-fade-up">
          <h1 className="text-[28px] font-semibold tracking-tight">{title}</h1>
          <p className="mt-1.5 text-[15px] text-muted">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
