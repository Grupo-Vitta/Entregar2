from odoo import api, fields, models
from odoo.exceptions import UserError
import requests

class EntregarShippingCarrier(models.Model):
    _inherit = 'delivery.carrier'

    api_token = fields.Char(string="Token de API")
    api_expiration = fields.Datetime(string="Expiración del Token")
    history_ids = fields.One2many(
        'entregar.shipping.history', 'shipping_id', string="Historial de Envío"
    )

    def authenticate_api(self):
        """ Autentica y obtiene un token de la API. """
        url = "https://homologacion.entregarweb.com/api/v1/auth/token"
        payload = {
            'client_api': 'a84e0675aba4322fbebd4ccf164f238deb9ea501b6ac15f16ae4c6aacf590426',
            'client_secret': 'cb4979d3152ee649fb7f94b3ba4ac2625baa803d1ae43e0b7642b6b105b78758'
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            result = response.json().get("result", [])
            self.api_token = result[0].get("api_token")
            self.api_expiration = fields.Datetime.now() + fields.Date.timedelta(hours=1)
        else:
            raise UserError("Error al autenticar con la API de Entregar")

    def fetch_shipping_history(self, code):
        """Consulta el historial de un envío y lo guarda en el modelo."""
        if not self.api_token:
            self.authenticate_api()

        url = f"https://homologacion.entregarweb.com/api/v1/shipping/historial/{code}"
        headers = {'Authorization': f'Bearer {self.api_token}'}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get('result', [])
            for entry in data:
                self.env['entregar.shipping.history'].create({
                    'shipping_id': self.id,
                    'date': entry['date']['date'],
                    'status': entry.get('state', '-'),
                    'location': entry.get('location', ''),
                    'price': entry.get('price', 0.0),
                })
        else:
            raise UserError("Error al obtener el historial del envío")

class EntregarShippingHistory(models.Model):
    _name = 'entregar.shipping.history'
    _description = 'Historial de Envíos - Entregar API'

    shipping_id = fields.Many2one(
        'delivery.carrier', string="Envío", ondelete="cascade"
    )
    date = fields.Datetime(string="Fecha")
    status = fields.Char(string="Estado")
    location = fields.Char(string="Ubicación")
    price = fields.Float(string="Precio")
