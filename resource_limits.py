"""Bounded admission policy; limits count work before allocation or dispatch."""
from collections import deque
import os
import threading
import time
from ipaddress import ip_address, ip_network
from fastapi import HTTPException


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

    def admit(self, key: str, count: int, seconds: int = 60) -> None:
        now = time.monotonic()
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
