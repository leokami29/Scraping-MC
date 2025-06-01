#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
from datetime import datetime
import os
import time

class ExcelHandler:
    def __init__(self):
        """
        Inicializa el manejador de Excel con múltiples hojas por categoría
        """
        self.excel_file = "productos_mercadolibre.xlsx"
        self.sheets = self._load_or_create_excel()
    
    def _load_or_create_excel(self):
        """
        Carga el archivo Excel existente o crea uno nuevo
        
        Returns:
            dict: Diccionario con los DataFrames de cada hoja
        """
        if os.path.exists(self.excel_file):
            try:
                print(f"📂 Cargando archivo existente: {self.excel_file}")
                return pd.read_excel(self.excel_file, sheet_name=None)
            except PermissionError:
                print(f"⚠️  No se puede acceder al archivo {self.excel_file}")
                print("Por favor, cierre el archivo si está abierto en Excel y presione Enter para continuar...")
                input()
                return self._load_or_create_excel()
        else:
            print(f"📝 Creando nuevo archivo: {self.excel_file}")
            return {}
    
    def _get_sheet_name(self, categoria):
        """
        Obtiene el nombre de la hoja para una categoría
        
        Args:
            categoria (str): Categoría del producto
            
        Returns:
            str: Nombre de la hoja
        """
        return categoria.lower().replace(' ', '_')
    
    def _get_or_create_sheet(self, categoria):
        """
        Obtiene o crea una hoja para una categoría
        
        Args:
            categoria (str): Categoría del producto
            
        Returns:
            pd.DataFrame: DataFrame de la hoja
        """
        sheet_name = self._get_sheet_name(categoria)
        
        if sheet_name not in self.sheets:
            print(f"📝 Creando nueva hoja: {sheet_name}")
            self.sheets[sheet_name] = pd.DataFrame(columns=[
                'marca', 'titulo', 'url', 'precio', 'precio_anterior',
                'descuento', 'envio', 'envio_gratis', 'envio_full', 'rating',
                'total_reviews', 'imagen', 'opiniones', 'fecha_actualizacion'
            ])
        
        return self.sheets[sheet_name]
    
    def _is_duplicate(self, product, categoria):
        """
        Verifica si un producto ya existe en la hoja de la categoría
        
        Args:
            product (dict): Producto a verificar
            categoria (str): Categoría del producto
            
        Returns:
            bool: True si es duplicado, False si no
        """
        df = self._get_or_create_sheet(categoria)
        
        # Buscar por URL (identificador único)
        if 'url' in product and product['url'] != 'N/A':
            return product['url'] in df['url'].values
        # Si no hay URL, buscar por título y marca
        return (product['titulo'] in df['titulo'].values and 
                product['marca'] in df['marca'].values)
    
    def _update_existing_product(self, product, categoria):
        """
        Actualiza un producto existente si hay cambios
        
        Args:
            product (dict): Producto con datos actualizados
            categoria (str): Categoría del producto
            
        Returns:
            bool: True si hubo cambios, False si no
        """
        df = self._get_or_create_sheet(categoria)
        
        if 'url' in product and product['url'] != 'N/A':
            mask = df['url'] == product['url']
        else:
            mask = (df['titulo'] == product['titulo']) & (df['marca'] == product['marca'])
        
        if not mask.any():
            return False
        
        existing_product = df[mask].iloc[0].to_dict()
        changes = []
        
        # Verificar cambios en cada campo
        for key in product:
            if key in existing_product and product[key] != existing_product[key]:
                changes.append(f"{key}: {existing_product[key]} -> {product[key]}")
                df.loc[mask, key] = product[key]
        
        if changes:
            print(f"🔄 Actualizando producto: {product['titulo']}")
            print("Cambios detectados:")
            for change in changes:
                print(f"  - {change}")
            df.loc[mask, 'fecha_actualizacion'] = datetime.now()
            return True
        
        return False
    
    def add_products(self, products, categoria):
        """
        Agrega nuevos productos a la hoja de la categoría
        
        Args:
            products (list): Lista de productos a agregar
            categoria (str): Categoría de los productos
            
        Returns:
            tuple: (nuevos, actualizados, duplicados)
        """
        nuevos = 0
        actualizados = 0
        duplicados = 0
        
        df = self._get_or_create_sheet(categoria)
        
        for product in products:
            # Agregar fecha de actualización
            product['fecha_actualizacion'] = datetime.now()
            
            if self._is_duplicate(product, categoria):
                if self._update_existing_product(product, categoria):
                    actualizados += 1
                else:
                    duplicados += 1
            else:
                df = pd.concat([df, pd.DataFrame([product])], ignore_index=True)
                nuevos += 1
        
        # Actualizar el DataFrame en el diccionario
        self.sheets[self._get_sheet_name(categoria)] = df
        
        # Guardar cambios
        self.save()
        
        return nuevos, actualizados, duplicados
    
    def save(self, max_retries=3):
        """
        Guarda todos los DataFrames en el archivo Excel
        
        Args:
            max_retries (int): Número máximo de intentos de guardado
        """
        for attempt in range(max_retries):
            try:
                with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                    for sheet_name, df in self.sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"💾 Guardando cambios en: {self.excel_file}")
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"⚠️  No se puede guardar el archivo {self.excel_file}")
                    print("Por favor, cierre el archivo si está abierto en Excel y presione Enter para continuar...")
                    input()
                    time.sleep(1)  # Esperar un momento antes de reintentar
                else:
                    print("❌ No se pudo guardar el archivo después de varios intentos")
                    print("Los cambios se mantendrán en memoria hasta que se pueda guardar")
                    raise
    
    def show_summary(self, categoria):
        """
        Muestra un resumen de los datos en la hoja de la categoría
        
        Args:
            categoria (str): Categoría a mostrar
        """
        sheet_name = self._get_sheet_name(categoria)
        if sheet_name not in self.sheets:
            print(f"❌ No existe la hoja para la categoría: {categoria}")
            return
        
        df = self.sheets[sheet_name]
        if df.empty:
            print(f"❌ No hay productos en la categoría: {categoria}")
            return
        
        print("\n📊 Resumen de datos:")
        print("="*50)
        print(f"Categoría: {categoria}")
        print(f"Total productos: {len(df)}")
        
        if 'precio' in df.columns:
            print(f"Precio promedio: ${df['precio'].mean():,.0f}")
            print(f"Precio mínimo: ${df['precio'].min():,.0f}")
            print(f"Precio máximo: ${df['precio'].max():,.0f}")
        
        if 'envio_gratis' in df.columns:
            envio_gratis = df['envio_gratis'].sum()
            print(f"Productos con envío gratis: {envio_gratis} ({envio_gratis/len(df)*100:.1f}%)")
        
        if 'envio_full' in df.columns:
            envio_full = df['envio_full'].sum()
            print(f"Productos con envío Full: {envio_full} ({envio_full/len(df)*100:.1f}%)")
        
        if 'rating' in df.columns:
            ratings = df[df['rating'] != 'N/A']['rating'].astype(float)
            if not ratings.empty:
                print(f"Rating promedio: {ratings.mean():.1f}")
        
        # Mostrar estadísticas de opiniones
        if 'opiniones' in df.columns:
            total_opiniones = sum(len(opiniones) for opiniones in df['opiniones'] if opiniones)
            if total_opiniones > 0:
                print(f"\n📝 Estadísticas de opiniones:")
                print(f"Total de opiniones: {total_opiniones}")
                print(f"Promedio de opiniones por producto: {total_opiniones/len(df):.1f}")
                
                # Calcular promedio de calificaciones
                calificaciones = []
                for opiniones in df['opiniones']:
                    if opiniones:
                        for opinion in opiniones:
                            if 'calificacion' in opinion:
                                calificaciones.append(opinion['calificacion'])
                
                if calificaciones:
                    print(f"Calificación promedio: {sum(calificaciones)/len(calificaciones):.1f}")
        
        # Mostrar última actualización
        if 'fecha_actualizacion' in df.columns:
            ultima_actualizacion = df['fecha_actualizacion'].max()
            print(f"\nÚltima actualización: {ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("="*50)
    
    def show_categories_summary(self):
        """Muestra un resumen de todas las categorías en el archivo"""
        if not self.sheets:
            print("❌ No hay categorías en el archivo")
            return
        
        print("\n📑 Resumen de categorías:")
        print("="*50)
        
        for sheet_name, df in self.sheets.items():
            categoria = sheet_name.replace('_', ' ').title()
            print(f"\n📦 {categoria}:")
            print(f"  Total productos: {len(df)}")
            
            if 'precio' in df.columns:
                print(f"  Precio promedio: ${df['precio'].mean():,.0f}")
                print(f"  Precio mínimo: ${df['precio'].min():,.0f}")
                print(f"  Precio máximo: ${df['precio'].max():,.0f}")
            
            if 'fecha_actualizacion' in df.columns:
                ultima_actualizacion = df['fecha_actualizacion'].max()
                print(f"  Última actualización: {ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*50)
    
    def get_existing_categories(self):
        """
        Obtiene la lista de categorías existentes
        
        Returns:
            list: Lista de categorías
        """
        return [sheet_name.replace('_', ' ').title() for sheet_name in self.sheets.keys()]

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