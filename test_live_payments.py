"""Live payments via HTTP, all provider calls and identity credentials mocked."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
import accounts
import account_store
import payments


class LivePaymentTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        env=patch.dict(os.environ, {'DATABASE_URL':os.environ.get('DATABASE_URL','') if getattr(self,'pg_url',None) else '', 'PAYMENTS_MODE':'live','LIVE_PAYMENTS_ENABLED':'1',
            'LIVE_PAID_STARTS_ENABLED':'1','PAYMONGO_LIVE_SECRET_KEY':'sk_live_offline',
            'PAYMONGO_LIVE_WEBHOOK_SECRET':'offline-live-secret','PAYMONGO_PUBLIC_BASE_URL':'https://offline.example.test',
            'PAYMENT_SUPPORT_EMAIL':'support@example.test','LIVE_TOPUP_INVITED_EMAILS':'owner@example.test',
            'PAYMONGO_TEST_DB_PATH':str(Path(folder.name)/'live.sqlite3'),'FREE_ACCESS_VOUCHER':'offline-voucher',
            'GOOGLE_CLIENT_ID':'offline','GOOGLE_CLIENT_SECRET':'offline',
            'AUTH_SESSION_SECRET':'offline-session-secret-with-more-than32chars','AUTH_PUBLIC_BASE_URL':'http://127.0.0.1:8000'})
        env.start();self.addCleanup(env.stop)
        app=FastAPI();accounts.configure_auth(app)
        import payments_live
        app.include_router(payments_live.router)
        self.client=TestClient(app);self.client.__enter__();self.addCleanup(lambda:self.client.__exit__(None,None,None))
        self.token,self.csrf=account_store.create_google_session('owner','owner@example.test','Owner')
        self.account_id=account_store.session_account(self.token)['id']
        self.client.cookies.set(accounts.ACCOUNT_COOKIE,self.token)
        self.client.headers.update({'Origin':'http://127.0.0.1:8000','X-CSRF-Token':self.csrf})
        self.provider=AsyncMock(); mock=patch.object(payments.httpx,'AsyncClient');mock.start().return_value.__aenter__.return_value=self.provider;self.addCleanup(mock.stop)

    def resources(self,amount=100,reference='fixture'):
        image='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a1uoAAAAASUVORK5CYII='
        attrs={'livemode':True,'amount':amount,'currency':'PHP'}
        items=[{'id':'pi_'+reference,'type':'payment_intent','attributes':{**attrs,'client_key':'offline','status':'awaiting_payment_method'}},
            {'id':'pm_'+reference,'type':'payment_method','attributes':{'livemode':True,'type':'qrph'}},
            {'id':'pi_'+reference,'type':'payment_intent','attributes':{**attrs,'status':'awaiting_next_action','next_action':{'code':{'image_url':image}}}}]
        results=[]
        for item in items:
            response=Mock();response.json.return_value={'data':item};results.append(response)
        self.provider.post.side_effect=results

    def create(self,key='offline-attempt-1234',package='credits-10'):
        return self.client.post('/api/payments/live/topups',json={'package_id':package},headers={'Idempotency-Key':key})

    def paid(self,row,kind='payment.paid'):
        attrs={'livemode':True,'type':kind,'data':{'id':'pay_'+row['id'],'type':'payment','attributes':{'livemode':True,'status':kind.split('.')[1],
            'amount':row['amount'],'currency':'PHP','payment_intent_id':'pi_fixture','metadata':{'topup_id':row['id']}}}}
        raw=json.dumps({'data':{'type':'event','attributes':attrs}}).encode();stamp=str(int(payments.time.time()))
        signature=hmac.new(b'offline-live-secret',stamp.encode()+b'.'+raw,hashlib.sha256).hexdigest()
        return self.client.post('/api/payments/live/webhook',content=raw,headers={'Paymongo-Signature':f't={stamp},li={signature}'})

    def test_invited_host_creates_reuses_and_restores_frozen_live_qr(self):
        self.resources(); result=self.create();self.assertEqual(result.status_code,201,result.text)
        row=result.json()['topup'];self.assertEqual((row['amount'],row['credits'],row['mode']),(100,10,'live'))
        self.assertEqual(self.create().json()['topup']['id'],row['id']);self.assertEqual(self.provider.post.call_count,3)
        with patch.dict(os.environ,{'LIVE_TOPUP_INVITED_EMAILS':''}):
            self.assertEqual(self.create().status_code,200)
            self.assertEqual(self.create(key='new-offline-attempt-5678').status_code,403)
            self.assertEqual(self.client.get('/api/payments/live/topups/'+row['id']).status_code,200)
        self.assertEqual(self.client.get('/api/auth/me').json()['live_credits'],0)

    def test_signed_paid_awards_live_once_and_never_demo(self):
        self.resources();row=self.create().json()['topup']
        self.assertEqual(self.paid(row).status_code,200)
        self.assertEqual(self.paid(row).status_code,200)
        view=self.client.get('/api/auth/me').json()
        self.assertEqual((view['live_credits'],view['test_credits']),(10,0))
        self.assertEqual(self.paid(row,'payment.failed').status_code,200)
        self.assertEqual(self.client.get('/api/payments/live/topups/'+row['id']).json()['topup']['status'],'paid')

    def test_missed_webhook_recovers_without_browser_and_cannot_award_twice(self):
        self.resources();row=self.create().json()['topup']
        payment={'id':'pay_'+row['id'],'type':'payment','attributes':{'livemode':True,'status':'paid','amount':100,'currency':'PHP','payment_intent_id':'pi_fixture','metadata':{'topup_id':row['id']}}}
        resource={'id':'pi_fixture','type':'payment_intent','attributes':{'livemode':True,'amount':100,'currency':'PHP','status':'succeeded','payments':[payment]}}
        response=Mock();response.json.return_value={'data':resource};self.provider.get.return_value=response
        import asyncio
        from payments_live import recover_payments
        asyncio.run(recover_payments())
        self.assertEqual(self.client.get('/api/auth/me').json()['live_credits'],10)
        self.assertEqual(self.paid(row).status_code,200)
        self.assertEqual(self.client.get('/api/auth/me').json()['live_credits'],10)

    def test_owner_csrf_and_live_signature_boundaries_preserve_wallet(self):
        self.resources();row=self.create().json()['topup']
        self.client.headers['X-CSRF-Token']='wrong'
        self.assertEqual(self.create(key='other-request-1234').status_code,403)
        self.client.headers['X-CSRF-Token']=self.csrf
        other,_=account_store.create_google_session('other','other@example.test','Other')
        self.client.cookies.set(accounts.ACCOUNT_COOKIE,other)
        self.assertEqual(self.client.get('/api/payments/live/topups/'+row['id']).status_code,404)
        self.client.cookies.set(accounts.ACCOUNT_COOKIE,self.token)
        self.assertEqual(self.client.post('/api/payments/live/webhook',content='{}',headers={'Paymongo-Signature':'wrong'}).status_code,401)
        self.assertEqual(self.client.get('/api/auth/me').json()['live_credits'],0)
        self.assertEqual(self.paid(row).status_code,200)
        self.assertEqual(self.client.get('/api/auth/me').json()['live_credits'],10)
