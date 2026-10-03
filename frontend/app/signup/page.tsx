import { AuthForm } from '@/components/auth/AuthForm';
import { AuthLayout } from '@/components/auth/AuthLayout';

export default function SignupPage() {
  return (
    <AuthLayout title="Create your account" subtitle="Two minutes of setup, then ARWA builds your plan.">
      <AuthForm mode="signup" />
    </AuthLayout>
  );
}
