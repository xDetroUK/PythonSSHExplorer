from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from scapy.all import ARP, Ether, srp
import sys,os,paramiko
class SSHFileBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Device Browser")
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()
        self.device_list = QListView()
        self.model = QStandardItemModel()
        self.device_list.setModel(self.model)
        self.device_list.doubleClicked.connect(self.device_double_clicked)
        self.layout.addWidget(self.device_list)
        self.setLayout(self.layout)
        self.display_connected_devices()
        self.ssh = None  # Store the SSHClient instance

    def scan_network(self):
        ip_range = "192.168.1.1/24"  # Adjust based on your network configuration
        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=3, verbose=0)[0]
        devices = []
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})
        return devices
    
    def display_connected_devices(self):
        devices = self.scan_network()
        for device in devices:
            item = QStandardItem(f"IP: {device['ip']} - MAC: {device['mac']}")
            self.model.appendRow(item)

    def device_double_clicked(self, index):
        item = self.model.itemFromIndex(index)
        ip = item.text().split(" - ")[0].replace("IP: ", "").strip()
        username, okPressed1 = QInputDialog.getText(self, "Enter SSH credentials","Username:", QLineEdit.Normal, "")
        if okPressed1:
            password, okPressed2 = QInputDialog.getText(self, "Enter SSH credentials","Password:", QLineEdit.Password, "")
            if okPressed2:
                self.connect_ssh(ip, username, password)
                
    def connect_ssh(self, ip, username, password):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(ip, username=username, password=password)
            QMessageBox.information(self, "SSH Connection", "Successfully connected to " + ip)
            self.show_directory_listing()
        except paramiko.AuthenticationException:
            QMessageBox.critical(self, "SSH Connection Error", "Authentication failed. Please check your username and password.")
        except paramiko.SSHException as e:
            QMessageBox.critical(self, "SSH Connection Error", f"SSH error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "SSH Connection Error", f"An error occurred: {str(e)}")

    def show_directory_listing(self):
        try:
            self.tree_model.clear()
            root_item = QStandardItem('/')
            self.tree_model.appendRow(root_item)
            parent_items = {"/": root_item}

            # List both directories and files
            stdin, stdout, stderr = self.ssh.exec_command(f'find "/" -type d -o -type f')
            directory_listing = stdout.read().decode()
            entries = directory_listing.strip().split('\n')

            for entry in entries:
                entry_path = entry.strip()
                entry_name = entry_path.split("/")[-1]
                entry_item = QStandardItem(entry_name)
                parent_path = "/".join(entry_path.split("/")[:-1])
                parent_item = parent_items.get(parent_path, root_item)
                parent_item.appendRow(entry_item)
                parent_items[entry_path] = entry_item
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def show_context_menu(self, pos):
        item = self.tree_view.indexAt(pos)
        if not item.isValid():
            return

        context_menu = QMenu(self)

        edit_action = QAction("Add", self)
        edit_action.triggered.connect(self.add_item)
        context_menu.addAction(edit_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_item)
        context_menu.addAction(copy_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)
        context_menu.addAction(delete_action)

        context_menu.exec_(self.tree_view.mapToGlobal(pos))

    def add_item(self):
        selected_item = self.tree_view.currentIndex()
        if selected_item.isValid():
            # Get the full remote directory path
            remote_dir_path = self.get_remote_path(selected_item)

            if remote_dir_path:
                try:
                    # Open an SFTP connection using the SSHClient
                    sftp = self.ssh.open_sftp()

                    # Ask the user to select a local file
                    local_file_path, _ = QFileDialog.getOpenFileName(
                        self, "Select File to Upload", QDir.homePath()
                    )

                    if local_file_path:
                        # Get the file name from the local file path
                        file_name = os.path.basename(local_file_path)

                        # Create the remote file path by joining the remote directory and the file name
                        remote_file_path = os.path.join(remote_dir_path, file_name)

                        # Upload the selected file to the remote directory
                        sftp.put(local_file_path, remote_file_path)

                        sftp.close()

                        # Update the directory listing after the upload
                        self.show_directory_listing()

                        QMessageBox.information(
                            self,
                            "Upload Successful",
                            f"{file_name} uploaded successfully to {remote_dir_path}",
                        )

                except Exception as e:
                    QMessageBox.critical(self, "Upload Error", str(e))

    def get_remote_path(self, item_index):
        # Recursively build the remote file path from the selected item's index
        item = self.tree_model.itemFromIndex(item_index)
        if item is None:
            return None

        item_text = item.text()
        parent_index = item.parent().index() if item.parent() else QModelIndex()

        if parent_index.isValid():
            parent_path = self.get_remote_path(parent_index)
            if parent_path:
                return os.path.join(parent_path, item_text)
        else:
            return "/" + item_text

    def copy_item(self):
        selected_item = self.tree_view.currentIndex()
        if selected_item.isValid():
            item_text = self.tree_model.itemFromIndex(selected_item).text()

            # Get the full remote file path
            remote_file_path = self.get_remote_path(selected_item)

            if remote_file_path:
                try:
                    # Open an SFTP connection using the SSHClient
                    sftp = self.ssh.open_sftp()

                    # Check if the selected item is a directory
                    if sftp.stat(remote_file_path).st_mode & 0o40000:
                        # It's a directory, so recursively download it
                        local_dir_path = QFileDialog.getExistingDirectory(
                            self, "Select Destination Directory", QDir.homePath()
                        )

                        if local_dir_path:
                            self.copy_directory(sftp, remote_file_path, local_dir_path)
                            QMessageBox.information(
                                self,
                                "Copy Successful",
                                f"{item_text} directory copied to {local_dir_path}",
                            )
                    else:
                        # It's a file, so copy it directly
                        dest_file_path, _ = QFileDialog.getSaveFileName(
                            self, "Save File", QDir.homePath() + "/" + item_text
                        )

                        if dest_file_path:
                            sftp.get(remote_file_path, dest_file_path)
                            QMessageBox.information(
                                self,
                                "Copy Successful",
                                f"{item_text} copied to {dest_file_path}",
                            )

                    sftp.close()

                except Exception as e:
                    QMessageBox.critical(self, "Copy Error", str(e))

    # Rest of the code remains the same

    def copy_directory(self, sftp, remote_dir_path, local_dir_path):
        # Recursively copy a directory and its contents from the remote server to the local machine
        try:
            os.makedirs(local_dir_path, exist_ok=True)
            for item in sftp.listdir(remote_dir_path):
                remote_item_path = remote_dir_path + "/" + item
                local_item_path = os.path.join(local_dir_path, item)

                if sftp.stat(remote_item_path).st_mode & 0o40000:
                    # If it's a directory, create the local directory and copy its contents
                    os.makedirs(local_item_path, exist_ok=True)
                    self.copy_directory(sftp, remote_item_path, local_item_path)
                else:
                    # It's a file, so copy it directly
                    sftp.get(remote_item_path, local_item_path)

        except Exception as e:
            QMessageBox.critical(self, "Copy Error", str(e))

    def delete_item(self):
        selected_item = self.tree_view.currentIndex()
        if selected_item.isValid():
            item_text = self.tree_model.itemFromIndex(selected_item).text()

            # Get the full remote file path
            remote_file_path = self.get_remote_path(selected_item)

            if remote_file_path:
                try:
                    # Open an SFTP connection using the SSHClient
                    sftp = self.ssh.open_sftp()

                    # Check if the selected item is a directory
                    if sftp.stat(remote_file_path).st_mode & 0o40000:
                        # It's a directory, so recursively delete it
                        self.delete_directory(sftp, remote_file_path)
                    else:
                        # It's a file, so delete it directly
                        sftp.remove(remote_file_path)

                    sftp.close()

                    # Update the directory listing after deletion
                    self.show_directory_listing()

                    QMessageBox.information(
                        self,
                        "Delete Successful",
                        f"{item_text} deleted successfully",
                    )

                except Exception as e:
                    QMessageBox.critical(self, "Delete Error", str(e))

    def delete_directory(self, sftp, remote_dir_path):
        # Recursively delete a directory and its contents from the remote server
        try:
            for item in sftp.listdir(remote_dir_path):
                remote_item_path = remote_dir_path + "/" + item

                if sftp.stat(remote_item_path).st_mode & 0o40000:
                    # If it's a directory, delete its contents and then delete the directory itself
                    self.delete_directory(sftp, remote_item_path)
                else:
                    # It's a file, so delete it directly
                    sftp.remove(remote_item_path)

            # Delete the directory itself after deleting its contents
            sftp.rmdir(remote_dir_path)

        except Exception as e:
            QMessageBox.critical(self, "Delete Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SSHFileBrowser()
    window.show()
    sys.exit(app.exec_())
