#!/usr/bin/env python3
"""Check paper-reader structure/provenance and optionally exercise it in Chromium."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import pymupdf as fitz


def require(value,message):
    if not value:raise ValueError(message)


def static_check(path,pdf_path=None,existing=False):
    outer=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    frame=outer.select_one('#reader-document');require(frame and frame.get('srcdoc'),'Missing embedded reader document')
    inner=BeautifulSoup(frame['srcdoc'],'html.parser')
    pdf_node=outer.select_one('#original-pdf');require(pdf_node,'Missing original PDF')
    pdf=base64.b64decode(pdf_node.get_text().strip(),validate=True)
    with fitz.open(stream=pdf,filetype='pdf') as document:page_count=len(document)
    if pdf_path:require(pdf==pdf_path.read_bytes(),'Embedded PDF differs from the supplied source')
    metadata_node=outer.select_one('#paper-guide-metadata');manifest_node=outer.select_one('#paper-guide-manifest')
    require(existing or (metadata_node and manifest_node),'No provenance manifest: use --existing for an existing reader without this skill schema')
    metadata=json.loads(metadata_node.get_text()) if metadata_node else {'page_count':page_count,'screen_zoom':1.25,'ai_default':True}
    manifest=json.loads(manifest_node.get_text()) if manifest_node else None
    require(metadata['page_count']==page_count,'PDF and metadata page counts differ')
    pages=inner.select('.paper-page');require([int(p['data-page']) for p in pages]==list(range(1,page_count+1)),'Pages are missing, duplicated or reordered')
    require(len(inner.select('.translation'))==len(inner.select('.source-text'))==len(inner.select('.ai-panel'))==page_count,'Source/translation/AI page coverage differs')
    require(not inner.select('.source-text > pre:not(.source-layout)'),'Full-page extracted text is still shown with fixed PDF line breaks')
    require(len(inner.select('.story-tab'))==len(inner.select('.story-panel'))==len(inner.select('.toc-stage'))>0,'Map and hierarchical contents stage counts differ')
    for doc in [outer,inner]:
        ids=[n['id'] for n in doc.find_all(id=True)];require(len(ids)==len(set(ids)),'Duplicate HTML IDs')
        for a in doc.select('a[href^="#"]'):require(a['href']=='#' or a['href'][1:] in ids,f'Broken anchor: {a["href"]}')
        require(not doc.select('script[src],link[rel="stylesheet"][href]'),'External runtime script or stylesheet')
        for img in doc.select('img[src]'):require(img['src'].startswith('data:'),'An image is not embedded')
        for style in doc.find_all('style'):require(not re.search(r'@import|url\(\s*["\']?(?:https?:|//)',style.get_text(),re.I),'A style depends on the network')
    ai_on=metadata.get('ai_default',True)
    require(('ai-mode' in inner.body.get('class',[]))==ai_on,'Static AI body state differs from its default')
    require(inner.select_one('#ai-toggle').get('aria-pressed')==str(ai_on).lower(),'Static AI control state differs')
    require(all(('hidden' not in a.attrs)==ai_on for a in inner.select('.ai-panel')),'Static AI panel state differs')
    if manifest:
        require(manifest['source_pdf']['sha256']==hashlib.sha256(pdf).hexdigest() and manifest['source_pdf']['bytes']==len(pdf),'PDF provenance identity differs')
        require([p['pdf_page'] for p in manifest['pages']]==list(range(1,page_count+1)),'Manifest page coverage differs')
        complete=all(p['source_status']=='verified' and p['translation_status']=='complete' for p in manifest['pages'])
        require(complete==manifest['coverage_complete'],'Coverage status is dishonest or inconsistent')
        for original in manifest['originals']:
            image=inner.find('img',attrs={'data-original-id':original['id']});require(image,f'Missing original image: {original["id"]}')
            raw=base64.b64decode(image['src'].split(',',1)[1],validate=True)
            require(hashlib.sha256(raw).hexdigest()==manifest['images'][original['path']]['sha256'],'Original image hash differs')
            require(int(image.find_parent(class_='paper-page')['data-page'])==original['pdf_page'],'Original image source page differs')
    return {'pages':page_count,'stages':len(inner.select('.story-tab')),'pdf_sha256':hashlib.sha256(pdf).hexdigest(),'coverage_complete':manifest['coverage_complete'] if manifest else 'not asserted for existing reader','static':'PASS'},metadata


def browser_check(path,metadata,browser_bin=None,screenshots=None):
    from playwright.sync_api import sync_playwright
    errors,network=[],[]
    with sync_playwright() as pw:
        options={'headless':True}
        if browser_bin:options['executable_path']=str(browser_bin)
        browser=pw.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1920,'height':1080});page.set_default_timeout(8000);page.emulate_media(reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:network.append(r.url) if r.url.startswith(('https:','http:')) else None)
        page.goto(path.resolve().as_uri(),wait_until='load');f=page.frame_locator('#reader-document')
        require(float(page.locator('html').evaluate('(e)=>getComputedStyle(e).zoom'))==float(metadata.get('screen_zoom',1.25)),'Screen zoom differs')
        require(float(f.locator('html').evaluate('(e)=>getComputedStyle(e).zoom'))==1,'Zoom compounded inside the frame')
        require(f.locator('body').evaluate('(e)=>e.classList.contains("ai-mode")')==metadata.get('ai_default',True),'AI initial state differs')

        def click(locator):
            # Playwright locator coordinates omit CSS zoom inherited across an iframe.
            rect=locator.evaluate('(e)=>e.getBoundingClientRect().toJSON()')
            viewport=f.locator('body').evaluate('()=>({w:innerWidth,h:innerHeight})')
            # Already-visible sticky controls must not be scrolled by the automation.
            if rect['top']<0 or rect['bottom']>viewport['h'] or rect['left']<0 or rect['right']>viewport['w']:
                locator.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
                rect=locator.evaluate('(e)=>e.getBoundingClientRect().toJSON()')
            frame=page.locator('#reader-document').bounding_box()
            page.mouse.click(frame['x']+(rect['x']+rect['width']/2)*frame['width']/viewport['w'],frame['y']+(rect['y']+rect['height']/2)*frame['height']/viewport['h'])

        require(f.locator('body').get_attribute('data-reading-mode')==metadata.get('initial_mode','zh'),'Initial reading mode differs')
        def set_mode(mode):
            for _ in range(3):
                if f.locator('body').get_attribute('data-reading-mode')==mode:return
                click(f.locator('#compare'))
            require(False,'Unable to select reading mode '+mode)
        for width in [390,768,1280,1920]:
            page.set_viewport_size({'width':width,'height':1000})
            for mode in ['zh','en','both']:
                set_mode(mode)
                require(f.locator('body').get_attribute('data-reading-mode')==mode,'Mode cycle failed')
                if mode=='both':require(f.locator('#compare').inner_text()=='中文/英文','Comparison mode must be labeled 中文/英文')
                for ai in [False,True]:
                    if f.locator('body').evaluate('(e)=>e.classList.contains("ai-mode")')!=ai:click(f.locator('#ai-toggle'))
                    require(f.locator('#ai-toggle').get_attribute('aria-pressed')==str(ai).lower(),'AI control state differs')
                    require(f.locator('.ai-panel:not([hidden])').count()==(metadata['page_count'] if ai else 0),'AI panels did not toggle independently')
                    require(f.locator('html').evaluate('(e)=>e.scrollWidth<=innerWidth'),'Page-wide horizontal overflow')
            if screenshots:
                screenshots.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(screenshots/f'reader-{width}.png'))
        # Normalize from both to zh, with AI enabled.
        click(f.locator('#compare'))
        tabs=f.locator('.story-tab')
        for i in range(tabs.count()):
            click(tabs.nth(i));require(tabs.nth(i).get_attribute('aria-selected')=='true','Research-stage selection failed')
            require(f.locator('.story-panel:not([hidden])').count()==1,'Research panels overlap')
        tabs.first.focus();page.keyboard.press('End');require(tabs.last.get_attribute('aria-selected')=='true','Story tabs lack keyboard navigation')
        # Read a real source token, test positive and impossible searches, then recover.
        click(f.locator('#compare'));source=f.locator('.source-text').first.inner_text();tokens=re.findall(r'[A-Za-z]{5,}',source)
        if tokens:
            f.locator('#search').fill(tokens[0]);page.wait_for_timeout(250);require(f.locator('.page-row:not(.hidden)').count()>0,'Positive search hides all pages')
        f.locator('#search').fill('__paper_guide_no_match_84e7__');f.locator('#empty').wait_for(state='visible')
        f.locator('#search').fill('');f.locator('#empty').wait_for(state='hidden')
        target=metadata['page_count'];f.locator('#jump').fill(str(target));f.locator('#jump-form').evaluate('(e)=>e.requestSubmit()')
        f.locator('#theme').evaluate('(e)=>e.click()');require(f.locator('html').get_attribute('data-theme')=='dark','Theme switch failed')
        images=f.locator('.english-figures img')
        if images.count():
            click(images.first);require(f.locator('#image-dialog').evaluate('(e)=>e.open'),'Image modal did not open')
            click(f.locator('#zoom-size'));require(f.locator('#zoom-image').evaluate('(e)=>e.classList.contains("full-size")'),'Original-size image mode failed')
            page.keyboard.press('Escape');require(not f.locator('#image-dialog').evaluate('(e)=>e.open'),'Escape did not close the modal')
        for panel in f.locator('.ai-panel').all():
            require(panel.evaluate('(e)=>!["auto","scroll","hidden","clip"].includes(getComputedStyle(e).overflowY)'),'AI panel traps/clips document scrolling')
        f.locator('.page-pdf').last.evaluate('(e)=>e.click()')
        require(page.locator('#panel-english').get_attribute('aria-hidden')=='false','Original PDF tab failed')
        require(f'page={target}' in page.locator('#english-document').get_attribute('src'),'Physical PDF page jump differs')
        page.locator('#tab-reader').click();require(f.locator('body').get_attribute('data-reading-mode')=='en','Returning from PDF reset reading mode')
        page.emulate_media(media='print');require(float(page.locator('html').evaluate('(e)=>getComputedStyle(e).zoom'))==1,'Print inherits screen zoom')
        require(f.locator('.ai-panel').first.is_hidden(),'Print shows the AI sidebar')
        page.emulate_media(media='screen');browser.close()
    require(not errors,f'JavaScript errors: {errors}');require(not network,f'External render dependencies: {network}')
    return {'status':'PASS','viewports':[390,768,1280,1920],'language_ai_states':6,'javascript_errors':errors,'external_requests':network}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('html',type=Path);parser.add_argument('--pdf',type=Path);parser.add_argument('--existing',action='store_true');parser.add_argument('--browser',action='store_true');parser.add_argument('--browser-bin',type=Path);parser.add_argument('--screenshots',type=Path);parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    try:
        result,metadata=static_check(args.html,args.pdf,args.existing)
        result['browser']=browser_check(args.html,metadata,args.browser_bin,args.screenshots) if args.browser else {'status':'NOT RUN'}
        if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,ImportError) as exc:parser.exit(2,f'Validation failed: {exc}\n')

if __name__=='__main__':main()
