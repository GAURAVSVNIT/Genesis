const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'api', 'v1', 'content.py');
console.log(`Processing ${filePath}`);

const lines = fs.readFileSync(filePath, 'utf8').split('\n');
const startIdx = 413; // 414th line (0-indexed)
const endIdx = 802;   // 803rd line (0-indexed)

const newLines = lines.map((line, idx) => {
    if (idx >= startIdx && idx <= endIdx) {
        if (line.trim().length > 0) {
            return '    ' + line;
        }
    }
    return line;
});

fs.writeFileSync(filePath, newLines.join('\n'));
console.log('Indentation fixed.');
