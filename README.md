# PiNAS: Raspberry Pi Network Attached Storage Interface

A web-based interface for managing files on a Raspberry Pi or any network-attached storage (NAS) device. Built with FastAPI, SQLAlchemy, and Jinja2 templates, PiNAS allows users to browse, upload, and delete files and directories through a web interface.

## Features

- User authentication and session management
- File and directory browsing
- File upload functionality
- File and directory deletion
- Admin user management
- Configurable base directory for file operations
- Environment variable-based configuration

## Use Cases

- Simple file management for local directories
- Basic file sharing within a small team
- Educational tool for learning web development with FastAPI
- Lightweight alternative to more complex file management systems

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pinas.git
   cd pinas
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following content:
   ```
   SESSION_SECRET_KEY=your-secure-secret-key
   ADMIN_PASSWORD=your-secure-admin-password
   BASE_PATH=/path/to/your/base/directory
   ```

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

6. Open your browser and navigate to `http://127.0.0.1:8000`

## Usage

1. Log in with the default admin credentials (username: `admin`, password: `your-secure-admin-password`)
2. Browse files and directories in the configured base path
3. Upload new files using the upload form
4. Delete files or directories using the delete button
5. Register new users (admin functionality)

## Configuration

The application can be configured using environment variables:

- `SESSION_SECRET_KEY`: Secret key for session management
- `ADMIN_PASSWORD`: Password for the default admin user
- `BASE_PATH`: Base directory for file operations

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
