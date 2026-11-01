import type { Database } from "@/lib/api";

interface Props {
  databases: Database[];
  selected: Database;
  onSelect: (id: number) => void;
}

export function DatabasePicker({ databases, selected, onSelect }: Props) {
  return (
    <label>
      Database
      <select value={selected.id} onChange={(e) => onSelect(Number(e.target.value))}>
        {databases.map((database) => (
          <option key={database.id} value={database.id}>
            {database.name} — {database.running ? "running" : "stopped"}, {database.counts?.chunks ?? 0} chunks
          </option>
        ))}
      </select>
    </label>
  );
}
