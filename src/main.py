#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scraper.mercadolibre import scrape_mercadolibre
from utils.excel_handler import ExcelHandler

def select_category(excel_handler):
    """
    Permite al usuario seleccionar o crear una categoría
    
    Args:
        excel_handler (ExcelHandler): Instancia del manejador de Excel
        
    Returns:
        str: Categoría seleccionada
    """
    existing_categories = excel_handler.get_existing_categories()
    
    if existing_categories:
        print("\n📑 Categorías existentes:")
        for i, cat in enumerate(existing_categories, 1):
            print(f"{i}. {cat}")
        print(f"{len(existing_categories) + 1}. Crear nueva categoría")
        
        while True:
            try:
                choice = int(input("\nSeleccione una opción: "))
                if 1 <= choice <= len(existing_categories):
                    return existing_categories[choice - 1]
                elif choice == len(existing_categories) + 1:
                    break
                else:
                    print("❌ Opción inválida")
            except ValueError:
                print("❌ Por favor ingrese un número")
    
    # Si no hay categorías o el usuario quiere crear una nueva
    while True:
        new_category = input("\nIngrese el nombre de la nueva categoría: ").strip()
        if new_category:
            return new_category
        print("❌ El nombre de la categoría no puede estar vacío")

def get_shipping_filters():
    """
    Solicita al usuario los filtros de envío
    
    Returns:
        dict: Filtros de envío seleccionados
    """
    print("\n🚚 Filtros de envío:")
    print("1. Sin filtros")
    print("2. Solo envío Full")
    print("3. Solo envío gratis")
    print("4. Envío Full y gratis")
    
    while True:
        try:
            choice = int(input("\nSeleccione una opción: "))
            if 1 <= choice <= 4:
                if choice == 1:
                    return {}
                elif choice == 2:
                    return {'envio_full': True}
                elif choice == 3:
                    return {'envio_gratis': True}
                else:  # choice == 4
                    return {'envio_full': True, 'envio_gratis': True}
            else:
                print("❌ Opción inválida")
        except ValueError:
            print("❌ Por favor ingrese un número")

def main():
    """
    Función principal que orquesta el proceso de scraping
    """
    print("🔍 MercadoLibre Scraper")
    print("="*50)
    
    # Inicializar el manejador de Excel
    excel_handler = ExcelHandler()
    
    # Seleccionar categoría
    categoria = select_category(excel_handler)
    print(f"\n✅ Categoría seleccionada: {categoria}")
    
    # Solicitar parámetros de búsqueda al usuario
    query = input("\nPor favor ingrese su búsqueda (ejemplo: 'laptop gaming'): ").lower()
    ubicacion = input("Ingrese la ubicación (ejemplo: 'buenos aires'): ").lower()
    orden = input("Ordenar por (precio|nuevo|relevancia): ").lower() or "relevancia"
    precio_min = input("Precio mínimo (opcional, dejar vacío si no aplica): ")
    precio_max = input("Precio máximo (opcional, dejar vacío si no aplica): ")
    max_products = int(input("Cantidad máxima de productos a obtener: "))
    
    # Obtener filtros de envío
    shipping_filters = get_shipping_filters()
    
    # Realizar el scraping
    products = scrape_mercadolibre(query, max_products, shipping_filters)
    
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