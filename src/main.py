#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scraper.mercadolibre import scrape_mercadolibre
from utils.excel_handler import ExcelHandler

def main():
    """
    Función principal que orquesta el proceso de scraping
    """
    print("🔍 MercadoLibre Scraper")
    print("="*50)
    
    # Solicitar parámetros de búsqueda al usuario
    query = input("Por favor ingrese su búsqueda (ejemplo: 'laptop gaming'): ").lower()
    categoria = input("Ingrese la categoría (ejemplo: 'laptops', 'monitores', 'teclados'): ").lower()
    ubicacion = input("Ingrese la ubicación (ejemplo: 'buenos aires'): ").lower()
    orden = input("Ordenar por (precio|nuevo|relevancia): ").lower() or "relevancia"
    precio_min = input("Precio mínimo (opcional, dejar vacío si no aplica): ")
    precio_max = input("Precio máximo (opcional, dejar vacío si no aplica): ")
    max_products = int(input("Cantidad máxima de productos a obtener: "))
    
    # Inicializar el manejador de Excel
    excel_handler = ExcelHandler()
    
    # Realizar el scraping
    products = scrape_mercadolibre(query, max_products)
    
    if products:
        # Agregar productos al Excel
        nuevos, actualizados, duplicados = excel_handler.add_products(products, categoria)
        
        print(f"\n📊 Resumen de la operación:")
        print(f"Nuevos productos: {nuevos}")
        print(f"Productos actualizados: {actualizados}")
        print(f"Productos sin cambios: {duplicados}")
        
        # Mostrar resumen de la categoría actual
        excel_handler.show_summary(categoria)
        
        # Mostrar resumen de todas las categorías
        excel_handler.show_categories_summary()
    else:
        print("\n❌ No se encontraron productos")

if __name__ == "__main__":
    main() 