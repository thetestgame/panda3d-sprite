"""
MIT License

Copyright (c) 2019 Nxt Games, LLC
Written by Jordan Maxwell 
08/04/2019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


from panda3d import core

from direct.directnotify.DirectNotifyGlobal import directNotify

import math

sprite_notify = directNotify.newCategory('sprite')

class SpriteCell(object):
    """
    Represents a cell in a sprite sheet
    """

    def __init__(self, col, row):
        self._col = col
        self._row = row

    @property
    def col(self):
        return self._col

    @property
    def row(self):
        return self._row

class SpriteAnimation(object):
    """
    Represents a sprite animation
    """

    def __init__(self, cells, fps):
        self._cells = cells
        self._fps = fps
        self.playhead = 0

    @property
    def cells(self):
        return self._cells

    @property
    def fps(self):
        return self._fps

class Sprite2D(object):
    """
    Represents a 2d sprite node in the scene graph. Handles cells
    and animation playback
    """

    ALIGN_CENTER = "Center"
    ALIGN_LEFT = "Left"
    ALIGN_RIGHT = "Right"
    ALIGN_BOTTOM = "Bottom"
    ALIGN_TOP = "Top"
    
    TRANS_ALPHA = core.TransparencyAttrib.MAlpha
    TRANS_DUAL = core.TransparencyAttrib.MDual

    # One pixel is divided by this much. If you load a 100x50 image with PIXEL_SCALE of 10.0
    # you get a card that is 1 unit wide, 0.5 units high
    PIXEL_SCALE = 5.0

    def __init__(self, file_path, name=None, layers={}, \
                  rows=1, cols=1, scale=1.0, two_sided=True, alpha=TRANS_ALPHA, \
                  repeat_x=1, repeat_y=1, anchor_x=ALIGN_LEFT, anchor_y=ALIGN_BOTTOM):

        scale *= self.PIXEL_SCALE

        self._animations = {}
        self._scale = scale
        self._repeat_x = repeat_x
        self._repeat_y = repeat_y
        self._flip = {'x': False, 'y': False}
        self._rows = rows
        self._cols = cols
    
        self._current_frame = 0
        self._current_anim = None
        self._loop_anim = False
        self._frame_interrupt = True
        self._play_task = None

        # Resolve file path
        base_img_file = self.__resolve_vfs_relative_path(
            file_path=file_path, 
            file_type='spritesheet')

        # Create the root node
        extension = name if name else base_img_file.get_basename_wo_extension()
        node_name = '%s:%s' % (self.__class__.__name__, extension)
        self._node = core.NodePath(node_name)
        if alpha:
            self._node.node().set_attrib(core.TransparencyAttrib.make(alpha))
        self._node.set_two_sided(two_sided)

        # Load the base sprite sheet
        self._img_file = None
        self._size_x = 0
        self._size_y = 0
        self._frames = []
        self._real_size_x = 0
        self._real_size_y = 0
        self._padded_img = None
        self._final_img = None

        self.__load_base_sheet(base_img_file)
        self.__construct_sprite_card(anchor_x, anchor_y)

        # Define layers
        self._layers = {}
        for layer_name in layers:
            layer_path = layers[layer_name]
            self.add_layer(layer_name, layer_path)

        # Build final image
        self.__update_final_image()
        self.__construct_sprite_texture()

    @property
    def animations(self):
        return self._animations

    @property
    def scale(self):
        return self._scale

    @property
    def repeat_x(self):
        return self._repeat_x

    @property
    def repeat_y(self):
        return self._repeat_y

    @property
    def flip(self):
        return self._flip

    @property
    def rows(self):
        return self._rows

    @property
    def cols(self):
        return self._cols

    @property
    def current_frame(self):
        return self._current_frame

    @property
    def current_anim(self):
        return self._current_anim

    @property
    def loop_anim(self):
        return self._loop_anim

    @property
    def frame_interrupt(self):
        return self._frame_interrupt

    @property
    def node(self):
        return self._node

    @property
    def img_file(self):
        return self._img_file

    @property
    def size_x(self):
        return self._size_x

    @property
    def size_y(self):
        return self._size_y

    @property
    def frames(self):
        return self._frames

    @property
    def real_size_x(self):
        return self._real_size_x

    @property
    def real_size_y(self):
        return self._real_size_y

    @property
    def padded_img(self):
        return self._padded_img

    @property
    def col_size(self):
        return self._col_size

    @property
    def row_size(self):
        return self._row_size

    @property
    def padding_x(self):
        return self._padding_x

    @property
    def padding_y(self):
        return self._padding_y

    @property
    def u_pad(self):
        return self._u_pad

    @property
    def v_pad(self):
        return self._v_pad

    @property
    def u_size(self):
        return self._u_size

    @property
    def v_size(self):
        return self._v_size

    @property
    def pos_left(self):
        return self._pos_left

    @property
    def pos_right(self):
        return self._pos_right

    @property
    def pos_top(self):
        return self._pos_top

    @property
    def pos_bottom(self):
        return self._pos_bottom

    @property
    def card(self):
        return self._card

    @property
    def offset_x(self):
        return self._offset_x

    @property
    def offset_y(self):
        return self._offset_y

    @property
    def texture(self):
        return self._texture

    @property
    def layer(self):
        return self._layers

    def __resolve_vfs_relative_path(self, file_path, okMissing=False, file_type=''):
        """
        Resolves a file path to a VFS relative Filename object
        for use in resource loading
        """

        if not isinstance(file_path, core.Filename):
            file_name = core.Filename(file_path)
        else:
            file_name = file_path

        vfs = core.VirtualFileSystem.get_global_ptr()
        search_path = core.get_model_path().get_value()

        # Verify the file exists
        found = vfs.resolve_filename(file_name, search_path)
        if not found:
            # Notify the user
            message = 'Failed to load %s file: %s' % (file_type, file_name.c_str())
            sprite_notify.warning('Search Path: %s' % str(search_path.get_directories()))

            if not okMissing:
                sprite_notify.error(message)
            else:
                sprite_notify.warning(message)

            return None

        return file_name

    def swap_base_spritesheet(self, sheet_path):
        """
        Swaps the base sprite sheet
        """
        
        file_name = self.__resolve_vfs_relative_path(
            file_path=sheet_path,
            file_type='spritesheet')
        
        self.__load_base_sheet(file_name)
        self.__update_final_image()
        self.__construct_sprite_texture()

    def add_layer(self, layer_name, sheet_path):
        """
        Adds a sprite sheet layer to the sprite object
        """

        file_name = self.__resolve_vfs_relative_path(
            file_path=sheet_path,
            file_type='spritesheet')

        self.__load_layer_sheet(layer_name, file_name)
        self.__update_final_image()
        self.__construct_sprite_texture()

    def remove_layer(self, layer_name):
        """
        Removes the sprite sheet layer from the sprite object
        """

        if layer_name not in self._layers:
            sprite_notify.warning('Failed to remove layer; %s does not exist' % layer_name)
            return

        del self._layers[layer_name]
        self.__update_final_image()
        self.__construct_sprite_texture()

    def __load_layer_sheet(self, layer_name, img_file):
        """
        Loads a layer sheet image file and assigns it to the 
        layers dictionary using its layer name
        """

        assert not img_file.empty()

        # Load the spritesheet
        img_header = core.PNMImageHeader()
        assert img_header.read_header(img_file)

        if sprite_notify.getDebug():
            sprite_notify.debug('Loading spritesheet layer: %s' % img_file)
        
        image = core.PNMImage()
        image.read(img_file)
        assert image.is_valid()

        size_x = image.get_x_size()
        size_y = image.get_y_size()

        assert size_x != 0
        assert size_y != 0

        assert self._size_x == size_x
        assert self._size_y == size_y

        self._layers[layer_name] = image

    def __load_base_sheet(self, img_file):
        """
        Loads the base sprite sheet from the VFS and performs
        the required math for display
        """

        # Load the spritesheet
        img_header = core.PNMImageHeader()
        assert img_header.read_header(img_file)

        if sprite_notify.getDebug():
            sprite_notify.debug('Loading spritesheet base: %s' % img_file)
        
        image = core.PNMImage()
        image.read(img_file)
        assert image.is_valid()

        size_x = image.get_x_size()
        size_y = image.get_y_size()

        assert size_x != 0
        assert size_y != 0

        if self._size_x != 0:
            assert self._size_x == size_x
        
        if self._size_y != 0:
            assert self._size_y == size_y

        self._size_x = size_x
        self._size_y = size_y

        self._img_file = img_file
        assert not self._img_file.empty()

        self._frames = []
        for row_idx in range(self._rows):
            for col_idx in range(self._cols):
                self._frames.append(SpriteCell(col_idx, row_idx))

        # We need to find the power of two size for the another PNMImage
        # so that the texture thats loaded on the geometry won't have artifacts
        texture_size_x = self._next_size(self._size_x)
        texture_size_y = self._next_size(self._size_y)

        # The actual size of the texture in memory
        self._real_size_x = texture_size_x
        self._real_size_y = texture_size_y

        self._padded_img = core.PNMImage(texture_size_x, texture_size_y)
        if image.has_alpha:
            self._padded_img.alpha_fill(0)
        self._padded_img.blend_sub_image(image, 0, 0)
        image.clear()

        # The pixel sizes for each cell
        self._col_size = self._size_x/self._cols
        self._row_size = self._size_y/self._rows

        # How much padding the texture has
        self._padding_x = texture_size_x - self._size_x
        self._padding_y = texture_size_y - self._size_y

        # Set UV padding
        self._u_pad = float(self._padding_x/texture_size_x)
        self._v_pad = float(self._padding_y/texture_size_y)

        # The UV dimensions for each cell
        self._u_size = (1.0 - self._u_pad) / self._cols
        self._v_size = (1.0 - self._v_pad) / self._rows

    def __update_final_image(self):
        """
        Constructs the final PNM image based on the base and all layers provided
        """

        # Set base image object
        self._final_img = self._padded_img

        # Blend layers
        for layer_name in self._layers:
            layer_image = self._layers[layer_name]
            self._final_img.blend_sub_image(layer_image, 0, 0)

    def __construct_sprite_card(self, anchor_x, anchor_y):
        """
        Constructs the sprite frame out of a card maker using the requested
        anchor points and size
        """

        # Create the geometry card
        card = core.CardMaker('%s-geom' % self.__class__.__name__)

        # Handle positioning based on anchors
        if anchor_x == self.ALIGN_LEFT:
            self._pos_left = 0
            self._pos_right = (self._col_size/self._scale) * self._repeat_x
        elif anchor_x == self.ALIGN_CENTER:
            self._pos_left = -(self._col_size/2.0/self._scale) * self._repeat_x
            self._pos_right = (self._col_size/2.0/self._scale) * self._repeat_x
        elif anchor_x == self.ALIGN_RIGHT:
            self._pos_left = -(self._col_size/self._scale) * self._repeat_x
            self._pos_right = 0

        if anchor_y == self.ALIGN_BOTTOM:
            self._pos_top = 0
            self._pos_bottom = (self._row_size/self._scale) * self._repeat_y
        elif anchor_y == self.ALIGN_CENTER:
            self._pos_top = -(self._row_size/2.0/self._scale) * self._repeat_y
            self._pos_bottom = (self._row_size/2.0/self._scale) * self._repeat_y
        elif anchor_y == self.ALIGN_TOP:
            self._pos_top = -(self._row_size/self._scale) * self._repeat_y
            self._pos_bottom = 0

        card.set_frame(self._pos_left, self._pos_right, self._pos_top, self._pos_bottom)
        card.set_has_uvs(True)
    
        assert self._node != None
        self._card = self._node.attach_new_node(card.generate())

    def __construct_sprite_texture(self):
        """
        Constructs the texture out of the final image PNM object
        for applying to the sprite frame
        """

        # Since the texture is padded, we need to set up offsets and scales to make
        # the texture fit the whole card
        self._offset_x = (float(self._col_size)/self._real_size_x)
        self._offset_y = (float(self._row_size)/self._real_size_y)

        self._node.set_tex_scale(
            core.TextureStage.get_default(), 
            self._offset_x * self._repeat_x, 
            self._offset_y * self._repeat_y)
        self._node.set_tex_offset(
            core.TextureStage.get_default(), 0, 1 - self._offset_y)

        # Create the sprite texture
        self._texture = core.Texture()
        self._texture.set_x_size(self._real_size_x)
        self._texture.set_y_size(self._real_size_y)
        self._texture.set_z_size(1)
        
        # Load the final layered and padded PNMImage into the texture
        self._texture.load(self._final_img)
        self._texture.set_magfilter(core.Texture.FTNearest)
        self._texture.set_minfilter(core.Texture.FTNearest)

        #Set up texture clamps according to repeats
        if self._repeat_x > 1:
            self._texture.set_wrap_u(core.Texture.WMRepeat)
        else:
            self._texture.set_wrap_u(core.Texture.WMClamp)
        
        if self._repeat_y > 1:
            self._texture.set_wrap_v(core.Texture.WMRepeat)
        else:
            self._texture.set_wrap_v(core.Texture.WMClamp)
        
        assert self._node != None
        self._node.set_texture(self._texture)

    def _next_size(self, num):
        """ 
        Finds the next power of two size for the given integer. 
        """

        p2x = max(1, math.log(num, 2))
        not_p2X = math.modf(p2x)[0] > 0

        return 2 ** int(not_p2X + p2x)

    def set_frame(self, frame=0):
        """ 
        Sets the current sprite to the given frame 
        """

        self._frame_nterrupt = True # A flag to tell the animation task to shut it up ur face
        self._current_frame = frame
        self.flip_texture()

    def play_animation(self, anim_name, loop=False):
        """ 
        Sets the sprite to animate the given named animation. 
        Booleon to loop animation
        """

        sprite_notify.debugStateCall(self)

        if not anim_name in self._animations:
            sprite_notify.warning('Failed to play animation: %s; Not loaded' % anim_name)
            return

        if self._play_task:
            taskMgr.remove(self._play_task)

        self._frame_interrupt = False # Clear any previous interrupt flags
        self._loop_anim = loop

        self._current_anim = self._animations.get(anim_name)
        self._current_anim.playhead = 0
        self._play_task = taskMgr.do_method_later(
            1.0/self._current_anim.fps,
            self.__animation_task, 
            "%s-sprite-animation" % self.__class__.__name__)

    def create_animation(self, anim_name, frames, fps=12):
        """ 
        Create a named animation. 
        Takes the animation name and a tuple of frame numbers 
        """

        animation = SpriteAnimation(frames, fps)
        self._animations[anim_name] = animation

        return animation

    def flip_x(self, val=None):
        """ 
        Flip the sprite on X. If no value given, it will invert the current flipping.
        """

        if val:
            self._flip['x'] = val
        else:
            if self._flip['x']:
                self._flip['x'] = False
            else:
                self._flip['x'] = True
        self.flip_texture()

        return self._flip['x']

    def flip_y(self, val=None):
        """ 
        See flip_x
        """

        if val:
            self._flip['y'] = val
        else:
            if self._flip['y']:
                self._flip['y'] = False
            else:
                self._flip['y'] = True
        self.flip_texture()

        return self._flip['y']

    def flip_texture(self):
        """ 
        Sets the texture coordinates of the texture to the current frame
        """

        s_u = self._offset_x * self._repeat_x
        s_v = self._offset_y * self._repeat_y
        o_u = 0 + self._frames[self._current_frame].col * self._u_size
        o_v = 1 - self._frames[self._current_frame].row * self._v_size - self._offset_y
        if self._flip['x']:
            s_u *= -1
            o_u = self._u_size + self._frames[self._current_frame].col * self._u_size
        if self._flip['y']:
            s_v *= -1
            o_v = 1 - self._frames[self._current_frame].row * self._v_size

        self._node.set_tex_scale(core.TextureStage.get_default(), s_u, s_v)
        self._node.set_tex_offset(core.TextureStage.get_default(), o_u, o_v)
    
    def clear(self):
        """ 
        Free up the texture memory being used 
        """

        self._texture.clear()
        self._padded_img.clear()
        self._node.remove_node()
    
    async def __animation_task(self, task):
        """
        Task used for sprite animation playback
        """

        if self._frame_interrupt:
            return task.done

        self._current_frame = self._current_anim.cells[self._current_anim.playhead]
        self.flip_texture()

        if self._current_anim.playhead + 1 < len(self._current_anim.cells):
            self._current_anim.playhead += 1
            return task.again

        if self._loop_anim:
            self._current_anim.playhead = 0
            return task.again

        return task.done