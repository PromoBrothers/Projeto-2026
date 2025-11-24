from bs4 import BeautifulSoup

with open('amazon_api_response.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

print("=" * 80)
print("ANALISANDO ESTRUTURA DOS PREÇOS")
print("=" * 80)

# Pegar todos os preços
price_elems = soup.select('.a-price .a-offscreen')

for i, price_elem in enumerate(price_elems, 1):
    print(f"\n{'='*40}")
    print(f"PREÇO {i}: {price_elem.get_text(strip=True)}")
    print(f"{'='*40}")

    # Subir na hierarquia para entender o contexto
    current = price_elem
    depth = 0
    while current and depth < 10:
        current = current.parent
        depth += 1

        if current and current.name == 'div':
            div_id = current.get('id', '')
            div_class = ' '.join(current.get('class', []))

            # Mostrar apenas divs com ID ou classes relevantes
            if div_id or any(keyword in div_class.lower() for keyword in ['price', 'core', 'apex', 'desktop', 'feature', 'product', 'detail']):
                print(f"  {'  ' * depth}DIV - ID: {div_id or 'N/A'} | Classes: {div_class[:60] if div_class else 'N/A'}")

    print()
