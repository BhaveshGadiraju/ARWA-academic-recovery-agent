'use client';

export function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center space-y-4 py-12">
      <div className="flex space-x-2">
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0s' }} />
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.2s' }} />
        <div className="h-3 w-3 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0.4s' }} />
      </div>
      <p className="text-sm text-muted-foreground">Loading...</p>
    </div>
  );
}
