import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

url = 'https://www.amazon.com.br/Echo-Dot-5%C2%AA-gera%C3%A7%C3%A3o-Cor-Preta/dp/B09B8VGCR8?ref=dlx_black_dg_dcl_B09B8VGCR8_dt_sl7_4a_pi&pf_rd_r=J2BFY89QAMFQVZG785AJ&pf_rd_p=7b6891fe-2bf4-4d13-be1e-f0767faf374a&th=1'

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Salvar HTML
with open('amazon_debug.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("HTML salvo em amazon_debug.html")

# Buscar todos os elementos que podem conter preço
print("\n=== BUSCANDO PREÇOS ===")
price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower())
for elem in price_elements[:10]:
    print(f"\nClass: {elem.get('class')}")
    print(f"Text: {elem.get_text(strip=True)[:100]}")

# Buscar por IDs relacionados a preço
print("\n=== BUSCANDO POR IDs ===")
price_ids = ['priceblock_ourprice', 'priceblock_dealprice', 'priceblock_saleprice', 'price_inside_buybox', 'corePrice_feature_div']
for price_id in price_ids:
    elem = soup.find(id=price_id)
    if elem:
        print(f"\nID: {price_id}")
        print(f"Text: {elem.get_text(strip=True)}")

# Buscar span com price
print("\n=== BUSCANDO SPANS COM PREÇO ===")
price_spans = soup.find_all('span', class_=lambda x: x and any(p in str(x).lower() for p in ['price', 'pricetopay']))
for span in price_spans[:10]:
    print(f"\nClass: {span.get('class')}")
    print(f"Text: {span.get_text(strip=True)}")
