'use client';

import { useEffect, useState } from 'react';
import {
  analyzeStyleProfile,
  getStyleProfile,
  resyncProfile,
  saveStyleProfile,
  type Business,
  type StyleProfile,
  type StyleTraits,
} from '@/services/api';

const SCALAR: { key: keyof StyleTraits; label: string }[] = [
  { key: 'tone', label: 'טון' },
  { key: 'formality', label: 'רמת רשמיות' },
  { key: 'typical_length', label: 'אורך תשובה אופייני' },
  { key: 'emoji_usage', label: "שימוש באימוג'י" },
  { key: 'greeting_style', label: 'איך אני פותח שיחה' },
  { key: 'signoff_style', label: 'איך אני מסיים שיחה' },
  { key: 'slang', label: 'סלנג / שפה' },
  { key: 'punctuation', label: 'פיסוק' },
  { key: 'humor', label: 'הומור' },
  { key: 'directness', label: 'ישירות' },
  { key: 'warmth', label: 'חום ואמפתיה' },
  { key: 'enthusiasm', label: 'התלהבות / אנרגיה' },
  { key: 'question_style', label: 'איך אני שואל שאלות' },
  { key: 'response_speed_style', label: 'סגנון תגובה (קצר/מפורט)' },
];
const LISTS: { key: keyof StyleTraits; label: string }[] = [
  { key: 'top_emojis', label: "אימוג'ים נפוצים" },
  { key: 'personality', label: 'תכונות אופי' },
  { key: 'common_phrases', label: 'ביטויים נפוצים' },
  { key: 'dos', label: 'מה המודל כן צריך לעשות' },
  { key: 'donts', label: 'מה המודל לא צריך לעשות' },
  { key: 'languages', label: 'שפות' },
];
const BIZ: { key: keyof Business; label: string }[] = [
  { key: 'name', label: 'שם העסק' },
  { key: 'description', label: 'מה העסק עושה' },
  { key: 'products_services', label: 'מוצרים / שירותים' },
  { key: 'business_tone', label: 'טון מול לקוחות' },
  { key: 'notes', label: 'הערות נוספות לעסק' },
];

export default function ProfilePage() {
  const [summary, setSummary] = useState('');
  const [traits, setTraits] = useState<StyleTraits>({});
  const [business, setBusiness] = useState<Business>({});
  const [count, setCount] = useState(0);
  const [hasProfile, setHasProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<'analyze' | 'save' | 'resync' | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const apply = (p: StyleProfile | null, fallbackCount = 0) => {
    if (!p) return;
    setSummary(p.summary || '');
    setTraits(p.traits || {});
    setBusiness(p.business || {});
    setCount(p.analyzed_count ?? fallbackCount);
    setHasProfile(true);
  };

  useEffect(() => {
    getStyleProfile()
      .then((d) => {
        setCount(d.profile?.analyzed_count ?? d.message_count);
        apply(d.profile, d.message_count);
      })
      .finally(() => setLoading(false));
  }, []);

  const analyze = async () => {
    setBusy('analyze');
    setErr(null);
    setMsg(null);
    try {
      const d = await analyzeStyleProfile();
      apply(d.profile, count);
      setMsg('הניתוח הושלם — זה מה שהמודל הבין עליך. אפשר לערוך ולשמור.');
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'הניתוח נכשל');
    } finally {
      setBusy(null);
    }
  };

  const resync = async () => {
    setBusy('resync');
    setErr(null);
    setMsg(null);
    try {
      const d = await resyncProfile();
      apply(d.profile, count);
      setMsg('סונכרן מהצ׳אטים שבחרת ונותח מחדש מ-0 — עכשיו מדויק יותר.');
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'הסנכרון נכשל');
    } finally {
      setBusy(null);
    }
  };

  const save = async () => {
    setBusy('save');
    setErr(null);
    setMsg(null);
    try {
      const d = await saveStyleProfile(summary, traits, business);
      apply(d.profile, count);
      setMsg('נשמר! מעכשיו המודל יענה לפי הפרופיל הזה.');
    } catch (e: any) {
      setErr(e?.response?.data?.detail || 'השמירה נכשלה');
    } finally {
      setBusy(null);
    }
  };

  const setScalar = (k: keyof StyleTraits, v: string) => setTraits((t) => ({ ...t, [k]: v }));
  const setList = (k: keyof StyleTraits, v: string) =>
    setTraits((t) => ({ ...t, [k]: v.split(',').map((s) => s.trim()).filter(Boolean) }));
  const listVal = (k: keyof StyleTraits) => {
    const v = traits[k];
    return Array.isArray(v) ? v.join(', ') : (v ?? '');
  };
  const setBiz = (k: keyof Business, v: string) => setBusiness((b) => ({ ...b, [k]: v }));

  return (
    <main className="min-h-screen px-4 py-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">הפרופיל שלי</h1>
      <p className="text-sm text-gray-600 mb-4">
        כך המודל הבין מי אתה ואיך אתה עונה — מתוך ההודעות שלך. אפשר לערוך כל דבר; המודל יענה לפי מה שתשמור כאן.
      </p>

      {msg && <div className="text-sm text-emerald-700 bg-emerald-50 rounded-lg p-2 mb-3">{msg}</div>}
      {err && <div className="text-sm text-rose-700 bg-rose-50 rounded-lg p-2 mb-3">{err}</div>}

      {loading ? (
        <div className="card text-sm text-gray-500">טוען…</div>
      ) : !hasProfile ? (
        <div className="card text-center">
          <p className="text-gray-700 mb-1">עוד לא נותח פרופיל.</p>
          <p className="text-xs text-gray-500 mb-4">
            סמן את הצ׳אטים הרצויים בעמוד <b>הרשאות</b>, ואז לחץ למטה — נייבא אותם מחדש ונבנה פרופיל מדויק.
          </p>
          <div className="flex gap-2 justify-center flex-wrap">
            <button className="btn-primary" onClick={resync} disabled={busy !== null}>
              {busy === 'resync' ? 'מסנכרן ומנתח…' : '↻ סנכרן ונתח מהצ׳אטים שבחרתי'}
            </button>
            {count > 0 && (
              <button className="btn-ghost" onClick={analyze} disabled={busy !== null}>
                {busy === 'analyze' ? 'מנתח…' : 'נתח מהקיים'}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="card">
            <label className="block text-sm font-semibold mb-1">מי אני (סיכום)</label>
            <textarea className="field" rows={4} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>

          <div className="card">
            <h2 className="font-semibold mb-3">תכונות הסגנון</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {SCALAR.map(({ key, label }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-600 mb-1">{label}</label>
                  <textarea
                    className="field resize-none"
                    rows={2}
                    value={(traits[key] as string) ?? ''}
                    onChange={(e) => setScalar(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 space-y-3">
              {LISTS.map(({ key, label }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-600 mb-1">{label} (מופרד בפסיקים)</label>
                  <textarea
                    className="field resize-none"
                    rows={2}
                    value={listVal(key)}
                    onChange={(e) => setList(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-1">העסק שלי</h2>
            <p className="text-xs text-gray-500 mb-3">
              פרטי העסק עוזרים למודל לענות נכון ללקוחות. מלא מה שרלוונטי (אפשר להשאיר ריק).
            </p>
            <div className="space-y-3">
              {BIZ.map(({ key, label }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-600 mb-1">{label}</label>
                  {key === 'description' || key === 'notes' ? (
                    <textarea
                      className="field"
                      rows={2}
                      value={(business[key] as string) ?? ''}
                      onChange={(e) => setBiz(key, e.target.value)}
                    />
                  ) : (
                    <input
                      className="field"
                      value={(business[key] as string) ?? ''}
                      onChange={(e) => setBiz(key, e.target.value)}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            <button className="btn-primary" onClick={save} disabled={busy !== null}>
              {busy === 'save' ? 'שומר…' : 'שמור שינויים'}
            </button>
            <button className="btn-ghost" onClick={resync} disabled={busy !== null}>
              {busy === 'resync' ? 'מסנכרן ומנתח…' : '↻ סנכרן ונתח מהצ׳אטים שבחרתי'}
            </button>
            <button className="btn-ghost" onClick={analyze} disabled={busy !== null}>
              {busy === 'analyze' ? 'מנתח…' : 'נתח מהקיים'}
            </button>
          </div>
          <p className="text-xs text-gray-400">
            מבוסס על {count} מההודעות שלך. "סנכרן" מייבא מחדש את הצ׳אטים שסימנת בהרשאות ובונה פרופיל מ-0.
          </p>
        </div>
      )}
    </main>
  );
}
