I built a full-featured SQLite database explorer using PyQt5 that provides a visual interface for managing SQLite databases. This tool allows users to:

Browse database structure

View and edit table data

Create/modify tables

Add/delete records

Perform schema modifications

🔧 Key Features
Database Navigation
Tree view of all tables in the database

Table viewer with full data display

Context menus for quick actions

Table Operations
Create new tables with custom columns

Delete existing tables with confirmation

Add/remove columns through intuitive dialogs

Data Management
Insert new records with type-aware inputs

Delete rows with referential integrity checks

Edit data directly in table view

💻 Technical Implementation
Core Architecture
python
Copy
class DatabaseExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        # Split view with tree (left) and table (right)
        self.splitter = QSplitter(Qt.Horizontal)
        self.treeView = QTreeView()  # Shows database schema
        self.tableView = QTableView()  # Shows table data
Database Connection
python
Copy
def loadDatabase(self):
    filePath = QFileDialog.getOpenFileName(...)
    if filePath:
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(filePath)
        if self.db.open():
            self.populateTreeView(filePath)
Context-Aware UI
python
Copy
def showContextMenu(self, position):
    contextMenu = QMenu(self)
    if index.isValid():  # Table selected
        contextMenu.addAction("Add", self.addColumn)
        contextMenu.addAction("Delete", self.deleteTable)
    else:  # Empty space
        contextMenu.addAction("Add Table", self.addTable)
🛠️ Skills Demonstrated
Database Engineering

SQLite schema inspection/manipulation

CRUD operation implementation

Referential integrity handling

UI/UX Development

Context-sensitive menus

Form validation and user feedback

Responsive layout management

Software Design

Model-View architecture

Clean separation of concerns

Error handling and recovery

🌟 Technical Highlights
1. Dynamic Table Creation
python
Copy
def addTable(self):
    # Interactive dialog for table creation
    dialog = QDialog(self)
    # Dynamically generates inputs for each column
    for i in range(num_columns):
        column_name_input = QLineEdit()
        column_type_input = QComboBox()
        # Builds proper CREATE TABLE statement
        columns_str = ', '.join(columns)
        cursor.execute(f"CREATE TABLE {table_name} ({columns_str})")
2. Type-Aware Data Entry
python
Copy
def addColumn(self):
    # Gets column metadata
    cursor.execute(f"PRAGMA table_info({selected_table})")
    # Creates appropriate input for each data type
    for column_name, column_type in column_details:
        if column_type == "INT":
            input = QSpinBox()
        else:
            input = QLineEdit()
3. Safe Deletion Handling
python
Copy
def deleteTableRow(self, row):
    # Finds primary key dynamically
    cursor.execute(f"PRAGMA table_info({selected_table})")
    primary_key_column = next((col[1] for col in columns_info if col[5] == 1))
    # Confirms with user before deletion
    reply = QMessageBox.question(...)
    if reply == QMessageBox.Yes:
        cursor.execute(f"DELETE FROM {table} WHERE {pk} = ?", (value,))
🚀 Usage
bash
Copy
python sqlite_explorer.py
Click "Load Database" to open a SQLite file

Browse tables in the left panel

Right-click for table operations

Edit data directly in the table view
