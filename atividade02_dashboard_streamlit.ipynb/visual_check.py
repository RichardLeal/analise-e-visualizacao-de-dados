"""Rendered desktop checks. Optional dev dependency: pip install playwright.

Uses installed Chrome in an isolated temporary profile; server must be on :8501.
Screenshots and measurements are saved in artifacts/visual/.
"""
import json
import os
import time
from urllib.request import urlopen
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8501")
ROOT = Path(__file__).parent
OUT = ROOT / "artifacts/visual"
OUT.mkdir(parents=True, exist_ok=True)

MEASURE = """() => {
 const r = el => {const b=el.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,bottom:b.bottom,right:b.right};};
 const panels = [...document.querySelectorAll('.card')].filter(el=>el.getClientRects().length).map(el=>({id:el.id || 'filters',...r(el),scrollHeight:el.scrollHeight,clientHeight:el.clientHeight,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth}));
 return {width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight,panels,
  error:document.querySelector('#error').hidden?null:document.querySelector('#error').textContent,
  plotly:document.querySelectorAll('.js-plotly-plot').length,
  bars:!!document.querySelector('#bars svg'),map:!!document.querySelector('#map').contentDocument?.querySelector('.leaflet-container')};
}"""

def component(page):
    page.wait_for_selector('iframe[title*="desktop_dashboard"]', timeout=60000)
    element = page.locator('iframe[title*="desktop_dashboard"]').element_handle()
    frame = element.content_frame()
    frame.wait_for_selector('#overview-bars .main-svg', timeout=60000)
    frame.wait_for_function("document.querySelector('#loading').hidden", timeout=60000)
    return frame

def assert_layout(layout):
    assert layout['scrollHeight'] <= layout['height']+1, layout
    assert layout['scrollWidth'] <= layout['width']+1, layout
    assert layout['outer']['scrollHeight'] <= layout['outer']['height']+1, layout
    assert layout['outer']['scrollWidth'] <= layout['outer']['width']+1, layout
    assert layout['outer']['mainScroll'] <= layout['outer']['mainHeight']+1, layout
    assert not layout['error'], layout
    for panel in layout['panels']:
        assert panel['bottom'] <= layout['height']+1, panel
        assert panel['right'] <= layout['width']+1, panel
        assert panel['scrollHeight'] <= panel['clientHeight']+1, panel
        assert panel['scrollWidth'] <= panel['clientWidth']+1, panel

def interactions(page, frame, width, height):
    frame.locator('#comparison').click()
    for name in ['PETRÓPOLIS','MENINO DEUS','MOINHOS DE VENTO','TRÊS FIGUEIRAS']:
        frame.locator('#picker-options').get_by_label(name, exact=True).check()
    assert frame.locator('#picker-options input:disabled').count() > 0
    page.screenshot(path=str(OUT/f'seletor-{width}x{height}.png'))
    frame.locator('#picker-apply').click()
    frame.wait_for_function("document.querySelectorAll('#comparison-table thead th').length===5")
    frame.locator('#focus').select_option('MENINO DEUS')
    frame.wait_for_function("payload.state.focus==='MENINO DEUS'")
    frame.locator('#construction-active').check()
    frame.wait_for_function('payload.state.construction_active')
    frame.locator('#include-missing').uncheck()
    frame.wait_for_function('!payload.state.include_missing')
    page.wait_for_timeout(700)
    compared=frame.evaluate(MEASURE)
    assert compared['scrollHeight'] <= compared['height']+1
    assert compared['scrollWidth'] <= compared['width']+1
    for panel in compared['panels']:
        assert panel['scrollHeight'] <= panel['clientHeight']+1, panel
        assert panel['scrollWidth'] <= panel['clientWidth']+1, panel
    page.screenshot(path=str(OUT/f'comparacao-{width}x{height}.png'))
    for metric in ['registros','compatibilidade','variacao','base_de_calculo','valor_m2']:
        frame.locator(f'input[name="map-metric"][value="{metric}"]').check()
        frame.wait_for_function('(metric)=>payload.state.metric===metric',arg=metric)
    frame.locator('#reset').click()
    frame.wait_for_function('!payload.state.construction_active && payload.state.comparison.length===0')
    # Actual typed bounds, in Brazilian notation; blur commits the filter.
    field=frame.get_by_label('Área privativa (m²): limite inferior',exact=True)
    field.fill('50');field.press('Tab')
    frame.wait_for_function('payload.state.area[0]===50')
    field=frame.get_by_label('Área privativa (m²): limite superior',exact=True)
    field.fill('80');field.press('Tab')
    frame.wait_for_function('payload.state.area[1]===80')
    frame.locator('#neighborhoods').click()
    frame.locator('#picker-options').get_by_label('JAR ITU SABARA',exact=True).check()
    frame.locator('#picker-apply').click()
    frame.wait_for_function("payload.state.neighborhoods.includes('JAR ITU SABARA')")
    assert 'Sem polígono' in frame.locator('#focus-note').inner_text()
    frame.locator('#minimum').fill('116199');frame.locator('#minimum').press('Tab')
    frame.wait_for_function('payload.eligible_count===0')
    frame.locator('#reset').click()
    frame.wait_for_function('payload.state.minimum===100 && payload.state.neighborhoods.length===0')
    frame.locator('#about-button').click()
    assert frame.locator('#info').is_visible()
    frame.locator('#info-close').click()

def capture_overview(page, frame, width, height, name):
    """Expand the capture viewport to include Streamlit's internal scroll container."""
    content_height = frame.evaluate("Math.ceil(document.querySelector('#dashboard').scrollHeight)+4")
    page.set_viewport_size({'width': width, 'height': max(height, content_height)})
    frame.locator('h1').scroll_into_view_if_needed()
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT/f'{name}-{width}x{height}.png'),full_page=True)
    page.set_viewport_size({'width': width, 'height': height})
    page.wait_for_timeout(600)


def overview_checks(page, frame, width, height, interactions_enabled):
    frame.wait_for_function("payload.state.view==='overview'")
    frame.locator('#overview-map').element_handle().content_frame().wait_for_selector('.leaflet-container')
    page.wait_for_timeout(1200)
    layout = frame.evaluate("""() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
      error_hidden:document.querySelector('#error').hidden, questions:[...document.querySelectorAll('.overview-line h2,.overview-bottom h2')].map(el=>({text:el.textContent,width:el.clientWidth,scroll:el.scrollWidth})),
      charts:[...document.querySelectorAll('.overview-plot')].map(el=>({width:el.clientWidth,height:el.clientHeight,svg:!!el.querySelector('svg')}))})""")
    assert layout['scrollWidth'] <= layout['width']+1, layout
    assert layout['error_hidden'], layout
    assert all(q['scroll'] <= q['width'] for q in layout['questions']), layout
    assert all(c['svg'] and c['height'] >= 200 for c in layout['charts']), layout
    # Overview is allowed vertical scrolling; capture its complete document.
    frame.locator('h1').scroll_into_view_if_needed()
    page.screenshot(path=str(OUT/f'overview-{width}x{height}.png'),full_page=True)
    capture_overview(page,frame,width,height,'overview-content')
    (OUT/f'overview-{width}x{height}.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
    if not interactions_enabled:
        return
    frame.locator('#overview-select').select_option('PETRÓPOLIS')
    frame.wait_for_function("payload.overview.focus.name==='PETRÓPOLIS' && document.querySelector('#loading').hidden")
    assert len(frame.evaluate('payload.overview.line.data')) == 2
    frame.locator('#overview-order').select_option('asc')
    frame.wait_for_function('payload.state.overview.ascending')
    frame.locator('#overview-count').select_option('5')
    frame.wait_for_function('payload.overview.ranking.length===5')
    frame.wait_for_function("document.querySelector('#overview-bars').data[0].y.length===5")
    # Plotly's transparent drag layer receives pointer events over the visible bars.
    frame.locator('#overview-bars .barlayer .point path').first.click(force=True)
    frame.wait_for_function('payload.state.overview.focus===payload.overview.ranking[0].bairro')
    frame.locator('#overview-map').scroll_into_view_if_needed()
    map_frame=frame.locator('#overview-map').element_handle().content_frame()
    map_frame.wait_for_selector('.leaflet-interactive')
    # Leaflet's actual layer handler exercises the iframe message bridge.
    map_frame.evaluate("""() => {const geo=Object.values(window).find(v=>v instanceof L.GeoJSON); const layer=geo.getLayers().find(l=>l.feature.properties.bairro_oficial==='MENINO DEUS'); layer.fire('click');}""")
    frame.wait_for_function("payload.state.overview.focus==='MENINO DEUS'")
    frame.locator('#overview-analyze').click()
    frame.wait_for_function("payload.state.view==='analysis' && payload.state.focus==='MENINO DEUS'")
    assert frame.locator('#focus').input_value() == 'MENINO DEUS'
    field=frame.get_by_label('Área privativa (m²): limite inferior',exact=True)
    field.fill('50');field.press('Tab')
    frame.wait_for_function('payload.state.area[0]===50')
    frame.locator('[data-view="overview"]').click()
    frame.wait_for_function("payload.state.view==='overview'")
    assert frame.evaluate('payload.overview.summary.total') == 116198
    frame.locator('#about-button').click()
    assert frame.locator('#info').is_visible()
    frame.locator('#info-close').click()
    frame.locator('[data-view="analysis"]').click()
    frame.wait_for_function("payload.state.view==='analysis'")
    assert frame.evaluate('payload.state.area[0]') == 50
    assert frame.locator('#comparison-table').is_visible()
    frame.locator('#reset').click()
    frame.wait_for_function('payload.state.area[0]===payload.defaults.area[0]')
    frame.locator('[data-view="overview"]').click()
    frame.wait_for_function("payload.state.view==='overview'")
    # No eligible neighborhood: explicit empty bars, city series retained, neutral map.
    frame.locator('#overview-minimum').fill('116199');frame.locator('#overview-minimum').press('Tab')
    frame.wait_for_function('payload.overview.eligible_count===0')
    assert frame.evaluate('payload.overview.summary.total') == 116198
    assert frame.evaluate('payload.overview.focus.sufficient') is False
    frame.locator('#overview-minimum').fill('100');frame.locator('#overview-minimum').press('Tab')
    frame.wait_for_function('payload.state.overview.minimum===100')
    frame.locator('#overview-order').select_option('desc')
    frame.wait_for_function('!payload.state.overview.ascending')
    frame.locator('#overview-count').select_option('10')
    frame.wait_for_function('payload.state.overview.count===10')
    frame.locator('#overview-select').select_option('PETRÓPOLIS')
    frame.wait_for_function("payload.overview.focus.name==='PETRÓPOLIS'")
    capture_overview(page,frame,width,height,'overview-selected')
    frame.locator('h1').scroll_into_view_if_needed()
    print(f'Overview interactions passed: {width}x{height}',flush=True)


def run(interactions_enabled=True):
    results=[]
    deadline=time.monotonic()+30
    while True:
        try:
            with urlopen(BASE_URL+'/_stcore/health',timeout=2) as response:
                if response.status==200:
                    break
        except OSError:
            if time.monotonic()>=deadline:
                raise
            time.sleep(.25)
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True)
        for width,height in [(1366,768),(1536,864),(1920,1080)]:
            page=browser.new_page(viewport={"width":width,"height":height},device_scale_factor=1,locale="pt-BR")
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(BASE_URL,wait_until="domcontentloaded")
            frame=component(page)
            overview_checks(page,frame,width,height,interactions_enabled)
            frame.locator('[data-view="analysis"]').click()
            frame.wait_for_function("payload.state.view==='analysis'")
            frame.wait_for_selector('#bars svg')
            page.wait_for_timeout(2500)
            layout=frame.evaluate(MEASURE)
            layout["outer"]=page.evaluate("() => ({height:innerHeight,width:innerWidth,scrollHeight:document.documentElement.scrollHeight,scrollWidth:document.documentElement.scrollWidth,mainHeight:document.querySelector('[data-testid=stMain]')?.clientHeight,mainScroll:document.querySelector('[data-testid=stMain]')?.scrollHeight})")
            layout["errors"]=errors
            assert_layout(layout)
            assert not errors, errors
            page.screenshot(path=str(OUT/f"dashboard-{width}x{height}.png"),full_page=True)
            map_frame=frame.locator('#map').element_handle().content_frame()
            legend=map_frame.locator('.legend').evaluate('(el)=>{const r=el.getBoundingClientRect();return {x:r.x,right:r.right,w:innerWidth}}')
            assert legend['x']>=0 and legend['right']<=legend['w'],legend
            map_frame.locator('path[stroke="#3669B2"]').hover()
            map_frame.locator('.leaflet-tooltip').wait_for()
            page.wait_for_timeout(100)
            tooltip=map_frame.evaluate("""() => {const r=document.querySelector('.leaflet-tooltip').getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,w:innerWidth,h:innerHeight}}""")
            assert tooltip['x']>=0 and tooltip['y']>=0 and tooltip['right']<=tooltip['w'] and tooltip['bottom']<=tooltip['h'],tooltip
            page.screenshot(path=str(OUT/f'tooltip-{width}x{height}.png'))
            frame.locator('h1').hover()
            results.append(layout)
            print(json.dumps(layout,ensure_ascii=False),flush=True)
            if interactions_enabled:
                interactions(page,frame,width,height)
            after=frame.evaluate(MEASURE)
            after['outer']=layout['outer']
            assert_layout(after)
            print(f'Validation passed: {width}x{height}',flush=True)
            page.close()
        browser.close()
    (OUT/"measurements.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__ == "__main__":
    import sys
    run(interactions_enabled='--screenshots-only' not in sys.argv)
