"""Authenticated transport plus coordinator views; external AI is mocked."""

import unittest
from fastapi.testclient import TestClient

from backend import game_server as server
from backend.rooms.coordinator import VerifiedActor
from tests.offline_accounts import authenticate


class RoomCoordinationProtocolTests(unittest.TestCase):
    def test_created_room_owns_coordinator_and_guests_reconnect_with_private_views(self):
        server.rooms.clear()
        authenticate(self)
        with TestClient(server.app) as client:
            account = authenticate(self, client)
            response = client.post("/api/rooms", data={"host_name": "Alex"},
                                   files=[("files", ("README.md", b"# Uploaded source\n"))])
            self.assertEqual(response.status_code, 201, response.text)
            host = response.json()
            guest = client.post(f"/api/rooms/{host['room_code']}/join", json={"name": "Sam"}).json()
            room = server.rooms[host["room_code"]]
            self.assertEqual(room.coordinator.view(VerifiedActor(host["player_token"], account["id"]))["self_seat"], 0)
            with client.websocket_connect(f"/ws/{room.code}") as host_socket:
                host_socket.send_json({"type": "hello", "token": host["player_token"]})
                host_socket.receive_json()
                with client.websocket_connect(f"/ws/{room.code}") as guest_socket:
                    guest_socket.send_json({"type": "hello", "token": guest["player_token"]})
                    guest_socket.receive_json()
                    host_socket.receive_json()
                    guest_socket.send_json({"type": "send_chat", "text": "  team note  ", "name": "Forged", "account_id": "other"})
                    guest_state = guest_socket.receive_json()["state"]
                    host_state = host_socket.receive_json()["state"]
                    self.assertEqual(guest_state["chat"], host_state["chat"])
                    self.assertEqual(guest_state["chat"][0]["name"], "Sam")
                    self.assertEqual(guest_state["chat"][0]["text"], "team note")
                    self.assertNotIn(account["id"], str(guest_state))
                    guest_socket.send_json({"type": "deadline", "seat": 1})
                    self.assertEqual(guest_socket.receive_json()["message"], "Unknown room action.")
                host_socket.receive_json()
                with client.websocket_connect(f"/ws/{room.code}") as reconnected:
                    reconnected.send_json({"type": "hello", "token": guest["player_token"]})
                    state = reconnected.receive_json()["state"]
                    self.assertEqual(state["self_seat"], 1)
                    self.assertFalse(state["self_is_host"])
                    self.assertEqual(state["chat"][0]["text"], "team note")
