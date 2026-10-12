import { useEffect, useState } from "react";
import type { RoomState } from "../types";

interface Position { turn: string; documentId: string; page: number; zoom: number; }

export function usePaperNavigation(room: RoomState) {
  const documents = room.documents ?? [];
  const turn = room.turns.at(-1);
  const turnKey = `${room.defense_view_id ?? "legacy"}:${room.turns.length}:${turn?.question ?? "lobby"}`;
  const citationDocument = documents.find(item => item.id === turn?.evidence_document_id);
  const target = citationDocument ?? documents[0];
  const initial: Position = {turn: turnKey, documentId: target?.id ?? "", page: citationDocument ? turn?.evidence_page ?? 1 : 1, zoom: 1};
  const storageKey = `defense-paper-position:${room.room_code}`;
  const [saved, setSaved] = useState<Position>(() => {
    try {
      const value = JSON.parse(sessionStorage.getItem(storageKey) ?? "null") as Position | null;
      const document = documents.find(item => item.id === value?.documentId);
      if (value && value.turn === turnKey && document && Number.isInteger(value.page) && value.page >= 1
          && value.page <= document.page_count && Number.isFinite(value.zoom) && value.zoom >= .5 && value.zoom <= 3) return value;
    } catch { /* Storage unavailable or stale. */ }
    return initial;
  });
  const valid = saved.turn === turnKey && documents.some(item => item.id === saved.documentId);
  const position = valid ? saved : {...initial, zoom: saved.zoom};
  useEffect(() => {
    if (!valid) setSaved(position);
  }, [valid, turnKey, target?.id]);
  useEffect(() => {
    try { sessionStorage.setItem(storageKey, JSON.stringify(position)); } catch { /* Reading still works. */ }
  }, [storageKey, position.turn, position.documentId, position.page, position.zoom]);
  return {
    document: documents.find(item => item.id === position.documentId),
    page: position.page, zoom: position.zoom,
    selectDocument: (documentId: string) => setSaved({...position, documentId, page: 1}),
    selectPage: (page: number) => setSaved({...position, page}),
    setZoom: (zoom: number) => setSaved({...position, zoom}),
    returnToCitation: () => setSaved({...initial, zoom: position.zoom}),
  };
}
