import bpy
from bpy_types import (Operator)
from bpy_extras.io_utils import (ImportHelper, ExportHelper)
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from . import (importer, exporter)

bl_info = {
    "name": "Clausewitz Import/Export",
    "category": "Import-Export",
    "author": "Bernhard Sirlinger",
    "version": (0, 3, 3),
    "blender": (2, 78, 0),
    "support": "TESTING",
    "wiki_url": "https://github.com/WebsiteDeveloper/ClausewitzBlenderPlugin/wiki",
    "tracker_url": "https://github.com/WebsiteDeveloper/ClausewitzBlenderPlugin/issues"
}

class ClausewitzExporter(Operator, ExportHelper):
    """Clausewitz Exporter"""
    bl_idname = "clausewitz.exporter"
    bl_label = "Export .mesh (Clausewitz Engine)"

    check_existing = BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},
        )

    filename_ext = ".mesh"

    filter_glob = StringProperty(
        default="*.mesh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )

    def execute(self, context):
        pdx = exporter.PdxFileExporter(self.filepath)
        pdx.export_mesh(bpy.context.active_object.name)
        return {'FINISHED'}

class ClausewitzImporter(Operator, ImportHelper):
    """Clausewitz Importer"""
    bl_idname = "clausewitz.importer"
    bl_label = "Import .mesh (Clausewitz Engine)"

    filename_ext = ".mesh"

    filter_glob = StringProperty(
        default="*.mesh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )

    def execute(self, context):
        pdx = importer.PdxFileImporter(self.filepath)
        pdx.import_mesh()

        return {'FINISHED'}      

def menu_func_export(self, context):
    self.layout.operator(ClausewitzExporter.bl_idname, text="Export .mesh (Clausewitz Engine)")

def menu_func_import(self, context):
    self.layout.operator(ClausewitzImporter.bl_idname, text="Import .mesh (Clausewitz Engine)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
