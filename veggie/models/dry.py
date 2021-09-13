# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.tools.float_utils import float_round as round
from openerp.exceptions import ValidationError, Warning
from datetime import timedelta, date, datetime, time
from num2words import num2words


import locale
import logging

_logger = logging.getLogger(__name__)

class ReportStockPickingDry(models.AbstractModel):
    _name = "report.veggie.roadmap_report_dry"
    

    def _all_products_for_clients(self, date):
        categoria_secos = []
        main_categ = None
        all_date = {}
        if len(date) > 1:
            for rec in date:
                for line in rec.sale_id:
                    for order_line in line.order_line:
                        if order_line.product_id.categ_id.name == 'Todos':
                            continue
                        if order_line.product_id.categ_id.parent_id.name:

                            main_categ = order_line.product_id.categ_id.parent_id.name if order_line.product_id.categ_id.parent_id else None
                            categ = order_line.product_id.categ_id.name
                            order_category = order_line.product_id.categ_id.order_report
                            product_name = order_line.product_id.description_pickingout
                            quantity_product = order_line.product_uom_qty     
                            if len(product_name) > 13:
                                product_name = product_name[:13]
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
                            if main_categ == 'Secos':
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
                            
                    date_order = datetime.strptime(rec.scheduled_date, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    all_date = {
                        'date_order': date_order,
                        'secos':categoria_secos,
                    }
                    

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
        _logger.debug(find_stock_pickig)
        for rec in find_stock_pickig:
            if rec.sale_id:
                for line in rec.sale_id:
                    secos = []
                    main_categ = None
                    code = None
                    date_order = datetime.strptime(
                        rec.scheduled_date, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    for order_line in line.order_line:
                        if order_line.product_id.categ_id.name == 'Todos':
                            continue
                        if order_line.product_id.categ_id:
                            if order_line.product_id.categ_id.parent_id:
                                main_categ = order_line.product_id.categ_id.parent_id.name if order_line.product_id.categ_id.parent_id else None
                                categ = order_line.product_id.categ_id.name
                                order_category = order_line.product_id.categ_id.order_report
                                product_name = order_line.product_id.description_pickingout
                                quantity_product = order_line.product_uom_qty
                                qr = str(line.name) + "S"
                                if rec.order and rec.rute:
                                    code = f'{rec.rute}{rec.order}'
                                elif rec.order and not rec.rute:
                                    code = f'{rec.order}'
                                elif rec.rute and not rec.order:
                                    code = f'{rec.rute}'
                                if len(product_name) > 13:
                                    product_name = product_name[:13]
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
                            _logger.debug(main_categ)
                            if main_categ == 'Secos':
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
                        rec.scheduled_date, "%Y-%m-%d %H:%M:%S").strftime('%A %d')
                    ruta_name = rec.rute if rec.rute else ''
                    order_name = rec.order if rec.order != 0 else ''
                    
                    ruta = f'{ruta_name}{order_name}'
                    stock_name_count = len(rec.origin)
                    stock_name_count = stock_name_count - 3 
                    stock_name= rec.origin[:stock_name_count]
                    code_name = rec.origin[stock_name_count:] + 'S'
                    categoria = main_categ[:-1]
                    categoria = 'SECOS'
                    
                    date = {
                        'categoria':categoria,
                        'date_order': date_order,
                        'cliente': line.partner_id.name,
                        'stock_name':stock_name,
                        'stock_name_cort':code_name,
                        'nombre_fant': line.partner_id.ref,
                        'dir': '%s %s' % (street, city),
                        'subtotal': line.amount_untaxed,
                        'total': line.amount_total,
                        'deuda': line.get_deuda_total(line.partner_id),
                        'secos': secos,
                        'code': code,
                        'qr_prueba': f'https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={qr}',
                        'ruta':ruta,
                    }

                    total_users.append(date)
                rec.dry_roadmap = True
 
        _logger.debug('legga')
        _logger.debug(total_users)
        list_so = {
            'total_users': total_users,
            'total_parent': total_parent,
        }
        _logger.debug(list_so)

        docargs = {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': list_so,
        }
        _logger.debug(docargs)
        del list_so
        secos = []
        

        return docargs
