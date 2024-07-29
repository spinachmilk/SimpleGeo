# Author-
# Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

# app = adsk.core.Application.get()
# ui = app.userInterface

# product = app.activeProduct
# design = adsk.fusion.Design.cast(product)
# rootComp = design.rootComponent

textPalette = adsk.core.Application.get().userInterface.palettes.itemById(
    "TextCommands"
)
msg = ""


def DebugPrint(message):
    """Display a message in the Fusion 360 Text Commands window."""
    if not textPalette.isVisible:
        textPalette.isVisible = True
    textPalette.writeText(message)


def genSketch(n):
    global msg
    app = adsk.core.Application.get()
    ui = app.userInterface

    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent

    # sketchPoints = rootComp.sketches.item(0).sketchPoints
    existingSketch = rootComp.sketches.item(n)
    # Get all sketch points from the existing sketch
    sketchPoints = existingSketch.sketchPoints
    all_points = [point.geometry for point in sketchPoints]
    all_points = [
        point
        for point in all_points
        if not (point.x == 0 and point.y == 0 and point.z == 0)
    ]
    min_x_point = min(all_points, key=lambda p: p.x)
    max_x_point = max(all_points, key=lambda p: p.x)
    min_y_point = min(all_points, key=lambda p: p.y)
    max_y_point = max(all_points, key=lambda p: p.y)
    min_z_point = min(all_points, key=lambda p: p.z)
    max_z_point = max(all_points, key=lambda p: p.z)
    msg += "sketch {}: {}, {}, {}\n".format(
        n, max_y_point.x, max_y_point.y, max_y_point.z
    )
    msg += "sketch {}: {}, {}, {}\n".format(
        n, min_y_point.x, min_y_point.y, min_y_point.z
    )
    DebugPrint(msg)
    # Create a new sketch
    if n == 0:
        newSketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
        newSketch.name = "xYsketch"

    elif n == 1:
        newSketch = rootComp.sketches.add(rootComp.xZConstructionPlane)
        newSketch.name = "xZsketch"
    elif n == 2:
        newSketch = rootComp.sketches.add(rootComp.yZConstructionPlane)
        newSketch.name = "yZsketch"

    # Create the rectangle using the 4 corner points from existing points
    sketchLines = newSketch.sketchCurves.sketchLines
    pointMinX = sketchLines.addByTwoPoints(min_x_point, min_y_point)
    pointMaxX = sketchLines.addByTwoPoints(min_y_point, max_x_point)
    pointMinY = sketchLines.addByTwoPoints(max_x_point, max_y_point)
    pointMaxY = sketchLines.addByTwoPoints(max_y_point, min_x_point)
    return min_x_point, max_x_point, min_y_point, max_y_point, min_z_point, max_z_point


def extrudeSketch(rootComp, profxy, min, max):
    # yZSketch = allSketches.itemByName("yZsketch")
    # profxy = yZSketch.profiles.item(0)

    # add extrution from circle sketch
    extrudes = rootComp.features.extrudeFeatures
    distance_shell_up = adsk.core.ValueInput.createByReal(abs(float(max.x - min.x)))
    # distance_shell_up = adsk.core.ValueInput.createByReal(20)
    if profxy.parentSketch.name == "yZsketch":
        ShellExtrudeInput = extrudes.createInput(
            profxy, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
    else:
        ShellExtrudeInput = extrudes.createInput(
            profxy, adsk.fusion.FeatureOperations.IntersectFeatureOperation
        )
    ShellExtrudeInput.isSolid = True
    extent_distance_up = adsk.fusion.DistanceExtentDefinition.create(distance_shell_up)
    extend_direction_up = adsk.fusion.ExtentDirections.PositiveExtentDirection
    deg0 = adsk.core.ValueInput.createByString("0 deg")
    offset = adsk.core.ValueInput.createByReal(abs(float(min.x)))

    ShellExtrudeInput.setOneSideExtent(extent_distance_up, extend_direction_up, deg0)
    start_offset = adsk.fusion.OffsetStartDefinition.create(offset)
    ShellExtrudeInput.startExtent = start_offset
    extrudeXY = extrudes.add(ShellExtrudeInput)


def run(context):
    ui = None
    try:

        app = adsk.core.Application.get()
        ui = app.userInterface

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent

        # get structure
        allSketches = rootComp.sketches
        allMeshBodies = rootComp.meshBodies

        nMeshObj = allMeshBodies.count
        if nMeshObj < 1:
            exit()
        else:
            meshObj = allMeshBodies.item(0)
            # msg     = 'nBody: {}\n'.format(meshObj)
        # DebugPrint(msg)

        # fix mesh obj ======================================================
        repFeature = rootComp.features.meshRepairFeatures
        meshInput = repFeature.createInput(meshObj)
        repFeature.add(meshInput)

        # reduce face
        reduceFeat = rootComp.features.meshReduceFeatures
        reduceFeatInput = reduceFeat.createInput(meshObj)
        reduceFeatInput.meshReduceMethodType = (
            adsk.fusion.MeshReduceMethodTypes.AdaptiveReduceType
        )
        reduceFeatInput.meshReduceTargetType = (
            adsk.fusion.MeshReduceTargetTypes.ProportionMeshReduceTargetType
        )
        reduceFeatInput.proportion = adsk.core.ValueInput.createByString("1")
        reduceFeat.add(reduceFeatInput)

        # convert to solidbody
        for mesh in allMeshBodies:
            ui.activeSelections.add(mesh)
            app.executeTextCommand("Commands.Start ParaMeshConvertCommand")
            # push OK button
            app.executeTextCommand("NuCommands.CommitCmd")

        # project solidbody to sketch
        # project all body geometry
        xZPlane = rootComp.xZConstructionPlane
        sketch = rootComp.sketches.add(rootComp.xYConstructionPlane).project(
            rootComp.bRepBodies.item(0)
        )

        sketch = rootComp.sketches.add(rootComp.xZConstructionPlane).project(
            rootComp.bRepBodies.item(0)
        )
        sketch = rootComp.sketches.add(rootComp.yZConstructionPlane).project(
            rootComp.bRepBodies.item(0)
        )

        msg = ""
        (
            YZmin_x_point,
            YZmax_x_point,
            YZmin_y_point,
            YZmax_y_point,
            min_z_point,
            max_z_point,
        ) = genSketch(2)
        (
            XYmin_x_point,
            XYmax_x_point,
            XYmin_y_point,
            XYmax_y_point,
            XYmin_z_point,
            XYmax_z_point,
        ) = genSketch(1)
        (
            XZmin_x_point,
            XZmax_x_point,
            XZmin_y_point,
            XZmax_y_point,
            XZmin_z_point,
            XZmax_z_point,
        ) = genSketch(0)
        # msg += "min: {}, {}, {}\n".format(
        #     XYmin_z_point.x, XYmin_z_point.y, XYmin_z_point.z
        # )
        # msg += "max: {}, {}, {}\n".format(
        #     XYmax_z_point.x, XYmax_z_point.y, XYmax_z_point.z
        # )
        # DebugPrint(msg)

        yZSketch = allSketches.itemByName("yZsketch")
        profxy = yZSketch.profiles.item(0)
        extrudeSketch(rootComp, profxy, XYmin_x_point, XYmax_x_point)

        xYSketch = allSketches.itemByName("xYsketch")
        profyz = xYSketch.profiles.item(0)

        # extrudeSketch(rootComp, profyz, min1_z_point, max1_z_point)

        extrudes = rootComp.features.extrudeFeatures
        distance_shell_up = adsk.core.ValueInput.createByReal(
            XYmax_y_point.y - XYmin_y_point.y
        )
        # distance_shell_up = adsk.core.ValueInput.createByReal(20)
        ShellExtrudeInput = extrudes.createInput(
            profyz, adsk.fusion.FeatureOperations.IntersectFeatureOperation
        )
        ShellExtrudeInput.isSolid = True
        extent_distance_up = adsk.fusion.DistanceExtentDefinition.create(
            distance_shell_up
        )
        extend_direction_up = adsk.fusion.ExtentDirections.PositiveExtentDirection
        deg0 = adsk.core.ValueInput.createByString("0 deg")
        offset = adsk.core.ValueInput.createByReal(abs(float(XYmax_y_point.y)))

        ShellExtrudeInput.setOneSideExtent(
            extent_distance_up, extend_direction_up, deg0
        )
        start_offset = adsk.fusion.OffsetStartDefinition.create(offset)
        ShellExtrudeInput.startExtent = start_offset
        extrudeXY = extrudes.add(ShellExtrudeInput)

        xZSketch = allSketches.itemByName("xZsketch")
        profxZ = xZSketch.profiles.item(0)
        extrudeSketch(rootComp, profxZ, XZmin_x_point, XZmax_x_point)

        # # add extrution from circle sketch
        # extrudes = rootComp.features.extrudeFeatures
        # distance_shell_up = adsk.core.ValueInput.createByReal(
        #     float(XYmax_x_point.x - XYmin_x_point.x)
        # )
        # # distance_shell_up = adsk.core.ValueInput.createByReal(20)
        # ShellExtrudeInput = extrudes.createInput(
        #     profxy, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        # )
        # ShellExtrudeInput.isSolid = True
        # extent_distance_up = adsk.fusion.DistanceExtentDefinition.create(
        #     distance_shell_up
        # )
        # extend_direction_up = adsk.fusion.ExtentDirections.PositiveExtentDirection
        # deg0 = adsk.core.ValueInput.createByString("0 deg")
        # offset = adsk.core.ValueInput.createByReal(float(XYmin_x_point.x))

        # ShellExtrudeInput.setOneSideExtent(
        #     extent_distance_up, extend_direction_up, deg0
        # )
        # start_offset = adsk.fusion.OffsetStartDefinition.create(offset)
        # ShellExtrudeInput.startExtent = start_offset
        # extrudeXY = extrudes.add(ShellExtrudeInput)

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
