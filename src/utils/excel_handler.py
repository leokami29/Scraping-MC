#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from datetime import datetime

def save_results(products, query):
    """
    Guarda los resultados en archivos CSV y JSON
    
    Args:
        products (list): Lista de productos
        query (str): Término de búsqueda
    
    Returns:
        tuple: (nombre_archivo_csv, nombre_archivo_json)
    """
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
    """
    Muestra resumen de los resultados
    
    Args:
        products (list): Lista de productos
    """
    if not products:
        print("❌ No se encontraron productos")
        return
    
    df = pd.DataFrame(products)
    
    print("\n📊 Resumen de resultados:")
    print("="*50)
    print(f"Total productos: {len(products)}")
    
    if 'precio' in df.columns:
        print(f"Precio promedio: ${df['precio'].mean():,.0f}")
        print(f"Precio mínimo: ${df['precio'].min():,.0f}")
        print(f"Precio máximo: ${df['precio'].max():,.0f}")
    
    if 'envio_gratis' in df.columns:
        envio_gratis = df['envio_gratis'].sum()
        print(f"Productos con envío gratis: {envio_gratis} ({envio_gratis/len(df)*100:.1f}%)")
    
    if 'rating' in df.columns:
        ratings = df[df['rating'] != 'N/A']['rating'].astype(float)
        if not ratings.empty:
            print(f"Rating promedio: {ratings.mean():.1f}")
    
    print("="*50) 