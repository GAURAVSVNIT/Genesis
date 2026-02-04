const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Processing ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');

// Target range (1-indexed): 414 to 802
// 0-indexed: 413 to 801
const startIdx = 413;
const endIdx = 801; 

for (let i = startIdx; i <= endIdx; i++) {
    const line = lines[i];
    if (line.trim().length > 0) {
        lines[i] = '    ' + line;
    }
}

fs.writeFileSync(filePath, lines.join('\n'));
console.log('Smart indentation applied.');
