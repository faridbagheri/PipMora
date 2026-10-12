"""Complete account -> research -> demo order -> journal -> coach -> analytics flow."""
import uuid
from urllib.parse import urlparse,parse_qs

def new_user(client):
    email=f"test-{uuid.uuid4().hex[:12]}@example.org"
    r=client.post('/api/auth/register',json={'email':email,'name':'PipMora Tester','password':'verylong-secure-passphrase'})
    assert r.status_code==201,r.text
    assert 'httponly' in r.headers['set-cookie'].lower()
    return email

def test_full_user_journey_and_persistence(client):
    email=new_user(client)
    assert client.get('/api/auth/me').json()['email']==email
    markets=client.get('/api/markets/candles',params={'symbol':'EUR/USD','timeframe':'1h'})
    assert markets.status_code==200
    assert markets.json()['source']=='SYNTHETIC DEMONSTRATION'
    candles=markets.json()['candles']
    assert candles[-1]['high']>=candles[-1]['low'] and candles[-1]['sma20'] is not None
    events=client.get('/api/calendar',params={'currency':'USD','impact':'HIGH'}).json()['events']
    assert events and all(e['currency']=='USD' and e['impact']=='HIGH' for e in events)
    price=client.get('/api/markets/analysis').json()['price']
    opened=client.post('/api/trading/positions',json={'symbol':'EUR/USD','side':'BUY','units':10000,'stop_loss':round(price-0.009,5),'take_profit':round(price+0.009,5),'reasoning':'Test trading plan','strategy':'range'})
    assert opened.status_code==201,opened.text
    position=opened.json()
    assert position['status']=='OPEN'
    positions=client.get('/api/trading/positions').json()
    assert any(p['id']==position['id'] for p in positions)
    close=client.post(f"/api/trading/positions/{position['id']}/close",json={})
    assert close.status_code==200,close.text
    trade=close.json()
    assert trade['notes']=='Test trading plan'
    assert trade['source']=='DEMO'
    assert client.post(f"/api/trading/positions/{position['id']}/close",json={}).status_code==409
    journal=client.get('/api/journal').json()
    assert any(t['id']==trade['id'] for t in journal)
    updated=client.patch(f"/api/journal/{trade['id']}",json={'notes':'Reviewed after closing','strategy':'reviewed'})
    assert updated.status_code==200 and updated.json()['notes']=='Reviewed after closing'
    coach=client.post('/api/coach',json={'question':'Why did this trade lose money?','trade_id':trade['id']})
    assert coach.status_code==200
    assert coach.json()['mode']=='RULE_BASED_EVIDENCE'
    assert f"Trade #{trade['id']}" in coach.json()['answer']
    stats=client.get('/api/analytics').json()
    assert stats['total_trades']==1
    assert stats['insufficient_sample']
    assert abs(stats['net_pnl']-trade['pnl_usd'])<.01
    assert client.get('/api/dashboard').json()['analytics']['total_trades']==1
    assert len(client.get('/api/coach/history').json())==1
    assert client.post('/api/auth/logout',json={}).status_code==200
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':email,'password':'verylong-secure-passphrase'}).status_code==200
    assert client.get('/api/journal').json()[0]['notes']=='Reviewed after closing'

def test_validation_authorization_and_password_reset(client):
    email=new_user(client)
    price=client.get('/api/markets/analysis').json()['price']
    bad=client.post('/api/trading/positions',json={'symbol':'EUR/USD','side':'BUY','units':10000,'stop_loss':round(price+0.01,5),'take_profit':round(price-0.01,5)})
    assert bad.status_code==422
    assert client.get('/api/calendar',params={'impact':'HIGH'}).status_code==200
    assert client.get('/api/markets/candles',params={'symbol':'BTC/USD'}).status_code==422
    assert client.get('/api/journal').json()==[]
    forgot=client.post('/api/auth/forgot-password',json={'email':email}).json()
    raw=parse_qs(urlparse(forgot['development_reset_link']).query)['token'][0]
    assert client.post('/api/auth/reset-password',json={'token':raw,'password':'a-new-secure-password'}).status_code==200
    assert client.post('/api/auth/reset-password',json={'token':raw,'password':'another-secure-password'}).status_code==400
    assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':email,'password':'a-new-secure-password'}).status_code==200
    a=client.get('/api/auth/me').json()
    assert client.patch('/api/profile',json={'name':'New name','theme':'light','timezone':'Europe/Paris'}).json()['theme']=='light'
    assert client.delete('/api/profile').status_code==200
    assert client.get('/api/auth/me').status_code==401

def test_replay_no_future_leak_and_automatic_journal(client):
    new_user(client)
    r=client.post('/api/replay/sessions',json={})
    assert r.status_code==201
    state=r.json();sid=state['id']
    assert len(state['candles'])==state['cursor']+1
    assert state['event']['actual'] is None
    price=state['candles'][-1]['close']
    p=client.post('/api/trading/positions',json={'symbol':'EUR/USD','side':'BUY','units':10000,'stop_loss':round(price-.008,5),'take_profit':round(price+.008,5),'replay_session_id':sid})
    assert p.status_code==201,p.text
    r=client.post(f'/api/replay/sessions/{sid}/advance',json={'steps':20})
    assert r.status_code==200
    now=r.json();assert len(now['candles'])==now['cursor']+1
    assert now['event']['actual'] is None
    r=client.post(f'/api/replay/sessions/{sid}/advance',json={'steps':20})
    assert r.json()['event']['released'] is True
    trade=client.post(f"/api/trading/positions/{p.json()['id']}/close",json={})
    assert trade.status_code==200
    assert trade.json()['source']=='REPLAY'
    assert len(client.get('/api/journal',params={'source':'REPLAY'}).json())==1
    # Other users must never be able to advance this session.
    client.post('/api/auth/logout',json={})
    new_user(client)
    assert client.get(f'/api/replay/sessions/{sid}').status_code==404

def test_manual_journal_currency_conversion(client):
    new_user(client)
    row=client.post('/api/journal/manual',json={'symbol':'USD/JPY','side':'BUY','units':10000,'entry':150,'exit':151,'notes':'Hypothetical manual test'})
    assert row.status_code==201,row.text
    assert abs(row.json()['pnl_usd']-10000/151)<0.01
    assert client.get('/api/trading/account').json()['balance']==10000

def test_manual_dates_and_origin_check(client):
    new_user(client)
    payload={'symbol':'EUR/USD','side':'SELL','units':2500,'entry':1.09,'exit':1.08,'opened_at':'2026-01-01T10:00:00Z','closed_at':'2026-01-01T11:00:00Z'}
    row=client.post('/api/journal/manual',json=payload)
    assert row.status_code==201,row.text
    assert row.json()['opened_at'].startswith('2026-01-01T10:00:00')
    payload['closed_at']='2026-01-01T09:00:00Z'
    assert client.post('/api/journal/manual',json=payload).status_code==422
    assert client.post('/api/auth/logout',json={},headers={'Origin':'https://malicious.example'}).status_code==403
    assert client.get('/api/auth/me').status_code==200

def test_private_trade_isolation(client):
    new_user(client)
    trade=client.post('/api/journal/manual',json={'symbol':'EUR/USD','side':'BUY','units':1000,'entry':1.08,'exit':1.09}).json()
    client.post('/api/auth/logout',json={})
    new_user(client)
    assert client.get('/api/journal').json()==[]
    assert client.patch(f"/api/journal/{trade['id']}",json={'notes':'tamper'}).status_code==404
    assert client.post('/api/coach',json={'question':'Review that trade','trade_id':trade['id']}).status_code==404

def test_replay_stop_is_executed_and_journaled(client):
    new_user(client)
    r=client.post('/api/replay/sessions',json={}).json()
    px=r['candles'][-1]['close']
    order=client.post('/api/trading/positions',json={'symbol':'EUR/USD','side':'BUY','units':5000,'stop_loss':round(px-.00001,5),'take_profit':round(px+.01,5),'replay_session_id':r['id']})
    assert order.status_code==201,order.text
    for i in range(4):
        client.post(f"/api/replay/sessions/{r['id']}/advance",json={'steps':20})
        trades=client.get('/api/journal',params={'source':'REPLAY'}).json()
        if trades:break
    assert trades and trades[0]['source']=='REPLAY'
    assert client.get(f"/api/replay/sessions/{r['id']}").json()['positions']==[]
