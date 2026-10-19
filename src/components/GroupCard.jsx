import ConfidenceBadge from "./ConfidenceBadge";
import { COLORS } from "../config";
import { formatMm } from "../utils/formatters";

export default function GroupCard({
  group,
  groups,
  positions,
  onRename,
  onColor,
  onRemove,
  onMove,
}) {
  const needsColor = !group.color && positions.length > 0;

  return (
    <div className={`card group-card${needsColor ? " group-card--no-color" : ""}`}>
      <div className="group-header">
        <input
          className="group-name-input"
          value={group.name}
          onChange={(event) => onRename(group.id, event.target.value)}
          aria-label="Nazwa zamówienia"
        />

        <label className="group-color">
          <span>Kolor:</span>
          <select
            value={group.color}
            onChange={(event) => onColor(group.id, event.target.value)}
            aria-label={`Kolor zamówienia ${group.name}`}
          >
            <option value="">— wybierz kolor —</option>
            {COLORS.map((color) => (
              <option key={color} value={color}>
                {color}
              </option>
            ))}
          </select>
        </label>

        {group.markerText && (
          <span
            className="group-marker"
            title="Tekst odczytany z notatki przy tej grupie -- podpowiedź przy wyborze koloru"
          >
            z notatki: „{group.markerText}”
          </span>
        )}

        <span className="muted group-count">{positions.length} poz.</span>
        <button
          className="secondary-button"
          type="button"
          onClick={() => onRemove(group.id)}
        >
          Usuń grupę
        </button>
      </div>

      {positions.length === 0 ? (
        <p className="muted">
          Grupa jest pusta — przenieś tu pozycje z innej grupy.
        </p>
      ) : (
        <div className="table-scroll">
          <table className="orders-table">
            <thead>
              <tr>
                {["Nazwa", "Dł. [mm]", "Wys. [mm]", "Szt.", "Odczytana linia", "Grupa"].map(
                  (heading) => (
                    <th key={heading}>{heading}</th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => (
                <tr
                  key={position.uid}
                  className={position.needs_review ? "order-row--review" : ""}
                >
                  <td><strong>{position.name}</strong></td>
                  <td>{formatMm(position.length_mm)}</td>
                  <td>{formatMm(position.height_mm)}</td>
                  <td>{position.quantity}</td>
                  <td className="raw-text-cell">
                    <span>{position.raw_text}</span>
                    {position.warnings.map((warning, index) => (
                      <div className="warning-text" key={index}>⚠ {warning}</div>
                    ))}
                  </td>
                  <td>
                    <select
                      value={position.groupId}
                      onChange={(event) => onMove(position.uid, Number(event.target.value))}
                      aria-label={`Przenieś pozycję ${position.name} do grupy`}
                    >
                      {groups.map((target) => (
                        <option key={target.id} value={target.id}>
                          {target.name || `Grupa ${target.id}`}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
