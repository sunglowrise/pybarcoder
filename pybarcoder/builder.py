#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created By Murray(m18527) on 2020/6/12 14:40
----------------------
"""
import base64
import os
import uuid

import barcode
from barcode.writer import ImageWriter, ImageFont, Image, ImageDraw

PATH = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(PATH, 'msyh.ttf.py')

VERSION = "0.9.1"


def px2mm(px, dpi=300):
    return (px * 25.4) / dpi


def mm2px(mm, dpi=300):
    return (mm * dpi) / 25.4


def pt2mm(pt):
    return pt * 0.352777778


class ImageWriterExt(ImageWriter):

    def __init__(self, ft_text=None, fb_text=None, rt_text=None, rb_text=None, fixed_width=0):
        super(ImageWriterExt, self).__init__()
        self.ft_text = ft_text or ''
        self.fb_text = fb_text or ''
        self.rt_text = rt_text or ''
        self.rb_text = rb_text or ''
        self.fixed_width = fixed_width
        self._zoom = 1

    def _init(self, code):
        size = self.calculate_size(len(code[0]), len(code), self.dpi)
        self._image = Image.new('RGB', size, self.background)
        self._draw = ImageDraw.Draw(self._image)
        self.text_length = len(code[0])

    def _paint_module(self, xpos, ypos, width, color):
        height = px2mm(self.font_size, self.dpi)
        ypos += self.text_distance / 2 + height
        size = [
            (mm2px(xpos, self.dpi), mm2px(ypos, self.dpi)),
            (mm2px(xpos + width, self.dpi), mm2px(ypos + self.module_height, self.dpi))
        ]
        self._draw.rectangle(size, outline=color, fill=color)

    def _paint_text(self, xpos, ypos):
        if self.fixed_width > self.module_width:
            _width = int(mm2px(2 * self.quiet_zone + self.fixed_width))
            self._zoom = _width / self._image.width
            self._image = self._image.resize((_width, self._image.height), Image.BILINEAR)
            self._draw = ImageDraw.Draw(self._image)
        font = ImageFont.truetype(FONT, self.font_size * 2)
        width, height = font.getsize(self.text)
        ypos = self.text_distance + self.module_height + px2mm(self.font_size, self.dpi) + self.text_line_distance / 2
        pos = (mm2px(xpos, self.dpi) - width // 2, mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.text, font=font, fill=self.foreground)
        self._paint_text_left_top()
        self._paint_text_left_bottom(ypos)
        self._paint_text_right_top()
        self._paint_text_right_bottom(ypos)

    def _paint_text_left_top(self):
        font = ImageFont.truetype(FONT, self.font_size * 2)
        width, height = font.getsize(self.ft_text)
        xpos = self.quiet_zone * self._zoom + px2mm(width, self.dpi)
        ypos = (self.text_distance - px2mm(height, self.dpi) + 1) / 2
        pos = (mm2px(xpos, self.dpi) - width,
               mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.ft_text, font=font, fill=self.foreground)

    def _paint_text_left_bottom(self, ypos):
        font = ImageFont.truetype(FONT, self.font_size * 2)
        width, height = font.getsize(self.fb_text)
        xpos = self.quiet_zone * self._zoom + px2mm(width, self.dpi)
        pos = (mm2px(xpos, self.dpi) - width,
               mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.fb_text, font=font, fill=self.foreground)

    def _paint_text_right_top(self):
        font = ImageFont.truetype(FONT, self.font_size * 2)
        width, height = font.getsize(self.rt_text)
        # xpos = self.module_width * self.text_length - px2mm(width, self.dpi) / 2 + self.quiet_zone
        xpos = px2mm(self._image.width - width / 2, self.dpi) - self.quiet_zone * self._zoom
        ypos = (self.text_distance - px2mm(height, self.dpi) + 1) / 2
        pos = (mm2px(xpos, self.dpi) - width // 2,
               mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.rt_text, font=font, fill=self.foreground)

    def _paint_text_right_bottom(self, ypos):
        font = ImageFont.truetype(FONT, self.font_size * 2)
        width, height = font.getsize(self.rb_text)
        # xpos = self.module_width * self.text_length - px2mm(width, self.dpi) / 2 + self.quiet_zone
        xpos = px2mm(self._image.width - width / 2, self.dpi) - self.quiet_zone * self._zoom
        pos = (mm2px(xpos, self.dpi) - width // 2,
               mm2px(ypos, self.dpi) - height // 4)
        self._draw.text(pos, self.rb_text, font=font, fill=self.foreground)


class BarCoder(object):
    def __init__(self, name="Code128"):
        self.bar_builder = None
        self.name = name
        self.path = None
        self.fixed_width = 0
        self.coder = barcode.get_barcode_class(self.name)
        self.options = self._default_options

    def set_msg(self, msg, ft_text='', fb_text='', rt_text='', rb_text='', add_checksum=False):
        if self.name.lower() == "code39":
            self.bar_builder = self.coder(msg, add_checksum=add_checksum, writer=ImageWriterExt(
                ft_text=ft_text, fb_text=fb_text, rt_text=rt_text, rb_text=rb_text
            ))
        else:
            self.bar_builder = self.coder(msg, writer=ImageWriterExt(
                ft_text=ft_text, fb_text=fb_text, rt_text=rt_text, rb_text=rb_text,
                fixed_width=self.fixed_width
            ))
        return self

    @property
    def _default_options(self):
        self.fixed_width = 0  # 条码总宽度，单位为毫米
        return {
            'module_width': 0.2,  # 默认值0.2，每个条码宽度，单位为毫米
            'fixed_width': self.fixed_width,  # 条码总宽度，单位为毫米
            'module_height': 8.0,  # 默认值15.0，条码高度，单位为毫米
            'quiet_zone': 1,  # 默认值6.5，两端空白宽度，单位为毫米
            'font_size': 10,  # 默认值10，文本字体大小，单位为磅
            'text_distance': 3,  # 默认值5.0，文本和条码之间的距离，单位为毫米
            'background': 'white',  # 默认值'white'，背景色
            'foreground': 'black',  # 默认值'black'，前景色
            'text': ' ',  # 默认值''，显示文本，默认显示编码，也可以自行设定
            'write_text': False,  # 默认值True，是否显示文本，如果为True自动生成text的值，如果为False则不生成,显示text文本
            'center_text': True,  # 默认值True，是否居中显示文本
            'format': 'PNG',  # 默认值'PNG'，保存文件格式，默认为PNG，也可以设为JPEG、BMP等，只在使用ImageWriter时有效。
            'dpi': 300,  # 默认值300，图片分辨率，只在使用ImageWriter时有效。
        }

    def set_options(self, options):
        if isinstance(options, dict):
            only = ["module_width", "fixed_width", "module_height", "quiet_zone", "font_size", "format", "dpi"]
            self.options.update({k: v for k, v in options.items() if k in only})
            self.fixed_width = self.options.get("fixed_width")
        return self

    def save(self, path="pic"):
        self.path = self.bar_builder.save(path, options=self.options)
        return self.path

    def base64(self, is_str=True):
        tmp_path = "/tmp/{}".format(uuid.uuid4().hex)
        tmp_path = self.save(path=tmp_path)
        with open(tmp_path, "rb") as f:
            base64_data = base64.b64encode(f.read())
            if is_str:
                base64_data = base64_data.decode(encoding="utf8")
            try:
                os.remove(tmp_path)
            except (Exception,):
                pass
        return base64_data


if __name__ == '__main__':
    BarCoder().set_options({
        # 'module_width': 0.2,  # 默认值0.2，每个条码宽度，单位为毫米
        # 'fixed_width': 50,  # 条码总宽度，单位为毫米
        # 'module_height': 8.0,  # 默认值15.0，条码高度，单位为毫米
        # 'quiet_zone': 3,  # 默认值6.5，两端空白宽度，单位为毫米
        # 'font_size': 12,  # 默认值10，文本字体大小，单位为磅
        # 'format': 'PNG',  # 默认值'PNG'，保存文件格式，默认为PNG，也可以设为JPEG、BMP等，只在使用ImageWriter时有效。
        # 'dpi': 300,  # 默认值300，图片分辨率，，只在使用ImageWriter时有效。
    }).set_msg("S123456789123456", "左上角信息", "左下角信息", "右上角信息", "右下角信息").save()
    print("生成成功")
