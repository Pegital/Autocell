from ast import List
import copy
import eto_UI
import os

from itertools import chain
import random
import Rhino.Geometry as rg
from rhinoscript import surface
from rhinoscript.curve import OffsetCurve
from rhinoscript.object import DeleteObject, HideObjects
from rhinoscript.plane import WorldXYPlane
import rhinoscriptsyntax as rs
from System import *
from Rhino import *
from Rhino.Geometry import *
from Rhino.Commands import *
from Rhino.DocObjects import *
from Rhino.Input import *
from scriptcontext import doc
import Rhino.DocObjects
from Rhino.Input import *
from Rhino.Input.Custom import *
from Rhino.Commands import *
from scriptcontext import *

import clr

clr.AddReference("Eto")
clr.AddReference("Rhino.UI")

from Rhino.UI import *
from Eto.Forms import *
from Eto.Drawing import *
import Eto

# guid
dialog = Dialog()
dialog.Title = "Guide"
dialog.Padding = Padding(5)
dialog.Resizable = True

image_view = ImageView()
image_view.Image = Bitmap(os.path.dirname(os.path.realpath(__file__)) + "/c2.png")

dialog.Content = image_view

dialog.ShowModal(RhinoEtoApp.MainWindow)
#
# Constants
#

ASK_FOR_POINT = "select point from grid"

ASK_FOR_ANOTHER_POINT = "select another point from grid"

ASK_FOR_END_OR_CONTINUE = "press 0 to end or press 1 to continue"

HIGHT_Of_CUBES = 4.0


#
# Functions
#
# Create a grid in Rhino.(by Amerah)
def DrawGrid(height_, width_):
    gridp = []
    gridrg = []
    for i in range(0, height_):
        for j in range(0, width_):
            ptA = rs.AddPoint(i * 5, j * 3, 0)
            pth = rg.Point3d(i * 5, j * 3, 0)
            gridp.append(ptA)
            gridrg.append(pth)
    return gridp, gridrg


# getting the centers of cubes(by Pegah)
def AllCenters(flatten_cubes):
    centroids = []
    for cubes in flatten_cubes:
        center_ = rs.SurfaceVolumeCentroid(cubes)
        if center_ is not None:
            centroids.append(center_[0])
    return centroids


# sorting function (by Amerah)
def sorting(e):
    return e.Y


# creating random seed(by Pegah)
def sample_seed(list1, number, seed_):

    (random.seed(seed_))
    too_delet = random.sample(list1, number)
    return too_delet


# Attraction points and its distances from grid(by Amerah)
def CreateAttractionPoint(centroids, attraction_point):
    # Create a list of tuples (point, distance)
    listC = [(point_, rs.Distance(attraction_point, point_)) for point_ in centroids]

    # Sort the list of tuples based on distances
    sorted_listB = sorted(listC, key=lambda x: x[1])

    # Extract the sorted points and distances from the sorted list
    sorted_centroids = [item[0] for item in sorted_listB]
    sorted_distances = [item[1] for item in sorted_listB]
    return sorted_distances, sorted_centroids


# deleting neighbors randomly and collect the remains(by Pegah)
def Delete_CollectRemains_cubes(flatten_cubes, cubetodel):
    remain_cubes = []
    # print("flattened cubes", len(flatten_cubes))
    # print("cubetodel cubes", len(cubetodel))
    for cube in flatten_cubes:
        center_ = rs.SurfaceVolumeCentroid(cube)
        if center_ is not None:
            matched = False

            for cdelete in cubetodel:
                if center_[0] == cdelete:
                    matched = True

            if matched == True:
                rs.DeleteObject(cube)
            if matched == False:
                remain_cubes.append(cube)
    return remain_cubes


# neighbors checking  in X, Y, Z axis(by Pegah)
def NeighborCheckXYZ(centroids, attraction_point, numberOfneighborstoDel):
    cubetodel = []
    seed_ = eto_UI.RequestSeedGenerator()

    for i in range(len(centroids)):
        eachcubeneighbors = []
        for j in range(len(centroids)):
            _disline = rg.Line(centroids[i], centroids[j])
            lendis = _disline.Length
            roundeddis = round(lendis)
            roundeddis2 = round(lendis, 1)
            # checking neighbor in x y z
            if roundeddis == 5.0 or roundeddis == 3.0 or roundeddis2 == 4.0:
                eachcubeneighbors.append(centroids[j])

        # Deleting randomly the from the neighbors cubes if the cube has 5 or 4 0r 6neighbors
        if (
            len(eachcubeneighbors) == 4
            or len(eachcubeneighbors) == 5
            or len(eachcubeneighbors) == 6
        ):
            f = CreateAttractionPoint(centroids, attraction_point)
            sorted_centroids = f[1]
            sorted_distances = f[0]

            to_delete = sample_seed(eachcubeneighbors, numberOfneighborstoDel, seed_)

            for tod in to_delete:
                cubetodel.append(tod)
            for k in range(len(sorted_distances)):
                if sorted_distances[k] < 8:
                    cubetodel.append(sorted_centroids[k])
    return cubetodel


# Copying cubes in 3 level above first level(by Amerah)
def CubesForAllLevels(cubes0):
    All_cubes = []

    for i in (0, 1, 2, 3):
        xform = rs.XformTranslation([0, 0, i * HIGHT_Of_CUBES])
        cubes1 = rs.TransformObjects(cubes0, xform, True)

        All_cubes.append(cubes1)
        rs.HiddenObjects(cubes0)
    # flattening the list of cubes

    flatten_cubes = list(chain.from_iterable(All_cubes))

    return flatten_cubes


# deleting duplicated cubes(by Pegah)
def DeletingDubCube(cubes):
    CpL = []

    for cube in cubes:
        volumCpt = rs.SurfaceVolumeCentroid(cube)
        if volumCpt is not None:
            volumcent = volumCpt[0]

            volumcenRound = []
            for i in volumcent:

                volumcenRound.append(round(i))
            CpL.append(volumcenRound)
    uniquesC = []
    uniques = []
    for a, b in zip(CpL, cubes):
        if a in uniquesC:
            rs.DeleteObject(b)
            print(a)
        if a not in uniques:
            uniquesC.append(a)
            uniques.append(b)
    return uniques


# Creating cubes first level(by Pegah)
def Cubes_initial(foundSQ):
    cubes0 = []
    cubes0Fixed = []
    for i in foundSQ:
        pt0 = rs.AddPoint(i[0])
        pt1 = rs.AddPoint(i[1])
        pt2 = rs.AddPoint(i[2])
        pt3 = rs.AddPoint(i[3])
        sp = [pt0, pt1, pt2, pt3]
        ssp = rs.SortPointList(sp)
        ssp.append(pt0)
        squers_ = rs.AddPolyline(ssp)
        print("sqq")

        # making cubes first level
        cubes = rs.ExtrudeCurveStraight(squers_, [0, 0, 0], [0, 0, 4.0])
        cubescl = rs.CapPlanarHoles(cubes)

        cubes0.append(cubes)
    fixedCubes = eto_UI.RequestFixedCubesGenerator()
    rs.HideObjects(fixedCubes)
    rs.HideObjects(cubes0)
    return cubes0, fixedCubes


# CreatingPointsFor Rectangles In Boundary(by Pegah)
def CreatingPointsForRectangles(toremainpt):
    foundSQ = []
    for i in range(len(toremainpt)):
        eachpt = toremainpt[i]

        # print("a. ", eachpt)

        pointToTheRight = rg.Point3d(eachpt)
        pointToTheRight.X = pointToTheRight.X + 5
        # print("b. ", eachpt)
        pointToThebottom = rg.Point3d(eachpt)
        pointToThebottom.Y = pointToThebottom.Y + 3
        # print("c. ", eachpt)
        pointToThebottomRight = rg.Point3d(eachpt)
        pointToThebottomRight.Y = pointToThebottomRight.Y + 3
        pointToThebottomRight.X = pointToThebottomRight.X + 5
        # print("d. ", eachpt)

        # checking if rectangle pints are in the list of remained points
        # if we had 3 points in right direction to create rectangle we collect them

        matchingItems = []
        for j in range(len(toremainpt)):
            pt = toremainpt[j]
            if (
                pt == pointToThebottom
                or pt == pointToThebottomRight
                or pt == pointToTheRight
            ):
                matchingItems.append(pt)

        if len(matchingItems) == 3:
            matchingItems.append(eachpt)
            foundSQ.append(matchingItems)
    return foundSQ


# checking points from grid is in boundary or not(by Pegah)
def CheckInBoundary(gp, boundryp):
    checkpt = []

    for ptg in gp:
        bllist = rs.PointInPlanarClosedCurve(ptg, boundryp[0])
        checkpt.append(bllist)
    return checkpt


# axis of column(by Amerah)
def makingFinalAxis(axis, remain_cubes2):
    crrvs = []
    for item in axis:
        for c in remain_cubes2:
            if rs.CurveBrepIntersect(item, c) is not None:
                crrvs.append((rs.CurveBrepIntersect(item, c)[0]))

    flattencrvs = list(
        chain(*[ele if isinstance(ele, list) else [ele] for ele in crrvs])
    )

    rs.HideObjects(axis)
    final_axis = []
    pl = [
        rs.AddPlaneSurface(rs.WorldXYPlane(), 40.0, 40.0),
        rs.AddPlaneSurface(rs.WorldXYPlane(), 10.0, 20.0),
    ]
    cl_ = []
    for cr in flattencrvs:
        ex_a = rs.ExtendCurve(cr, 0, 0, pl)

        if ex_a is None:
            a = rs.ExtrudeCurveStraight(cr, (0, 0, 0), (0, 0.13, 0))
            b = rs.ExtrudeCurveStraight(cr, (0, 0, 0), (0, -0.13, 0))
            cl1 = rs.OffsetSurface(a, 0.13, None, True, True)
            cl2 = rs.OffsetSurface(b, 0.13, None, True, True)
            cl_.append(cl1)
            cl_.append(cl2)
            rs.HideObjects(a)
            rs.HideObjects(b)

        if ex_a is not None:
            final_axis.append(ex_a)
            d = rs.ExtrudeCurveStraight(ex_a, (0, 0, 0), (0, 0.13, 0))
            f = rs.ExtrudeCurveStraight(ex_a, (0, 0, 0), (0, -0.13, 0))
            cl3 = rs.OffsetSurface(d, 0.13, None, True, True)
            cl4 = rs.OffsetSurface(f, 0.13, None, True, True)
            cl_.append(cl3)
            cl_.append(cl4)
            rs.HideObjects(d)
            rs.HideObjects(f)

    rs.HideObjects(pl)

    rs.ObjectColor(cl_, (255, 255, 255))

    return cl_


# exploding polysurfaces(by Amerah)
def explode_polysurfaces(polysurfaces):
    exploded_surfaces = []

    for polysurface in polysurfaces:
        if rs.IsPolysurface(polysurface):
            surfaces = rs.ExplodePolysurfaces(polysurface, delete_input=True)
            exploded_surfaces.extend(surfaces)

    return exploded_surfaces


# dividing surfaces in horizontal and vertical(by Pegah)
def check_Horizontal(explodedPoly):
    horizontalSrf = []
    verticalSrf = []
    for surfaces in explodedPoly:
        AreaCpt = rs.SurfaceAreaCentroid(surfaces)
        if AreaCpt is not None:

            if (
                AreaCpt[0][2] == 0
                or AreaCpt[0][2] == 4.0
                or AreaCpt[0][2] == 8
                or AreaCpt[0][2] == 12
                or AreaCpt[0][2] == 16
            ):
                horizontalSrf.append(surfaces)
            else:
                verticalSrf.append(surfaces)
        Ceilings = rs.ObjectColor(horizontalSrf, color=[26, 38, 191])
        Walls = rs.ObjectColor(verticalSrf, color=[16, 161, 98])

    return verticalSrf, horizontalSrf


# deleting duplicated surface Horizontal(by Pegah)
def DeletingDub(Hsrf):
    CpL = []

    for surfaces in Hsrf:
        AreaCpt = rs.SurfaceAreaCentroid(surfaces)
        if AreaCpt is not None:
            CpL.append(AreaCpt[0])
    uniquesC = []
    uniques = []
    for a, b in zip(CpL, Hsrf):
        if a in uniquesC:
            rs.DeleteObject(b)
        if a not in uniques:
            uniquesC.append(a)
            uniques.append(b)
    return uniques


# offsetting boundry to make the slab(by Pegah)
def offsetClosedCrv(Cb):

    D = 0.1
    b_list = []
    for Cbr in Cb:
        Crv = Rhino.DocObjects.ObjRef(Cbr).Curve()
        ac = Crv.Offset(
            rg.Point3d(0, 0, Crv.PointAtEnd.Z),
            rg.Vector3d(0, 0, 1),
            D,
            0.0001,
            rg.CurveOffsetCornerStyle.Sharp,
        )
        if ac is not None and len(ac) > 0:
            _C = rg.Curve.JoinCurves(ac)
            if _C is not None and len(_C) > 0:
                C = _C[0]
                curve_object_id = doc.Objects.AddCurve(C)
                doc.Objects.Select(curve_object_id)
                b_list.append(curve_object_id)

    return b_list


# deleting duplicated surface vertical(by Pegah)
def DeletinginterioreW(Hsrf):
    todelet = []

    for i, surfaces in enumerate(Hsrf):
        AreaCpt = rs.SurfaceAreaCentroid(surfaces)
        if AreaCpt is None:
            raise Exception("is none-outer")

        for j, surfacesinnerL in enumerate(Hsrf):
            AreaCptinnerL = rs.SurfaceAreaCentroid(surfacesinnerL)
            if AreaCptinnerL is None:
                raise Exception("is none-inner")

            def check_round(a, b, tol):
                return (a + tol >= b) and (a - tol <= b)

            # print("areacpt", AreaCpt[0], "areacptinnerL", AreaCptinnerL[0])
            if (
                check_round(AreaCpt[0][0], AreaCptinnerL[0][0], 1)
                and check_round(AreaCpt[0][1], AreaCptinnerL[0][1], 1)
                and check_round(AreaCpt[0][2], AreaCptinnerL[0][2], 1)
                and (i != j)
            ):
                todelet.append(surfaces)
                todelet.append(surfacesinnerL)

    rs.DeleteObjects(todelet)


# deleting duplication after room creation(by Pegah)
def Deletingdup(Hsrf, roomw):
    todelet = []
    tokeep = []

    def check_round(a, b, tol):
        return (a + tol >= b) and (a - tol <= b)

    for i, surfaces in enumerate(Hsrf):
        AreaCpt = rs.SurfaceAreaCentroid(surfaces)
        if AreaCpt is not None:

            for j, surfacesinnerL in enumerate(roomw):
                AreaCptinnerL = rs.SurfaceAreaCentroid(surfacesinnerL)
                if AreaCptinnerL is not None:

                    # print("areacpt", AreaCpt[0], "areacptinnerL", AreaCptinnerL[0])
                    if (
                        check_round(AreaCpt[0][0], AreaCptinnerL[0][0], 1)
                        and check_round(AreaCpt[0][1], AreaCptinnerL[0][1], 1)
                        and check_round(AreaCpt[0][2], AreaCptinnerL[0][2], 1)
                    ):

                        todelet.append(surfacesinnerL)
                        tokeep.append(surfaces)

    rs.DeleteObjects(todelet)
    return tokeep


# creating rooms(by Amerah)
def Room_Selection(allHorizantal):
    def floor_selecting():

        roomsrf = eto_UI.RequestroomGenerator()
        if roomsrf is not None:

            rooms = []
            for item in roomsrf:
                # s = item.Object()
                roomcev = rs.DuplicateSurfaceBorder(item, type=1)
                if roomcev is None:
                    raise Exception("roomcev is none")

                wallroom = rs.ExtrudeCurveStraight(roomcev, (0, 0, 0), (0, 0, 4.0))

                if wallroom is None:
                    raise Exception("wallroom is none")

                if rs.IsPolysurface(wallroom):
                    w = rs.ExplodePolysurfaces(wallroom, delete_input=True)
                rooms.append(w)
        return rooms

    def hidingForuser(level):
        for surfaces in allHorizantal:
            surfacecenterH = rs.SurfaceAreaCentroid(surfaces)
            if surfacecenterH is None:
                continue
            if round(surfacecenterH[0][2]) != round(level * 4.0):
                rs.HideObjects(surfaces)

    allrooms = []
    for i in range(4):
        print("doing the level:", i)
        hidingForuser(i)
        rooms = floor_selecting()
        allrooms.append(rooms)

        rs.ShowObjects(allHorizantal)
    return allrooms


# extracting bordersfor slabs(by Amerah)
def borderfloor(surfaces):
    listboundry = []
    floor = []
    forpanel = []
    for i in range(len(surfaces)):
        border = rs.DuplicateSurfaceBorder(surfaces[i], type=1)

        floor.append(border)
        if border is None:
            raise Exception("border was none.")

        xform = rs.XformTranslation([0, 0, -1 * (HIGHT_Of_CUBES)])
        boundryS = rs.TransformObjects(border, xform, True)
        rs.ObjectColor(boundryS, (220, 1, 1))
        listboundry.append(boundryS)

    return listboundry, floor


# Main
#
# selecting curtain walls(by Pegah)
def Facade_Construction(_surfaceToS, border):
    surface_border = []
    if _surfaceToS is not None:
        # deleting curtain walls from list of walls to prepare them for paneling

        obj = eto_UI.RequestcurtainWall()
        if obj is None:
            raise Exception("obj is none")

        outerFrame = []

        for id in obj[0]:
            aa = rs.SurfaceArea(id)
            crv = rs.DuplicateSurfaceBorder(id)
            if crv is not None:
                surface_border.append(Rhino.DocObjects.ObjRef(crv[0]).Curve())

            crvL = rs.ExplodeCurves(crv, delete_input=True)
            cc = rs.SurfaceAreaCentroid(id)
            if cc is None:
                raise Exception("cc is none")
            if cc is not None:
                for i in crvL:
                    frame = rs.OffsetCurve(i, cc[0], 0.1, [0, 1, 0])
                    if frame is None:
                        raise Exception("frame is none.")
                    framesrf = rs.AddLoftSrf([i, frame])
                    if framesrf is None:
                        raise Exception("framesrf is none")

                    fram__ = rs.OffsetSurface(
                        framesrf,
                        0.05,
                        tolerance=None,
                        both_sides=True,
                        create_solid=True,
                    )
                    if fram__ is not None:
                        if obj is not None:

                            if aa is not None:

                                listL = []
                                pointsh = []
                                pointsv = []
                                if aa[0] > 15:
                                    for i in crvL:

                                        Lc = rs.CurveLength(i)
                                        if Lc is not None:

                                            if Lc == 5:

                                                domain = rs.CurveDomain(i)
                                                t = domain[1] - 1
                                                t1 = domain[1] - 2
                                                t2 = domain[0] + 1
                                                t3 = domain[0] + 2

                                                tpram = [t, t2, t1, t3]

                                                for j in tpram:
                                                    point = rs.EvaluateCurve(i, j)
                                                    pointsh.append(point)
                                                print(pointsh)

                                            if Lc == 4:
                                                domain = rs.CurveDomain(i)

                                                t2 = domain[0] + 1
                                                t = domain[1] - 1
                                                tpram = [t, t2]

                                            for j in tpram:
                                                point = rs.EvaluateCurve(i, j)
                                                pointsv.append(point)
                                    l1 = rs.AddLine(pointsv[1], pointsv[6])
                                    l2 = rs.AddLine(pointsv[0], pointsv[7])
                                    if obj[1] == False:
                                        p1 = [
                                            pointsv[0][0],
                                            pointsv[0][1],
                                            pointsv[0][2] + 1.0,
                                        ]
                                        p7 = [
                                            pointsv[7][0],
                                            pointsv[7][1],
                                            pointsv[7][2] + 1.0,
                                        ]
                                        l2 = rs.AddLine(p1, p7)

                                    l3 = rs.AddLine(pointsv[2], pointsv[9])
                                    l4 = rs.AddLine(pointsv[3], pointsv[8])
                                    l5 = rs.AddLine(pointsv[4], pointsv[11])
                                    l6 = rs.AddLine(pointsv[5], pointsv[10])
                                    listL.append(l1)
                                    listL.append(l2)
                                    listL.append(l3)
                                    listL.append(l4)
                                    listL.append(l5)
                                    listL.append(l6)
                                else:
                                    for i in crvL:

                                        Lc = rs.CurveLength(i)
                                        if Lc is not None:

                                            if Lc == 3:

                                                domain = rs.CurveDomain(i)
                                                t = domain[1] - 1

                                                t2 = domain[0] + 1

                                                tpram = [t, t2]

                                                for j in tpram:
                                                    point = rs.EvaluateCurve(i, j)
                                                    pointsh.append(point)
                                                print(pointsh)

                                            if Lc == 4:
                                                domain = rs.CurveDomain(i)

                                                t2 = domain[0] + 1
                                                t = domain[1] - 1

                                                tpram = [t, t2]

                                            for j in tpram:
                                                point = rs.EvaluateCurve(i, j)
                                                pointsv.append(point)

                                    l2 = rs.AddLine(pointsv[1], pointsv[4])
                                    if obj[1] == False:
                                        p1 = [
                                            pointsv[1][0],
                                            pointsv[1][1],
                                            pointsv[1][2] + 1.0,
                                        ]
                                        p5 = [
                                            pointsv[4][0],
                                            pointsv[4][1],
                                            pointsv[4][2] + 1.0,
                                        ]
                                        l2 = rs.AddLine(p1, p5)
                                    l1 = rs.AddLine(pointsv[0], pointsv[5])

                                    l3 = rs.AddLine(pointsv[2], pointsv[7])
                                    l4 = rs.AddLine(pointsv[3], pointsv[6])
                                    listL.append(l1)
                                    listL.append(l2)
                                    listL.append(l3)
                                    listL.append(l4)

                outerFrame.append(fram__)

            profils = []

            for L in listL:

                ofsL = rs.OffsetCurveOnSurface(L, id, 0.05)
                if ofsL is None:
                    raise Exception("ofsL is none.")
                ofsL1 = rs.OffsetCurveOnSurface(L, id, -0.05)
                if ofsL1 is None:
                    raise Exception("ofsL1 is none.")

                ofstList = [ofsL, ofsL1]
                profil = rs.AddLoftSrf(ofstList)
                if profil is None:
                    raise Exception("profil is none.")
                if profil is not None:
                    innerPr = rs.OffsetSurface(
                        profil,
                        -0.05,
                        tolerance=None,
                        both_sides=False,
                        create_solid=True,
                    )
                    profils.append(innerPr)

        ##########################
        # panelizing the remain walls
    userInputs = eto_UI.panel_size()
    if userInputs is None:
        raise Exception("userInputs is none")
    if userInputs is not None:
        todelet = []
        tokeep = []

        def check_round(a, b, tol):
            return (a + tol >= b) and (a - tol <= b)

        for i, surfaces in enumerate(_surfaceToS):
            AreaCpt = rs.SurfaceAreaCentroid(surfaces)
            if AreaCpt is None:
                print("areapt is none")

            else:
                shouldDelete = False
                for j, surfacesinnerL in enumerate(obj[0]):
                    print(surfacesinnerL)
                    AreaCptinnerL = rs.SurfaceAreaCentroid(surfacesinnerL)
                    if AreaCptinnerL is None:
                        print("areapt is none2")
                    else:

                        # print("areacpt", AreaCpt[0], "areacptinnerL", AreaCptinnerL[0])
                        if (
                            check_round(AreaCpt[0][0], AreaCptinnerL[0][0], 1.5)
                            and check_round(AreaCpt[0][1], AreaCptinnerL[0][1], 1.5)
                            and check_round(AreaCpt[0][2], AreaCptinnerL[0][2], 1.5)
                        ):
                            shouldDelete = True
                if shouldDelete:
                    todelet.append(surfaces)
                else:
                    tokeep.append(surfaces)

        # conture in z direction for creating panels
        def Conture(obj_refs):

            gp = GetPoint()
            gp.SetCommandPrompt("Contour plane base point")
            gp.Get()
            if gp.CommandResult() != Result.Success:
                return gp.CommandResult()
            base_point = gp.Point()
            print(type(base_point))

            gp.DrawLineFromPoint(base_point, True)
            gp.SetCommandPrompt("Direction perpendicular to contour planes")
            gp.Get()
            if gp.CommandResult() != Result.Success:
                return gp.CommandResult()
            end_point = gp.Point()
            print(type(end_point))

            if base_point.DistanceTo(end_point) < RhinoMath.ZeroTolerance:
                return Result.Nothing

            distance = userInputs[1]
            rc, distance = RhinoGet.GetNumber(
                "Distance between contours", False, distance
            )
            if rc != Result.Success:
                return rc

            interval = Math.Abs(distance)
            crvId = []
            counter = 0

            for obj_refu in obj_refs:

                geometry = Rhino.DocObjects.ObjRef(obj_refu).Brep()

                if type(geometry) == Brep:

                    curves = Brep.CreateContourCurves(
                        geometry, base_point, end_point, interval
                    )

                    for curve in curves:

                        if curve == curves[-1]:
                            print(curve)

                        else:
                            curve_object_id = doc.Objects.AddCurve(curve)
                            doc.Objects.Select(curve_object_id)
                            crvId.append(curve_object_id)
                    print("curve loop")

                    if curves != None:
                        doc.Views.Redraw()
            print("exite obj_refs")

            return crvId

        srfTocont = []
        for h in tokeep:

            s_ = rs.OffsetSurface(h, 0.1)

            if s_ is None:
                print("f")

            srfTocont.append(s_)
        rs.DeleteObjects(todelet)
        crvc = Conture(srfTocont)
        crv = []
        if crvc is None:
            raise Exception("crv is none")
        if crvc is not None:

            oflist = []
            for _c in crvc:
                pt = rs.CurveMidPoint(_c)
                if pt is None:
                    print("could notmake pt")
                crvv = rs.OffsetCurve(_c, pt, 0.001)
                if crvv is None:
                    print("could not offset line")
                if crvv is not None:
                    oflist.append(crvv)

            cvv = rs.JoinCurves(oflist, True, 0.0001)
            for v in cvv:
                j = rs.ExtendCurveLength(v, 0, 2, 0.001)
                if j is None:
                    print("could not offset")
                if j is not None:

                    crv.append(j)

            # dividing conture curves to create panels
            all__panels = []
            for i in crv:
                divosionPt = rs.DivideCurveLength(
                    i, userInputs[0], create_points=False, return_points=True
                )

                if divosionPt is not None:

                    # creating segments in conture lines

                    for n in range(len(divosionPt) - 1):

                        panelL = rs.AddLine(divosionPt[n], divosionPt[n + 1])

                        # the solution for covering column before deceiding for expose structure
                        # if n == 0:
                        # pp = rs.ExtendCurveLength(panelL, 0, 0, 0.15)
                        # panelS = rs.ExtrudeCurveStraight(pp,(0, 0, 0),(0, 0, userInputs[1]),

                        # panel_1 = rs.OffsetSurface(panelS, 0.05, None, False, True)

                        # if n == -1:
                        # pp = rs.ExtendCurveLength(panelL, 0, 1, 0.15)
                        # panelS = rs.ExtrudeCurveStraight(
                        # pp,
                        # (0, 0, 0),
                        # (0, 0, userInputs[1]),
                        # )
                        # panel_1 = rs.OffsetSurface(panelS, -0.05, None, False, True)

                        # panel line extrouding

                        panelS = rs.ExtrudeCurveStraight(
                            panelL,
                            (0, 0, 0),
                            (0, 0, userInputs[1]),
                        )

                        panel1 = rs.OffsetSurface(panelS, -0.05, None, False, True)
                        all__panels.append(panel1)
                else:
                    print("prameters are not list")
        for i in tokeep:
            ref_ = Rhino.DocObjects.ObjRef(i).Brep()
            if type(ref_) == Brep:
                print(ref_)
                rs.OffsetSurface(ref_, 0.1, None, True, True)

        for p in range(len(all__panels)):
            listR = range(202, 255, 1)
            listb = range(50, 255, 5)
            brand = (random.sample(listb, 1))[0]
            rrand = (random.sample(listR, 1))[0]

            if brand == 255 and rrand == 255:
                grand = 255
                print("white")
            grand = brand - 50
            rs.ObjectColor(all__panels[p], (rrand, grand, brand))


gp = DrawGrid(10, 10)[0]
gprg = DrawGrid(10, 10)[1]


# Repeat the process until user needs.(by Pegah)
def CubeCreator(list_polyline):
    print("input: ", list_polyline)
    rs.HideObject(gp)
    pts = eto_UI.RequestBoundaryGenerator()
    if pts is None:
        print("NONE1")
        return None
    if pts is not None:

        # Get 4 points.
        pt1 = pts[0]
        pt2 = pts[1]
        pt3 = pts[2]
        pt4 = pts[3]

        # Create hidden lines to measure the angles;
        # because user should not be able to draw rectangles.
        # not being able to draw rectangle is the assignment.
        pt11 = rg.Point3d(rs.PointCoordinates(pt1))
        pt22 = rg.Point3d(rs.PointCoordinates(pt2))
        pt33 = rg.Point3d(rs.PointCoordinates(pt3))
        pt44 = rg.Point3d(rs.PointCoordinates(pt4))
        first_line = rg.Line(pt11, pt22)
        second_line = rg.Line(pt11, pt44)
        third_line = rg.Line(pt33, pt22)
        fourth_line = rg.Line(pt33, pt44)

        # Measuring the angle between first line and second line;
        # in order to identify geometry as a rectangle or not;
        # creating condition if it is a rectangle then user can draw
        if rs.Angle2(first_line, second_line) == (90, 270) and rs.Angle2(
            third_line, fourth_line
        ) == (90, 270):
            list_points = [pt1, pt2, pt3, pt4, pt1]
            polyline_ = rs.AddPolyline(list_points)
            list_polyline.append(polyline_)
            # print("appended to polylines")

        if len(list_polyline) < 2:
            return CubeCreator(list_polyline)
        boundryp = []
        if len(list_polyline) > 1:

            last_poly = list_polyline[-1]
            sel_last_poly = list_polyline[-2]
            print("last_poly => ", last_poly)
            print("sel_last_poly => ", sel_last_poly)
            # try:
            intersection = rs.CurveCurveIntersection(last_poly, sel_last_poly)
            # except:
            #     rs.DeleteObjects(list_polyline[-1])
            # print("press 1 and select points again to create rectangle")

            if intersection is None or intersection == 0:
                print("you should form a surface with intersection.")
                rs.DeleteObjects(list_polyline[-1])
                return CubeCreator(list_polyline)

            if intersection is not None and intersection != 0:
                # print("I have some intersections, now.")

                # Asking to exit the loop or continue.
                button = rs.GetInteger(ASK_FOR_END_OR_CONTINUE)
                if button != 0:
                    # print("continuing with selection...")

                    return CubeCreator(list_polyline)

            # Getting the boundry of the building from what use draw
            print("curve list: ", list_polyline)
            boundryp = rs.CurveBooleanUnion(list_polyline)
            if not boundryp:
                raise Exception("curve boolean union failed")

        # Hiding the polylinne for user because the intersected curve can be seen in next steps
        rs.HideObject(list_polyline)

        checkpt = CheckInBoundary(gp, boundryp)
        toremainpt = []
        toremainpt_rs = []
        toremovepr = []
        for index in range(len(gprg)):
            if checkpt[index] == 0:
                toremovepr.append(gp[index])
            if checkpt[index] == 1 or checkpt[index] == 2:
                toremainpt.append(gprg[index])
                print("to remain", toremainpt)
                toremainpt_rs.append(gp[index])
        # creating columns
        mptc = rs.XformTranslation([0, 0, 4 * HIGHT_Of_CUBES])
        toremainpt2 = rs.TransformObjects(toremainpt_rs, mptc, True)
        rs.HideObject(toremainpt2)
        axis = []
        for item in range(len(toremainpt_rs)):
            axis.append(rs.AddLine(toremainpt_rs[item], toremainpt2[item]))

        # creating cubes in the boundary from remained points:

        # creating points for rectangle
        foundSQ = CreatingPointsForRectangles(toremainpt)

        # drawing rectangle on ground and creating cubes in first level
        cubes0 = Cubes_initial(foundSQ)

        # cubes for other levels
        flatten_cubes = CubesForAllLevels(cubes0[0])
        fixedFlCubes = CubesForAllLevels(cubes0[1])
        copy_flattenCubes = rs.CopyObjects(flatten_cubes)
        copy_fixed = rs.CopyObjects(fixedFlCubes)
        rs.ShowObjects(fixedFlCubes)

        print("all", len(flatten_cubes))
        print("share", len(fixedFlCubes))

    return flatten_cubes, fixedFlCubes, axis, copy_flattenCubes, copy_fixed
    ################


# random cube removing event(by Pegah)
def Variouse_Seeds(flatten_cub, fixedFlCub, axiss):

    flatten_cubes = flatten_cub
    fixedFlCubes = fixedFlCub
    axis = axiss

    for a, b in zip(AllCenters(flatten_cubes), flatten_cubes):
        for i, c in zip(AllCenters(fixedFlCubes), fixedFlCubes):
            if a == i:

                flatten_cubes.remove(b)
    # getting the centers
    centroids = AllCenters(flatten_cubes)

    # creating attraction points
    userInputs = eto_UI.RequestCubeGenerator()
    attraction_point = userInputs[0]
    numberOfneighborstoDel = userInputs[1]
    # checking the number of neighbors by centroid points

    cubetodel = NeighborCheckXYZ(centroids, attraction_point, numberOfneighborstoDel)

    # deleting some cubes randomly and collect the remains
    remain_cubes = Delete_CollectRemains_cubes(flatten_cubes, cubetodel)
    # print(len(remain_cubes))

    # checking for floating cubs
    centers_remaun_cubes = []
    center_of_remaincubes = AllCenters(remain_cubes)
    if center_of_remaincubes is not None:
        centers_remaun_cubes.append(center_of_remaincubes[0])

    verticalch = []
    toadd = []
    dicube = {}
    for i in range(len(centers_remaun_cubes)):
        addcc = False
        cb = centers_remaun_cubes[i]
        X = round(cb.X)
        Y = round(cb.Y)
        Z = round(cb.Z)
        for j in range(len(centers_remaun_cubes)):
            if (
                round(centers_remaun_cubes[i].X, 1)
                == round(centers_remaun_cubes[j].X, 1)
                and round(centers_remaun_cubes[i].Y, 1)
                == round(centers_remaun_cubes[j].Y, 1)
                and centers_remaun_cubes[i].Z > centers_remaun_cubes[j].Z
            ):
                _disline = centers_remaun_cubes[i].Z - centers_remaun_cubes[j].Z

                roundeddis = round(_disline, 1)
                # print(roundeddis,"i=",i,"j=",j)

                if roundeddis > 6.0:
                    # print("found",roundeddis,"i=",i,"j=",j)
                    addcc = True
        if addcc == True:
            toadd.append(centers_remaun_cubes[i])

        # Creating dicts for each level of the nested dicts, that don't have one.
        if not (X in dicube):
            dicube[X] = {}
        if not (Y in dicube[X]):
            dicube[X][Y] = {}

        dicube[X][Y][Z] = cb

    for x in dicube.values():
        for y in x.values():
            if min(y.keys()) > 6:
                for c in y.values():
                    print("deleting cube:", c)
                    verticalch.append(c)

    # adding neighbors vertically to the floating cubes
    remain_cubes2 = []
    center_ = AllCenters(remain_cubes)
    for cube in remain_cubes:
        if center_ is not None:
            for addd in toadd:
                if center_[0] == addd:
                    xform = rs.XformTranslation([0, 0, -2 * (HIGHT_Of_CUBES)])
                    cubes1 = rs.TransformObjects(cube, xform, True)

        matched = False
        for delete in verticalch:
            if center_[0] == delete:
                matched = True
                rs.DeleteObject(cube)
        if matched == False:
            remain_cubes2.append(cube)

    centers_remain2_cubes = []
    center_of_remain2cubes = AllCenters(remain_cubes2)
    if center_of_remain2cubes is not None:
        centers_remain2_cubes.append(center_of_remain2cubes[0])
    # print( centers_remain2_cubes)
    newneighbers = []
    for i in range(len(centers_remain2_cubes)):
        checking = False
        for j in range(len(centers_remain2_cubes)):
            _disline = rg.Line(centers_remain2_cubes[i], centers_remain2_cubes[j])
            lendis = _disline.Length
            roundeddis = round(lendis)

            # checking neighbor in x y so they would not be alone
            if (roundeddis == 5.0 or roundeddis == 3.0) and round(
                centers_remain2_cubes[i].Z
            ) == round(centers_remain2_cubes[j].Z):
                # print("found a mate for:", centers_remain2_cubes[i], " @@@ ", centers_remain2_cubes[j] )
                checking = True
                break

        if checking == False:
            # print("want to be deleted again==========>",centers_remain2_cubes[i])
            newneighbers.append(centers_remain2_cubes[i])
    ########repeated vertical for floating###########
    centers_remaun_cubes = []
    center_of_remaincubes = AllCenters(remain_cubes)
    if center_of_remaincubes is not None:
        centers_remaun_cubes.append(center_of_remaincubes[0])

    verticalch = []
    toadd = []
    dicube = {}
    for i in range(len(centers_remaun_cubes)):
        addcc = False
        cb = centers_remaun_cubes[i]
        X = round(cb.X)
        Y = round(cb.Y)
        Z = round(cb.Z)
        for j in range(len(centers_remaun_cubes)):
            if (
                round(centers_remaun_cubes[i].X, 1)
                == round(centers_remaun_cubes[j].X, 1)
                and round(centers_remaun_cubes[i].Y, 1)
                == round(centers_remaun_cubes[j].Y, 1)
                and centers_remaun_cubes[i].Z > centers_remaun_cubes[j].Z
            ):
                _disline = centers_remaun_cubes[i].Z - centers_remaun_cubes[j].Z

                roundeddis = round(_disline, 1)
                # print(roundeddis,"i=",i,"j=",j)

                if roundeddis > 6.0:
                    # print("found",roundeddis,"i=",i,"j=",j)
                    addcc = True
        if addcc == True:
            toadd.append(centers_remaun_cubes[i])

        # Creating dicts for each level of the nested dicts, that don't have one.
        if not (X in dicube):
            dicube[X] = {}
        if not (Y in dicube[X]):
            dicube[X][Y] = {}

        dicube[X][Y][Z] = cb

    for x in dicube.values():
        for y in x.values():
            if min(y.keys()) > 6:
                for c in y.values():
                    print("deleting cube:", c)
                    verticalch.append(c)

    # adding neighbors vertically to the floating cubes
    remain_cubes2 = []
    center_ = AllCenters(remain_cubes)
    for cube in remain_cubes:
        if center_ is not None:
            for addd in toadd:
                if center_[0] == addd:
                    xform = rs.XformTranslation([0, 0, -2 * (HIGHT_Of_CUBES)])
                    cubes1 = rs.TransformObjects(cube, xform, True)

        matched = False
        for delete in verticalch:
            if center_[0] == delete:
                matched = True
                rs.DeleteObject(cube)
        if matched == False:
            remain_cubes2.append(cube)

    final_axis = makingFinalAxis(axis, remain_cubes2)

    remain_cubes2.extend(fixedFlCubes)
    rs.ShowObjects(remain_cubes2)
    return remain_cubes2, final_axis


# give oportunity to user to change the randomness or contineu(by Pegah)
def AskingUserSatisfaction(button, recubes, flattenC, fixed, ax):
    remain_cubes2 = recubes
    flatten_cub = flattenC
    fixedFlCub = fixed
    axiss = ax
    button2 = button

    ##returnto
    if button2 == 0:
        rs.HideObjects(remain_cubes2)
        explodedPoly = explode_polysurfaces(remain_cubes2)

        horizontal_surfca = check_Horizontal(explodedPoly)

        all_horizontal = horizontal_surfca[1]

        vertical1 = horizontal_surfca[0]

        dedup = DeletingDub(all_horizontal)
        floors = []
        for item in dedup:
            d = Rhino.DocObjects.ObjRef(item)
            s = Rhino.DocObjects.ObjRef.Brep(d)
            if s is not None:
                floors.append(s)
        floorL = rg.Brep.JoinBreps(floors, 0.001)
        DeletinginterioreW(vertical1)

        rs.HideObjects(vertical1)
        borderC = borderfloor(floorL)

        wallroom = Room_Selection(dedup)

        rs.ShowObjects(vertical1)
        roomw = []
        for rsss in wallroom:
            for rss in rsss:
                for r in rss:
                    roomw.append(r)

        walls_ = Deletingdup(vertical1, roomw)

        return vertical1, dedup, borderC[1]


#######################


# (by Pegah)
def Main():

    print("beginning Phase 1")
    phase1result = CubeCreator(list_polyline=[])
    if phase1result is not None:
        flattened_cube_is = phase1result[0]

        phase1resultV = Variouse_Seeds(
            copy.deepcopy(phase1result[0]),
            copy.deepcopy(phase1result[1]),
            copy.deepcopy(phase1result[2]),
        )

        button2 = rs.GetInteger(ASK_FOR_END_OR_CONTINUE)
        m = 1
        while button2 == 1:
            m = m + 10

            mform = rs.XformTranslation([((-10) * m), 0, 0])
            v = rs.TransformObjects(copy.deepcopy(phase1resultV[0]), mform, False)
            cubes = rs.CopyObjects(phase1result[3])
            cubesF = rs.CopyObjects(phase1result[4])
            rs.DeleteObjects(phase1resultV[1])
            phase1resultV = Variouse_Seeds(
                copy.deepcopy(cubes),
                copy.deepcopy(cubesF),
                copy.deepcopy(phase1result[2]),
            )

            button2 = rs.GetInteger("continu 0 or change randomness 1")
        print("beginning Phase 2")
        if button2 == 0:
            if v:
                rs.DeleteObjects(v)
            vs = AskingUserSatisfaction(
                button2,
                copy.deepcopy(phase1resultV[0]),
                copy.deepcopy(phase1result[0]),
                copy.deepcopy(phase1result[1]),
                copy.deepcopy(phase1result[2]),
            )
            if vs is not None:
                for b in vs[2]:

                    slab_b = offsetClosedCrv(b)
                    if slab_b is not None:
                        for i in slab_b:
                            slab = rs.ExtrudeCurveStraight(i, (0, 0, 0), (0, 0, -0.3))
                            if slab is not None:
                                rs.CapPlanarHoles(slab)
                                rs.ObjectColor(slab, (255, 255, 255))
                Facade_Construction(copy.deepcopy(vs[0]), copy.deepcopy(vs[2]))

    if phase1result is None:
        raise Exception("something impossible happened.")


Main()
