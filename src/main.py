#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scraper.mercadolibre import scrape_mercadolibre
from utils.excel_handler import save_results, show_summary

def main():
    """
    Función principal que orquesta el proceso de scraping
    """
    print("🔍 MercadoLibre Scraper")
    print("="*50)
    
    # Solicitar parámetros de búsqueda al usuario
    query = input("Por favor ingrese su búsqueda (ejemplo: 'laptop gaming'): ").lower()
    categoria = input("Ingrese la categoría (opcional, dejar vacío si no aplica): ").lower()
    ubicacion = input("Ingrese la ubicación (ejemplo: 'buenos aires'): ").lower()
    orden = input("Ordenar por (precio|nuevo|relevancia): ").lower() or "relevancia"
    precio_min = input("Precio mínimo (opcional, dejar vacío si no aplica): ")
    precio_max = input("Precio máximo (opcional, dejar vacío si no aplica): ")
    max_products = int(input("Cantidad máxima de productos a obtener: "))
    
    # Construir el nombre del archivo
    archivo = f"resultados_{query.replace(' ', '_')}"
    if categoria:
        archivo += f"_{categoria.replace(' ', '_')}"
    
    # Realizar el scraping
    products = scrape_mercadolibre(query, max_products)
    
    if products:
        # Guardar resultados
        csv_file, json_file = save_results(products, archivo)
        print(f"\n✅ Resultados guardados en:")
        print(f"CSV: {csv_file}")
        print(f"JSON: {json_file}")
        
        # Mostrar resumen
        show_summary(products)
    else:
        print("\n❌ No se encontraron productos")

if __name__ == "__main__":
    main() 