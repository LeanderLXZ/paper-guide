#!/usr/bin/env python3
"""Inspect local PDF pages or crop an original figure/table with provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf as fitz


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    inspect=sub.add_parser('inspect');inspect.add_argument('pdf',type=Path);inspect.add_argument('--out',required=True,type=Path);inspect.add_argument('--render-pages',action='store_true')
    crop=sub.add_parser('crop');crop.add_argument('pdf',type=Path);crop.add_argument('--page',required=True,type=int);crop.add_argument('--bbox',required=True,type=float,nargs=4,metavar=('X0','Y0','X1','Y1'));crop.add_argument('--rotate',default=0,type=int,choices=[0,90,180,270]);crop.add_argument('--dpi',default=150,type=int);crop.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();data=args.pdf.read_bytes()
    with fitz.open(stream=data,filetype='pdf') as document:
        if args.command=='inspect':
            args.out.mkdir(parents=True,exist_ok=True);pages=[]
            for i,page in enumerate(document,1):
                # Layout extraction is evidence for authoring, not display-ready English.
                text=page.get_text('text',sort=True);target=args.out/f'p{i:03d}.txt';target.write_text(text,encoding='utf-8')
                pages.append({'pdf_page':i,'printed_label':None,'text_file':target.name,'text_chars':len(text.strip()),'extraction_status':'extracted_unverified' if text.strip() else 'image_only','rotation':page.rotation,'width_pt':page.rect.width,'height_pt':page.rect.height})
                if args.render_pages:page.get_pixmap(dpi=110).save(args.out/f'p{i:03d}.png')
            result={'source_pdf':{'name':args.pdf.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)},'page_count':len(document),'pages':pages}
            (args.out/'inspection.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
        else:
            if not 1<=args.page<=len(document):parser.error('--page is a physical, 1-based PDF page number')
            page=document[args.page-1]
            # Work in the unrotated page coordinate system to make crop records unambiguous.
            original_rotation=page.rotation;page.set_rotation(0)
            clip=fitz.Rect(args.bbox)
            if clip.is_empty or not page.rect.contains(clip):parser.error('--bbox must be nonempty and lie inside the unrotated PDF page')
            if not 36<=args.dpi<=600:parser.error('--dpi must be between 36 and 600')
            args.out.parent.mkdir(parents=True,exist_ok=True)
            pix=page.get_pixmap(matrix=fitz.Matrix(args.dpi/72,args.dpi/72).prerotate(args.rotate),clip=clip,alpha=False);pix.save(args.out)
            record={'pdf_page':args.page,'region':{'bbox':args.bbox,'units':'pt','origin':'top-left','rotation_degrees':args.rotate,'source_page_rotation':original_rotation},'source_pdf_sha256':hashlib.sha256(data).hexdigest(),'image_sha256':hashlib.sha256(args.out.read_bytes()).hexdigest(),'width':pix.width,'height':pix.height,'orientation_verified':False}
            args.out.with_suffix(args.out.suffix+'.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))

if __name__=='__main__':main()
