"""Authenticated owner-only management; no public room or payment-provider data."""
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator

from accounts import account_response, require_owner
from account_store import AccessError
from management_store import ManagementStore

router = APIRouter(prefix='/api/manager', tags=['owner management'])


class TesterRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(max_length=254)
    enabled: StrictBool

    @field_validator('email')
    @classmethod
    def email_address(cls, value):
        import re
        value = value.strip().casefold()
        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value):
            raise ValueError('Enter a valid Google email address.')
        return value


class CreditRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    delta: StrictInt = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=5, max_length=255)

    @field_validator('delta')
    @classmethod
    def nonzero(cls, value):
        if value == 0: raise ValueError('Choose a nonzero credit adjustment.')
        return value

    @field_validator('reason')
    @classmethod
    def meaningful(cls, value):
        value = value.strip()
        if len(value) < 5: raise ValueError('Include a reason for this change.')
        return value


@router.get('/users')
def users(request: Request, q: str = Query('', max_length=254), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    require_owner(request)
    return account_response(ManagementStore().users(q, limit, offset))


@router.get('/testers')
def testers(request: Request):
    require_owner(request)
    return account_response({'testers': ManagementStore().testers()})


@router.put('/testers')
def set_tester(body: TesterRequest, request: Request):
    actor = require_owner(request, mutation=True)
    ManagementStore().set_tester(actor['id'], body.email, body.enabled)
    return account_response({'email': body.email, 'enabled': body.enabled})


@router.get('/audit')
def audit(request: Request, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    require_owner(request)
    return account_response({'entries': ManagementStore().audit(limit, offset)})


@router.post('/users/{account_id}/credits')
def adjust(account_id: str, body: CreditRequest, request: Request,
           idempotency_key: str = Header(..., min_length=16, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')):
    actor = require_owner(request, mutation=True)
    try:
        result = ManagementStore().adjust(actor['id'], account_id, body.delta, body.reason, idempotency_key)
    except LookupError:
        raise HTTPException(404, 'Account not found.') from None
    except AccessError as error:
        raise HTTPException(409, str(error)) from None
    return account_response(result)
