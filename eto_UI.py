from pprint import pprint


import Rhino
import System
from System.Collections.ObjectModel import ObservableCollection
import scriptcontext
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import math
import Rhino.UI
import Eto.Drawing as drawing
import Eto.Forms as forms

#(by Amerah)
class PointDialog(forms.Dialog[bool]):
    def __init__(self):
        self.pts = []

        # Initialize dialog box
        self.Title = "Cube Configurator"
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        # Create labels for the dialog
        self.pts_label = forms.Label(
            Text="Select 4 points from grid to create rectangle (clockwise and each time new rectangle should intersect the previous):"
        )
        # Create the buttons
        self.pts_select = forms.Button(Text="Select")
        # On button Clicks events
        self.pts_select.Click += self.SelectPtsButtonClick
        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.pts_label, self.pts_select)
        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout

    # Select points from Rhino and return to dialog
    def OnGetRhinoObjects(self, sender, e):
        objp = rs.GetObjects("Select points")
        for p in objp:
            self.pts.append(p)

    def SelectPtsButtonClick(self, sender, e):
        Rhino.UI.EtoExtensions.PushPickButton(self, self.OnGetRhinoObjects)

    def Get_list_pt(self):
        return self.pts

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)
        return None

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        if self.pts:
            self.Close(True)
        else:
            self.Close(False)

    ## End of Dialog Class ##

#(by Pegah)
class CubeDialog(forms.Dialog[bool]):
    # Dialog box Class initializer
    def __init__(self):
        # parameters to export

        self.neighborsToDelete = 1

        self.attractionPoint = "attraction"
        # Initialize dialog box
        self.Title = "Cube Configurator"
        self.Padding = drawing.Padding(10)
        self.Resizable = True

        # Create labels for the dialog
        self.toDelNeighbors_label = forms.Label(
            Text="How many neighbors do you want to delete for each cube?(1 or 2 recommended)"
        )
        self.attraction_label = forms.Label(Text="Select one attraction point :")

        self.toDelNeighbors_label_n = forms.Label(Text="numbers:")

        # Create the buttons

        self.attraction_select = forms.Button(Text="Select")

        # Create the input dialogs
        self.toDelNumber = forms.TextBox(Text=None)

        # On button Clicks events

        self.attraction_select.Click += self.SelectPtsButtonClick

        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.attraction_label, self.attraction_select)
        layout.AddRow(self.toDelNeighbors_label)

        layout.BeginVertical()
        layout.AddRow(
            self.toDelNeighbors_label,
            self.toDelNumber,
        )

        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout

    # Select points from Rhino and return to dialog
    def OnGetRhinoObjects(self, sender, e):
        self.attractionPoint = rs.GetPoint(
            "Select an attraction point to delete more cubes"
        )

    def SelectPtsButtonClick(self, sender, e):
        Rhino.UI.EtoExtensions.PushPickButton(self, self.OnGetRhinoObjects)

    def Save_neighbors_number(self):
        self.neighborsToDelete = int(self.toDelNumber.Text)

    # Get the value of the parameters

    def Get_number(self):
        return self.neighborsToDelete

    def Get_pt(self):
        return self.attractionPoint

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        self.Save_neighbors_number()

        if self.neighborsToDelete and self.attractionPoint:
            self.Close(True)
        else:
            self.Close(False)

    ## End of Dialog Class ##

#(by Pegah)
def RequestBoundaryGenerator():
    dialog = PointDialog()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        pts = dialog.Get_list_pt()

        return pts
    else:
        print("Invalid inputs! Please try again.")
        return None

#(by Pegah)
def RequestCubeGenerator():
    dialog = CubeDialog()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        neighborsToDelete = dialog.Get_number()
        # numberOfSingle_room = dialog.Get_number()
        # numberOfDouble_room = dialog.Get_number()
        attractionPoint = dialog.Get_pt()
        return (
            attractionPoint,
            neighborsToDelete,
            ##numberOfDouble_room,
        )
    else:
        print("Invalid inputs! Please try again.")
        return None, None, None

#(by Amerah)
class Corridors(forms.Dialog[bool]):
    def __init__(self):
        self.cubes = []

        # Initialize dialog box
        self.Title = "Corridors and vertical connections"
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        # Create labels for the dialog
        self.cubes_label = forms.Label(Text="Select Cubes to fix in all levels:")
        # Create the buttons
        self.cubes_select = forms.Button(Text="Select")
        # On button Clicks events
        self.cubes_select.Click += self.SelectBrepButtonClick
        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.cubes_label, self.cubes_select)
        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout
        # Select points from Rhino and return to dialog

    def OnGetRhinoObjects(self, sender, e):
        objc = rs.GetObjects("Select cubes")
        for c in objc:
            self.cubes.append(c)

    def SelectBrepButtonClick(self, sender, e):
        Rhino.UI.EtoExtensions.PushPickButton(self, self.OnGetRhinoObjects)

    def Get_list_cubes(self):
        return self.cubes

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)
        return None

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        if self.cubes:
            self.Close(True)
        else:
            self.Close(False)


def RequestFixedCubesGenerator():
    dialog = Corridors()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        cubes = dialog.Get_list_cubes()

        return cubes
    else:
        print("Invalid inputs! Please try again.")
        return None

#(by Amerah)
class SeedDialog(forms.Dialog[bool]):
    # Dialog box Class initializer
    def __init__(self):
        # parameters to export

        self.Seed = 1

        # Initialize dialog box
        self.Title = "Seed Configurator"
        self.Padding = drawing.Padding(10)
        self.Resizable = True

        # Create labels for the dialog
        self.Seed_label = forms.Label(Text="Put an integer for your random seed(0-20)")

        self.seed_label_n = forms.Label(Text="numbers:")

        # Create the input dialogs
        self.toDelNumber = forms.TextBox(Text=None)

        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.Seed_label)

        layout.BeginVertical()
        layout.AddRow(
            self.Seed_label,
            self.toDelNumber,
        )

        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout

    def Save_Seed_number(self):
        self.Seednum = int(self.toDelNumber.Text)

    # Get the value of the parameters

    def Get_number(self):
        return self.Seednum

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        self.Save_Seed_number()

        if self.Seednum:
            self.Close(True)
        else:
            self.Close(False)


def RequestSeedGenerator():
    dialog = SeedDialog()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        SeedToDelete = dialog.Get_number()

        return SeedToDelete
    else:
        print("Invalid inputs! Please try again.")
        return None, None, None

#(by Amerah)
class roomGenerator(forms.Dialog[bool]):
    def __init__(self):
        self.rooms = []

        # Initialize dialog box
        self.Title = "Selecting student rooms"
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        # Create labels for the dialog
        self.room_label = forms.Label(Text="Select rooms:")
        # Create the buttons
        self.rooms_select = forms.Button(Text="Select")
        # On button Clicks events
        self.rooms_select.Click += self.SelectBrepButtonClick
        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.room_label, self.rooms_select)
        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout
        # Select points from Rhino and return to dialog

    def OnGetRhinoObjects(self, sender, e):
        objr = rs.GetObjects("Select rooms")
        for c in objr:
            self.rooms.append(c)

    def SelectBrepButtonClick(self, sender, e):
        Rhino.UI.EtoExtensions.PushPickButton(self, self.OnGetRhinoObjects)

    def Get_list_rooms(self):
        return self.rooms

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)
        return None

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        if self.rooms:
            self.Close(True)
        else:
            self.Close(False)


def RequestroomGenerator():
    dialog = roomGenerator()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        Rooms = dialog.Get_list_rooms()

        return Rooms
    else:
        print("Invalid inputs! Please try again.")
        return None


# facade
# curtainWall#(by Pegah)
############################################################################
class curtainWall(forms.Dialog[bool]):
    def __init__(self):
        self.walls = []
        self.checkbox = False
        # Initialize dialog box
        self.Title = "Selecting walls for curtain wall"
        self.Padding = drawing.Padding(10)
        self.Resizable = True
        # Create labels for the dialog
        self.wall_label = forms.Label(Text="Select walls to convert to curtain wall:")
        # Create the buttons
        self.wall_select = forms.Button(Text="Select")
        # On button Clicks events
        self.wall_select.Click += self.SelectBrepButtonClick
        # checkbox
        self.m_checkbox = forms.CheckBox(Text="wide in middle")

        # Create the submit and abort button
        self.SubmitButton = forms.Button(Text="Submit")
        self.SubmitButton.Click += self.OnSubmitButtonClick
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCloseButtonClick

        # Create a table layout and add all the controls
        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(45, 10)
        layout.AddRow(self.wall_label, self.wall_select)
        layout.AddRow(self.m_checkbox, self.m_checkbox)
        layout.EndVertical()
        layout.AddRow(None)  # spacer

        layout.AddRow(self.SubmitButton, self.AbortButton)

        # Set the dialog content
        self.Content = layout
        # Select points from Rhino and return to dialog

    def OnGetRhinoObjects(self, sender, e):
        objr = rs.GetObjects("Select walls")
        for c in objr:
            self.walls.append(c)

    def SelectBrepButtonClick(self, sender, e):
        Rhino.UI.EtoExtensions.PushPickButton(self, self.OnGetRhinoObjects)

    def Get_list_walls(self):
        return self.walls

    def GetBool(self):
        if self.m_checkbox.Checked:
            self.checkbox = True

        return self.checkbox

    # Close button click handler
    def OnCloseButtonClick(self, sender, e):

        self.Close(True)
        return None

    # Submit button click handler
    def OnSubmitButtonClick(self, sender, e):
        if self.walls:
            self.Close(True)
        else:
            self.Close(False)


def RequestcurtainWall():
    dialog = curtainWall()
    rc = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    if rc:
        Cwalls = dialog.Get_list_walls()
        wide = dialog.GetBool()

        return Cwalls, wide
    else:
        print("Invalid inputs! Please try again.")
        return None


# panel class#(by Pegah)
################################################################################
class panels(object):

    # Initializer
    def __init__(self, panelS, size):
        self.m_name = panelS
        self.m_size = size

    @property
    def Name(self):
        return self.m_name

    @property
    def Size(self):
        return self.m_size


class PanelEtoListBoxDialog(forms.Dialog[bool]):

    # Initializer
    def __init__(self, collection):
        self.m_collection = collection
        # Initialize dialog box properties
        self.Title = "panel size"
        self.Padding = drawing.Padding(5)
        self.Resizable = True
        # Create a label control
        label = forms.Label()
        label.Text = "Select a panel:"
        # Create dynamic layout control
        layout = forms.DynamicLayout()
        layout.Padding = drawing.Padding(5)
        layout.Spacing = drawing.Size(5, 5)
        # Add controls to layout
        layout.AddRow(label)
        layout.AddRow(self.CreateListBox())
        layout.AddRow(None)  # spacer
        layout.AddRow(self.CreateButtons())
        # Set the dialog content
        self.Content = layout

    # Delegate function to retrieve the name of a Fruit object
    def panelselecting(self, panels):
        return panels.Name

    # Creates a ListBox control
    def CreateListBox(self):
        # Create labels
        listbox = forms.ListBox()
        listbox.Size = drawing.Size(100, 150)
        listbox.ItemTextBinding = forms.Binding.Delegate[panels, System.String](
            self.panelselecting
        )
        listbox.DataStore = self.m_collection
        listbox.SelectedIndex = 0
        self.m_listbox = listbox
        return self.m_listbox

    # OK button click handler
    def OnOkButtonClick(self, sender, e):
        self.m_selected_index = self.m_listbox.SelectedIndex
        self.Close(True)

    # Cancel button click handler
    def OnCancelButtonClick(self, sender, e):
        self.Close(False)

    # Create button controls
    def CreateButtons(self):
        # Create the default button
        self.DefaultButton = forms.Button(Text="OK")
        self.DefaultButton.Click += self.OnOkButtonClick
        # Create the abort button
        self.AbortButton = forms.Button(Text="Cancel")
        self.AbortButton.Click += self.OnCancelButtonClick
        # Create button layout
        button_layout = forms.DynamicLayout()
        button_layout.Spacing = drawing.Size(5, 5)
        button_layout.AddRow(None, self.DefaultButton, self.AbortButton, None)
        return button_layout

    # Returns the selected index
    @property
    def SelectedIndex(self):
        return self.m_selected_index


def panel_size():

    # Create and initialize collection
    collection = ObservableCollection[panels]()
    collection.Add(panels("panel1*1", [1, 1]))
    collection.Add(panels("panel1*2", [1, 2]))

    # Create and display dialog
    dlg = PanelEtoListBoxDialog(collection)
    rc = dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    if rc:
        # Print results
        panells = collection[dlg.SelectedIndex]

        return panells.Size
