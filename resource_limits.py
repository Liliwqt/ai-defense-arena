"""Bounded admission policy; limits count work before allocation or dispatch."""
from collections import deque
import asyncio
import os
import re
import threading
import time
from ipaddress import ip_address, ip_network
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def limit(name: str, default: int, maximum: int = 10000) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        raise ValueError(f'{name} must be an integer.') from None
    if not 1 <= value <= maximum:
        raise ValueError(f'{name} must be between 1 and {maximum}.')
    return value


class RateLimit:
    def __init__(self):
        self._windows = {}
        self._lock = threading.Lock()
        self.clock = time.monotonic

    def admit(self, key: str, count: int, seconds: int = 60) -> None:
        now = self.clock()
        with self._lock:
            self._windows = {k: q for k, q in self._windows.items() if q and q[-1] > now - seconds}
            if key not in self._windows and len(self._windows) >= 4096:
                raise HTTPException(429, 'The service is busy. Retry shortly.', headers={'Retry-After': '60'})
            queue = self._windows.setdefault(key, deque())
            while queue and queue[0] <= now - seconds:
                queue.popleft()
            if len(queue) >= count:
                delay = max(1, int(seconds - (now - queue[0])) + 1)
                raise HTTPException(429, 'Request allowance used. Retry shortly.', headers={'Retry-After': str(delay)})
            queue.append(now)


creation_rate = RateLimit()
ai_rate = RateLimit()


class Capacity:
    """Reserve real in-flight resources, without retaining empty network keys."""
    def __init__(self):
        self.total = 0
        self.networks = {}
        self.lock = threading.Lock()

    def acquire(self, network: str, total: int, per_network: int) -> None:
        with self.lock:
            if self.total >= total or self.networks.get(network, 0) >= per_network:
                raise HTTPException(429, 'Connection capacity reached. Retry shortly.', headers={'Retry-After': '10'})
            self.total += 1
            self.networks[network] = self.networks.get(network, 0) + 1

    def release(self, network: str) -> None:
        with self.lock:
            count = self.networks.get(network, 0)
            if count:
                self.total -= 1
                if count == 1:
                    del self.networks[network]
                else:
                    self.networks[network] = count - 1


join_rate = RateLimit()
join_capacity = Capacity()
socket_capacity = Capacity()
socket_connect_rate = RateLimit()
socket_player_rate = RateLimit()
socket_message_rate = RateLimit()
socket_room_rate = RateLimit()
MAX_JOIN_BYTES = 4096


class JoinAdmissionMiddleware:
    """Bound anonymous JSON before framework buffering, including unknown rooms."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http' or scope['method'] != 'POST'
                or not re.fullmatch(r'/api/rooms/[^/]+/join/?', scope['path'])):
            await self.app(scope, receive, send)
            return
        network = client_network(Request(scope))
        reserved = False
        started = False
        try:
            join_rate.admit(network, 60)
            join_capacity.acquire(network, 32, 8)
            reserved = True
            async def tracked_send(message):
                nonlocal started
                if message['type'] == 'http.response.start':
                    started = True
                await send(message)

            async def forward():
                # Admit a tiny bounded buffer here, before any framework catches
                # receive errors or attempts JSON decoding.
                body = bytearray()
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > MAX_JOIN_BYTES:
                        raise HTTPException(413, 'Join request is too large.')
                    body.extend(chunk)
                    if not message.get('more_body', False):
                        break
                delivered = False
                async def admitted_receive():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                    return await receive()
                await self.app(scope, admitted_receive, tracked_send)

            # Count actual bytes, never trust a supplied Content-Length.
            await asyncio.wait_for(forward(), 10)
        except asyncio.TimeoutError:
            if not started:
                await JSONResponse({'detail': 'Joining took too long. Retry shortly.'}, status_code=408)(scope, receive, send)
        except HTTPException as error:
            if started:
                raise
            await JSONResponse({'detail': error.detail}, status_code=error.status_code, headers=error.headers)(scope, receive, send)
        finally:
            if reserved:
                join_capacity.release(network)


def client_network(request) -> str:
    """Only configured proxy peers may supply a forwarded client chain."""
    peer = request.client.host if request.client else 'unknown'
    trusted = [ip_network(item.strip()) for item in os.getenv('TRUSTED_PROXY_NETWORKS', '').split(',') if item.strip()]
    def trusted_ip(value):
        try:
            return any(ip_address(value) in net for net in trusted)
        except ValueError:
            return False
    if trusted_ip(peer):
        chain = request.headers.get('x-forwarded-for', '').split(',')
        for hop in reversed(chain):
            if not trusted_ip(peer):
                break
            peer = hop.strip()
    try:
        address = ip_address(peer)
        return str(ip_network(f'{address}/64', strict=False)) if address.version == 6 else str(address)
    except ValueError:
        return 'unknown'


class AIBudget:
    def __init__(self):
        self.attempts = {}
        self.total = 0
        self.question_budget = 8

    def reset_run(self, budget: int):
        self.attempts = {key: value for key, value in self.attempts.items() if key == 'plan'}
        self.total = 0
        self.question_budget = budget

    def remaining(self, key: str, cap: int) -> int:
        return max(0, cap - self.attempts.get(key, 0))

    def admit(self, key: str, cap: int, owner: str):
        if not self.remaining(key, cap) or (key != 'plan' and self.total >= 9 * self.question_budget + 6):
            raise HTTPException(429, 'AI retry allowance used. Use the available answer or recovery action.')
        ai_rate.admit(owner, limit('AI_OWNER_PER_MINUTE', 12))
        self.attempts[key] = self.attempts.get(key, 0) + 1
        if key != 'plan':
            self.total += 1
