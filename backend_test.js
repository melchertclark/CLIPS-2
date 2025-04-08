const http = require('http');
const fs = require('fs');
const path = require('path');

// Read port from backend_port.txt
function getBackendPort() {
  try {
    const portFile = path.join(__dirname, 'backend_port.txt');
    
    if (fs.existsSync(portFile)) {
      const port = parseInt(fs.readFileSync(portFile, 'utf8').trim(), 10);
      console.log(`Read backend port ${port} from file`);
      
      if (!isNaN(port) && port > 0) {
        return port;
      }
    }
    
    console.log('Port file not found or invalid, using default port 3000');
    return 3000;
  } catch (error) {
    console.error('Error reading backend port file:', error);
    return 3000;
  }
}

// Simple function to test backend connectivity using Node's http module
function testBackendConnection() {
  const port = getBackendPort();
  console.log(`Testing connection to backend on port ${port}...`);
  
  // Explicitly use 127.0.0.1 (IPv4) instead of localhost which might resolve to IPv6
  const options = {
    hostname: '127.0.0.1',
    port: port,
    path: '/api/status',
    method: 'GET'
  };
  
  const req = http.request(options, (res) => {
    console.log(`STATUS: ${res.statusCode}`);
    console.log(`HEADERS: ${JSON.stringify(res.headers)}`);
    
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      console.log('RESPONSE BODY:');
      console.log(data);
      console.log('\nSUCCESS: Backend is running and responding properly!');
    });
  });
  
  req.on('error', (e) => {
    console.error(`ERROR connecting to backend: ${e.message}`);
    console.log('Make sure the backend is running with: python3 backend/main.py');
  });
  
  req.end();
}

// Run the test
testBackendConnection();