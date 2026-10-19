
import GroupCard from "./GroupCard";

export default function ResultsPanel({
  error,
  loading,
  result,
  groups,
  positions,
  reviewCount,
  groupsWithoutColor,
  onAddGroup,
  onCopyJson,
  onClearAll,
  onRenameGroup,
  onSetGroupColor,
  onRemoveGroup,
  onMovePosition,
}) {
  const resultOrders = result ? result.groups.flatMap((group) => group.orders) : [];

  return (
    <section className="results-column" aria-label="Wyniki OCR">
      {error && <div className="notice notice--error">{error}</div>}
      {loading && <div className="card muted">Model analizuje zdjęcie...</div>}

      {(groups.length > 0 || result) && (
        <>
          <div className="card groups-toolbar">
            <strong>Zamówienia ({groups.length})</strong>
            <span className={groupsWithoutColor > 0 ? "group-warning" : "muted"}>
              {groupsWithoutColor > 0
                ? `⚠ Grupy bez koloru: ${groupsWithoutColor}`
                : groups.length > 0
                  ? "Wszystkie grupy mają kolor"
                  : ""}
            </span>
            <div className="groups-toolbar__actions">
              <button className="secondary-button" type="button" onClick={onAddGroup}>
                + Nowa grupa
              </button>
              <button className="secondary-button" type="button" onClick={onCopyJson} disabled={groups.length === 0}>
                Kopiuj JSON
              </button>
              <button className="secondary-button" type="button" onClick={onClearAll} disabled={groups.length === 0}>
                Wyczyść wszystko
              </button>
            </div>
          </div>

          {groups.length === 0 && (
            <div className="card muted">
              Nic nie rozpoznano — zobacz „Surowy odczyt OCR” poniżej.
            </div>
          )}

          {groups.map((group) => (
            <GroupCard
              key={group.id}
              group={group}
              groups={groups}
              positions={positions.filter((position) => position.groupId === group.id)}
              onRename={onRenameGroup}
              onColor={onSetGroupColor}
              onRemove={onRemoveGroup}
              onMove={onMovePosition}
            />
          ))}
        </>
      )}

      {result && result.unparsed_lines.length > 0 && (
        <div className="card unparsed-card">
          <h2>Linie, których nie udało się odczytać</h2>
          <p className="muted">
            Wyglądały na pozycje (zawierały liczby), ale nie znaleziono w nich pary wymiarów.
          </p>
          {result.unparsed_lines.map((line, index) => (
            <div className="monospace-line" key={index}>{line}</div>
          ))}
        </div>
      )}

      {/* {result && (
        <details className="card raw-details">
          <summary>Surowy odczyt OCR ({result.ocr_lines.length} linii) — do diagnozowania błędów</summary>
          <div className="ocr-lines">
            {result.ocr_lines.map((line, index) => (
              <div className="ocr-line" key={index}>
                <ConfidenceBadge value={line.confidence} />
                <span>{line.text}</span>
              </div>
            ))}
          </div>
        </details>
      )} */}
    </section>
  );
}
