'use client';

import { useState } from 'react';
import ConfidenceBadge from './ConfidenceBadge';
import { sendFeedback, sendMessage } from '@/services/api';
import { useSuggestions } from '@/store/suggestionsStore';
import type { NewSuggestion } from '@/services/socket';

export default function SuggestionCard({ s }: { s: NewSuggestion }) {
  const remove = useSuggestions((st) => st.remove);
  const [edit, setEdit] = useState(s.suggestion);
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);

  const onApprove = async () => {
    setBusy(true);
    try {
      await sendMessage(s.contact_id, edit);
      await sendFeedback(s.suggestion_id, edit, edit === s.suggestion ? 'approve' : 'edit');
      remove(s.suggestion_id);
    } finally {
      setBusy(false);
    }
  };
  const onSkip = async () => {
    setBusy(true);
    try {
      await sendFeedback(s.suggestion_id, '', 'skip');
      remove(s.suggestion_id);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <strong className="text-sm">{s.contact_name}</strong>
          <ConfidenceBadge confidence={s.confidence} label={s.label} />
        </div>
      </div>
      <div className="text-sm text-gray-700 mb-3">
        <span className="text-gray-400">נכנס: </span>
        {s.incoming}
      </div>
      <div className="text-base mb-3 whitespace-pre-wrap">
        {editing ? (
          <textarea
            className="field min-h-[80px]"
            value={edit}
            onChange={(e) => setEdit(e.target.value)}
          />
        ) : (
          <div onClick={() => setEditing(true)} className="cursor-text">
            {edit}
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <button className="btn-primary" disabled={busy} onClick={onApprove}>
          שלח
        </button>
        <button
          className="btn-ghost"
          disabled={busy}
          onClick={() => setEditing((v) => !v)}
        >
          {editing ? 'סיים עריכה' : 'ערוך'}
        </button>
        <button className="btn-danger" disabled={busy} onClick={onSkip}>
          דלג
        </button>
      </div>
    </div>
  );
}
