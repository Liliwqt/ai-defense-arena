export interface RoomCreationProgress {
  percent: number | null;
  stage: "uploading" | "processing" | "ready";
}

interface RoomCredentials {
  room_code: string;
  player_token: string;
}

/** Percent measures the multipart upload, not server extraction or remaining time. */
export function createRoom(
  form: FormData,
  csrfToken: string,
  onProgress: (progress: RoomCreationProgress) => void,
): Promise<RoomCredentials> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.upload.addEventListener("progress", event => {
      const percent = event.lengthComputable && event.total > 0
        ? Math.min(100, Math.floor(event.loaded / event.total * 100))
        : null;
      onProgress({ percent, stage: percent === 100 ? "processing" : "uploading" });
    });
    request.upload.addEventListener("load", () => onProgress({ percent: 100, stage: "processing" }));
    request.addEventListener("load", () => {
      let body: Record<string, unknown> = {};
      try { body = JSON.parse(request.responseText); } catch { /* Use safe status fallback below. */ }
      if (request.status < 200 || request.status >= 300) {
        const detail = typeof body?.detail === "string" ? body.detail
          : typeof body?.message === "string" ? body.message : `Request failed (${request.status}).`;
        reject(new Error(detail));
      } else if (typeof body?.room_code !== "string" || !body.room_code ||
                 typeof body?.player_token !== "string" || !body.player_token) {
        reject(new Error("The server returned an incomplete room response. Please retry."));
      } else {
        onProgress({ percent: 100, stage: "ready" });
        resolve({ room_code: body.room_code, player_token: body.player_token });
      }
    });
    request.addEventListener("error", () => reject(new Error("Could not connect to create the room. Check your connection and retry.")));
    request.addEventListener("abort", () => reject(new Error("Room creation was interrupted. Please retry.")));
    request.addEventListener("timeout", () => reject(new Error("Room creation took too long. Please retry.")));
    request.open("POST", "/api/rooms");
    // Same-origin XHR sends the host session cookie; retain CSRF validation.
    request.setRequestHeader("X-CSRF-Token", csrfToken);
    request.send(form);
  });
}
