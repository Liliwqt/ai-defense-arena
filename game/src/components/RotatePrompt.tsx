export function RotatePrompt() {
  return (
    <div
      id="rotate-prompt"
      role="status"
      className="rotate-prompt"
      style={{ display: undefined }} // let CSS media query control
    >
      <div className="rotate-content">
        <div className="rotate-icon" aria-hidden="true">
          ↻
        </div>
        <h2 className="rotate-title">
          Rotate your phone
        </h2>
        <p className="rotate-copy">
          The defense room is designed for landscape play. Turn your phone
          sideways to continue.
        </p>
      </div>
    </div>
  );
}
