"""Normal account-owned live QR payments. Disabled until explicitly configured."""
import os
import re
import sqlite3

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from accounts import require_account, check_csrf
from account_store import AccessError, database_path
from financial_policy import LIVE_PACKAGES, live_mode, support_email, live_payment_setup_valid
from live_store import LiveStore
from payments import Settings, TopupRequest, create_qr, response

router=APIRouter(prefix='/api/payments/live',tags=['live payments'])


class RefundReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    topup_id:str=Field(min_length=1,max_length=128)
    reason:str=Field(min_length=10,max_length=255)


class RefundReconcile(BaseModel):
    model_config=ConfigDict(extra='forbid')
    provider_id:str=Field(pattern=r'^ref_[A-Za-z0-9]+$',max_length=128)


def operator(request):
    from account_store import connect_store
    account=require_account(request);check_csrf(request,account)
    subject=os.environ.get('PAYMENT_OPERATOR_GOOGLE_SUB','').strip()
    with connect_store(database_path()) as db:
        row=db.execute('SELECT google_sub FROM accounts WHERE id=?',(account['id'],)).fetchone()
    if not subject or not row or row['google_sub']!=subject:
        raise HTTPException(403,'This operation requires the configured payment operator.')
    return account['id']


@router.post('/operator/refunds')
def review_refund(body:RefundReview,request:Request):
    actor=operator(request)
    try:
        row,created=LiveStore().hold_refund(body.topup_id,actor,body.reason.strip())
    except AccessError as error:
        raise HTTPException(409,str(error)) from None
    return response({'refund':row},201 if created else 200)


@router.post('/operator/refunds/{refund_id}/reconcile')
async def reconcile_refund(refund_id:str,body:RefundReconcile,request:Request):
    actor=operator(request);config=settings()
    # Enable only after checking the merchant's QR refund capability and resource contract.
    if os.environ.get('PAYMONGO_REFUND_RECONCILIATION_ENABLED')!='1':
        raise HTTPException(503,'Provider refund verification has not been enabled.')
    if not LiveStore().refund(refund_id):raise HTTPException(404,'Refund review not found.')
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            result=await client.get('https://api.paymongo.com/refunds/'+body.provider_id,auth=(config.key,''))
            result.raise_for_status();resource=result.json()['data']
        if resource.get('id')!=body.provider_id:raise ValueError
        row=LiveStore().reconcile_refund(refund_id,resource,actor)
    except AccessError as error:
        raise HTTPException(409,str(error)) from None
    except (httpx.HTTPError,ValueError,KeyError,TypeError,AttributeError):
        raise HTTPException(502,'Refund verification is unavailable; the hold is retained.') from None
    return response({'refund':row})


def settings(*,creation=False):
    key=os.environ.get('PAYMONGO_LIVE_SECRET_KEY','').strip()
    secret=os.environ.get('PAYMONGO_LIVE_WEBHOOK_SECRET','').strip()
    origin=os.environ.get('PAYMONGO_PUBLIC_BASE_URL','').strip().rstrip('/')
    if not live_payment_setup_valid():
        raise HTTPException(503,'Payments are temporarily unavailable.')
    if creation and (os.environ.get('LIVE_PAYMENTS_ENABLED')!='1' or not support_email()):
        raise HTTPException(503,'Top-ups are temporarily unavailable.')
    return Settings(key,secret,origin,database_path(),True)


@router.get('/config')
def config():
    try:
        settings(creation=True); enabled=True
    except (HTTPException,ValueError):
        enabled=False
    return response({'mode':'live','enabled':enabled,'packages':[p.public() for p in LIVE_PACKAGES.values()],
                     'support_email':support_email(),'run_cost':10})


@router.post('/topups')
async def create(body:TopupRequest,request:Request,idempotency_key:str=Header(default='')):
    account=require_account(request);check_csrf(request,account)
    config=settings(creation=True)
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,128}',idempotency_key):
        raise HTTPException(400,'Use a valid purchase request and try again.')
    store=LiveStore()
    try:
        row,is_new=store.begin_topup(account['id'],body.package_id,idempotency_key)
    except PermissionError as error:
        raise HTTPException(403,str(error)) from None
    except AccessError as error:
        raise HTTPException(409,str(error)) from None
    if not is_new:
        return response({'topup':store.public(row)})
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            intent,image,expires=await create_qr(client,config,row,store=store)
        row=store.register_topup(row['id'],intent,image,expires)
    except (httpx.HTTPError,ValueError,KeyError,TypeError,AttributeError,sqlite3.IntegrityError):
        store.creation_failed(row['id'])
        raise HTTPException(502,'The QR could not be verified. Your attempt is retained; check purchase history before trying a new purchase.') from None
    return response({'topup':store.public(row)},201)


@router.get('/topups/{topup_id}')
def read(topup_id:str,request:Request):
    account=require_account(request)
    row=LiveStore().get(topup_id)
    if not row or row['account_id']!=account['id']:
        raise HTTPException(404,'Purchase not found.')
    return response({'topup':LiveStore.public(row)})


@router.post('/webhook')
async def webhook(request:Request,paymongo_signature:str=Header(default='')):
    import json
    import time
    from payments import verify_signature,reconcile_topup_event
    from purchase_store import PurchaseError
    config=settings()
    raw=bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw)>1_000_000:
            raise HTTPException(413,'Notification too large.')
    verify_signature(bytes(raw),paymongo_signature,config.webhook_secret,time.time(),livemode=True)
    try:
        reconcile_topup_event(json.loads(raw),LiveStore(),livemode=True)
    except PurchaseError as error:
        raise HTTPException(503 if error.kind=='registration_pending' else 400,'Payment notification could not be applied safely.') from None
    except (ValueError,UnicodeDecodeError):
        raise HTTPException(400,'Invalid payment notification.') from None
    return response({'received':True})


async def recover_payments():
    """A bounded durable recovery sweep. A browser never supplies settlement evidence."""
    import time
    from payments import PAYMENT_API,validated_payment_intent,reconcile_topup_event
    from purchase_store import PurchaseError
    try:
        config=settings()
    except HTTPException:
        return
    store=LiveStore()
    rows=store.recovery_batch(int(time.time()))
    if not rows:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        for row in rows:
            try:
                result=await client.get(PAYMENT_API+'/payment_intents/'+row['intent_id'],auth=(config.key,''))
                result.raise_for_status();resource=result.json()['data']
                attrs=validated_payment_intent(resource,row,livemode=True)
                if resource['id']!=row['intent_id'] or attrs.get('status')!='succeeded':
                    continue
                paid=[payment for payment in attrs.get('payments',[]) if payment.get('attributes',{}).get('status')=='paid']
                if len(paid)!=1 or paid[0]['attributes'].get('payment_intent_id')!=row['intent_id']:
                    continue
                reconcile_topup_event({'data':{'type':'event','attributes':{'livemode':True,'type':'payment.paid','data':paid[0]}}},store,livemode=True)
            except (httpx.HTTPError,ValueError,KeyError,TypeError,AttributeError,HTTPException,PurchaseError):
                # Persisted backoff keeps ambiguity retryable without leaking provider data.
                continue
