export default function UploadPanel({
  inputRef,
  previewUrl,
  file,
  enhance,
  loading,
  dragOver,
  onSelectFile,
  onEnhanceChange,
  onRunOcr,
  onDragOver,
  onDragLeave,
  onDrop,
  onDragEnter,
}) {
  return (
    <section className="card upload-card" aria-label="Zdjęcie i ustawienia">
      <div
        className={`dropzone${dragOver ? " dropzone--active" : ""}${previewUrl ? " dropzone--with-preview" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        {previewUrl ? (
          <img className="image-preview" src={previewUrl} alt="Podgląd wybranego zdjęcia" />
        ) : (
          <span className="muted dropzone-hint">
            Kliknij lub przeciągnij zdjęcie tutaj
          </span>
        )}
      </div>

      <input
        ref={inputRef}
        className="file-input"
        type="file"
        accept="image/*"
        onChange={(event) => onSelectFile(event.target.files?.[0])}
      />

      <div className="settings">
        <label className="setting-label">
          <input
            type="checkbox"
            checked={enhance}
            onChange={(event) => onEnhanceChange(event.target.checked)}
          />
          Wyrównaj oświetlenie (CLAHE)
        </label>

        <button className="primary-button" onClick={onRunOcr} disabled={!file || loading}>
          {loading ? "Odczytuję..." : "Odczytaj zamówienia"}
        </button>

      </div>
    </section>
  );
}
