const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Checking ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');
const startIdx = 413; // Line 414
const endIdx = 801;   // Line 802

for (let i = startIdx; i <= endIdx; i++) {
    const line = lines[i];
    // Ignore empty lines
    if (line.trim().length === 0) continue;
    
    // Check indentation
    const indent = line.search(/\S/);
    if (indent < 8) {
        console.log(`FAIL at Line ${i+1}: Indent ${indent} spaces. Content: "${line}"`);
    } else if (indent % 4 !== 0) {
        console.log(`WARN at Line ${i+1}: Indent ${indent} spaces (not multiple of 4). Content: "${line}"`);
    }
}
console.log('Check complete.');
