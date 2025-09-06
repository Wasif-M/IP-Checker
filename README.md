# DOT 5 - Advanced Bulk IP Checker

A powerful web-based tool for checking multiple IP addresses and proxy servers against a target URL. Built with FastAPI and modern web technologies.

## Features

- **Bulk IP Checking**: Test multiple IPs simultaneously
- **Multiple Formats**: Supports IP, IP:PORT, and user:pass@IP:PORT formats
- **Port Expansion**: Automatically tries common ports if none specified
- **Real-time Results**: Live status updates with ✅ real / ❌ fake indicators
- **CSV Export**: Download results for further analysis
- **Configurable**: Adjustable timeout, thread count, and port lists
- **Modern UI**: Beautiful dark theme interface

## Project Structure

```
dot5/
├─ server.py          # FastAPI backend server
├─ checker.py         # Core proxy checking logic
├─ requirements.txt   # Python dependencies
├─ README.md         # This file
└─ public/           # Frontend files
   ├─ index.html     # Main HTML interface
   ├─ style.css      # Styling
   └─ app.js         # Frontend JavaScript
```

## Installation & Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

### 5. Access the Application

Open your browser and navigate to: **http://localhost:8000**

## Usage

### Input Format

The tool accepts various IP formats:

- **IP only**: `192.168.1.1` (will try common ports)
- **IP with port**: `192.168.1.1:8080`
- **IP with authentication**: `user:password@192.168.1.1:3128`

### Configuration Options

- **Timeout**: Request timeout in seconds (default: 6)
- **Threads**: Maximum concurrent connections (default: 20)
- **Ports**: Comma-separated list of ports to try if none specified

### Running Checks

1. Paste your IP list into the textarea
2. Adjust settings if needed
3. Click "Run Check"
4. Monitor real-time results
5. Export to CSV when complete

## API Endpoints

### POST /api/check-bulk
Check multiple IPs against the target URL.

**Request Body:**
```json
{
  "ips": ["192.168.1.1", "10.0.0.1:8080"],
  "timeout": 6.0,
  "max_workers": 20,
  "try_ports": [80, 8080, 3128, 8000, 8888]
}
```

### POST /api/export-csv
Export results to CSV format.

**Request Body:**
```json
{
  "results": [...]
}
```

## Target URL

The application is configured to check against: **http://bathrooms-renovation.xyz/**

## Technical Details

- **Backend**: FastAPI with async support
- **Proxy Testing**: Uses both HEAD and GET requests for reliability
- **Concurrency**: ThreadPoolExecutor for parallel processing
- **User Agents**: Rotates between common browser user agents
- **Error Handling**: Comprehensive error reporting and fallback strategies

## Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Requests**: HTTP library for proxy testing
- **asyncio**: Asynchronous programming support

## Troubleshooting

### Common Issues

1. **"Error contacting server"**: Ensure the server is running and accessible
2. **Slow performance**: Reduce thread count or increase timeout
3. **Port conflicts**: Change the server port if 8000 is in use

### Performance Tips

- Use appropriate thread count for your network
- Adjust timeout based on proxy response times
- Consider network latency when setting timeouts

## License

This project is provided as-is for educational and testing purposes.

## Support

For issues or questions, check the console output for detailed error messages. 