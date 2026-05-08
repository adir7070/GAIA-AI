type Props = { confidence: number; label: 'ANSWER_NOW' | 'ASK_USER_FOR_TEACHING' | 'UNSURE' };

const COLOR: Record<Props['label'], string> = {
  ANSWER_NOW: 'bg-emerald-100 text-emerald-800',
  UNSURE: 'bg-amber-100 text-amber-800',
  ASK_USER_FOR_TEACHING: 'bg-rose-100 text-rose-800',
};

const TEXT: Record<Props['label'], string> = {
  ANSWER_NOW: 'בטוח',
  UNSURE: 'לא בטוח',
  ASK_USER_FOR_TEACHING: 'לא יודע',
};

export default function ConfidenceBadge({ confidence, label }: Props) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${COLOR[label]}`}>
      <span>{TEXT[label]}</span>
      <span className="opacity-60">· {(confidence * 100).toFixed(0)}%</span>
    </span>
  );
}
