import asyncio, json
from playwright.async_api import async_playwright
B='http://localhost:8123'
PAGES=['/','/about/','/programmes/','/programmes/computer-science/','/admissions/','/news/','/student-portal/','/contact/','/404.html','/offline.html']
WIDTHS=[320,375,768,1024,1440]
async def main():
    async with async_playwright() as p:
        br=await p.chromium.launch(args=['--no-sandbox'])
        bad=[]
        for w in WIDTHS:
            ctx=await br.new_context(viewport={'width':w,'height':800}); pg=await ctx.new_page()
            for u in PAGES:
                await pg.goto(B+u); await pg.wait_for_load_state('networkidle')
                r=await pg.evaluate('''()=>{const de=document.documentElement;const over=[...document.querySelectorAll('body *')].filter(e=>{const b=e.getBoundingClientRect();return b.right>innerWidth+1&&b.width>0&&!e.closest('dialog:not([open])')&&getComputedStyle(e).position!=='absolute'}).slice(0,3).map(e=>e.tagName+'.'+e.className);
                 const small=[...document.querySelectorAll('a,button,input,select')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0&&b.height<40&&!e.closest('p,li.crumb')&&!e.closest('.crumbs')&&!e.closest('.card__title')&&!e.closest('.contact-strip')&&!e.closest('.site-footer')&&e.offsetParent!==null}).slice(0,3).map(e=>e.tagName+':'+(e.textContent||'').trim().slice(0,20)+':'+Math.round(e.getBoundingClientRect().height));
                 const fs=Math.min(...[...document.querySelectorAll('main p,main li,main a,main dd')].map(e=>parseFloat(getComputedStyle(e).fontSize)));
                 return {sw:de.scrollWidth,iw:innerWidth,over,small,fs}}''')
                if r['sw']>r['iw'] or r['over'] or r['small'] or r['fs']<14: bad.append((w,u,r))
            if w in (320,375,1440):
                await pg.goto(B+'/'); await pg.screenshot(path=f'/tmp/shot-home-{w}.png',full_page=True)
            await ctx.close()
        print('layout issues:'); 
        seen=set()
        for w,u,r in bad:
            k=(u,str(r['small']),r['sw']>r['iw'],str(r['over']),r['fs']<14)
            if k not in seen: seen.add(k); print(' ',w,u,{kk:v for kk,v in r.items() if v and kk not in('iw',)})
        print('  total flagged:',len(bad)) if bad else print('  none at 5 widths x 10 pages')
        # behaviour tests at 375
        ctx=await br.new_context(viewport={'width':375,'height':800}); pg=await ctx.new_page()
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto(B+'/'); 
        vis=await pg.is_visible('.nav'); print('desktop nav hidden on mobile:',not vis)
        await pg.click('.menu-btn'); print('drawer open:',await pg.evaluate("document.getElementById('drawer').open"))
        await pg.keyboard.press('Escape'); print('drawer closed by Esc:',not await pg.evaluate("document.getElementById('drawer').open"),'| focus back on menu button:',await pg.evaluate("document.activeElement.className"))
        await pg.keyboard.press('Tab'); print('first Tab target:',await pg.evaluate("document.activeElement.className||document.activeElement.textContent"))
        await pg.goto(B+'/programmes/'); await pg.fill('#q','cyber'); print('filter "cyber":',await pg.inner_text('#count'))
        await pg.fill('#q','zzz'); print('filter no match:',await pg.inner_text('#count'),'| empty state visible:',await pg.is_visible('#none'))
        await pg.fill('#q',''); await pg.select_option('#cat','creative'); print('category creative:',await pg.inner_text('#count'))
        await pg.goto(B+'/'); await pg.wait_for_selector('#news .state'); print('home news empty state:',(await pg.inner_text('#news .state h3')))
        # apply links all point to verified endpoint
        hrefs=await pg.evaluate("[...document.querySelectorAll('a[href*=onrender]')].map(a=>a.href)"); print('apply links:',set(hrefs))
        # offline behaviour
        await pg.goto(B+'/admissions/'); await pg.evaluate('navigator.serviceWorker.ready'); await pg.reload(); await pg.wait_for_timeout(500)
        await ctx.set_offline(True)
        await pg.click('main a.btn--gold >> nth=0'); await pg.wait_for_timeout(200)
        print('offline apply note shown:',await pg.is_visible('#offline-note'))
        r=await pg.goto(B+'/admissions/'); print('offline visited page from cache:',r.status if r else None, await pg.title())
        r=await pg.goto(B+'/contact/'); print('offline unvisited page ->',await pg.inner_text('h1'))
        await ctx.set_offline(False)
        print('page errors:',errs)
        # no-JS check of programmes
        c2=await br.new_context(viewport={'width':375,'height':800},java_script_enabled=False); p2=await c2.new_page()
        await p2.goto(B+'/programmes/'); print('no-JS programme cards:',await p2.locator('article.card').count())
        await br.close()
asyncio.run(main())
