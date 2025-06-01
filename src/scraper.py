#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper simple para MercadoLibre
Uso: python ml_simple_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from datetime import datetime

def scrape_mercadolibre(query, max_products):
    """
    Función principal para hacer scraping de MercadoLibre
    
    Args:
        query (str): Término de búsqueda (ej: "laptops")
        max_products (int): Cantidad máxima de productos a obtener
    
    Returns:
        list: Lista de productos
    """
    
    # Configuración
    base_url = "https://listado.mercadolibre.com.co"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    products = []
    page = 1
    items_per_page = 50
    
    print(f"🔍 Buscando: {query}")
    print(f"🎯 Objetivo: {max_products} productos")
    print("="*50)
    
    while len(products) < max_products:
        print(f"📄 Scrapeando página {page}...", end=" ")
        
        # Solicitar parámetros de búsqueda al usuario
        query = input("Por favor ingrese su búsqueda (ejemplo: 'laptop gaming'): ").lower()
        categoria = input("Ingrese la categoría (opcional, dejar vacío si no aplica): ").lower()
        ubicacion = input("Ingrese la ubicación (ejemplo: 'buenos aires'): ").lower()
        orden = input("Ordenar por (precio|nuevo|relevancia): ").lower() or "relevancia"
        precio_min = input("Precio mínimo (opcional, dejar vacío si no aplica): ")
        precio_max = input("Precio máximo (opcional, dejar vacío si no aplica): ")
        
        # Construir el nombre del archivo
        archivo = f"resultados_{query.replace(' ', '_')}"
        if categoria:
            archivo += f"_{categoria.replace(' ', '_')}"
        archivo += ".csv"
        
        # Construir la URL base
        url = f"{base_url}/{query.replace(' ', '-')}"
        
        # Agregar parámetros opcionales a la URL
        params = []
        if ubicacion:
            params.append(f"_City_{ubicacion.replace(' ', '-')}")
        if precio_min:
            params.append(f"_PriceRange_{precio_min}-")
        if precio_max:
            params.append(f"_PriceRange-{precio_max}")
        if orden:
            orden_map = {
                "precio": "_PriceRange",
                "nuevo": "_New",
                "relevancia": "_NoIndex_True"
            }
            params.append(orden_map.get(orden, "_NoIndex_True"))
        
        # Construir la URL final
        if params:
            url += "_" + "_".join(params)
        else:
            url += "_NoIndex_True"
        
        if page > 1:
            url += f"_Desde_{(page-1)*items_per_page + 1}"
        
        try:
            # Hacer request
            response = session.get(url)
            response.raise_for_status()
            
            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar productos
            product_containers = soup.find_all('div', class_='poly-card')
            
            if not product_containers:
                print("❌ No se encontraron productos")
                break
            
            page_products = 0
            for container in product_containers:
                if len(products) >= max_products:
                    break
                
                product = extract_product_info(container)
                if product:
                    products.append(product)
                    page_products += 1
            
            print(f"✅ {page_products} productos")
            
            # Verificar si hay más páginas
            pagination = soup.find('ul', class_='andes-pagination')
            if not has_next_page(pagination):
                print("ℹ️  No hay más páginas")
                break
            
            page += 1
            time.sleep(1.5)  # Pausa para evitar ser bloqueado
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    return products

def extract_product_info(container):
    """Extrae información de un producto"""
    try:
        product = {}
        
        # Marca
        brand = container.find('span', class_='poly-component__brand')
        product['marca'] = brand.get_text().strip() if brand else 'N/A'
        
        # Título
        title = container.find('a', class_='poly-component__title')
        product['titulo'] = title.get_text().strip() if title else 'N/A'
        product['url'] = title['href'] if title else 'N/A'
        
        # Precio actual
        current_price = container.find('div', class_='poly-price__current')
        if current_price:
            price_fraction = current_price.find('span', class_='andes-money-amount__fraction')
            if price_fraction:
                price_text = price_fraction.get_text().strip()
                product['precio'] = clean_price(price_text)
            else:
                product['precio'] = 0
        else:
            product['precio'] = 0
        
        # Precio anterior (oferta)
        old_price = container.find('s', class_='andes-money-amount--previous')
        if old_price:
            old_fraction = old_price.find('span', class_='andes-money-amount__fraction')
            product['precio_anterior'] = clean_price(old_fraction.get_text().strip()) if old_fraction else 0
        else:
            product['precio_anterior'] = 0
        
        # Descuento
        discount = container.find('span', class_='andes-money-amount__discount')
        product['descuento'] = discount.get_text().strip() if discount else 'N/A'
        
        # Envío
        shipping = container.find('div', class_='poly-component__shipping')
        if shipping:
            shipping_text = shipping.get_text().strip()
            product['envio'] = shipping_text
            product['envio_gratis'] = 'gratis' in shipping_text.lower()
        else:
            product['envio'] = 'N/A'
            product['envio_gratis'] = False
        
        # Rating
        reviews = container.find('div', class_='poly-component__reviews')
        if reviews:
            rating = reviews.find('span', class_='poly-reviews__rating')
            product['rating'] = rating.get_text().strip() if rating else 'N/A'
            
            total = reviews.find('span', class_='poly-reviews__total')
            if total:
                match = re.search(r'\((\d+)\)', total.get_text())
                product['total_reviews'] = match.group(1) if match else '0'
            else:
                product['total_reviews'] = '0'
        else:
            product['rating'] = 'N/A'
            product['total_reviews'] = '0'
        
        # Imagen
        img = container.find('img', class_='poly-component__picture')
        product['imagen'] = img['src'] if img else 'N/A'
        
        return product
        
    except Exception as e:
        print(f"Error extrayendo producto: {e}")
        return None

def clean_price(price_text):
    """Convierte texto de precio a número"""
    try:
        # Remover puntos y convertir a número
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else 0
    except:
        return 0

def has_next_page(pagination):
    """Verifica si hay página siguiente"""
    if not pagination:
        return False
    
    next_button = pagination.find('li', class_='andes-pagination__button--next')
    if next_button:
        return 'andes-pagination__button--disabled' not in next_button.get('class', [])
    return False

def save_results(products, query):
    """Guarda los resultados en archivos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV
    csv_filename = f"{query}_{len(products)}_productos_{timestamp}.csv"
    df = pd.DataFrame(products)
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    
    # JSON
    json_filename = f"{query}_{len(products)}_productos_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    return csv_filename, json_filename

def show_summary(products):
    """Muestra resumen de los resultados"""
    if not products:
        print("❌ No se encontraron productos")
        return
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total productos: {len(products)}")
    
    # Estadísticas de precios
    precios = [p['precio'] for p in products if p['precio'] > 0]
    if precios:
        print(f"   Precio promedio: ${sum(precios)/len(precios):,.0f}")
        print(f"   Precio mínimo: ${min(precios):,.0f}")
        print(f"   Precio máximo: ${max(precios):,.0f}")
    
    # Envío gratis
    envio_gratis = sum(1 for p in products if p.get('envio_gratis', False))
    porcentaje = (envio_gratis/len(products)*100) if products else 0
    print(f"   Con envío gratis: {envio_gratis}/{len(products)} ({porcentaje:.1f}%)")
    
    # Top marcas
    marcas = {}
    for p in products:
        marca = p.get('marca', 'N/A')
        marcas[marca] = marcas.get(marca, 0) + 1
    
    top_marcas = sorted(marcas.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"   Top marcas: {', '.join([f'{m}({c})' for m, c in top_marcas])}")

def main():
    """Función principal"""
    print("🛒 MERCADOLIBRE SCRAPER")
    print("="*30)
    
    # Obtener parámetros del usuario
    query = input("Término de búsqueda (ej: laptops): ").strip()
    if not query:
        query = "laptops"  # valor por defecto
    
    try:
        max_products = int(input("Cantidad de productos (ej: 100): "))
    except ValueError:
        max_products = 100  # valor por defecto
    
    # Ejecutar scraping
    start_time = time.time()
    products = scrape_mercadolibre(query, max_products)
    end_time = time.time()
    
    # Mostrar resultados
    print(f"\n⏱️  Tiempo total: {end_time - start_time:.1f} segundos")
    show_summary(products)
    
    if products:
        # Guardar archivos
        csv_file, json_file = save_results(products, query)
        print(f"\n💾 Archivos guardados:")
        print(f"   📊 CSV: {csv_file}")
        print(f"   📋 JSON: {json_file}")
        
        # Mostrar algunos productos
        print(f"\n🔍 PRIMEROS 3 PRODUCTOS:")
        for i, product in enumerate(products[:3], 1):
            print(f"\n{i}. {product['titulo'][:60]}...")
            print(f"   💰 Precio: ${product['precio']:,}")
            if product['precio_anterior'] > 0:
                print(f"   🏷️  Antes: ${product['precio_anterior']:,} ({product['descuento']})")
            print(f"   ⭐ Rating: {product['rating']} ({product['total_reviews']} reviews)")
            print(f"   🚚 {product['envio']}")
    
    print(f"\n✅ Scraping completado!")

if __name__ == "__main__":
    main()