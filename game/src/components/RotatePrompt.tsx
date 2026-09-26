export function RotatePrompt() {
  return (
    <div
      id="rotate-prompt"
      role="status"
      className="hidden portrait:grid fixed inset-0 z-30 place-items-center bg-[#081729f5] p-6 text-center"
      style={{ display: undefined }} // let CSS media query control
    >
      <div className="max-w-[320px]">
        <div className="text-[4rem] text-[#77c7f7] leading-none" aria-hidden="true">
          ↻
        </div>
        <h2 className="text-[1.65rem] my-[9px] text-[#eaf2ff]">
          Rotate your phone
        </h2>
        <p className="text-[#bbd3e8] leading-relaxed m-0">
          The defense room is designed for landscape play. Turn your phone
          sideways to continue.
        </p>
      </div>
    </div>
  );
}
