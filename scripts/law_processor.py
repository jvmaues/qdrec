import re
from io import StringIO
from fastapi import Depends
import pandas as pd

import requests
from bs4 import BeautifulSoup
import json
import time

from api.crud.crud import create_excerpt_metadata, create_named_entity
from api.model.schemas import ExcerptMetadataCreate, NamedEntityCreate

from database.connection import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_law_info(law_number: str) -> dict:

    cookies = {
        'f5_cspm': '1234',
        'TS00000000076': '086567d05fab2800ab1e2291076ea15187abba24bd18adccdd95af9931c98e6da53c6fdb139ac6b99dc6c64671f862370816478e8d09d0008ae05b0dafc18e4e987e81d3926e883a641a9437b4bc379e042276c2cae5e8b1743055ee5b11f65b348086cd5f836afcbe1b2ff1e64954a74997754ff3ed00f1c734c9c9b862a8bc5819e233fb81b6a70ac1333e44374c1022fedee633d6285ef0e4a823cce077ddc203a71748a5b2a0b3d402f863b5e259099663c00c1b8f3a92f628a4df6a2696dbead8600ff0adbe8c780f6781a433d7198202e85747a408323e1573d3d646d0ce9ec7a28abd3fbd9699ed8acdaa49189a994e8f0c5c75e9d9cfad15bca4b0fda1bb4d0e213fd796',
        'TSPD_101_DID': '086567d05fab2800ab1e2291076ea15187abba24bd18adccdd95af9931c98e6da53c6fdb139ac6b99dc6c64671f862370816478e8d063800db48615c1db2ff9237fe95fb832a176c55afdcddf8fc43fe5e402a99a4cb13a8f638d6c2c71534905a146ae07368a963d3b4c438edcc645f',
        'TS01acd2cb': '0150f80db11cde550b56384fcfbf3d13198562088e68b8efe1479aa6ca09167ac619bf07d0fe83c96817836a981d514cc7eb240b6c38f9930b5cacf15364627245bbb0562c25f44f17cbd444795a8c8ecbc216872c',
        'TSPD_101': '086567d05fab2800400e1c8a59589afb79cd0b4c5e4079f3985ae084ae834072f35e15ee7409cb3bbd1b95d05026e0dc0882129f360518009daa6fff2b30c927304602e69b56a39104eeedb0a518443c',
        'TS99db2205077': '086567d05fab2800bcef89333be6d3bf8237378ed363369388e4b404479d51d4befafacd32ad878ce0185d82f5ff8408087ce97f5d172000c7a87c5211019e8a1900adfaeec9ae435ea67b198b200266ba54704df6147303',
        'TS6b6d31b1027': '086567d05fab200034e2c174f6db6fb11625ec9ca3e93ca7f0b8b1c144ddc0e4458e3e21a6af067e085027e6cb113000d69afa520f0fd74731a875409615f404d4bedba4658fe62c861c40540ad21c96a252c2a821c9b151c12b8117dbd2c416',
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'f5_cspm=1234; TS00000000076=086567d05fab2800088fb59476ad4bfb13e3d23dd4c1e5fc8db0fbc40c4a3e00b342c4f9c1e6e8933888a773e74e344c08b6baffa109d00050bf073f0c543ae6cc5e0f0a3e72b5b76edab836b0db73e664551a53198b3b4cf6e2bc422608ee7175dd5387493eaaddcd23134e4f0e0fa2ef754c5379b7076dfd34a3be6707cfd4bd7d2b97b82e5938070ef261b528c4abab389b15b864d4fbfd74f46a82910dc008d33242b74534051c874193a5dcde2846c767e2dad3360502afaf91462c7166769c2f1f58e61e3cc4d5885602bd9cd9a1993e681951ca1ad76e556d9811becca1be03351debca6fa60500492fa47be5951964515316c1f79d4fc43dfd5f469715c6af3212d8d5b0; TSPD_101_DID=086567d05fab2800088fb59476ad4bfb13e3d23dd4c1e5fc8db0fbc40c4a3e00b342c4f9c1e6e8933888a773e74e344c08b6baffa106380029093da7ff315f0341545f72b078e4514fc4c3110a5f8465e49aaf0efa7df7fb0ed2821294498e0299247c3e190849d7bd0f24810093d4e3; TS01acd2cb=0150f80db1389bb9f487ed0e879a4068b846c401981a55a03fde4e61114f258e46ed1ccfd01297063c84833d920d77e6d2abf8e9dfd9e06501cf1ec9becc081d8500575a5b5245476b07454db0bae952c433ef044a; TSPD_101=086567d05fab2800aabf33d5701b5cdf40ca7f16036e893ddd1c3ec9a98cd44e366f459841dc1d60a50a49e9265dbcd708ba4e3099051800d3a65cbd3e71ac1a304602e69b56a39104eeedb0a518443c; TS99db2205077=086567d05fab2800c08aabbc77fa2afda2b4ab21be22c7719feedd93937cf8dfbe04c1de2ed02e757709cf3545f4914a086c68300917200012c1c0d9523533471900adfaeec9ae435ea67b198b200266ba54704df6147303; TS6b6d31b1027=086567d05fab2000f06cf2d518f77c509e492f8d4f021521e14b2688ce14146ddf2a3315b2a2433b0883e2162111300024b13cf213b7219e81e1b45f88ec3eb4ec20a4601515b2e1ba2c21f38c93147f88b75ccab7d7f89d21ecd034f61899a0',
        'Origin': 'https://legislacao.presidencia.gov.br',
        'Referer': 'https://legislacao.presidencia.gov.br/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
    }

    data = {
        'pagina': '0',
        'posicao': '0',
        'termo': '',
        'num_ato': law_number,
        'ano_ato': '',
        'dat_inicio': '',
        'dat_termino': '',
        'tipo_macro_ato': '',
        'tipo_ato': '',
        'situacao_ato': '',
        'presidente_exercicio': '',
        'chefe_governo': '',
        'dsc_referenda_ministerial': '',
        'referenda_ministerial': '',
        'origem': '',
        'diario_extra': '',
        'data_resenha': '',
        'num_mes_resenha': '',
        'num_ano_resenha': '',
        'ordenacao': 'maior_data',
        'conteudo_tipo_macro_ato': '',
        'conteudo_tipo_ato': '',
        'conteudo_situacao_ato': '',
        'conteudo_presidente_exercicio': '',
        'conteudo_chefe_governo': '',
        'conteudo_referenda_ministerial': '',
        'conteudo_origem': '',
        'conteudo_diario_extra': '',
    }

    response = requests.post(
        'https://legislacao.presidencia.gov.br/pesquisa/ajax/resultado_pesquisa_legislacao.php',
        cookies=cookies,
        headers=headers,
        data=data,
    )

    dict_response =  {}
    
    time.sleep(2)

    soup = BeautifulSoup(response.text, 'html.parser')

    content = soup.find_all('h4', class_='card-title')
    link = content[0].a.get('href')
    

    lei_data = content[0].text.strip().replace('de', '-', 1)

    lei, data = lei_data.split('-')

    dict_response['link'] = link.strip()
    dict_response['lei'] = lei.strip()
    dict_response['data'] = data.strip()

    response_2 = requests.get(dict_response['link'], headers=headers, verify=False)

    soup = BeautifulSoup(response_2.content, 'html.parser')

    content = soup.find_all('p')

    doc = ""

    for text in content:
        doc+=(text.text)

    dict_response['doc_lei'] = doc

    response_json_str = json.dumps(dict_response)

    return response_json_str



def find_law(id:str, text:str) -> list:
    laws=[]
    cnt=0
    law_regex = "(?i)(Lei|Decreto)\s*(?:[Ff]ederal|[Mm]unicipal)?\s*(?:n?[oº]?°?\s*)?(\d{1,6})[./](\d{1,4})(/(\d{2,4}))?"

    num_regex = "^\d{2}\.\d{3}$"
    
    for law in re.finditer(law_regex, str(text)):
        cnt+=1

        content = law.group()

        pattern = r"\b\d{1,2}\.\d{3}\b"

        num_law = re.findall(pattern, content)

        if len(num_law) == 0:
            continue
        
        content_dict = get_law_info(num_law)
        
        laws.append({
                'excerpt_id': id,
                'content': content_dict,
                'start_offset': law.start(),
                'end_offset': law.start() + len(law.group()),
                'entity_type': 'LAW'
                })
    return laws


def execute_law(file):
    
    contents = file.file.read()
    s = str(contents,'utf-8')
    data = StringIO(s)
    df = pd.read_csv(data)
    count_excerpt = 0
    count_named_entities = 0

    for index, row in df.iterrows():
        names = find_law(row['excerpt_id'], row['excerpt'])
        excerpt_metadata = ExcerptMetadataCreate(excerpt_id=row['excerpt_id'], uf=row['source_state_code'], cidade=row['source_territory_name'], tema=row['excerpt_subthemes'], data=row['source_created_at'])
        db_gen = get_db()
        db = next(db_gen)
        count_excerpt+=1 if (create_excerpt_metadata(db, excerpt_metadata)) else False
        if len(names) > 0:
            for name in names:
                item = NamedEntityCreate(excerpt_id=name['excerpt_id'], content=name['content'], start_offset=name['start_offset'], end_offset=name['end_offset'], entity_type=name['entity_type'])

                count_named_entities+=1 if (create_named_entity(db, item)) else False

    return "Saved " + str(count_excerpt) + " excerpt ids and " + str(count_named_entities) + " named entitites"
