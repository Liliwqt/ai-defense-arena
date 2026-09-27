export function RotatePrompt() {
  return (
    <div
      id="rotate-prompt"
      role="status"
      className="hidden portrait:grid fixed inset-0 z-30 place-items-center bg-[#e5f0fbf5] p-6 text-center"
      style={{ display: undefined }} // let CSS media query control
    >
      <div className="max-w-[320px]">
        <div className="text-[4rem] text-[#3a8fe1] leading-none" aria-hidden="true">
          ↻
        </div>
        <h2 className="text-[1.65rem] my-[9px] text-[#1b2944]">
          Rotate your phone
        </h2>
        <p className="text-[#526984] leading-relaxed m-0">
          The defense room is designed for landscape play. Turn your phone
          sideways to continue.
        </p>
      </div>
    </div>
  );
}
