#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from datetime import datetime
import os

class ExcelHandler:
    def __init__(self):
        """
        Inicializa el manejador de Excel con un único archivo para todas las categorías
        """
        self.excel_file = "productos_mercadolibre.xlsx"
        self.df = self._load_or_create_excel()
    
    def _load_or_create_excel(self):
        """
        Carga el archivo Excel existente o crea uno nuevo
        
        Returns:
            pd.DataFrame: DataFrame con los datos
        """
        if os.path.exists(self.excel_file):
            print(f"📂 Cargando archivo existente: {self.excel_file}")
            return pd.read_excel(self.excel_file)
        else:
            print(f"📝 Creando nuevo archivo: {self.excel_file}")
            return pd.DataFrame(columns=[
                'categoria', 'marca', 'titulo', 'url', 'precio', 'precio_anterior',
                'descuento', 'envio', 'envio_gratis', 'rating',
                'total_reviews', 'imagen', 'fecha_actualizacion'
            ])
    
    def _is_duplicate(self, product, categoria):
        """
        Verifica si un producto ya existe en el DataFrame para una categoría específica
        
        Args:
            product (dict): Producto a verificar
            categoria (str): Categoría del producto
            
        Returns:
            bool: True si es duplicado, False si no
        """
        # Filtrar por categoría
        df_categoria = self.df[self.df['categoria'] == categoria]
        
        # Buscar por URL (identificador único)
        if 'url' in product and product['url'] != 'N/A':
            return product['url'] in df_categoria['url'].values
        # Si no hay URL, buscar por título y marca
        return (product['titulo'] in df_categoria['titulo'].values and 
                product['marca'] in df_categoria['marca'].values)
    
    def _update_existing_product(self, product, categoria):
        """
        Actualiza un producto existente si hay cambios
        
        Args:
            product (dict): Producto con datos actualizados
            categoria (str): Categoría del producto
            
        Returns:
            bool: True si hubo cambios, False si no
        """
        # Filtrar por categoría
        mask = self.df['categoria'] == categoria
        
        if 'url' in product and product['url'] != 'N/A':
            mask = mask & (self.df['url'] == product['url'])
        else:
            mask = mask & (self.df['titulo'] == product['titulo']) & (self.df['marca'] == product['marca'])
        
        if not mask.any():
            return False
        
        existing_product = self.df[mask].iloc[0].to_dict()
        changes = []
        
        # Verificar cambios en cada campo
        for key in product:
            if key in existing_product and product[key] != existing_product[key]:
                changes.append(f"{key}: {existing_product[key]} -> {product[key]}")
                self.df.loc[mask, key] = product[key]
        
        if changes:
            print(f"🔄 Actualizando producto: {product['titulo']}")
            print("Cambios detectados:")
            for change in changes:
                print(f"  - {change}")
            self.df.loc[mask, 'fecha_actualizacion'] = datetime.now()
            return True
        
        return False
    
    def add_products(self, products, categoria):
        """
        Agrega nuevos productos al Excel, actualizando los existentes
        
        Args:
            products (list): Lista de productos a agregar
            categoria (str): Categoría de los productos
            
        Returns:
            tuple: (nuevos, actualizados, duplicados)
        """
        nuevos = 0
        actualizados = 0
        duplicados = 0
        
        for product in products:
            # Agregar fecha de actualización y categoría
            product['fecha_actualizacion'] = datetime.now()
            product['categoria'] = categoria
            
            if self._is_duplicate(product, categoria):
                if self._update_existing_product(product, categoria):
                    actualizados += 1
                else:
                    duplicados += 1
            else:
                self.df = pd.concat([self.df, pd.DataFrame([product])], ignore_index=True)
                nuevos += 1
        
        # Guardar cambios
        self.save()
        
        return nuevos, actualizados, duplicados
    
    def save(self):
        """Guarda el DataFrame en el archivo Excel"""
        self.df.to_excel(self.excel_file, index=False)
        print(f"💾 Guardando cambios en: {self.excel_file}")
    
    def show_summary(self, categoria=None):
        """
        Muestra un resumen de los datos en el Excel
        
        Args:
            categoria (str, optional): Si se especifica, muestra solo el resumen de esa categoría
        """
        if self.df.empty:
            print("❌ No hay productos en el archivo")
            return
        
        # Filtrar por categoría si se especifica
        df_to_show = self.df[self.df['categoria'] == categoria] if categoria else self.df
        
        if df_to_show.empty:
            print(f"❌ No hay productos en la categoría: {categoria}")
            return
        
        print("\n📊 Resumen de datos:")
        print("="*50)
        
        if categoria:
            print(f"Categoría: {categoria}")
        
        print(f"Total productos: {len(df_to_show)}")
        
        if 'precio' in df_to_show.columns:
            print(f"Precio promedio: ${df_to_show['precio'].mean():,.0f}")
            print(f"Precio mínimo: ${df_to_show['precio'].min():,.0f}")
            print(f"Precio máximo: ${df_to_show['precio'].max():,.0f}")
        
        if 'envio_gratis' in df_to_show.columns:
            envio_gratis = df_to_show['envio_gratis'].sum()
            print(f"Productos con envío gratis: {envio_gratis} ({envio_gratis/len(df_to_show)*100:.1f}%)")
        
        if 'rating' in df_to_show.columns:
            ratings = df_to_show[df_to_show['rating'] != 'N/A']['rating'].astype(float)
            if not ratings.empty:
                print(f"Rating promedio: {ratings.mean():.1f}")
        
        # Mostrar última actualización
        if 'fecha_actualizacion' in df_to_show.columns:
            ultima_actualizacion = df_to_show['fecha_actualizacion'].max()
            print(f"\nÚltima actualización: {ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("="*50)
    
    def show_categories_summary(self):
        """Muestra un resumen de todas las categorías en el archivo"""
        if self.df.empty:
            print("❌ No hay productos en el archivo")
            return
        
        print("\n📑 Resumen de categorías:")
        print("="*50)
        
        # Agrupar por categoría y contar productos
        categorias = self.df.groupby('categoria').agg({
            'titulo': 'count',
            'precio': ['mean', 'min', 'max'],
            'fecha_actualizacion': 'max'
        }).round(2)
        
        for categoria, row in categorias.iterrows():
            print(f"\n📦 {categoria}:")
            print(f"  Total productos: {row[('titulo', 'count')]}")
            print(f"  Precio promedio: ${row[('precio', 'mean')]:,.0f}")
            print(f"  Precio mínimo: ${row[('precio', 'min')]:,.0f}")
            print(f"  Precio máximo: ${row[('precio', 'max')]:,.0f}")
            print(f"  Última actualización: {row[('fecha_actualizacion', 'max')].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*50)

def save_results(products, query, categoria):
    """
    Función de compatibilidad para mantener la interfaz anterior
    
    Args:
        products (list): Lista de productos
        query (str): Término de búsqueda
        categoria (str): Categoría de los productos
    
    Returns:
        tuple: (nombre_archivo_excel, None)
    """
    handler = ExcelHandler()
    nuevos, actualizados, duplicados = handler.add_products(products, categoria)
    
    print(f"\n📊 Resumen de la operación:")
    print(f"Nuevos productos: {nuevos}")
    print(f"Productos actualizados: {actualizados}")
    print(f"Productos sin cambios: {duplicados}")
    
    handler.show_summary(categoria)
    handler.show_categories_summary()
    
    return handler.excel_file, None 