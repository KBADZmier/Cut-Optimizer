import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
import "./Groups.css";
import { API_BASE } from "./config";
import UploadPanel from "./components/UploadPanel";
import ResultsPanel from "./components/ResultsPanel";

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [enhance, setEnhance] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [backendStatus, setBackendStatus] = useState("sprawdzam...");
  const [dragOver, setDragOver] = useState(false);
  const [groups, setGroups] = useState([]);
  const [positions, setPositions] = useState([]);

  const inputRef = useRef(null);
  const idCounter = useRef(0);

  const nextId = () => {
    idCounter.current += 1;
    return idCounter.current;
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then((response) => response.json())
      .then((data) =>
        setBackendStatus(data.ok ? `działa (model: ${data.backend})` : "ładuje model..."),
      )
      .catch(() => setBackendStatus("NIEDOSTĘPNY — uruchom backend (uvicorn)"));
  }, []);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return undefined;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const selectFile = useCallback((newFile) => {
    if (!newFile || !newFile.type.startsWith("image/")) return;
    setFile(newFile);
    setResult(null);
    setError(null);
  }, []);

  useEffect(() => {
    function onPaste(event) {
      const item = [...(event.clipboardData?.items || [])].find((entry) =>
        entry.type.startsWith("image/"),
      );
      if (item) selectFile(item.getAsFile());
    }

    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [selectFile]);

  // ---------- Operacje na grupach ----------
  function addGroup({ markerText = "", orders = [] } = {}) {
    const groupId = nextId();
    const newPositions = orders.map((order) => ({
      ...order,
      uid: nextId(),
      groupId,
    }));

    setGroups((previous) => [
      ...previous,
      {
        id: groupId,
        name: `Zamówienie ${previous.length + 1}`,
        color: "",
        markerText,
      },
    ]);

    if (newPositions.length > 0) {
      setPositions((previous) => [...previous, ...newPositions]);
    }
  }

  function renameGroup(groupId, name) {
    setGroups((previous) =>
      previous.map((group) => (group.id === groupId ? { ...group, name } : group)),
    );
  }

  function setGroupColor(groupId, color) {
    setGroups((previous) =>
      previous.map((group) => (group.id === groupId ? { ...group, color } : group)),
    );
  }

  function removeGroup(groupId) {
    const count = positions.filter((position) => position.groupId === groupId).length;
    if (count > 0 && !window.confirm(`Usunąć grupę razem z ${count} pozycjami?`)) return;

    setGroups((previous) => previous.filter((group) => group.id !== groupId));
    setPositions((previous) => previous.filter((position) => position.groupId !== groupId));
  }

  function movePosition(uid, targetGroupId) {
    setPositions((previous) =>
      previous.map((position) =>
        position.uid === uid ? { ...position, groupId: targetGroupId } : position,
      ),
    );
  }

  function clearAll() {
    if (positions.length > 0 && !window.confirm("Usunąć wszystkie grupy i pozycje?")) return;
    setGroups([]);
    setPositions([]);
  }

  function copyJson() {
    const payload = {
      groups: groups.map((group) => ({
        name: group.name,
        color: group.color,
        marker_text: group.markerText,
        orders: positions
          .filter((position) => position.groupId === group.id)
          .map(({ uid, groupId, ...order }) => order),
      })),
    };

    navigator.clipboard?.writeText(JSON.stringify(payload, null, 2));
  }

  // ---------- OCR ----------
  async function runOcr() {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const params = new URLSearchParams({ enhance_contrast: String(enhance) });
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/ocr?${params}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Błąd HTTP ${response.status}`);
      }

      const data = await response.json();

      if (
        !Array.isArray(data.groups) ||
        data.groups.some((group) => typeof group.marker_text !== "string")
      ) {
        throw new Error(
          "Backend zwrócił odpowiedź w starym formacie (brak „marker_text” w grupach). " +
            "Podmień Backend/main.py i notes_ocr/pipeline.py + parser.py na najnowsze " +
            "wersje i zrestartuj uvicorn.",
        );
      }

      setResult(data);
      data.groups.forEach((group) =>
        addGroup({ markerText: group.marker_text, orders: group.orders }),
      );
    } catch (err) {
      setError(
        err instanceof TypeError
          ? `Nie można połączyć się z backendem (${API_BASE}). Czy uvicorn działa?`
          : err.message,
      );
    } finally {
      setLoading(false);
    }
  }

  const resultOrders = result ? result.groups.flatMap((group) => group.orders) : [];
  const reviewCount = resultOrders.filter((order) => order.needs_review).length;
  const groupsWithoutColor = groups.filter(
    (group) => !group.color && positions.some((position) => position.groupId === group.id),
  ).length;

  function handleDragOver(event) {
    event.preventDefault();
    setDragOver(true);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragOver(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  return (
    <main className="app-page">
      <header className="app-header">
        <h1>Odczyt zamówień ze zdjęcia notatki</h1>
        <p className="muted backend-status">
          Backend: <strong>{backendStatus}</strong>
          <span className="backend-url">{API_BASE}</span>
        </p>
      </header>

      <div className="app-layout">
        <UploadPanel
          inputRef={inputRef}
          previewUrl={previewUrl}
          file={file}
          enhance={enhance}
          loading={loading}
          dragOver={dragOver}
          onSelectFile={selectFile}
          onEnhanceChange={setEnhance}
          onRunOcr={runOcr}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        />

        <ResultsPanel
          error={error}
          loading={loading}
          result={result}
          groups={groups}
          positions={positions}
          reviewCount={reviewCount}
          groupsWithoutColor={groupsWithoutColor}
          onAddGroup={() => addGroup()}
          onCopyJson={copyJson}
          onClearAll={clearAll}
          onRenameGroup={renameGroup}
          onSetGroupColor={setGroupColor}
          onRemoveGroup={removeGroup}
          onMovePosition={movePosition}
        />
      </div>
    </main>
  );
}
