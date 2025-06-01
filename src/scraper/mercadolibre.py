#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def scrape_mercadolibre(query, max_products, shipping_filters=None, max_reviews=5):
    """
    Función principal para hacer scraping de MercadoLibre
    
    Args:
        query (str): Término de búsqueda (ej: "laptops")
        max_products (int): Cantidad máxima de productos a obtener
        shipping_filters (dict): Filtros de envío (envio_full, envio_gratis)
        max_reviews (int): Cantidad máxima de opiniones a obtener por producto
    
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
    if shipping_filters:
        print("🚚 Filtros de envío:")
        if shipping_filters.get('envio_full'):
            print("  - Envío Full")
        if shipping_filters.get('envio_gratis'):
            print("  - Envío Gratis")
    print("="*50)
    
    while len(products) < max_products:
        print(f"📄 Scrapeando página {page}...", end=" ")
        
        # Construir la URL base
        url = f"{base_url}/{query.replace(' ', '-')}"
        
        # Agregar filtros de envío a la URL
        if shipping_filters:
            filters = []
            if shipping_filters.get('envio_full'):
                filters.append('shipping_highlighted_fulfillment')
            if shipping_filters.get('envio_gratis'):
                filters.append('shipping_cost_highlighted_free')
            if filters:
                url += f"_Shipping_{'-'.join(filters)}"
        
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
                    # Obtener opiniones del producto
                    if product['url'] != 'N/A':
                        print(f"\n📝 Obteniendo opiniones para: {product['titulo'][:50]}...")
                        product['opiniones'] = get_product_reviews(session, product['url'], max_reviews)
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

def get_product_reviews(session, product_url, max_reviews):
    """
    Obtiene las opiniones de un producto
    
    Args:
        session (requests.Session): Sesión de requests
        product_url (str): URL del producto
        max_reviews (int): Cantidad máxima de opiniones a obtener
    
    Returns:
        list: Lista de opiniones
    """
    try:
        # Hacer request a la página del producto
        response = session.get(product_url)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar contenedor de opiniones
        reviews = []
        review_containers = soup.find_all('article', class_='ui-review-capability-comments__comment')
        
        for container in review_containers[:max_reviews]:
            review = {}
            
            # Obtener calificación
            rating_container = container.find('div', class_='ui-review-capability-comments__comment__rating')
            if rating_container:
                stars = rating_container.find_all('svg', class_='ui-review-capability-comments__comment__rating__star')
                review['calificacion'] = len(stars)
            else:
                review['calificacion'] = 0
            
            # Obtener fecha
            date = container.find('span', class_='ui-review-capability-comments__comment__date')
            review['fecha'] = date.get_text().strip() if date else 'N/A'
            
            # Obtener contenido
            content = container.find('p', class_='ui-review-capability-comments__comment__content')
            review['contenido'] = content.get_text().strip() if content else 'N/A'
            
            # Obtener votos útiles
            likes = container.find('p', class_='ui-review-capability-valorizations__button-like__text')
            review['votos_utiles'] = likes.get_text().strip() if likes else '0'
            
            reviews.append(review)
        
        return reviews
        
    except Exception as e:
        print(f"Error obteniendo opiniones: {e}")
        return []

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
            
            # Detectar envío gratis
            product['envio_gratis'] = 'gratis' in shipping_text.lower()
            
            # Detectar envío full
            product['envio_full'] = False
            full_shipping = container.find('li', class_='ui-search-filter-highlighted-shipping_highlighted_fulfillment')
            if full_shipping:
                product['envio_full'] = True
                product['envio'] = 'Envío Full'
        else:
            product['envio'] = 'N/A'
            product['envio_gratis'] = False
            product['envio_full'] = False
        
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