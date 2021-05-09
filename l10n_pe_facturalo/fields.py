from odoo.fields import Binary

import base64
from odoo.tools import pycompat
from odoo.tools.mimetypes import guess_mimetype
import psycopg2
from odoo.exceptions import UserError
from odoo import _


class BinaryExtend:
    def convert_to_column(self, value, record, values=None, validate=True):
            # Binary values may be byte strings (python 2.6 byte array), but
            # the legacy OpenERP convention is to transfer and store binaries
            # as base64-encoded strings. The base64 string may be provided as a
            # unicode in some circumstances, hence the str() cast here.
            # This str() coercion will only work for pure ASCII unicode strings,
            # on purpose - non base64 data must be passed as a 8bit byte strings.
            if not value:
                return None
            # Detect if the binary content is an SVG for restricting its upload
            # only to system users.
            if value[:1] == b'P':  # Fast detection of first 6 bits of '<' (0x3C)
                decoded_value = guess_mimetype(base64.b64decode(value))
                # Full mimetype detection
                if (decoded_value.startswith('image/svg') and not record.env.user._is_system() and
                        decoded_value != 'image/svg+xml'):
                    raise UserError(_("Only admins can upload SVG files."))
            if isinstance(value, bytes):
                return psycopg2.Binary(value)
            try:
                return psycopg2.Binary(pycompat.text_type(value).encode('ascii'))
            except UnicodeEncodeError:
                raise UserError(_("ASCII characters are required for %s in %s") % (value, self.name))


Binary.convert_to_column = BinaryExtend.convert_to_column
