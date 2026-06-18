interface StatusBadgeProps {
  status: string;
  /** Tailwind color classes (bg + text) for this status. */
  colorClass: string;
}

/** Small uppercase status pill. Color is supplied by the caller's status→class map. */
const StatusBadge = ({ status, colorClass }: StatusBadgeProps) => (
  <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${colorClass}`}>{status}</span>
);

export default StatusBadge;
