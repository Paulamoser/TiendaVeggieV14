# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.tools.float_utils import float_round as round
from openerp.exceptions import ValidationError, Warning
from datetime import timedelta, date, datetime, time
from num2words import num2words

import locale
import logging

_logger = logging.getLogger(__name__)


class ReportStockPickingQs(models.AbstractModel):
    _name = "report.veggie.roadmap_report"

    def _all_products_for_clients(self, date):
        categoria_cogelados = []
        categoria_refrigerados = []
        categoria_secos = []
        main_categ = None
        all_date = {}
        if len(date) > 1:
            for rec in date:
                for line in rec.sale_id:
                    for order_line in line.order_line:
                        if order_line.product_id.categ_id.parent_id.name:
                            main_categ = order_line.product_id.categ_id.parent_id.name if order_line.product_id.categ_id.parent_id else None
                            categ = order_line.product_id.categ_id.name
                            order_category = order_line.product_id.categ_id.order_report
                            product_name = order_line.product_id.description_pickingout
                            quantity_product = order_line.product_uom_qty                                              
                            line_data = {
                                'categ': categ,
                                'main_categ': main_categ,
                                'order_category': order_category,
                                'total_products': int(quantity_product),
                                'data': [{
                                    'product_name': product_name,
                                    'quantity_product': int(quantity_product),
                                    'order_product':order_line.product_id.order_report,

                                }]
                            }
                        else:
                            raise ValidationError(f'El producto  {order_line.product_id.description_pickingout}, no tiene categoria padre, referencia {rec.name}!! ')  
                        try:
                            if main_categ == 'Congelados':
                                
                                if categoria_cogelados:
                                    categoria_cogelados = self.filterCategory(categoria_cogelados,line_data)
                                    
                                else:
                                    categoria_cogelados.append(line_data)
                                    
                                categoria_cogelados = sorted(
                                    categoria_cogelados, key=lambda k: k['order_category'])
                                
                                for sorted_produc in categoria_cogelados:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])
                            elif main_categ == 'Refrigerados':
                                
                                if categoria_refrigerados:
                                    categoria_refrigerados = self.filterCategory(categoria_refrigerados,line_data)
    
                                else:
                                    categoria_refrigerados.append(line_data)
                                    
                                categoria_refrigerados = sorted(
                                    categoria_refrigerados, key=lambda k: k['order_category'])
                                for sorted_produc in categoria_refrigerados:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])

                            elif main_categ == 'Secos':
                                if categoria_secos:
                                    categoria_secos = self.filterCategory(categoria_secos,line_data)
                                        
                                else:
                                    categoria_secos.append(line_data)
                                    
                                categoria_secos = sorted(
                                    categoria_secos, key=lambda k: k['order_category'])
                                
                                for sorted_produc in categoria_secos:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])

                            else:
                                _logger.debug('no tiene categoria este producto %s' % (
                                    order_line.product_id.name))
                            del line_data
                        except Exception as e:
                            raise ValidationError('Verifique que todos los productos tengas categoria Padre!!')

                    date_order = datetime.strptime(line.date_order, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    all_date = {
                        'date_order': date_order,
                        'congelados': categoria_cogelados,
                        'refrigerados':categoria_refrigerados,
                        'secos':categoria_secos,
                    }
        del categoria_cogelados 
        del categoria_refrigerados 
        del categoria_secos 
        
        return all_date
                
    def filterCategory(self, categ, categ_new):

        exist  = categ_new['categ'] in [line['categ'] for line in categ]

        if exist == False:
            categ.append(categ_new)
        else:
            data_position = next((index for (index, d) in enumerate(categ) if d["categ"] == categ_new['categ']), None)
            data_position_product = next((index for (index, d) in enumerate(categ[data_position]['data']) if d["product_name"] == categ_new['data'][0]['product_name']), None)
            if data_position_product != None:
                categ[data_position]['total_products'] += categ_new['total_products']
                categ[data_position]['data'][data_position_product]['quantity_product'] += categ_new['data'][0]['quantity_product']
            else:
                categ[data_position]['total_products'] += categ_new['total_products']
                categ[data_position]['data'].append(categ_new['data'][0])

        return categ


    @api.model
    def _get_report_values(self, docids, data=None):
        try:
            locale.setlocale(locale.LC_TIME, 'es_AR.UTF-8')
        except Exception as e:
            raise ValidationError(e)
            
        total_parent = False
        total_users = []

        find_stock_pickig = self.env['stock.picking'].search([
            ('id', 'in', docids)
        ])
        if len(find_stock_pickig) > 1:
            total_parent = self._all_products_for_clients(find_stock_pickig)

        for rec in find_stock_pickig:
            if rec.sale_id:
                for line in rec.sale_id:
                    congelados = []
                    refrigerados = []
                    secos = []
                    code = None
                    main_categ = None
                    date_order = datetime.strptime(
                        line.date_order, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    for order_line in line.order_line:
                        if order_line.product_id.categ_id:
                            if order_line.product_id.categ_id.parent_id:
                                main_categ = order_line.product_id.categ_id.parent_id.name if order_line.product_id.categ_id.parent_id else None
                                categ = order_line.product_id.categ_id.name
                                order_category = order_line.product_id.categ_id.order_report
                                product_name = order_line.product_id.description_pickingout
                                quantity_product = order_line.product_uom_qty
                                qr = str(line.name) + str(main_categ[0])
                                if rec.order and rec.rute:
                                    code = f'{rec.rute}{rec.order}'
                                elif rec.order and not rec.rute:
                                    code = f'{rec.order}'
                                elif rec.rute and not rec.order:
                                    code = f'{rec.rute}'
                                line_data = {
                                    'categ': categ,
                                    'main_categ': main_categ,
                                    'url': f'https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={qr}',
                                    'order_category': order_category,
                                    'total_products': int(quantity_product),
                                    'data': [{
                                        'order_product':order_line.product_id.order_report,
                                        'product_name': product_name,
                                        'quantity_product': int(quantity_product),
                                    }]
                                }
                            else:
                                raise ValidationError(f'El producto  {order_line.product_id.description_pickingout}, no tiene categoria padre, referencia {rec.name}!! ') 
                            if main_categ == 'Congelados':
                                if congelados:
                                    congelados = self.filterCategory(congelados,line_data)
                                else:
                                    congelados.append(line_data)                                
                                congelados = sorted(congelados, key=lambda k: k['order_category'])
                                for sorted_produc in congelados:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])
                            elif main_categ == 'Refrigerados':
                                if refrigerados:
                                    refrigerados = self.filterCategory(refrigerados,line_data)
                                else:
                                    refrigerados.append(line_data)
                        
                                refrigerados = sorted(
                                    refrigerados, key=lambda k: k['order_category'])
                                for sorted_produc in refrigerados:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])
                                
                            elif main_categ == 'Secos':
                                if secos:
                                    secos = self.filterCategory(secos,line_data)
                                else:
                                    secos.append(line_data)
                                    
                                secos = sorted(
                                    secos, key=lambda k: k['order_category'])            
                                for sorted_produc in secos:
                                    sorted_produc['data'] = sorted(sorted_produc['data'], key=lambda k: k['order_product'])
                            line_data = None

                    street = line.partner_id.street if line.partner_id.street is not False else ''
                    city = line.partner_id.city if line.partner_id.city is not False else ''
                    date_order = datetime.strptime(
                        line.date_order, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    date = {
                        'date_order': date_order,
                        'cliente': line.partner_id.name,
                        'dir': '%s %s' % (street, city),
                        'subtotal': line.amount_untaxed,
                        'total': line.amount_total,
                        'deuda': line.get_deuda_total(line.partner_id),
                        'congelados': congelados,
                        'code': code,
                        'refrigerados': refrigerados,
                        'secos': secos,
                        'qr_prueba': f'https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={qr}'
                    }

                    total_users.append(date)
 

        list_so = {
            'total_users': total_users,
            'total_parent': total_parent,
        }

        docargs = {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': list_so,
        }
        del list_so
        del congelados
        del refrigerados
        del secos 
        del total_parent

        return docargs