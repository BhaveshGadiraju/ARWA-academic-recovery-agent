import { AuthForm } from '@/components/auth/AuthForm';
import { AuthLayout } from '@/components/auth/AuthLayout';

export default function LoginPage() {
  return (
    <AuthLayout title="Welcome back" subtitle="Log in to see today’s recovery plan.">
      <AuthForm mode="login" />
    </AuthLayout>
  );
}
