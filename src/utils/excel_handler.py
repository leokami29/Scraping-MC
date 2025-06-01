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
        self.json_dir = "json_categorias"
        self.sheets = self._load_or_create_excel()
        
        # Crear directorio para JSONs si no existe
        if not os.path.exists(self.json_dir):
            os.makedirs(self.json_dir)
    
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
            # Definir tipos de datos para cada columna
            dtypes = {
                'marca': str,
                'titulo': str,
                'url': str,
                'precio': 'Int64',  # Tipo nullable integer
                'precio_anterior': 'Int64',  # Tipo nullable integer
                'descuento': str,
                'envio': str,
                'envio_gratis': bool,
                'envio_full': bool,
                'rating': str,
                'total_reviews': str,
                'imagen': str,
                'imagenes': object,
                'opiniones': object,
                'fecha_actualizacion': 'datetime64[ns]'
            }
            
            # Crear DataFrame con tipos de datos específicos
            self.sheets[sheet_name] = pd.DataFrame(columns=list(dtypes.keys())).astype(dtypes)
        
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
            
            # Asegurar que todos los campos requeridos existan y tengan el tipo correcto
            for field in df.columns:
                if field not in product:
                    if field in ['imagenes', 'opiniones']:
                        product[field] = []
                    elif field in ['envio_gratis', 'envio_full']:
                        product[field] = False
                    elif field in ['precio', 'precio_anterior']:
                        product[field] = pd.NA  # Usar pd.NA para valores nulos
                    else:
                        product[field] = 'N/A'
                else:
                    # Convertir valores según el tipo esperado
                    if field in ['precio', 'precio_anterior']:
                        try:
                            product[field] = int(product[field]) if product[field] != 'N/A' else pd.NA
                        except (ValueError, TypeError):
                            product[field] = pd.NA
                    elif field in ['envio_gratis', 'envio_full']:
                        product[field] = bool(product[field])
                    elif field in ['imagenes', 'opiniones']:
                        if not isinstance(product[field], list):
                            product[field] = []
            
            if self._is_duplicate(product, categoria):
                if self._update_existing_product(product, categoria):
                    actualizados += 1
                else:
                    duplicados += 1
            else:
                try:
                    # Convertir el producto a DataFrame con los tipos de datos correctos
                    new_df = pd.DataFrame([product])
                    new_df = new_df.astype(df.dtypes)
                    df = pd.concat([df, new_df], ignore_index=True)
                    nuevos += 1
                except Exception as e:
                    print(f"⚠️ Error al agregar producto: {e}")
                    print(f"Producto: {product['titulo']}")
                    continue
        
        # Actualizar el DataFrame en el diccionario
        self.sheets[self._get_sheet_name(categoria)] = df
        
        # Guardar cambios
        self.save()
        
        return nuevos, actualizados, duplicados
    
    def _get_json_filename(self, categoria):
        """
        Obtiene el nombre del archivo JSON para una categoría
        
        Args:
            categoria (str): Categoría del producto
            
        Returns:
            str: Nombre del archivo JSON
        """
        return os.path.join(self.json_dir, f"{categoria.lower().replace(' ', '_')}.json")
    
    def _convert_to_json_serializable(self, value):
        """
        Convierte valores de pandas a tipos serializables para JSON
        
        Args:
            value: Valor a convertir
            
        Returns:
            Valor serializable para JSON
        """
        if isinstance(value, pd.Timestamp):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, list):
            return [self._convert_to_json_serializable(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in value.items()}
        elif pd.isna(value):
            return None
        return value
    
    def _prepare_category_json(self, categoria, df):
        """
        Prepara los datos de una categoría para guardar en JSON
        
        Args:
            categoria (str): Nombre de la categoría
            df (pd.DataFrame): DataFrame con los productos
            
        Returns:
            dict: Datos organizados de la categoría
        """
        json_data = {
            'metadata': {
                'categoria': categoria,
                'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_productos': len(df)
            },
            'estadisticas': {
                'precio_promedio': float(df['precio'].mean()),
                'precio_minimo': int(df['precio'].min()),
                'precio_maximo': int(df['precio'].max()),
                'productos_envio_gratis': int(df['envio_gratis'].sum()),
                'productos_envio_full': int(df['envio_full'].sum())
            },
            'productos': []
        }
        
        # Agregar estadísticas de imágenes si existen
        if 'imagenes' in df.columns:
            total_imagenes = sum(len(imagenes) for imagenes in df['imagenes'] if isinstance(imagenes, list))
            json_data['estadisticas']['total_imagenes'] = total_imagenes
            json_data['estadisticas']['promedio_imagenes'] = round(total_imagenes / len(df), 1)
        
        # Agregar estadísticas de opiniones si existen
        if 'opiniones' in df.columns:
            total_opiniones = sum(len(opiniones) for opiniones in df['opiniones'] if isinstance(opiniones, list))
            if total_opiniones > 0:
                json_data['estadisticas']['total_opiniones'] = total_opiniones
                json_data['estadisticas']['promedio_opiniones'] = round(total_opiniones / len(df), 1)
                
                # Calcular promedio de calificaciones
                calificaciones = []
                for opiniones in df['opiniones']:
                    if isinstance(opiniones, list):
                        for opinion in opiniones:
                            if isinstance(opinion, dict) and 'calificacion' in opinion:
                                calificaciones.append(opinion['calificacion'])
                
                if calificaciones:
                    json_data['estadisticas']['calificacion_promedio'] = round(sum(calificaciones) / len(calificaciones), 1)
        
        # Agregar productos
        for _, row in df.iterrows():
            producto = row.to_dict()
            producto = self._convert_to_json_serializable(producto)
            json_data['productos'].append(producto)
        
        return json_data
    
    def save_category_json(self, categoria):
        """
        Guarda los datos de una categoría en su archivo JSON
        
        Args:
            categoria (str): Categoría a guardar
        """
        try:
            sheet_name = self._get_sheet_name(categoria)
            if sheet_name not in self.sheets:
                print(f"❌ No existe la categoría: {categoria}")
                return
            
            df = self.sheets[sheet_name]
            json_data = self._prepare_category_json(categoria, df)
            
            json_file = self._get_json_filename(categoria)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Guardando datos de {categoria} en: {json_file}")
        except Exception as e:
            print(f"❌ Error guardando JSON de {categoria}: {e}")
    
    def save(self, max_retries=3):
        """
        Guarda todos los DataFrames en el archivo Excel y los JSONs por categoría
        
        Args:
            max_retries (int): Número máximo de intentos de guardado
        """
        for attempt in range(max_retries):
            try:
                with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                    for sheet_name, df in self.sheets.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"💾 Guardando cambios en: {self.excel_file}")
                
                # Guardar JSONs por categoría
                for sheet_name in self.sheets.keys():
                    categoria = sheet_name.replace('_', ' ').title()
                    self.save_category_json(categoria)
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
        
        # Mostrar estadísticas de imágenes
        if 'imagenes' in df.columns:
            total_imagenes = sum(len(imagenes) for imagenes in df['imagenes'] if isinstance(imagenes, list))
            if total_imagenes > 0:
                print(f"\n🖼️  Estadísticas de imágenes:")
                print(f"Total de imágenes: {total_imagenes}")
                print(f"Promedio de imágenes por producto: {total_imagenes/len(df):.1f}")
        
        # Mostrar estadísticas de opiniones
        if 'opiniones' in df.columns:
            total_opiniones = sum(len(opiniones) for opiniones in df['opiniones'] if isinstance(opiniones, list))
            if total_opiniones > 0:
                print(f"\n📝 Estadísticas de opiniones:")
                print(f"Total de opiniones: {total_opiniones}")
                print(f"Promedio de opiniones por producto: {total_opiniones/len(df):.1f}")
                
                # Calcular promedio de calificaciones
                calificaciones = []
                for opiniones in df['opiniones']:
                    if isinstance(opiniones, list):
                        for opinion in opiniones:
                            if isinstance(opinion, dict) and 'calificacion' in opinion:
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