import type { DrawerMode, RoomState } from "../types";

interface HUDProps {
  roomState: RoomState | null;
  roomCode: string | null;
  previewMode: boolean;
  onOpenDrawer: (mode: DrawerMode) => void;
}

export function HUD({ roomState, roomCode, previewMode, onOpenDrawer }: HUDProps) {
  const phase = roomState?.phase;
  const answered = (roomState?.turns ?? []).filter((t) => t.answer).length;

  const pillCode = roomState
    ? `Room ${roomState.room_code || roomCode || "—"}`
    : "No room yet";

  const pillProgress =
    phase === "complete"
      ? "COMPLETE"
      : roomState
        ? `${answered} ANSWERED`
        : "READY";

  return (
    <header
      className="absolute inset-x-0 top-0 z-10 flex items-center justify-between gap-4 min-h-[74px] px-[clamp(14px,2.3vw,30px)] py-3"
      style={{
        background: "linear-gradient(#081729ed, #0817299c 72%, transparent)",
      }}
    >
      <div className="min-w-0">
        <p
          className="text-[#85acd4] text-[0.68rem] font-black tracking-[0.16em] mb-1"
          aria-hidden="true"
        >
          PROJECT DEFENSE SIMULATOR
        </p>
        <h1
          className="text-[clamp(1.15rem,2vw,1.9rem)] leading-tight tracking-[-0.04em] m-0 whitespace-nowrap text-[#eaf2ff]"
        >
          AI Defense Arena
        </h1>
      </div>
      <div className="flex items-center justify-end gap-2 min-w-0 flex-wrap">
        <span
          id="room-pill"
          className="inline-flex items-center min-h-[34px] px-3 py-[7px] rounded-full text-[0.73rem] font-black whitespace-nowrap bg-[#18334f] border border-[#406688] text-[#cae9ff]"
        >
          {pillCode}
        </span>
        <span
          id="round-indicator"
          className="inline-flex items-center min-h-[34px] px-3 py-[7px] rounded-full text-[0.73rem] font-black whitespace-nowrap bg-[#291f3c] border border-[#725789] text-[#ead8ff]"
        >
          {pillProgress}
        </span>
        <button
          type="button"
          onClick={() => onOpenDrawer("controls")}
          aria-controls="drawer"
          className="bg-[#17314c] border border-[#4b769c] rounded-[9px] text-[#eef7ff] px-3 py-2 text-[0.78rem] font-black min-h-[34px] hover:bg-[#315879]"
        >
          Controls
        </button>
        {!previewMode && (
          <button
            type="button"
            onClick={() => onOpenDrawer("transcript")}
            aria-controls="drawer"
            className="bg-[#17314c] border border-[#4b769c] rounded-[9px] text-[#eef7ff] px-3 py-2 text-[0.78rem] font-black min-h-[34px] hover:bg-[#315879]"
          >
            Transcript
          </button>
        )}
      </div>
    </header>
  );
}
