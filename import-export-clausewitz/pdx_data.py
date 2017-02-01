import io
import struct
from . import (utils)

class PdxFile():
    """Class representing a Paradox Clausewitz Engine .mesh File."""
    def __init__(self, filename):
        self.filename = filename
        self.__file_reference__ = None
        self.rawData = []
        self.nodes = []

    def read(self):
        """Read and Parse the specified File."""
        self.__file_reference__ = io.open(self.filename, "rb")
        self.rawData = self.__file_reference__.read()

        self.__parse__()

    def __parse__(self):
        data = self.rawData.lstrip(b"@@b@")

        buffer = utils.BufferReader(data)

        while not buffer.IsEOF():
            char = buffer.NextChar()

            if char == "!":
                self.nodes.append(self.read_property(buffer))
            elif char == "[":
                self.nodes.append(self.read_object(buffer, 0, None))

        print("Parsed")

        self.__file_reference__.close()

    def read_property(self, buffer: utils.BufferReader):
        """Read a .mesh Property using the provided Buffer"""
        name = ""
        property_data = []

        lower_bound = buffer.GetCurrentOffset()

        name_length = buffer.NextInt8()

        for i in range(0, name_length):
            name += buffer.NextChar()

        name = utils.TranslatePropertyName(name)

        char = buffer.NextChar()

        if char == "i":
            data_count = buffer.NextUInt32()

            for i in range(0, data_count):
                property_data.append(buffer.NextInt32())
        elif char == "f":
            data_count = buffer.NextUInt32()

            for i in range(0, data_count):
                property_data.append(buffer.NextFloat32())
        elif char == "s":
            value = ""
            stringType = buffer.NextUInt32()
            dataCount = buffer.NextUInt32()

            value = utils.ReadNullByteString(buffer)

            property_data = value

        upper_bound = buffer.GetCurrentOffset()

        if name == "pdxasset":
            result = PdxAsset()
            result.bounds = (lower_bound, upper_bound)
        else:
            result = PdxProperty(name, (lower_bound, upper_bound))
            result.value = property_data

        return result

    def read_object(self, buffer: utils.BufferReader, depth, prev_obj):
        """Reads object Data"""
        char = buffer.NextChar()
        object_properties = []
        sub_objects = []

        if char == "[":
            return self.read_object(buffer, depth + 1, prev_obj)
        else:
            object_name = char + utils.ReadNullByteString(buffer)

            print("Object: " + object_name)

            if prev_obj is not None:
                try:
                    print("Name: " + prev_obj.name)
                except:
                    print("Type: ", type(prev_obj))

            if object_name == "object":
                result = PdxWorld(sub_objects)
            elif object_name == "mesh":
                result = PdxMesh()
            elif object_name == "locator":
                result = PdxLocators()
            else:
                result = PdxObject(object_name, [], depth)

            while not buffer.IsEOF():
                char = buffer.NextChar(True)

                if char == "!":
                    buffer.NextChar()
                    object_properties.append(self.read_property(buffer))
                elif char == "[":
                    print("Depth: ", depth, " : ", utils.PreviewObjectDepth(buffer))
                    if depth < utils.PreviewObjectDepth(buffer):
                        if isinstance(prev_obj, PdxLocators) or isinstance(prev_obj, PdxMesh):
                            sub_objects.append(self.read_object(buffer, 0, prev_obj))
                        else:
                            sub_objects.append(self.read_object(buffer, 0, result))
                    else:
                        break

            temp = ""
            for i in range(0, depth):
                temp += "-"
            print(temp + "Sub Objects: ", len(sub_objects))

            if object_name == "object":
                result = PdxWorld(sub_objects)
            elif object_name == "mesh":
                result = PdxMesh()
                result.verts = utils.TransposeCoordinateArray3D(object_properties[0].value)
                result.faces = utils.TransposeCoordinateArray3D(object_properties[4].value)
                result.normals = object_properties[1].value
                result.tangents = object_properties[2].value
                result.uv_coords = utils.TransposeCoordinateArray2D(object_properties[3].value)
                result.bounds = sub_objects[0]
                result.material = sub_objects[1]
            elif object_name == "locator":
                result = PdxLocators()
                result.locators = sub_objects
            elif object_name == "aabb":
                result = PdxBounds(object_properties[0].value, object_properties[1].value)
            elif object_name == "material":
                result = PdxMaterial()
                result.shaders = object_properties[0].value
                result.diffs = object_properties[1].value
                result.normals = object_properties[2].value
                result.specs = object_properties[3].value
            else:
                if isinstance(prev_obj, PdxLocators):
                    result = PdxLocator(object_name, object_properties[0].value)
                elif isinstance(prev_obj, PdxWorld) and object_name.endswith("MeshShape"):
                    result = PdxShape(object_name)
                    result.mesh = sub_objects[0]
                else:
                    result = PdxObject(object_name, object_properties, depth)

            return result

class PdxAsset():
    def __init__(self):
        self.bounds = (0,0)
        self.name = "pdxasset"
        self.value = 0

    def get_binary_data(self):
        result = bytearray()

        result.extend(struct.pack("cb" + str(len(self.name)) + "s", b'!', len(self.name), self.name.encode('UTF-8')))
        result.extend(struct.pack("cI", b'i', self.value))

        return result

class PdxMesh():
    def __init__(self):
        self.bounds = (0,0)
        self.verts = []
        self.faces = []
        self.tangents = []
        self.normals = []
        self.uv_coords = []
        self.material = None

    def get_binary_data(self):
        return bytearray()

class PdxMaterial():
    def __init__(self):
        self.shaders = ""
        self.diffs = ""
        self.normals = ""
        self.specs = ""

    def get_binary_data(self):
        return bytearray()

class PdxProperty():
    """Temporary class to hold the Values of a parsed Property until it gets mapped to the object"""
    def __init__(self, name, bounds):
        self.name = name
        self.bounds = bounds
        self.value = []

    def get_binary_data(self):
        return bytearray()

class PdxWorld():
    def __init__(self, objects):
        self.objects = objects

    def get_binary_data(self):
        result = bytearray()

        result.extend(struct.pack("7sb", b'[object', 0)) #.encode('UTF-8')

        for i in range(0, len(self.objects)):
            result.extend(self.objects[i].get_binary_data())
        print("World")
        return result

class PdxShape():
    def __init__(self, name):
        self.name = name
        self.mesh = None

    def get_binary_data(self):
        result = bytearray()

        result.extend(struct.pack("2s", b'[['))
        result.extend(struct.pack(str(len(self.name)) + "sb", self.name.encode('UTF-8'), 0))
        result.extend(self.mesh.get_binary_data())

        return result

class PdxBounds():
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def get_binary_data(self):
        return bytearray()

class PdxObject():
    """Temporary object"""
    def __init__(self, name, properties, depth):
        self.name = name
        self.properties = properties
        self.depth = depth

    def get_binary_data(self):
        return bytearray()

class PdxLocators():
    def __init__(self):
        self.bounds = (0,0)
        self.locators = []

    def get_binary_data(self):
        result = bytearray()

        result.extend(struct.pack("8sb", b'[locator', 0))

        for i in range(0, len(self.locators)):
            result.extend(self.locators[i].get_binary_data())

        return result

class PdxLocator():
    def __init__(self, name, pos):
        self.bounds = (0,0)
        self.name = name
        self.pos = pos

    def get_binary_data(self):
        result = bytearray()

        result.extend(struct.pack("2s", b'[['))
        result.extend(struct.pack(str(len(self.name)) + "sb", self.name.encode('UTF-8'), 0))
        result.extend(struct.pack("cbsifff", b'!', 0, b'pf', 3, self.pos[0], self.pos[1], self.pos[2]))
        result.extend(struct.pack("cbsifff", b'!', 0, b'qf', 3, 0.0, 0.0, 0.0))

        return result
    