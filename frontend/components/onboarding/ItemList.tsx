'use client';

import { useState, type ReactNode } from 'react';
import { Icon } from '@/components/ui/Icon';
import { FormError } from '@/components/ui/Field';

interface Item {
  id: string;
  title: string;
  meta: ReactNode;
}

interface ItemListProps {
  items: Item[];
  onRemove: (id: string) => Promise<void>;
  empty: string;
}

/** Compact list of things added during onboarding, each removable. */
export function ItemList({ items, onRemove, empty }: ItemListProps) {
  const [error, setError] = useState<string | null>(null);

  const remove = async (id: string) => {
    setError(null);
    try {
      await onRemove(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove that item.');
    }
  };

  if (!items.length) {
    return (
      <p className="rounded-2xl border border-dashed border-line-strong px-4 py-5 text-center text-sm text-muted">{empty}</p>
    );
  }
  return (
    <div className="space-y-2">
      <ul className="divide-y divide-line rounded-2xl border border-line bg-surface">
        {items.map((item) => (
          <li key={item.id} className="flex animate-fade-up items-center justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{item.title}</p>
              <p className="truncate text-xs text-muted">{item.meta}</p>
            </div>
            <button
              onClick={() => remove(item.id)}
              className="rounded-full p-1.5 text-faint hover:bg-sunken hover:text-bad"
              aria-label={`Remove ${item.title}`}
            >
              <Icon name="trash" size={16} />
            </button>
          </li>
        ))}
      </ul>
      <FormError message={error} />
    </div>
  );
}
