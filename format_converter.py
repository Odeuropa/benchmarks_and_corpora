#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cassis import load_typesystem, load_cas_from_xmi 
from zipfile import ZipFile
from glob import glob
import argparse

def convert_xml2BIO(lang='en', xmi_file_name='teresa'):

    available_languages = [l.split('/')[-1].lower() for l in glob('./benchmarks/*')]

    if lang.lower() not in available_languages:
        print(f'{lang} folder does not exists. The available languages are {available_languages}')
        return


    for datafolder in glob('benchmarks/'+lang.upper()+'/xml/*'):
        
        for zfile in glob(datafolder+'/webanno*.zip'):
            
            typesystemfile_content, doc = None, None
            with ZipFile(zfile) as myzip:
                with myzip.open('TypeSystem.xml', 'r') as myfile:
                    typesystemfile_content = myfile.read().decode()
                typesystem = load_typesystem(typesystemfile_content)
                
                try:
                    with myzip.open('teresa.xmi') as myfile:
                        doc = load_cas_from_xmi(myfile.read().decode(), typesystem=typesystem)
                except:
                    continue
                    
            span_list = []
            for sp in doc.select('custom.Span'):
                span_list.append({'covered_text':sp.get_covered_text(), 'label':sp.label, 'begin':sp.begin, 'end':sp.end})

            if len(span_list) == 0:
                continue
                
            tok_list = []
            for tok in doc.select('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token'):
                tok_list.append({'covered_text':tok.get_covered_text(), "begin":tok.begin, "end":tok.end})

            recent_annot_index = 0
            for tok in tok_list:
                recent_span = span_list[recent_annot_index]
                if tok['covered_text'] is None or recent_span['label'] is None:
                    continue
                if recent_span['begin'] == tok['begin']:
                    print(tok['covered_text']+'\t'+'B-'+recent_span['label'])
                elif recent_span['begin'] < tok['begin'] and recent_span['end'] >= tok['end']:
                    print(tok['covered_text']+'\t'+'I-'+recent_span['label'])
                else:
                    print(tok['covered_text']+'\t'+'O')

                if tok['covered_text'] == '.':
                    print()

                if tok['end'] == recent_span['end']:
                    left_longest_annot_index = recent_annot_index
                    while span_list[left_longest_annot_index]['end'] >= span_list[recent_annot_index]['begin']:
                        if (recent_annot_index + 1) < len(span_list):
                            recent_annot_index += 1
                        else:
                            break

if __name__ == "__main__":

    my_parser = argparse.ArgumentParser(description='convert Odeuropa benchmark data from a format to another one.')
    my_parser.add_argument('--i', '--iformat', type=str, help='the source format', required=True)
    my_parser.add_argument('--o', '--oformat', type=str, help='the target format', required=True)
    my_parser.add_argument('--l', '--lang', type=str, help='the language folder', required=True)

    args = my_parser.parse_args()

    # print(args.iformat, args.oformat, args.lang)


    if args.iformat == 'xml' and args.oformat == 'bio':
        convert_xml2BIO(args.lang)
    else:
        print(f'The conversion from {args.iformat} to {args.oformat} is not defined.')
