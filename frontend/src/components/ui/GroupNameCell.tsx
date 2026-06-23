type GroupValue = string | string[] | null | undefined;

interface GroupNameCellProps {
  value: GroupValue;
  align?: 'left' | 'center';
}

const normalizeGroups = (value: GroupValue) => {
  const raw = Array.isArray(value) ? value : typeof value === 'string' ? value.split(',') : [];
  return raw.map((group) => group.trim()).filter(Boolean);
};

const GroupNameCell = ({ value, align = 'left' }: GroupNameCellProps) => {
  const groups = normalizeGroups(value);

  if (groups.length === 0) {
    return <span className="text-gray-400">—</span>;
  }

  return (
    <div className={`flex flex-col gap-1 ${align === 'center' ? 'items-center' : 'items-start'}`}>
      {groups.map((group) => (
        <span key={group} className="text-gray-600 text-xs font-medium">
          {group}
        </span>
      ))}
    </div>
  );
};

export default GroupNameCell;
