#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zipfile import ZipFile
from glob import glob
import argparse
import json

def convert_xml2BIO(lang='en', xmi_file_name='teresa.xmi'):
    from cassis import load_typesystem, load_cas_from_xmi 
    
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
                    with myzip.open(xmi_file_name) as myfile:
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
                
            sent_list = []
            for snt in doc.select('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence'):
                sent_list.append({'covered_text':snt.get_covered_text(), 'begin':snt.begin, 'end':snt.end})

            recent_annot_index = 0
            recent_sent_index = 0
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

                #if tok['covered_text'] in '.!?':
                if tok['end'] == sent_list[recent_sent_index]['end']:
                    print() # new line between sentences.
                    recent_sent_index += 1
                    if len(sent_list) > recent_sent_index:
                        print(sent_list[recent_sent_index]['covered_text'])
                    else:
                        print('last sent in doc')

                if tok['end'] == recent_span['end']:
                    left_longest_annot_index = recent_annot_index
                    while span_list[left_longest_annot_index]['end'] >= span_list[recent_annot_index]['begin']:
                        if (recent_annot_index + 1) < len(span_list):
                            recent_annot_index += 1
                        else:
                            break
                            
def convert_sentbio2sentJSON(sentbiofile):
    with open(sentbiofile) as f:
        sentence_chunks = f.read().split('\n\n')

#     print(sentence_chunks[1], end='\n\n')

    testsents = []
    for tok_annots in sentence_chunks:
    #     print(tok_annots)

        sent_tokens_list = []
        sent_annots_list = []

        for tk_ann_str in tok_annots.split('\n'):
            tk_ann_list = tk_ann_str.split('\t')

            if len(tk_ann_list) != 2:
#                 print('Skipped:')
#                 print('tk_ann_str:', tk_ann_str)
#                 print('tk_ann_list:', tk_ann_list)
                continue

            sent_tokens_list.append(tk_ann_list[0])
            sent_annots_list.append(tk_ann_list[1])
            
        final_sent_instance = {}
        final_sent_instance['text'] = " ".join(sent_tokens_list)
        final_sent_instance['label'] = 'smell' if (len(set(sent_annots_list))>1) else 'nonsmell'

        print(json.dumps(final_sent_instance, ensure_ascii=False))
    

if __name__ == "__main__":

    my_parser = argparse.ArgumentParser(description='convert Odeuropa benchmark data from a format to another one.')
    my_parser.add_argument('-i', '--iformat', type=str, help='the source format', required=True)
    my_parser.add_argument('-o', '--oformat', type=str, help='the target format', required=True)
    my_parser.add_argument('-l', '--lang', type=str, help='the language')
    my_parser.add_argument('-b', '--sentbiofile', type=str, help='the language')

    args = my_parser.parse_args()

    print('args are:', args)


    if args.iformat == 'xml' and args.oformat == 'sentbio':
        convert_xml2BIO(args.lang, 'teresa.xmi')
    elif args.iformat == 'sentbio' and args.oformat == 'sentjson':
        convert_sentbio2sentJSON(args.sentbiofile)
    else:
        print(f'The conversion from {args.iformat} to {args.oformat} is not defined.')
