'use client';

import { useEffect, useState } from 'react';
import { useAssignmentActions } from '@/hooks/useAssignmentActions';
import { formatMinutes } from '@/lib/format';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/Field';
import { Modal } from '@/components/ui/Modal';

export interface FocusTarget {
  assignmentId: string;
  title: string;
  plannedMinutes: number;
}

interface Props {
  target: FocusTarget | null;
  onClose: () => void;
  onLogged: () => void;
}

/**
 * Elapsed seconds measured from the wall clock. The interval only triggers
 * re-renders, because browsers throttle timers in background tabs and counting
 * ticks would under-log a session the student spent in another tab.
 */
function useElapsedSeconds(running: boolean, resetKey: unknown) {
  const [bankedMs, setBankedMs] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [, setTick] = useState(0);

  useEffect(() => {
    setBankedMs(0);
  }, [resetKey]);

  useEffect(() => {
    if (!running) return;
    const start = Date.now();
    setStartedAt(start);
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => {
      clearInterval(id);
      setBankedMs((ms) => ms + Date.now() - start);
      setStartedAt(null);
    };
  }, [running, resetKey]);

  const liveMs = startedAt === null ? 0 : Date.now() - startedAt;
  return Math.floor((bankedMs + liveMs) / 1000);
}

/** A focus timer for one plan block. Finishing logs a real study session. */
export function FocusSession({ target, onClose, onLogged }: Props) {
  const { logStudy, setCompleted } = useAssignmentActions();
  const [running, setRunning] = useState(true);
  const seconds = useElapsedSeconds(Boolean(target) && running, target);
  const [markDone, setMarkDone] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRunning(true);
    setMarkDone(false);
    setError(null);
  }, [target]);

  if (!target) return null;

  const minutes = Math.floor(seconds / 60);
  const clock = `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  const progress = Math.min(1, seconds / (target.plannedMinutes * 60));

  const finish = async () => {
    setSaving(true);
    setError(null);
    try {
      if (minutes >= 1) await logStudy(target.assignmentId, minutes);
      if (markDone) await setCompleted(target.assignmentId, true);
      onLogged();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save this session.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open title="Focus session" onClose={onClose}>
      <p className="text-center text-sm text-muted">{target.title}</p>
      <p className="mt-4 text-center text-[56px] font-semibold tabular-nums tracking-tight">{clock}</p>
      <div className="mx-auto mt-3 h-1.5 max-w-xs overflow-hidden rounded-full bg-sunken">
        <div className="h-full rounded-full bg-ink transition-[width] duration-1000" style={{ width: `${progress * 100}%` }} />
      </div>
      <p className="mt-2 text-center text-xs text-faint">Planned block: {formatMinutes(target.plannedMinutes)}</p>

      <label className="mt-6 flex items-center justify-center gap-2 text-sm text-ink-soft">
        <input type="checkbox" checked={markDone} onChange={(e) => setMarkDone(e.target.checked)} className="h-4 w-4 accent-[var(--color-ink)]" />
        I finished this assignment
      </label>
      <div className="mt-4">
        <FormError message={error} />
      </div>
      <div className="mt-6 flex justify-center gap-3">
        <Button variant="secondary" onClick={() => setRunning((r) => !r)}>
          {running ? 'Pause' : 'Resume'}
        </Button>
        <Button onClick={finish} loading={saving} disabled={minutes < 1 && !markDone}>
          {minutes >= 1 ? `Finish & log ${formatMinutes(minutes)}` : 'Finish'}
        </Button>
      </div>
    </Modal>
  );
}
