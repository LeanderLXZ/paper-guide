#!/usr/bin/env python3
"""Build a self-contained paper reader from editorial JSON and local assets."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import tempfile
import re
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
import pymupdf as fitz

SKILL = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(data):
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def ui(pair):
    require(isinstance(pair, dict) and pair.get('zh') and pair.get('en'), 'A label needs nonempty zh and en values')
    return '<span class="ui-zh" lang="zh-CN">' + escape(pair['zh']) + '</span><span class="ui-en" lang="en">' + escape(pair['en']) + '</span>'


def fill_template(path, values):
    template = path.read_text(encoding='utf-8')
    expected = set(re.findall(r'__PG_[A-Z0-9_]+__', template))
    require(expected == set(values), f'Template keys differ in {path.name}: {expected ^ set(values)}')
    # Substitute once so marker-like strings in user content are never interpreted.
    return re.sub(r'__PG_[A-Z0-9_]+__', lambda m: values[m[0]], template)


def build(model_path: Path, output: Path, allow_incomplete=False):
    require(output.suffix.lower() == '.html', 'Output must be an .html file')
    base = model_path.resolve().parent
    model = json.loads(model_path.read_text(encoding='utf-8'))
    require(model.get('schema') == 'paper-guide/v1', 'Expected schema paper-guide/v1')
    paper = model['paper']
    pdf_path = (base / paper['pdf']).resolve()
    pdf = pdf_path.read_bytes()
    with fitz.open(stream=pdf, filetype='pdf') as document:
        page_count = len(document)
        bounds = []
        for page in document:
            page.set_rotation(0)
            bounds.append(page.rect)
    pages, stages = model['pages'], model['stages']
    require(page_count > 0, 'Source PDF is empty')
    require(all(type(p.get('pdf_page')) is int for p in pages), 'Physical page numbers must be integers')
    require(type(model.get('ai_default', True)) is bool, 'ai_default must be a boolean')
    require(model.get('initial_mode', 'zh') in {'zh','en','both'}, 'initial_mode must be zh, en or both')
    require([p.get('pdf_page') for p in pages] == list(range(1, page_count + 1)), 'pages must cover every physical PDF page once, in order, starting at 1')
    require(stages, 'At least one research stage is required')
    require(all(paper.get(k) for k in ['title_zh', 'title_en', 'authors']), 'Paper titles and authors are required')
    zoom = float(model.get('screen_zoom', 1.25))
    require(.5 <= zoom <= 3, 'screen_zoom must be between 0.5 and 3')
    assets, status, rows = {}, [], []
    inputs = {model_path.resolve(), pdf_path}
    original_ids = set()

    def asset(path):
        require(isinstance(path, str) and not re.match(r'[a-z][a-z0-9+.-]*:', path, re.I), 'Assets must use local paths')
        target = (base / path).resolve()
        inputs.add(target)
        mime = mimetypes.guess_type(target.name)[0]
        require(mime in {'image/png', 'image/jpeg', 'image/webp', 'image/gif'}, f'Use PNG/JPEG/WebP/GIF for source images: {path}; native diagrams may be inline SVG')
        data = target.read_bytes()
        assets[path] = {'kind': mime, **identity(data)}
        return f'data:{mime};base64,' + base64.b64encode(data).decode()

    def fragment(value, originals=None):
        require(isinstance(value, str), 'HTML fragments must be strings, not paths')
        soup = BeautifulSoup(value, 'html.parser')
        require(not soup.find(['script', 'style', 'iframe', 'object', 'embed', 'base', 'link', 'form', 'foreignObject', 'video', 'audio', 'source', 'track', 'meta', 'input']), 'Content fragments may not contain active documents, scripts, styles or forms')
        for node in soup.find_all(True):
            for key, val in node.attrs.items():
                require(not key.lower().startswith('on'), f'Event handler attributes are not content: {key}')
                require(key not in {'srcset', 'poster', 'srcdoc'}, f'Unsupported resource attribute: {key}')
                if key == 'style':
                    require(not re.search(r'url\s*\(|@import', str(val), re.I), 'Content styles cannot load resources')
                if key == 'src':
                    require(node.name == 'img', 'Only img elements may load content resources')
                if key in {'href', 'xlink:href'}:
                    require(not re.match(r'(?:javascript|data):', str(val), re.I), 'Executable/content data links are not allowed')
                    if node.name not in {'a'}:
                        require(str(val).startswith('#'), 'SVG references must be local fragment IDs')
            if node.has_attr('data-original'):
                key = node['data-original']
                require(originals is not None and key in originals, f'Unknown original-image marker: {key}')
                node.replace_with(BeautifulSoup(originals[key], 'html.parser'))
            elif node.name == 'img':
                require(node.get('src'), 'Every image requires a local src')
                node['src'] = asset(node['src'])
        return str(soup)

    for page in pages:
        n = page['pdf_page']
        source_status = page.get('source_status')
        translation_status = page.get('translation_status')
        require(source_status in {'verified', 'uncertain', 'image_only'}, f'Page {n}: invalid source_status')
        require(translation_status in {'complete', 'partial', 'unavailable'}, f'Page {n}: invalid translation_status')
        complete = source_status == 'verified' and translation_status == 'complete'
        require(complete or allow_incomplete, f'Page {n}: incomplete/unverified; use --allow-incomplete only for an intentionally partial deliverable')
        en, zh = page.get('english_html', ''), page.get('translation_html', '')
        originals_on_page = page.get('originals', [])
        has_english = bool(BeautifulSoup(en, 'html.parser').get_text(strip=True)) or bool(originals_on_page and all(o.get('caption_en','').strip() for o in originals_on_page))
        has_chinese = bool(BeautifulSoup(zh, 'html.parser').get_text(strip=True)) or bool(originals_on_page and all(o.get('caption_zh','').strip() for o in originals_on_page))
        require(source_status != 'verified' or has_english, f'Page {n}: verified source needs English text')
        require(translation_status != 'complete' or has_chinese, f'Page {n}: complete translation is empty')
        ai = page.get('ai')
        require(ai and ai.get('title') and ai.get('summary') and ai.get('blocks'), f'Page {n}: page-specific AI notes are required, including honest gap explanations')
        status.append({'pdf_page': n, 'printed_label': page.get('printed_label'), 'source_status': source_status, 'translation_status': translation_status})
        originals = {}
        for original in page.get('originals', []):
            key = original['id']
            require(re.fullmatch(r'[a-z][a-z0-9_-]*', key) and key not in original_ids, f'Duplicate or invalid original image ID: {key}')
            original_ids.add(key)
            require(original.get('kind') in {'figure', 'table'} and original.get('label') and original.get('caption_en'), f'{key}: kind, original label and English caption are required')
            require(original.get('orientation_verified') is True, f'{key}: inspect and confirm the original is upright and not clipped')
            region = original.get('region')
            require(isinstance(region, dict) and region.get('units') == 'pt' and region.get('origin') == 'top-left' and len(region.get('bbox', [])) == 4, f'{key}: region needs an unrotated PDF bbox in top-left pt coordinates')
            box=region['bbox']
            require(all(type(v) in {int,float} for v in box) and not fitz.Rect(box).is_empty and bounds[n-1].contains(fitz.Rect(box)), f'{key}: crop box must lie inside the unrotated source page')
            url = asset(original['path'])
            label, caption = original['label'], original['caption_en']
            originals[key] = '<figure data-original-id="' + key + '"><img loading="lazy" src="' + url + '" alt="' + escape(label, quote=True) + '" data-original-id="' + key + '" data-original-kind="' + original['kind'] + '" data-original-label="' + escape(label, quote=True) + '" data-caption-en="' + escape(caption, quote=True) + '"><figcaption>' + escape(label) + ' · PDF ' + str(n) + '<br>' + escape(caption) + ('<br>' + escape(original['caption_zh']) if original.get('caption_zh') else '') + '</figcaption></figure>'
        # Validate all author HTML before inserting the trusted generated data-URL figures.
        translated = fragment(zh, originals)
        for key, figure in originals.items():
            if not BeautifulSoup(translated, 'html.parser').find('figure', attrs={'data-original-id': key}):
                translated += figure
        english = fragment(en)
        if not english.strip() and originals_on_page:
            english = ''.join('<p>'+escape(o['caption_en'])+'</p>' for o in originals_on_page)
        require(not BeautifulSoup(english, 'html.parser').select('pre:not(.source-layout)'), f'Page {n}: prose must be p blocks; reserve pre.source-layout for aligned data/equations')
        source_notice = '' if source_status == 'verified' else '<p class="overview-note" role="note">' + ui({'zh': '原文文字尚未完全核验，请查看本页原 PDF。', 'en': 'Source text is not fully verified; consult this PDF page.'}) + '</p>'
        translation_notice = '' if translation_status == 'complete' else '<p class="overview-note" role="note">' + ui({'zh': '本页译文不完整；缺失部分未补写。', 'en': 'Translation is incomplete; missing material has not been invented.'}) + '</p>'
        printed = str(page['printed_label']) if page.get('printed_label') is not None else ''
        label = f'原文第 {n:02d} / {page_count} 页' + (' · 印刷页 ' + printed if printed else '')
        ai_blocks = ''.join('<section class="ai-block"><h3>' + escape(b['title']) + '</h3><p>' + escape(b['body']) + '</p></section>' for b in ai['blocks'])
        rows.append(f'<div class="page-row" data-page="{n}"><section class="paper-page" data-page="{n}" data-printed-label="{escape(printed, quote=True)}" id="p{n:02d}"><div class="page-label">{escape(label)}<div class="page-tools"><button class="page-compare" type="button">展开英文</button><button class="page-pdf" data-open-pdf="{n}" type="button">原版 PDF</button></div></div><div class="page-grid"><div class="translation" lang="zh-CN">{translation_notice}{translated}</div><details class="source-panel"><summary>英文原文 · 第 {n} 页</summary><div class="source-text" lang="en">{source_notice}{english}</div></details></div></section><aside class="ai-panel" id="ai-p{n:02d}" aria-labelledby="ai-title-{n:02d}"><div class="ai-kicker"><span>AI 解读</span><span>对应原文第 {n} 页</span></div><h2 id="ai-title-{n:02d}">{escape(ai["title"])}</h2><div class="ai-summary"><p>{escape(ai["summary"])}</p></div>{ai_blocks}</aside></div>')

    def page_link(label, n):
        require(type(n) is int and 1 <= n <= page_count, f'Invalid physical PDF page: {n}')
        return f'<a href="#p{n:02d}" data-page-target="{n}">' + ui(label) + '</a>'

    tabs, panels, toc = [], [], []
    previous_start = 0
    for i, stage in enumerate(stages, 1):
        start, end = stage['page_start'], stage['page_end']
        require(type(start) is int and type(end) is int and 1 <= start <= end <= page_count, f'Stage {i}: invalid page range')
        auto_start = stage.get('auto_start', start)
        require(type(auto_start) is int and 1 <= auto_start <= page_count and previous_start <= auto_start, f'Stage {i}: auto_start must be ordered physical page numbers')
        previous_start = auto_start
        require(stage.get('steps'), f'Stage {i} needs concrete substeps')
        tabs.append(f'<button class="story-tab" id="story-tab-{i}" data-story-step="{i}" role="tab" aria-controls="story-panel-{i}" aria-selected="{str(i==1).lower()}" tabindex="{0 if i==1 else -1}" type="button"><span class="story-step">{i:02d} →</span><strong>{ui(stage["title"])}</strong><span class="story-question">{ui(stage["subtitle"])}</span></button>')
        steps = ''.join(f'<li class="story-substep"><div class="story-substep-heading"><span class="story-substep-index">{i}.{j}</span><h5>{ui(step["title"])}</h5></div><p>{ui(step["body"])}</p>{page_link({"zh":"原文第 "+str(step["page"])+" 页 ↗","en":"Original page "+str(step["page"])+" ↗"},step["page"])}</li>' for j,step in enumerate(stage['steps'],1))
        panels.append(f'<div class="story-panel" id="story-panel-{i}" role="tabpanel" aria-labelledby="story-tab-{i}" tabindex="0"' + (' hidden' if i>1 else '') + f'><div class="story-panel-heading"><h3><span class="story-index">{i:02d}</span>{ui(stage["title"])}</h3><span class="story-pages">PDF {start}–{end}</span></div><p class="story-subtitle">{ui(stage["subtitle"])}</p><p class="story-why"><b>{ui({"zh":"本节目的","en":"Purpose"})}</b> {ui(stage["purpose"])}</p><ol class="story-substeps">{steps}</ol>{fragment(stage.get("diagram_html",""))}<div class="story-takeaway">{ui(stage["takeaway"])}</div><p class="story-next">{ui(stage["next"])}</p></div>')
        def nav_links(items, depth=1):
            require(depth <= 8, 'Navigation nesting is too deep')
            return '<ol class="toc-children">' + ''.join('<li>' + page_link(item['label'], item['page']) + (nav_links(item['children'],depth+1) if item.get('children') else '') + '</li>' for item in items) + '</ol>'
        links = stage.get('links') or [{'label': step['title'], 'page': step['page']} for step in stage['steps']]
        toc.append(f'<li><details class="toc-stage" data-stage="{i}" data-start="{start}" data-auto-start="{auto_start}"' + (' open' if i==1 else '') + f'><summary><span class="toc-number">{i:02d}</span>{ui(stage["title"])}</summary><a class="toc-stage-overview" href="#story-tab-{i}" data-map-stage="{i}">{ui({"zh":"查看本节研究步骤 ↗","en":"View this stage’s steps ↗"})}</a>{nav_links(links)}</details></li>')

    full = all(p['source_status']=='verified' and p['translation_status']=='complete' for p in status)
    summary = model.get('summary', {'zh':'按论文研究顺序阅读原文、译文与 AI 解读。','en':'Read the paper through its research sequence, source text, translation and AI notes.'})
    map_html = '<div class="map-heading"><div><p class="map-kicker">RESEARCH DESIGN &amp; ARGUMENT</p><h2 id="map-title"><span class="map-index">00</span>'+ui({'zh':'论文研究框架与研究路线','en':'Research Framework and Roadmap'})+'</h2></div><span class="map-count">'+str(len(stages))+' '+ui({'zh':'个研究环节','en':'research stages'})+'</span></div><p class="map-intro">'+ui(summary)+'</p><p id="map-hint" class="map-hint">'+ui({'zh':'选择研究环节，查看具体步骤、结论和原文位置。','en':'Select a research stage for concrete steps, findings and source locations.'})+'</p><div class="story-tabs" role="tablist" aria-describedby="map-hint" aria-label="论文研究路线">'+''.join(tabs)+'</div>'+''.join(panels)
    doi = paper.get('doi', '')
    require(not doi or re.fullmatch(r'10\.\d{4,9}/[^\s<>"\']+', doi), 'Invalid DOI')
    hero = '<div class="eyebrow">PAPER READING GUIDE</div><h1>'+ui({'zh':paper['title_zh'],'en':paper['title_en']})+'</h1><p class="subtitle">'+escape(paper['title_en'])+'</p><p class="authors">'+escape(paper['authors'])+'</p><div class="citation">'+ui({'zh':paper.get('citation_zh',''), 'en':paper.get('citation_en','')})+'</div>' if paper.get('citation_zh') and paper.get('citation_en') else '<div class="eyebrow">PAPER READING GUIDE</div><h1>'+ui({'zh':paper['title_zh'],'en':paper['title_en']})+'</h1><p class="subtitle">'+escape(paper['title_en'])+'</p><p class="authors">'+escape(paper['authors'])+'</p>'
    if doi:
        hero += '<p>DOI: <a target="_blank" rel="noopener" href="https://doi.org/'+escape(doi,quote=True)+'">'+escape(doi)+'</a></p>'
    hero += '<div class="hero-meta"><span class="pill">'+str(page_count)+' '+ui({'zh':'个原文页面','en':'original pages'})+'</span><span class="pill">'+ui({'zh':'全文译文已覆盖' if full else '部分内容尚未核验／翻译','en':'Translation coverage complete' if full else 'Partial or unverified coverage'})+'</span><span class="pill">'+ui({'zh':'原图与原 PDF · 离线阅读','en':'Original figures and PDF · Offline reading'})+'</span></div><p class="hero-note">'+ui({'zh':'AI 解读是辅助说明，示例仅用于解释；精确陈述请核对原文。中文译文为辅助阅读的非官方译文，原文版权归原权利人所有。','en':'AI notes and examples aid understanding; consult the source for precise claims. The translation is unofficial. Original rights remain with their holders.'})+'</p>'
    metadata = {'schema':'paper-guide/v1','title_zh':paper['title_zh'],'title_en':paper['title_en'],'page_count':page_count,'initial_mode':model.get('initial_mode','zh'),'screen_zoom':zoom,'ai_default':model.get('ai_default',True)}
    manifest = {'schema':'paper-guide-manifest/v1','source_pdf':{'name':pdf_path.name,**identity(pdf)},'input_model':identity(model_path.read_bytes()),'pages':status,'coverage_complete':full,'images':assets,'originals':[{'pdf_page':p['pdf_page'],**o} for p in pages for o in p.get('originals',[])],'stages':len(stages),'build_sources':{str(p.relative_to(SKILL)):identity(p.read_bytes()) for p in [Path(__file__).resolve(),SKILL/'assets/reader.html',SKILL/'assets/shell.html']}}
    reader = fill_template(SKILL/'assets/reader.html', {'__PG_TITLE__':escape(paper['title_zh']+' · 论文导读'),'__PG_HERO__':hero,'__PG_MAP__':map_html,'__PG_TOC__':''.join(toc),'__PG_PAGES__':''.join(rows),'__PG_FOOTER__':ui({'zh':'原文、译文与 AI 解读逐页对应；引用请以原 PDF 为准。','en':'Source, translation and AI notes are aligned by PDF page; cite the original PDF.'}),'__PG_CONFIG__':json_script(metadata),'__PG_AI_IDS__':' '.join(f'ai-p{i:02d}' for i in range(1,page_count+1)),'__PG_PAGE_COUNT__':str(page_count),'__PG_SEARCH_META__':'全文 '+str(page_count)+' 页 · 论文研究路线'})
    if not metadata['ai_default']:
        parsed=BeautifulSoup(reader,'html.parser')
        parsed.body['class']=[c for c in parsed.body.get('class',[]) if c!='ai-mode']
        parsed.select_one('#ai-toggle')['aria-pressed']='false'
        parsed.select_one('#ai-toggle')['aria-expanded']='false'
        parsed.select_one('#ai-toggle').string='AI 解读'
        for panel in parsed.select('.ai-panel'):panel['hidden']=''
        reader=str(parsed)
    result = fill_template(SKILL/'assets/shell.html', {'__PG_TITLE_ZH__':escape(paper['title_zh']+' · 论文导读'),'__PG_READER_SRCDOC__':escape(reader,quote=True),'__PG_PDF_BASE64__':base64.b64encode(pdf).decode(),'__PG_METADATA__':json_script(metadata),'__PG_MANIFEST__':json_script(manifest),'__PG_ZOOM__':str(zoom)})
    output.parent.mkdir(parents=True,exist_ok=True)
    require(output.resolve() not in inputs, 'Output would overwrite a source input')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=output.parent,prefix='.'+output.name+'.',delete=False) as handle:
            temporary=Path(handle.name)
            handle.write(result)
        os.replace(temporary,output)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return {'output':str(output),'bytes':len(result.encode()),'pages':page_count,'stages':len(stages),'coverage_complete':full,'source_pdf_sha256':manifest['source_pdf']['sha256']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--allow-incomplete',action='store_true',help='Build an explicitly marked partial/unverified reader')
    args=parser.parse_args()
    try:
        print(json.dumps(build(args.model,args.out,args.allow_incomplete),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,json.JSONDecodeError) as exc:
        parser.exit(2,f'Build failed: {exc}\n')

if __name__=='__main__':
    main()
