# Author-
# Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

app = adsk.core.Application.get()
ui = app.userInterface

product = app.activeProduct
design = adsk.fusion.Design.cast(product)
rootComp = design.rootComponent

extrudeFeature = rootComp.features.extrudeFeatures
combineFeature = rootComp.features.combineFeatures
moveFeature = rootComp.features.moveFeatures
textPalette = adsk.core.Application.get().userInterface.palettes.itemById(
    "TextCommands"
)
msg = ""


def select3Points():

    # Message box to instruct the user
    ui.messageBox("Select only 3 vertices point by clicking on them!!")

    # Create an ObjectCollection to store selected vertices.
    verticesCollection = adsk.core.ObjectCollection.create()

    for i in range(3):
        try:
            # Prompt the user to select a vertex.
            vertexSelection = ui.selectEntity(
                'Select a vertex or press "Esc" to finish', "Vertices"
            )

            # If the selection is None, the user pressed "Esc" to exit
            if not vertexSelection:
                break

            # Add the selected vertex to the collection.
            selectedVertex = vertexSelection.entity
            verticesCollection.add(selectedVertex)
        except:
            # If the selection process is canceled, break the loop
            break
    # ui.messageBox(f"Total vertices selected: {verticesCollection.count}")

    pointColl = adsk.core.ObjectCollection.create()
    for i in range(verticesCollection.count):
        vertex = adsk.fusion.BRepVertex.cast(verticesCollection.item(i))
        position = vertex
        pointColl.add(position)
    return pointColl


def setView(constructionPlane: adsk.fusion.ConstructionPlane):

    # Get the sketch plane
    # plane = sketch.referencePlane

    # Get the normal vector of the plane
    normal_vector = constructionPlane.geometry.normal
    view = app.activeViewport

    # Set the view to be perpendicular to the sketch constructionPlane
    origin = constructionPlane.geometry.origin
    cam = view.camera
    cam.viewOrientation = adsk.core.ViewOrientations.TopViewOrientation
    cam.eye = adsk.core.Point3D.create(
        origin.x + normal_vector.x * 10,
        origin.y + normal_vector.y * 10,
        origin.z + normal_vector.z * 10,
    )
    cam.target = constructionPlane.geometry.origin
    cam.upVector = adsk.core.Vector3D.create(
        0, 1, 0
    )  # Optional: Adjust to fit your needs
    view.camera = cam
    view.fit()
    view.refresh()


def selectPoints():
    # Create an ObjectCollection to store selected vertices.
    verticesCollection = adsk.core.ObjectCollection.create()

    # Message box to instruct the user
    ui.messageBox(
        'Select vertices point by clicking on them, as much as possible. Press "Esc" to finish the selection.'
    )

    while True:
        try:
            # Prompt the user to select a vertex.
            vertexSelection = ui.selectEntity(
                'Select a vertex or press "Esc" to finish', "SketchPoints"
            )

            # If the selection is None, the user pressed "Esc" to exit
            if not vertexSelection:
                break

            # Add the selected vertex to the collection.
            selectedVertex = vertexSelection.entity
            verticesCollection.add(selectedVertex)
        except:
            # If the selection process is canceled, break the loop
            break
    # ui.messageBox(f"Total vertices selected: {verticesCollection.count}")

    pointColl = adsk.core.ObjectCollection.create()
    for i in range(verticesCollection.count):
        vertex = adsk.fusion.SketchPoint.cast(verticesCollection.item(i))
        position = vertex
        pointColl.add(position)
    return pointColl


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
    try:
        ui.messageBox("Select 1 mesh file as input!!!")

        meshSelection = ui.selectEntity(
            'Select a vertex or press "Esc" to finish', "MeshBodies"
        )
        meshObj = meshSelection.entity
        selectedName = meshObj.name
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
        reducedMesh = reduceFeat.add(reduceFeatInput)
        reducedMesh

        # convert to solidbody
        # for mesh in allMeshBodies:
        ui.activeSelections.add(reducedMesh)
        app.executeTextCommand("Commands.Start ParaMeshConvertCommand")
        # push OK button
        app.executeTextCommand("NuCommands.CommitCmd")

        # combine them all
        bodies = rootComp.bRepBodies
        targetBody = bodies.item(0)
        toolBodyColl = adsk.core.ObjectCollection.create()
        for i in range(1, bodies.count):
            toolBodyColl.add(bodies.item(i))
        combineInput = combineFeature.createInput(targetBody, toolBodyColl)
        combineInput.isKeepToolBodies = False
        singleBody = combineFeature.add(combineInput)
        singleBody.name = "combinedBody"
        rootComp.bRepBodies.item(0).name = selectedName

        for i in range(rootComp.meshBodies.count):
            rootComp.meshBodies.item(i).isLightBulbOn = False

        # Extract the geometry of the selected points
        constructionPoints = select3Points()
        point1 = constructionPoints.item(0)
        point2 = constructionPoints.item(1)
        point3 = constructionPoints.item(2)

        # Create a construction plane input based on three points
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        planeInput.setByThreePoints(point1, point2, point3)
        constructionPlane = planes.add(planeInput)
        constructionPlane.name = "3PointPlane"

        sketch = rootComp.sketches.add(constructionPlane)

        projectedSketch = sketch.project(rootComp.bRepBodies.item(0))
        sketch.name = "projectedSketch"
        rootComp.bRepBodies.item(0).isLightBulbOn = False
        constructionPlane.isLightBulbOn = True

        # rootComp.constructionPlanes.itemByName('3PointPlane')
        generatedSketch = rootComp.sketches.add(constructionPlane)
        generatedSketch.name = "generatedSketchLine"
        sketchPoints = selectPoints()
        for i in range(len(sketchPoints) - 1):
            start_point = adsk.fusion.SketchPoint.cast(sketchPoints.item(i)).geometry
            end_point = adsk.fusion.SketchPoint.cast(sketchPoints.item(i + 1)).geometry
            #     # Create a line between the current point and the next point
            generatedSketch.sketchCurves.sketchLines.addByTwoPoints(
                start_point, end_point
            )

        # app.activeViewport.
        setView(constructionPlane)

        genProf = generatedSketch.profiles.item(0)
        distance = adsk.core.ValueInput.createByString("10mm")
        extrudeInput = extrudeFeature.createInput(
            genProf, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )

        extrudeInput.setSymmetricExtent(distance, True)
        finalBody = extrudeFeature.add(extrudeInput)
        finalBody.name = "finalBody"

        body = rootComp.bRepBodies.item(1)

        allOccs = rootComp.occurrences
        transform = adsk.core.Matrix3D.create()

        # Create a new component
        allOccs = rootComp.occurrences
        newCompOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
        newComp = adsk.fusion.Component.cast(newCompOcc.component)

        # Move the body to the new component
        # Create a new base feature in the new component
        baseFeatures = newComp.features.baseFeatures
        baseFeature = baseFeatures.add()

        # Start the base feature edit to add geometry
        baseFeature.startEdit()
        newComp.bRepBodies.add(body, baseFeature)
        baseFeature.finishEdit()

        # Remove the body from the original component

        # design.rootComponent.allOccurrences
        # product = app.activeProduct
        # design = adsk.fusion.Design.cast(product)
        # rootComp = design.rootComponent
        # ui.messageBox(str(rootComp.bRepBodies.count))
        # for i in range(rootComp.bRepBodies.count):
        #     rootComp.bRepBodies.item(i).deleteMe()
        # ui.messageBox(str(rootComp.bRepBodies.item(0).name))
        # ui.messageBox(str(rootComp.bRepBodies.item(0).isTransient))
        # rootComp.bRepBodies.item(0).deleteMe()

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
